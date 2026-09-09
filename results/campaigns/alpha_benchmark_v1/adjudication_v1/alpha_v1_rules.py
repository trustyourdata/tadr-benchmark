"""Approved V1 annotation overlay, derived solely from frozen design and contract.

This module never accepts reports or target observations. It does not change
scenario snapshots, scientific inputs, physical annotations or metric definitions.
"""
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP, localcontext

from tadr_benchmark.companions import VariantExpectations
from tadr_benchmark.evaluation.metrics import Opportunity
from tadr_benchmark.serialization import canonical_bytes, sha256

CONTRACT_BASIS = {
    'C1': {
        'name': 'Algorithm 1.0 category cap / implementation baseline 1.0.12',
        'rule': 'For each final Finding, category weight times severity base times canonical Finding confidence; sum per category; cap at 40 and emit category_cap only when the uncapped sum is strictly greater than 40. CRITICAL base=28; leakage weight=1.6; inference_mismatch weight=1.3.',
        'members': {'tadr/config/scoring.py':['CATEGORY_CAP','CATEGORY_WEIGHTS','SEVERITY_BASE'],
                    'tadr/contracts/enums.py':['Category','Severity'],
                    'tadr/core/scoring.py':['finding_penalty','score_findings']},
    },
    'C2': {
        'name': 'Pre-existing evidence confidence for the affected full-reference recipes',
        'rule': 'Full-scan equality leakage uses EXACT_FULL_SCAN base .97, full coverage, no parse penalty and no stability flag; support multiplier is 1 at n>=1000, .95 at n>=200, .85 at n>=50, else .70. Confidence rounds HALF_UP to two decimals before scoring: .97 at n=10000; .92 at n=200. Metadata inference presence uses .99 without a row penalty. Reciprocal-mapping leakage uses STATISTICAL .88 at full coverage and n>=1000, remaining below the category-cap threshold for one Finding.',
        'members': {'tadr/config/confidence.py':['BASE_CONFIDENCE','ROW_STABILITY','PRESENCE_CHECKS'],
                    'tadr/core/confidence.py':['finding_confidence','confidence_for_finding'],
                    'tadr/core/numeric_policy.py':['quantize','canonical_confidence'],
                    'tadr/checks/leakage.py':['evaluate'],
                    'tadr/checks/inference.py':['evaluate']},
    },
    'C3': {
        'name': 'Pre-existing event name heuristic and expected datetime coercion',
        'rule': 'DATE_NAMES includes event. A string column whose lower-case name contains a date-name token is a datetime candidate and receives expected_type=datetime independently of its reported inferred_type. This expected-type rule does not exempt identifier roles. For the existing non-null event_<integer> values, datetime coercion has zero successes and the full population supplies attempts and failures.',
        'members': {'tadr/analyzer/parsing.py':['DATE_NAMES','parse_datetime'],
                    'tadr/analyzer/type_inference.py':['datetime_candidate','expected_type'],
                    'tadr/analyzer/profiler.py':['_profile']},
    },
    'C4': {
        'name': 'Pre-existing schema.parse_failures applicability and severity',
        'rule': 'The expected datetime column is eligible for schema.parse_failures. A nonzero attempt population with failure fraction 1 is above the existing HIGH threshold .20 (LOW .01; MEDIUM .05), so column:event_key has a HIGH final Finding with full-scan counter population. No new confidence assertion is added to the annotation. The contract explains observed confidence .62 through STATISTICAL .88 and minimum parse factor .70, rounded HALF_UP.',
        'members': {'tadr/checks/applicability.py':['candidates'],
                    'tadr/checks/schema.py':['evaluate'],
                    'tadr/config/thresholds.py':['CHECK_THRESHOLDS'],
                    'tadr/config/confidence.py':['BASE_CONFIDENCE','MIN_PARSE_FACTOR'],
                    'tadr/core/confidence.py':['finding_confidence']},
    },
}

def contract_cap_annotations(scenario, original):
    """Limited cap annotation arithmetic, not a scoring oracle or target call."""
    recipe=scenario['generator_parameters']
    n=recipe['row_count']
    inferred=deepcopy(original['expected_category_caps'])
    basis=[]
    with localcontext() as ctx:
        ctx.prec=50
        leakage=[f for f in original['findings'] if f['check_id']=='leakage.target_direct']
        if leakage:
            assert len(leakage)==1 and leakage[0]['severity']=='CRITICAL'
            family,case=recipe['family'],recipe['case']
            if family=='leak' and case in {'mapping','bool_numeric_mapping'}:
                base=Decimal('.88'); branch='reciprocal mapping / STATISTICAL'
            else:
                assert (family=='leak' and case in {'equality','numeric_normalization','support49','support50','support200'}) or (family=='composite' and case in {'leak_missing','leak_inference'})
                base=Decimal('.97'); branch='full-scan equality / EXACT_FULL_SCAN'
            factor=next(Decimal(v) for minimum,v in ((1000,'1'),(200,'.95'),(50,'.85'),(0,'.70')) if n>=minimum)
            confidence=(base*factor).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
            if leakage[0]['confidence'] is not None:
                assert confidence==Decimal(str(leakage[0]['confidence']))
            uncapped=Decimal('1.6')*Decimal(28)*confidence
            if uncapped>40:
                inferred['leakage']=40.0
                basis.append({'category':'leakage','finding_count':1,'confidence':str(confidence),'uncapped_penalty':str(uncapped),'cap':40,'contract_basis_ids':['C1','C2'],'recipe_branch':branch,'full_reference_rows':n})
        inference=[f for f in original['findings'] if f['check_id']=='inference.missing_at_inference']
        assert all(f['severity']=='CRITICAL' and f['population']=='metadata' for f in inference)
        uncapped=len(inference)*Decimal('1.3')*Decimal(28)*Decimal('.99')
        if uncapped>40:
            inferred['inference_mismatch']=40.0
            basis.append({'category':'inference_mismatch','finding_count':len(inference),'confidence':'.99','uncapped_penalty':str(uncapped),'cap':40,'contract_basis_ids':['C1','C2'],'recipe_branch':'declared inference availability / EXACT_METADATA'})
    return inferred,basis

def correct_annotation(scenario, original, original_frame):
    """Inputs are design objects only; outputs preserve all physical opportunities."""
    sid=scenario['scenario_id']
    assert scenario['generator_parameters']['family'] not in {'sampling','scale'}
    assert original['variant_id']=='full_reference'
    corrected=deepcopy(original)
    frame=deepcopy(original_frame)
    changes=[]
    category_caps,derivation=contract_cap_annotations(scenario,original)
    if category_caps!=original['expected_category_caps']:
        corrected['expected_category_caps']=category_caps
        changes.append({'category':'category_cap_annotation_defect','old':original['expected_category_caps'],'corrected':category_caps,'contract_basis_ids':['C1','C2'],'derivation':derivation,'justification':'The existing scoring contract requires these caps for the frozen declared Findings and recipe support; an empty exact-cap expectation is incorrect.','scientific_execution_changed':False})
    if 'event_key' in scenario['expected_affected_columns'] or 'event_key' in scenario['task_parameters']['id_columns']:
        # All affected designs declare this string key; the value spelling is
        # fixed by generators.tabular and verified separately against sources.
        assert scenario['row_count']==10000
        assert scenario['generator_parameters']['representation'] in {'csv','pqstr'}
        assert not any(f['check_id']=='schema.parse_failures' and f['subject']=='column:event_key' for f in original['findings'])
        added={'check_id':'schema.parse_failures','subject':'column:event_key','severity':'HIGH','population':'full','confidence':None}
        corrected['findings'].append(added)
        corrected['absent_check_ids']=[c for c in corrected['absent_check_ids'] if c!='schema.parse_failures']
        strata={o['stratum'] for o in frame if o['track']=='normative' and o['check_id']=='schema.parse_failures'}
        assert len(strata)==1
        opportunity=Opportunity(opportunity_id='opportunity.'+sha256(canonical_bytes([sid,'normative','schema.parse_failures','column:event_key'])),scenario_id=sid,physical_defect_id=None,track='normative',check_id='schema.parse_failures',subject='column:event_key',positive=True,severity='HIGH',stratum=next(iter(strata)),matching_check_ids=['schema.parse_failures']).model_dump(mode='json')
        assert not any(o['opportunity_id']==opportunity['opportunity_id'] for o in frame)
        frame.append(opportunity)
        frame.sort(key=lambda o:o['opportunity_id'])
        changes.append({'category':'event_key_pinned_contract_frame_correction','old':{'finding':None,'check_explicitly_absent':'schema.parse_failures' in original['absent_check_ids'],'opportunity':None},'corrected':{'finding':added,'check_explicitly_absent':False,'opportunity':opportunity},'contract_basis_ids':['C3','C4'],'justification':'A pre-existing lexical date-name rule makes this a normative datetime-coercion Finding; legitimate identifier semantics remain a separate adverse practical specificity observation.','scientific_execution_changed':False,'physical_truth_changed':False,'primary_clean_control_membership_changed':False})
    VariantExpectations.model_validate(corrected)
    for o in frame: Opportunity.model_validate(o)
    assert [o for o in frame if o['track']=='controlled_condition']==[o for o in original_frame if o['track']=='controlled_condition']
    return corrected,frame,changes
