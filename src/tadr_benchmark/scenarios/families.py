"""Finite deterministic family expansion into strict, individually hashed cases."""

from itertools import product
from pathlib import Path
from string import Formatter
from typing import Literal

from pydantic import Field, model_validator

from ..campaigns.loader import load_model
from ..models import Contract, Identifier, ScenarioSpec
from .expectations import make_scenario
from .recipe import recipe_from_id


class FamilyDefinition(Contract):
    family_id: Identifier
    family_version: Literal["1.0"]
    id_template: str
    axes: dict[Identifier, list[int | str]]

    @model_validator(mode="after")
    def exact_finite_axes(self):
        fields = []
        for _, name, spec, conversion in Formatter().parse(self.id_template):
            if name is not None:
                if not name.isidentifier() or spec or conversion:
                    raise ValueError("family templates accept plain finite axis names only")
                fields.append(name)
        if set(fields) != set(self.axes) or len(fields) != len(set(fields)):
            raise ValueError("family template and axes differ")
        size = 1
        for values in self.axes.values():
            if not values or len(values) != len(set(values)):
                raise ValueError("empty or duplicate family levels")
            size *= len(values)
        if size > 10000:
            raise ValueError("family expansion exceeds finite inventory limit")
        return self


class FamilyInventory(Contract):
    scenario_set_version: Literal["1.0"]
    families: list[FamilyDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_families(self):
        if len({f.family_id for f in self.families}) != len(self.families):
            raise ValueError("duplicate family identity")
        return self


def expand_families(inventory: FamilyInventory) -> list[ScenarioSpec]:
    scenarios = {}
    for family in sorted(inventory.families, key=lambda f: f.family_id):
        axes = sorted(family.axes)
        for values in product(*(family.axes[key] for key in axes)):
            identity = family.id_template.format_map(dict(zip(axes, values)))
            if identity in scenarios:
                raise ValueError("overlapping family scenario ID")
            scenarios[identity] = make_scenario(recipe_from_id(identity))
    return [scenarios[key] for key in sorted(scenarios)]


def load_family_scenarios(root: Path) -> list[ScenarioSpec]:
    scenarios = []
    for path in sorted((root / "scenarios" / "families").glob("*")):
        if path.suffix in {".json", ".yaml", ".yml"}:
            scenarios.extend(expand_families(load_model(path, FamilyInventory)))
    return scenarios
