from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Mapping


class Formula:
    """Base class for immutable propositional formulas."""

@dataclass(frozen=True , slots= True)
class Var(Formula):
    name : str

    def __post_init__(self)-> None:
        if not self.name or not self.name.strip():
            raise ValueError("A proposition variable needs a non-empty name.")

    def __str__(self):
        return self.name


@dataclass(frozen=True, slots= True)
class BoolConst(Formula):
    value : bool

    def __str__(self):
        return "T" if self.value else "⊥"


@dataclass(frozen=True, slots=True)
class Not(Formula):
    operand: Formula

    def __str__(self):
        return f"¬({self.operand})"


@dataclass(frozen=True, slots=True)
class And(Formula):
    left: Formula
    right: Formula

    def __str__(self):
        return f"({self.left} ∧ {self.right})"


@dataclass(frozen=True, slots=True)
class Or(Formula):
    left: Formula
    right: Formula
    
    def __str__(self):
        return f"({self.left} ∨ {self.right})"


@dataclass(frozen=True, slots=True)
class Implies(Formula):
    left: Formula
    right: Formula
    
    def __str__(self) -> str:
        return f"({self.left} → {self.right})"


def variables(formula: Formula) -> frozenset[str]:
    """Return the names of all propositional variables in 'formula'."""

    if isinstance(formula, Var):
        return frozenset((formula.name,))
    if isinstance(formula, BoolConst):
        return frozenset()
    if isinstance(formula, Not):
        return variables(formula.operand)
    if isinstance(formula, (And, Or, Implies)):
        return variables(formula.left) | variables(formula.right)
    raise  TypeError(f"Unsupported formula node : {type(formula).__name__}")

def evaluate(formula : Formula, assignment: Mapping[str, bool]) -> bool:
    """Evaluate a formula under a compelete or partial variable assignment.
    A missing variable raises 'KeyErorr' instead of silently choosing a value."""

    if isinstance(formula, Var):
        try:
            return bool(assignment[formula.name])
        except KeyError as exc:
            raise KeyError(f" No truth value suplied for variable {formula.name!r}.") from exc
    if isinstance(formula, BoolConst):
        return formula.value
    if isinstance(formula, Not):
        return not evaluate(formula.operand , assignment)
    if isinstance(formula , And):
        return evaluate(formula.left, assignment) and evaluate(formula.right , assignment)
    if isinstance(formula , Or):
        return evaluate(formula.left, assignment) or evaluate(formula.right , assignment)
    if isinstance(formula , Implies):
        return (not evaluate(formula.left, assignment)) or evaluate(formula.right , assignment)
    raise TypeError(f"Unsupported formula node: {type(formula).__name__}")

def is_satisfiable(formulas: tuple[Formula, ...]| list[Formula]) -> bool:

    formula_tuple = tuple(formulas)
    names = sorted(set().union(*(variables(formula) for formula in formula_tuple)))

    for values in product((False , True), repeat= len(names)):
        assignment = dict(zip(names, values, strict= True))
        if all (evaluate(formula , assignment) for formula in formula_tuple):
            return True
    return False

def is_consistent(formulas: tuple[Formula, ...] | list[Formula]) -> bool:
    return is_satisfiable(formulas)