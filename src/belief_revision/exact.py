from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import combinations
from typing import Mapping
from .logic import Formula, is_satisfiable

class UnsatisfiableInputError(ValueError):
    """Raised when the new information is contradictory by itself."""

class InconsistentBeliefBaseError(ValueError):
    """Raised when th initial belief base is already inconsistent."""

def _subsets(items: tuple[Formula, ...]):
    """Yeild every subset in increasing-cardinality, stable input order."""
    for size in range(len(items) + 1):
        yield from combinations(items , size)

def _validate_base(base: tuple[Formula, ...]):
    if len(set(base)) != len(base):
        raise ValueError("Belief-base formulas must be structurally uniqe in this prototype.")


def conflict_kernels(
        base: tuple[Formula,...] | list[Formula],
        new_information: Formula,
)-> tuple[tuple[Formula,...],...]:

    items = tuple(base)
    _validate_base(items)

    if not is_satisfiable(items):
        raise InconsistentBeliefBaseError(
            "The initial belief base is inconsistent; repairing old conflict is out of scope."
        )

    if not is_satisfiable((new_information,)):
        raise UnsatisfiableInputError(
            "New information is incosistent by itself; no belief deletion can repair it."
        )

    kernels : list[tuple[Formula,...]] = []
    kernel_sets: list[frozenset[Formula]] = []

    for candidate in _subsets(items):
        candidate_set = frozenset(candidate)
        if any(kernel <= candidate_set for kernel in kernel_sets):
            continue
        if not is_satisfiable(candidate + (new_information,)):
            kernels.append(candidate)
            kernel_sets.append(candidate_set)

    return tuple(kernels)


def minimum_hitting_sets(
        base: tuple[Formula,...] | list[Formula],
        kernels: tuple[tuple[Formula,...],...] | list[tuple[Formula,...]],
        costs: Mapping[Formula, int | float | Decimal] | None = None,
)-> tuple[tuple[Formula,...],...]:

    items = tuple(base)
    _validate_base(items)
    kernels_tuple = tuple(tuple(kernel) for kernel in kernels)

    if not kernels_tuple:
        return ((),)

    base_set = frozenset(items)
    for kernel in kernels_tuple:
        if not kernel:
            raise ValueError("An empty conflict kernel means the input is unsatisfiable by itself.")
        if not frozenset(kernel) <= base_set:
            raise ValueError("Every kernel must be a subset of supplied belief base.")

    raw_cost: dict[Formula, Decimal] = {}
    for formula in items:
        supplied_cost = (costs or {}).get(formula, 1)
        try:
            cost = Decimal(str(supplied_cost))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f" deletion cost for {formula} must be numeric; got {supplied_cost!r}.") from exc
        if not cost.is_finite() or cost <= 0:
            raise ValueError(f"Deletin cost for {formula} must be finite and positive; got {supplied_cost}.")
        raw_cost[formula] = cost

        relevant = tuple(formula for formula in items if any(formula in k for k in kernels_tuple))
        best_cost : Decimal | None = None
        best_sets : list[tuple[Formula,...]] = []

    for deletion in _subsets(relevant):
        deletion_set = frozenset(deletion)
        if not all (deletion_set.intersection(kernel) for kernel in kernels_tuple):
            continue

        cost = sum((raw_cost[formula] for formula in deletion), Decimal("0"))
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_sets = [deletion]
        elif cost == best_cost:
            best_sets.append(deletion)
    if not best_sets:
        raise RuntimeError(" No hiting set exists for a non-empty family of finite kernels.")
    return tuple(best_sets)

@dataclass(frozen= True, slots= True)
class RevisionResult:

     kernels: tuple[tuple[Formula,...],...]
     optimal_deletions : tuple[tuple[Formula,...],...]
     outputs: tuple[tuple[Formula,...],...]


def exact_revision(
        base: tuple[Formula, ...] | list[Formula],
        new_information: Formula,
        costs: Mapping[ Formula, int| float| Decimal] | None = None,
) -> RevisionResult:

    items = tuple(base)
    _validate_base(items)
    kernels = conflict_kernels ( items , new_information)
    deletions = minimum_hitting_sets(items, kernels, costs)
    deletion_sets = tuple(frozenset(delta) for delta in deletions)

    outputs: list[tuple[Formula,...]] = []
    for deletion_set in deletion_sets:
        remaining = tuple(formula for formula in items if formula not in deletion_set)
        output = remaining if new_information in remaining else remaining + (new_information,)
        if not is_satisfiable(output):
            raise AssertionError("Internal error: returned revision is inconsistent.")
        outputs.append(output)

    return RevisionResult( kernels, deletions, tuple(outputs))