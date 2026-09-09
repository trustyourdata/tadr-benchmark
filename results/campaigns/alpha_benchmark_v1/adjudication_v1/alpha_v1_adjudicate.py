"""Reprocess immutable Alpha evidence with the explicitly approved V1 overlay."""
import builtins,copy,csv,json,sys,subprocess
sys.dont_write_bytecode=True
from collections import Counter,defaultdict
from pathlib import Path

_import=builtins.__import__
def no_target_import(name,*args,**kwargs):
    if name=='tadr' or name.startswith('tadr.'):
        raise AssertionError('Target code is forbidden during adjudication')
    return _import(name,*args,**kwargs)
builtins.__import__=no_target_import

from tadr_benchmark.serialization import canonical_bytes,sha256
from tadr_benchmark.models import CampaignManifest,ScenarioSpec,RunResult
from tadr_benchmark.companions import ScenarioExpectations,VariantExpectations,DiagnosticRecord
from tadr_benchmark.execution.attempts import AttemptRecord
from tadr_benchmark.evaluation.metrics import Opportunity,evaluate_frame,evaluate_scenario,aggregate_detection,ratio
from tadr_benchmark.reporting.queries import ReportInputs,table_rows,csv_bytes,TABLE_COLUMNS,coverage_cells,ratio_cells
from tadr_benchmark.instrumentation.environment import capture_environment
from tadr_benchmark.safety import scan_files,text_issues
from alpha_v1_rules import CONTRACT_BASIS,correct_annotation

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'campaigns/ALPHA_BENCHMARK_V1.yaml').is_file())
REVIEW=ROOT/'.work/reviews'
C=REVIEW/'alpha_execution/candidate'
OUT=REVIEW/'alpha_execution/adjudication_v1'
EXECUTION='a76bb9458b181500c7bfb9efefcfecfbb019b5a9'
PROCESSING='4887bd579d394de523bab0ccb227840d66447fd9'
WHEEL='a37ec8d336d16dbe4b7a7448071808daaf5e3e0ab03afe3bb7de0ce6882bc31d'
csv.field_size_limit(2**31-1)
def read(name): return json.loads((C/name).read_bytes())
def jsonlines(name): return [json.loads(v) for v in (C/name).read_bytes().splitlines() if v]
def table(name):
    with (C/'tables'/name).open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))
def inventory(): return {p.relative_to(C).as_posix():sha256(p.read_bytes()) for p in C.rglob('*') if p.is_file()}
def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def add_ratio(n,d): return ratio(n,d).model_dump(mode='json')

def detection_table(members):
    grouped=defaultdict(list)
    for fmt,variant,m in members:
        grouped[(m.track,m.check_id,m.stratum,fmt,variant,m.severity_cutoff)].append(m)
    result=[]
    names={'conditional_precision':'conditional_precision','conditional_recall':'conditional_recall','conditional_fpr':'conditional_fpr','scenario_detection':'scenario_detection','all_required_detected':'all_required','severity_correctness':'severity','detection_and_severity':'detection_severity','localization':'localization'}
    for (track,check,stratum,fmt,variant,cutoff),values in sorted(grouped.items()):
        m=aggregate_detection(values)
        row=dict(track=track,check_id=check,stratum=stratum,format=fmt,analysis_variant=variant,severity_cutoff=cutoff,**coverage_cells(m),**{k:getattr(m,k) for k in ('tp','fp','fn','tn')},**ratio_cells('end_to_end_detection_yield',m.end_to_end_detection_yield))
        for name,prefix in names.items(): row.update(ratio_cells(prefix,getattr(m,name)))
        row.update(out_of_frame_finding_ids=m.out_of_frame_finding_ids,mapped_detector_details=m.mapped_detector_details)
        result.append(row)
    return result

def summary(members,scenario_metrics,annotations,reports):
    results={}
    for track in ('normative','controlled_condition'):
        for cutoff in ('INFO','LOW'):
            for fmt in ('combined','csv','parquet'):
                group=[m for f,v,m in members if m.track==track and m.severity_cutoff==cutoff and (fmt=='combined' or f==fmt)]
                s={k:sum(getattr(m,k) for m in group) for k in ('tp','fp','fn','tn','planned_opportunities','evaluable_opportunities','planned_positive_opportunities')}
                results['/'.join((track,cutoff,fmt))]={**s,'conditional_precision':add_ratio(s['tp'],s['tp']+s['fp']),'conditional_recall':add_ratio(s['tp'],s['tp']+s['fn']),'conditional_fpr':add_ratio(s['fp'],s['fp']+s['tn']),'successful_report_coverage':add_ratio(s['evaluable_opportunities'],s['planned_opportunities']),'end_to_end_detection_yield':add_ratio(s['tp'],s['planned_positive_opportunities']) if track=='controlled_condition' else None,'severity_correctness':add_ratio(sum(m.severity_correctness.numerator for m in group),sum(m.severity_correctness.denominator for m in group))}
    vals=list(scenario_metrics.values())
    gates=[m['gates_and_suppression'] for m in vals]
    # Independently count exact expected Findings, severities, gates and suppression
    # directly from the corrected labels and original report fields.
    independent=Counter()
    for sid,label in annotations.items():
        rep=reports[sid]
        seen={(f['metadata']['check_id'],f['metadata']['subject_key']):f for f in rep['findings']}
        for f in label['findings']:
            actual=seen.get((f['check_id'],f['subject']))
            independent['expected_findings']+=1
            independent['matched_expected_findings']+=actual is not None
            independent['correct_expected_severity']+=actual is not None and actual['severity'].upper()==f['severity']
            if f['confidence'] is not None:
                independent['explicit_confidence_labels']+=1
                independent['correct_explicit_confidence']+=actual is not None and float(actual['confidence'])==f['confidence']
        gate_kind={'leakage':'direct_leakage','inference_mismatch':'missing_at_inference',None:'invalid_timestamp'}
        observed={(gate_kind.get(g['category'],'unknown'),float(g['value'])) for g in rep['score_breakdown']['caps_applied'] if g['type']=='hard_gate'}
        expected={(g['kind'],float(g['cap'])) for g in label['gates']}
        independent['gate_set_cells']+=1
        independent['correct_gate_sets']+=observed==expected
        independent['expected_gate_occurrences']+=len(expected)
        independent['matched_gate_occurrences']+=len(expected&observed)
        independent['unexpected_gate_occurrences']+=len(observed-expected)
        for s in label['suppressions']:
            independent['suppression_opportunities']+=1
            independent['correct_suppression']+=(s['winner'],s['subject']) in seen and (s['loser'],s['subject']) not in seen
    info=results['normative/INFO/combined']
    assert info['tp']==independent['matched_expected_findings']
    assert info['planned_positive_opportunities']==independent['expected_findings']
    assert info['severity_correctness']['numerator']==independent['correct_expected_severity']
    return {'whole_cell_normative_conformance':add_ratio(sum(m['normative_conformant'] for m in vals),len(vals)),
        'gate_correctness':add_ratio(sum(g['gate_correctness']['numerator'] for g in gates),len(gates)),
        'category_caps_correctness':add_ratio(sum(g['category_caps_correct'] for g in gates),len(gates)),
        'score_respects_gates':add_ratio(sum(g['score_respects_gates'] for g in gates),len(gates)),
        'suppression_correctness':add_ratio(sum(g['suppression_correctness']['numerator'] for g in gates),sum(g['suppression_correctness']['denominator'] for g in gates)),
        'out_of_frame_findings':sum(len(m['out_of_frame_finding_ids']) for m in vals),
        'independent_report_field_checks':dict(independent),'detection':results,
        'normative_scenario_detection':add_ratio(sum(m['normative']['scenario_detection']['numerator'] for m in vals),sum(m['normative']['scenario_detection']['denominator'] for m in vals)),
        'normative_all_required':add_ratio(sum(m['normative']['all_required_detected']['numerator'] for m in vals),sum(m['normative']['all_required_detected']['denominator'] for m in vals))}

def process():
    assert git('rev-parse','HEAD')==PROCESSING and not git('status','--porcelain')
    baseline=inventory()
    assert len(baseline)==1062 and baseline['checksums.sha256']=='6bfde18953a2a822218f1ad31f3e007ad809526e188374daf2b8ddc6daf1d498'
    for line in (C/'checksums.sha256').read_text().splitlines():
        digest,name=line.split('  ',1); assert baseline[name]==digest
    original_review=REVIEW/'ALPHA_BENCHMARK_V1_SCIENTIFIC_RESULT_REVIEW.md'
    history_hash=sha256(original_review.read_bytes())
    original_processing=read('processing_provenance.json')
    assert original_processing['execution_git_commit']==EXECUTION and original_processing['processing_git_commit']==PROCESSING
    scenarios={p.stem:json.loads(p.read_bytes()) for p in (C/'scenarios').glob('*.json')}
    labels={e['scenario_id']:e for e in read('expectations.json')}
    matrix=table('scenario_matrix.csv')
    original_annotations={}; corrected_annotations={}; old_frames={}; new_frames={}; corrections=[]
    # Construct the complete amendment set BEFORE opening any canonical reports.
    for row in matrix:
        if row['family'] in {'sampling','scale'}: continue
        sid=row['scenario_id']
        original=next(v for v in labels[sid]['normative'] if v['variant_id']=='full_reference')
        frame=json.loads(row['opportunity_frames'])['full_reference']
        corrected,new_frame,changes=correct_annotation(scenarios[sid],original,frame)
        original_annotations[sid]=original; corrected_annotations[sid]=corrected
        old_frames[sid]=frame;new_frames[sid]=new_frame
        if changes:
            corrections.append({'scenario_id':sid,'scenario_sha256':labels[sid]['scenario_sha256'],'variant':'full_reference',
                'original_annotation':original,'corrected_annotation':corrected,
                'original_normative_frame':[o for o in frame if o['track']=='normative'],
                'corrected_normative_frame':[o for o in new_frame if o['track']=='normative'],
                'physical_frame_sha256_unchanged':sha256(canonical_bytes([o for o in frame if o['track']=='controlled_condition'])),
                'changes':changes,'scientific_execution_changed':False})
    correction_counts=Counter(c['category'] for row in corrections for c in row['changes'])
    assert correction_counts=={'event_key_pinned_contract_frame_correction':68,'category_cap_annotation_defect':18}
    print(json.dumps({'design_only_annotation_derivation':'passed','corrections':correction_counts}),flush=True)
    runs=[RunResult.model_validate(v) for v in jsonlines('runs.jsonl')]
    attempts=[AttemptRecord.model_validate(v) for v in jsonlines('attempts.jsonl')]
    diagnostics=[DiagnosticRecord.model_validate_json(p.read_bytes()) for p in sorted((C/'diagnostics').glob('*.json'))]
    assert len(runs)==len(attempts)==578 and len(diagnostics)==72 and not jsonlines('failures.jsonl')
    assert all(a.selected_as_final_outcome and a.attempt_index==0 for a in attempts)
    assert sum(r.phase=='warmup' for r in runs)==13 and sum(r.phase=='measurement' for r in runs)==565
    reports={r.run_id:(C/'reports'/f'{r.run_id}.json').read_bytes() for r in runs}
    assert all(sha256(reports[r.run_id])==r.canonical_report_sha256 and r.benchmark_git_commit==EXECUTION and r.target_installation_artifact_sha256==WHEEL for r in runs)
    inputs=ReportInputs(CampaignManifest.model_validate(read('manifest.json')),[ScenarioSpec.model_validate(s) for s in scenarios.values()],runs,[],reports,attempts,[ScenarioExpectations.model_validate(e) for e in labels.values()],diagnostics)
    original_tables=table_rows(inputs)
    for name,rows in original_tables.items():
        assert csv_bytes(TABLE_COLUMNS[name],rows)==(C/'tables'/name).read_bytes(),name
    print(json.dumps({'original_tables_rederived':len(original_tables),'sampling_determinism_performance_and_clean_metrics':'byte-identical'}),flush=True)
    standard={r.scenario_id:r for r in runs if r.phase=='measurement' and r.repeat_index==0 and r.determinism_case_id=='standard' and r.scenario_id in original_annotations}
    assert set(standard)==set(original_annotations)
    decoded={sid:json.loads(reports[r.run_id]) for sid,r in standard.items()}
    old_members=[];new_members=[];old_metrics={};new_metrics={}
    matrix_new=copy.deepcopy(original_tables['scenario_matrix.csv'])
    practical=[]
    for sid,r in sorted(standard.items()):
        rep=decoded[sid]
        frames=[[Opportunity.model_validate(o) for o in f] for f in (old_frames[sid],new_frames[sid])]
        old=VariantExpectations.model_validate(original_annotations[sid]);new=VariantExpectations.model_validate(corrected_annotations[sid])
        old_metrics[sid]=evaluate_scenario(frames[0],old,rep)
        new_metrics[sid]=evaluate_scenario(frames[1],new,rep)
        original_matrix=next(x for x in original_tables['scenario_matrix.csv'] if x['scenario_id']==sid)
        assert old_metrics[sid]==original_matrix['scenario_metrics']['full_reference']
        assert old_metrics[sid]['controlled_condition']==new_metrics[sid]['controlled_condition']
        for cutoff in ('INFO','LOW'):
            before=evaluate_frame(frames[0],rep,cutoff=cutoff);after=evaluate_frame(frames[1],rep,cutoff=cutoff)
            assert [x for x in before if x.track=='controlled_condition']==[x for x in after if x.track=='controlled_condition']
            old_members.extend((r.source_format,r.analysis_variant,m) for m in before)
            new_members.extend((r.source_format,r.analysis_variant,m) for m in after)
        mm=next(x for x in matrix_new if x['scenario_id']==sid)
        mm['normative_expectations']=[corrected_annotations[sid]]
        mm['opportunity_frames']['full_reference']=new_frames[sid]
        mm['scenario_metrics']['full_reference']=new_metrics[sid]
        if len(new_frames[sid])!=len(old_frames[sid]):
            event=next(f for f in rep['findings'] if f['id']=='schema.parse_failures::column:event_key')
            practical.append({'scenario_id':sid,'logical_case_id':sid.rsplit('.',1)[0],'run_id':r.run_id,'canonical_report_sha256':r.canonical_report_sha256,'source_file_sha256':r.source_file_sha256,
                'observed_finding':event,'readiness':rep['readiness_score'],'total_risk':rep['total_risk'],'schema_category_risk':rep['category_risks']['schema'],
                'interpretation':'ADVERSE practical Alpha specificity result: legitimate event_<integer> identifiers; not physically malformed datetime values. Normatively required by the pre-existing event name heuristic.',
                'physical_truth_changed':False,'primary_clean_control_eligible':labels[sid]['primary_clean_control_eligible']})
    original_detection=detection_table(old_members);new_detection=detection_table(new_members)
    assert csv_bytes(TABLE_COLUMNS['detection_by_check.csv'],original_detection)==(C/'tables/detection_by_check.csv').read_bytes()
    for cutoff in ('INFO','LOW'):
        assert [r for r in original_detection if r['track']=='controlled_condition' and r['severity_cutoff']==cutoff]==[r for r in new_detection if r['track']=='controlled_condition' and r['severity_cutoff']==cutoff]
    before=summary(old_members,old_metrics,original_annotations,decoded)
    after=summary(new_members,new_metrics,corrected_annotations,decoded)
    for key in ('gate_correctness','score_respects_gates','suppression_correctness'):
        assert before[key]==after[key]
    for key in before['detection']:
        if key.startswith('controlled_condition'): assert before['detection'][key]==after['detection'][key]
    for item in corrections:
        sid=item['scenario_id']
        item['effect_on_derived_metrics']={'original':old_metrics[sid],'adjudicated':new_metrics[sid],
            'normative_opportunity_change':len(item['corrected_normative_frame'])-len(item['original_normative_frame']),
            'physical_opportunity_change':0}
    assert len(practical)==68 and len({p['logical_case_id'] for p in practical})==34
    assert not any(p['primary_clean_control_eligible'] for p in practical)
    remaining=[sid for sid,m in new_metrics.items() if not m['normative_conformant']]
    # Software controls use disposable copies, never saved as scientific reports.
    sid=practical[0]['scenario_id'];label=VariantExpectations.model_validate(corrected_annotations[sid]);frame=[Opportunity.model_validate(o) for o in new_frames[sid]]
    changed=copy.deepcopy(decoded[sid]);changed['findings']=[f for f in changed['findings'] if f['id']!='schema.parse_failures::column:event_key']
    assert not evaluate_scenario(frame,label,changed)['normative_conformant']
    changed=copy.deepcopy(decoded[sid]);next(f for f in changed['findings'] if f['id']=='schema.parse_failures::column:event_key')['severity']='low'
    assert not evaluate_scenario(frame,label,changed)['normative_conformant']
    cap_sid=next(i['scenario_id'] for i in corrections if any(c['category']=='category_cap_annotation_defect' for c in i['changes']))
    changed=copy.deepcopy(decoded[cap_sid]);changed['score_breakdown']['caps_applied']=[g for g in changed['score_breakdown']['caps_applied'] if g['type']!='category_cap']
    assert not evaluate_scenario([Opportunity.model_validate(o) for o in new_frames[cap_sid]],VariantExpectations.model_validate(corrected_annotations[cap_sid]),changed)['normative_conformant']
    print(json.dumps({'original_conformance':before['whole_cell_normative_conformance'],'adjudicated_conformance':after['whole_cell_normative_conformance'],'remaining_nonconformances':len(remaining),'normative_INFO':after['detection']['normative/INFO/combined'],'negative_software_controls':'passed'}),flush=True)
    if '--inspect' in sys.argv:
        return
    audit_inputs={name:(REVIEW/f'alpha_v1_{name}.json') for name in ('source_audit','contract_audit')}
    for name,path in audit_inputs.items():
        if not path.exists(): audit_inputs[name]=OUT/f'{name}.json'
    source_audit=json.loads(audit_inputs['source_audit'].read_bytes())
    contract_audit=json.loads(audit_inputs['contract_audit'].read_bytes())
    assert source_audit['source_hashes_verified']==370 and source_audit['original_report_hashes_verified']==578 and source_audit['original_diagnostics_verified']==72
    assert contract_audit['target_artifact_sha256']==WHEEL and contract_audit['verification']=='passed'
    source_event={x['scenario_id']:x for x in source_audit['event_key_sources']}
    assert all(source_event[p['scenario_id']]['malformed_identifier_values']==0 for p in practical)
    contract_basis={'target_installation_artifact_sha256':WHEEL,'target_algorithm_version':'1.0','target_baseline_revision':'1.0.12','rules':CONTRACT_BASIS,'static_member_verification':contract_audit,'basis_precedes_scientific_execution':True}
    rules_path=Path(__file__).with_name('alpha_v1_rules.py')
    provenance={'record_kind':'alpha_v1_annotation_adjudication_provenance','format_version':'1.0','scientific_execution_revision':EXECUTION,
        'benchmark_processing_revision':PROCESSING,'original_candidate_checksums_sha256':baseline['checksums.sha256'],
        'original_processing_provenance_sha256':baseline['processing_provenance.json'],'original_scientific_review_sha256':history_hash,
        'processor_artifacts':{'alpha_v1_adjudicate.py':sha256(Path(__file__).read_bytes()),'alpha_v1_rules.py':sha256(rules_path.read_bytes())},
        'processor_commit_status':'Supplemental operator scripts identified by content hashes; no new Git revision or commit is claimed.',
        'adjudication_processing_environment':capture_environment().model_dump(mode='json'),
        'scope':'Approved V1 annotation and interpretation correction only; original candidate remains ORIGINAL PREREGISTERED-LABEL RESULT.',
        'scientific_execution_changed':False,'target_imports':0,'scientific_invocations':0}
    assertions={'canonical_reports_unchanged':True,'source_hashes_unchanged':True,'attempt_ledger_unchanged':True,'physical_ground_truth_and_frames_unchanged':True,
        'physical_metrics_unchanged':True,'sampling_metrics_unchanged':True,'determinism_metrics_unchanged':True,'performance_metrics_unchanged':True,
        'format_comparisons_unchanged':True,'primary_clean_control_denominators_unchanged':True,'instrumentation_unchanged':True,'scientific_runspecs_unchanged':True,
        'practical_event_key_adverse_result_retained':True,'original_tables_rederived':len(original_tables),'software_counterexample_checks':3}
    preservation={'assertions':assertions,'original_candidate_file_hashes_before':baseline,'original_candidate_file_hashes_after':inventory(),
        'source_audit':source_audit,'report_hash_inventory_sha256':sha256(canonical_bytes({r.run_id:r.canonical_report_sha256 for r in sorted(runs,key=lambda r:r.run_id)})),
        'source_hash_inventory_sha256':sha256(canonical_bytes({x['scenario_id']:x['source_file_sha256'] for x in read('dataset_manifest.json')})),
        'attempts_sha256':baseline['attempts.jsonl'],'instrumentation_sha256':baseline['instrumentation.jsonl']}
    assert preservation['original_candidate_file_hashes_before']==preservation['original_candidate_file_hashes_after']
    critical=int(bool(remaining))
    verdict='NOT READY FOR FREEZE — FURTHER ADJUDICATION REQUIRED' if critical else 'READY FOR FREEZE REVIEW'
    results={'original_preregistered_label_result':before,'adjudicated_pinned_contract_result':after,'remaining_nonconformant_scenario_ids':remaining,
        'correction_counts':dict(correction_counts),'event_key_representation_cells':len(practical),'event_key_logical_pairs':len({p['logical_case_id'] for p in practical}),
        'remaining_issues':{'CRITICAL':critical,'IMPORTANT':2,'MINOR':1},'verdict':verdict}
    record={'adjudication_id':'ALPHA_BENCHMARK_V1.V1','format_version':'1.0','authorization':'Explicitly approved category-cap annotations and event_key contract/practical-semantics separation; no scientific reruns or physical-ground-truth changes.',
        'execution_revision':EXECUTION,'benchmark_processing_revision':PROCESSING,'original_annotation_artifact_sha256':baseline['expectations.json'],
        'original_scenario_matrix_sha256':baseline['tables/scenario_matrix.csv'],'contract_basis_artifact':'contract_basis.json',
        'original_result_label':'ORIGINAL PREREGISTERED-LABEL RESULT','corrected_result_label':'ADJUDICATED PINNED-CONTRACT RESULT',
        'corrections':corrections,'effect_on_derived_metrics':results,'scientific_execution_changed':False}
    artifacts={'adjudication.json':canonical_bytes(record),'contract_basis.json':canonical_bytes(contract_basis),'adjudication_provenance.json':canonical_bytes(provenance),
        'source_audit.json':canonical_bytes(source_audit),'contract_audit.json':canonical_bytes(contract_audit),
        'summary.json':canonical_bytes(results),'evidence_preservation.json':canonical_bytes(preservation),'practical_event_key.json':canonical_bytes(practical),
        'corrected_normative_annotations.json':canonical_bytes(corrected_annotations),'adjudicated_scenario_metrics.json':canonical_bytes(new_metrics),
        'tables/adjudicated_detection_by_check.csv':csv_bytes(TABLE_COLUMNS['detection_by_check.csv'],new_detection),
        'tables/adjudicated_scenario_matrix.csv':csv_bytes(TABLE_COLUMNS['scenario_matrix.csv'],matrix_new),
        'alpha_v1_adjudicate.py':Path(__file__).read_bytes(),'alpha_v1_rules.py':rules_path.read_bytes()}
    # Report generation is a separate deterministic presentation function.
    from alpha_v1_review import make_review
    presentation=Path(__file__).with_name('alpha_v1_review.py')
    artifacts['alpha_v1_review.py']=presentation.read_bytes()
    provenance['processor_artifacts']['alpha_v1_review.py']=sha256(presentation.read_bytes())
    artifacts['adjudication_provenance.json']=canonical_bytes(provenance)
    bundled_review=make_review(record,provenance,preservation,practical,scenarios)
    review=make_review(record,provenance,preservation,practical,scenarios,
        artifact_base='alpha_execution/adjudication_v1/',candidate_base='alpha_execution/candidate/',history_base='')
    artifacts['ADJUDICATION_REVIEW.md']=bundled_review.encode('utf-8')
    checksums=''.join(f'{sha256(raw)}  {name}\n' for name,raw in sorted(artifacts.items())).encode()
    artifacts['checksums.sha256']=checksums
    assert not text_issues(review)
    assert inventory()==baseline and sha256(original_review.read_bytes())==history_hash
    assert not git('status','--porcelain')
    if '--check' in sys.argv:
        assert {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}==set(artifacts)
        assert all((OUT/name).read_bytes()==raw for name,raw in artifacts.items())
        assert (REVIEW/'ALPHA_BENCHMARK_V1_ADJUDICATION_REVIEW.md').read_text(encoding='utf-8')==review
    else:
        assert not OUT.exists(), 'Existing adjudication is immutable; inspect instead of overwriting'
        for name,raw in artifacts.items():
            p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        assert not (REVIEW/'ALPHA_BENCHMARK_V1_ADJUDICATION_REVIEW.md').exists()
        (REVIEW/'ALPHA_BENCHMARK_V1_ADJUDICATION_REVIEW.md').write_text(review,encoding='utf-8',newline='\n')
    assert not scan_files(OUT,sorted(artifacts))
    assert all((OUT/name).read_bytes()==raw for name,raw in artifacts.items())
    assert inventory()==baseline and not git('status','--porcelain') and not git('diff','--check')
    print(json.dumps({'adjudication_artifacts':len(artifacts),'original_conformance':before['whole_cell_normative_conformance'],
        'adjudicated_conformance':after['whole_cell_normative_conformance'],'evidence_unchanged':True,'safety':'passed','remaining_issues':results['remaining_issues'],'verdict':verdict}),flush=True)

if __name__=='__main__':
    process()
