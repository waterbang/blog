"""An executable, standard-library-only self-iteration scorer.

Run: python self_iteration_score.py

Objective: increase weighted task pass rate without losing any task that the
baseline passed. Scope: a fixed, deterministic evaluation contract.

IMPORTANT: score_iteration consumes receipts from a trusted evaluator. It does
not sandbox arbitrary agent code, authenticate receipts, or prove generalization.
The demo runner executes ONLY the trusted, local pure-function examples below.
Run untrusted candidates in an externally isolated process with enforced resource
limits, and construct their receipts outside the candidate's writable environment.
"""
from __future__ import annotations

import hashlib
import json
import math
import unittest
from dataclasses import dataclass, replace
from typing import Callable, Mapping
from types import MappingProxyType


@dataclass(frozen=True)
class Evaluation:
    artifact_id: str
    contract_id: str
    outcomes: Mapping[str, bool | None]  # None = evaluator could not establish a result
    checks: Mapping[str, bool | None]    # mandatory checks from the trusted evaluator
    evidence: Mapping[str, str]         # observed output or evaluator diagnostics


@dataclass(frozen=True)
class Contract:
    # suite_id binds fixtures, expected outputs, runner version, and environment.
    suite_id: str
    weights: Mapping[str, float]
    required_checks: tuple[str, ...]
    min_gain_pp: float = 1.0

    def __post_init__(self):
        if not self.suite_id or not self.weights or not self.required_checks:
            raise ValueError("A suite, tasks, and mandatory checks are required")
        if any(not isinstance(k, str) or not k for k in self.weights):
            raise ValueError("Task IDs must be nonempty strings")
        if any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0
               for w in self.weights.values()):
            raise ValueError("Every task weight must be finite and positive")
        if (any(not isinstance(k, str) or not k for k in self.required_checks)
                or len(set(self.required_checks)) != len(self.required_checks)):
            raise ValueError("Mandatory check names must be unique nonempty strings")
        if (type(self.min_gain_pp) not in (int, float)
                or not math.isfinite(self.min_gain_pp)
                or not 0 < self.min_gain_pp <= 100):
            raise ValueError("min_gain_pp must be in (0, 100]")
        scale = max(self.weights.values())
        if any(w / scale == 0 for w in self.weights.values()):
            raise ValueError("Weight range exceeds floating-point precision")
        object.__setattr__(self, "weights", MappingProxyType(
            {k: float(v) for k, v in self.weights.items()}))
        object.__setattr__(self, "required_checks", tuple(self.required_checks))
        object.__setattr__(self, "min_gain_pp", float(self.min_gain_pp))

    @property
    def id(self) -> str:
        data = {"scorer": "weighted-pass-no-regression-v1",
                "suite_id": self.suite_id, "weights": dict(self.weights),
                "required_checks": self.required_checks,
                "min_gain_pp": self.min_gain_pp}
        return hashlib.sha256(json.dumps(
            data, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()).hexdigest()


def score_iteration(
    baseline: Evaluation,
    candidate: Evaluation,
    contract: Contract,
) -> dict:
    """Return eligibility, gain in percentage points, and a promotion decision.

    -1 is an ineligibility sentinel, NOT a measurement of candidate quality.
    ERROR means insufficient/non-comparable evidence; REJECT means a measured
    contract violation. A valid score is always in [0, 100]. No rounding is used
    for the acceptance comparison.

    Configuration errors raise ValueError when constructing Contract. Missing or
    invalid run evidence fails closed. The baseline must pass mandatory checks.
    """
    weights = contract.weights
    required_checks = contract.required_checks
    min_gain_pp = contract.min_gain_pp
    contract_id = contract.id
    # Scaling avoids overflow in the weight sum.
    scale = max(weights.values())
    scaled = {k: w / scale for k, w in weights.items()}
    total_weight = math.fsum(scaled.values())

    def blocked(status: str, reason: str, ids: tuple[str, ...] = ()) -> dict:
        return {"status": status, "score": -1.0, "adopt": False,
                "reason": reason, "case_ids": ids}

    task_ids = set(weights)
    check_ids = set(required_checks)
    for name, report in (("baseline", baseline), ("candidate", candidate)):
        if not report.artifact_id or report.contract_id != contract_id:
            return blocked("ERROR", f"{name}: identity/contract mismatch")
        if set(report.outcomes) != task_ids or set(report.evidence) != task_ids:
            return blocked("ERROR", f"{name}: incomplete or unexpected task evidence")
        if set(report.checks) != check_ids:
            return blocked("ERROR", f"{name}: mandatory check set mismatch")
        if any(type(v) is not bool for v in report.outcomes.values()):
            return blocked("ERROR", f"{name}: unresolved or invalid task outcome")
        if any(type(v) is not bool for v in report.checks.values()):
            return blocked("ERROR", f"{name}: unresolved or invalid mandatory check")
        if any(not isinstance(v, str) or not v.strip()
               for v in report.evidence.values()):
            return blocked("ERROR", f"{name}: missing evidence text")

    if not all(baseline.checks.values()):
        return blocked("ERROR", "baseline does not satisfy mandatory checks")
    if not all(candidate.checks.values()):
        return blocked("REJECT", "candidate violates mandatory checks")

    regressions = tuple(k for k in weights
                        if baseline.outcomes[k] and not candidate.outcomes[k])
    if regressions:
        return blocked("REJECT", "previously passing tasks regressed", regressions)

    newly_passed = tuple(k for k in weights
                        if candidate.outcomes[k] and not baseline.outcomes[k])
    gain = 100.0 * (math.fsum(scaled[k] for k in newly_passed) / total_weight)
    quality = lambda report: 100.0 * (
        math.fsum(scaled[k] for k in weights if report.outcomes[k]) / total_weight)
    adopt = gain >= min_gain_pp
    return {"status": "ACCEPT" if adopt else "KEEP", "score": gain,
            "adopt": adopt, "baseline_quality": quality(baseline),
            "candidate_quality": quality(candidate), "newly_passed": newly_passed,
            "reason": "gain meets threshold" if adopt else "gain below threshold"}


# ----- Trusted, deterministic demonstration -----
# Requirements: trim whitespace, Unicode-casefold, remove empty strings and
# duplicates, preserve first occurrence, and do not mutate the input list.
CASES = {
    "ordinary": (["AI", "Rust"], ["ai", "rust"]),
    "duplicates": (["AI", "ai", "Rust"], ["ai", "rust"]),
    "empty_input": ([], []),
    "empty_items": (["", "AI"], ["ai"]),
    "keep_order": (["Rust", "AI"], ["rust", "ai"]),
    "trim": (["  AI  ", " Rust "], ["ai", "rust"]),
    "whitespace_only": (["  ", "AI"], ["ai"]),
    "unicode_casefold": (["Straße", "STRASSE"], ["strasse"]),
}
CHECKS = ("input_unchanged", "output_is_string_list")
WEIGHTS = {key: 1.0 for key in CASES}
SUITE_MANIFEST = {"cases": CASES, "runner": "trusted-demo-runner-v1",
                  "environment": "trusted-pure-function-demo-v1"}
SUITE_ID = hashlib.sha256(json.dumps(
    SUITE_MANIFEST, sort_keys=True, ensure_ascii=False, separators=(",", ":")
).encode()).hexdigest()
CONTRACT = Contract(SUITE_ID, WEIGHTS, CHECKS, min_gain_pp=1.0)


def old(tags: list[str]) -> list[str]:
    return list(dict.fromkeys(t.lower() for t in tags if t))


def partial(tags: list[str]) -> list[str]:
    return list(dict.fromkeys(t.strip().lower() for t in tags if t.strip()))


def good(tags: list[str]) -> list[str]:
    return list(dict.fromkeys(t.strip().casefold() for t in tags if t.strip()))


def regressing(tags: list[str]) -> list[str]:
    return sorted(good(tags))


def mutating(tags: list[str]) -> list[str]:
    tags[:] = good(tags)
    return tags


def crashing(tags: list[str]) -> list[str]:
    raise RuntimeError("candidate failure, not infrastructure failure")


def run_trusted_demo(
    fn: Callable[[list[str]], list[str]],
    contract: Contract = CONTRACT,
) -> Evaluation:
    """For the trusted functions in this file only; this is NOT a sandbox."""
    outcomes, evidence = {}, {}
    checks = {key: True for key in CHECKS}
    for key, (inputs, expected) in CASES.items():
        working_input = list(inputs)
        try:
            output = fn(working_input)
            outcomes[key] = output == expected
            evidence[key] = f"observed={output!r}; expected={expected!r}"
            checks["output_is_string_list"] &= (
                type(output) is list and all(type(x) is str for x in output))
        except Exception as exc:
            # An observed candidate exception is a failed task, not unknown data.
            outcomes[key] = False
            evidence[key] = f"candidate exception: {type(exc).__name__}: {exc}"
            checks["output_is_string_list"] = False
        checks["input_unchanged"] &= working_input == inputs
    return Evaluation(fn.__name__, contract.id, outcomes, checks, evidence)


def score(baseline: Evaluation, candidate: Evaluation,
          contract: Contract = CONTRACT) -> dict:
    return score_iteration(baseline, candidate, contract)


class ScorerTests(unittest.TestCase):
    def setUp(self):
        self.b = run_trusted_demo(old)
        self.c = run_trusted_demo(good)

    def test_actual_improvement(self):
        r = score(self.b, self.c)
        self.assertEqual((r["score"], r["adopt"]), (37.5, True))
        self.assertEqual((r["baseline_quality"], r["candidate_quality"]), (62.5, 100))

    def test_partial_improvement(self):
        self.assertEqual(score(self.b, run_trusted_demo(partial))["score"], 25.0)

    def test_equal_result_is_not_improvement(self):
        r = score(self.b, self.b)
        self.assertEqual((r["score"], r["status"]), (0.0, "KEEP"))

    def test_more_passes_with_regression_rejected(self):
        report = run_trusted_demo(regressing)
        self.assertEqual(sum(report.outcomes.values()), 7)
        r = score(self.b, report)
        self.assertEqual(r["score"], -1)
        self.assertEqual(r["case_ids"], ("keep_order",))

    def test_all_outputs_pass_but_invariant_fails(self):
        report = run_trusted_demo(mutating)
        self.assertEqual(sum(report.outcomes.values()), 8)
        self.assertEqual(score(self.b, report)["status"], "REJECT")

    def test_missing_case(self):
        outcomes = dict(self.c.outcomes)
        del outcomes["trim"]
        self.assertEqual(score(self.b, replace(self.c, outcomes=outcomes))["status"], "ERROR")

    def test_extra_case(self):
        outcomes = {**self.c.outcomes, "unexpected": True}
        self.assertEqual(score(self.b, replace(self.c, outcomes=outcomes))["status"], "ERROR")

    def test_unknown_outcome(self):
        outcomes = {**self.c.outcomes, "trim": None}
        self.assertEqual(score(self.b, replace(self.c, outcomes=outcomes))["status"], "ERROR")

    def test_candidate_exception_is_failure(self):
        report = run_trusted_demo(crashing)
        self.assertTrue(all(v is False for v in report.outcomes.values()))
        self.assertEqual(score(self.b, report)["status"], "REJECT")

    def test_contract_mismatch(self):
        self.assertEqual(score(self.b, replace(self.c, contract_id="different"))["status"], "ERROR")

    def test_unknown_guard(self):
        checks = {**self.c.checks, "input_unchanged": None}
        self.assertEqual(score(self.b, replace(self.c, checks=checks))["status"], "ERROR")

    def test_missing_guard(self):
        self.assertEqual(score(self.b, replace(self.c, checks={}))["status"], "ERROR")

    def test_missing_evidence(self):
        self.assertEqual(score(self.b, replace(self.c, evidence={}))["status"], "ERROR")

    def test_invalid_baseline(self):
        checks = {**self.b.checks, "input_unchanged": False}
        self.assertEqual(score(replace(self.b, checks=checks), self.c)["status"], "ERROR")

    def test_threshold_boundary(self):
        for threshold, expected in ((37.5, True), (37.5001, False)):
            contract = replace(CONTRACT, min_gain_pp=threshold)
            b = run_trusted_demo(old, contract)
            c = run_trusted_demo(good, contract)
            self.assertEqual(score(b, c, contract)["adopt"], expected)

    def test_invalid_configuration(self):
        invalid = [0, -1, float("nan"), float("inf"), True]
        for x in invalid:
            with self.subTest(weight=x), self.assertRaises(ValueError):
                replace(CONTRACT, weights={**WEIGHTS, "trim": x})
        for x in invalid + [101]:
            with self.subTest(threshold=x), self.assertRaises(ValueError):
                replace(CONTRACT, min_gain_pp=x)

    def test_nonboolean_outcome(self):
        outcomes = {**self.c.outcomes, "trim": 1}
        self.assertEqual(score(self.b, replace(self.c, outcomes=outcomes))["status"], "ERROR")

    def test_weighted_score(self):
        contract = replace(CONTRACT, weights={**WEIGHTS, "unicode_casefold": 3.0})
        b = run_trusted_demo(old, contract)
        c = run_trusted_demo(good, contract)
        self.assertEqual(score(b, c, contract)["score"], 50.0)

    def test_policy_changes_invalidate_old_receipts(self):
        for contract in (replace(CONTRACT, min_gain_pp=2.0),
                         replace(CONTRACT, weights={**WEIGHTS, "trim": 2.0})):
            self.assertNotEqual(contract.id, CONTRACT.id)
            self.assertEqual(score(self.b, self.c, contract)["status"], "ERROR")

    def test_contract_weights_are_immutable(self):
        with self.assertRaises(TypeError):
            CONTRACT.weights["trim"] = 9.0

    def test_exhaustive_four_task_decisions(self):
        ids = tuple(str(i) for i in range(4))
        contract = Contract("four-task-fixture", {k: 1.0 for k in ids}, ("safe",))
        def report(mask):
            return Evaluation(str(mask), contract.id,
                              {k: bool(mask & (1 << i)) for i, k in enumerate(ids)},
                              {"safe": True}, {k: "observed fixture outcome" for k in ids})
        for bmask in range(16):
            for cmask in range(16):
                b, c = report(bmask), report(cmask)
                r = score_iteration(b, c, contract)
                has_regression = any(b.outcomes[k] and not c.outcomes[k] for k in ids)
                gain = 25.0 * (sum(c.outcomes.values()) - sum(b.outcomes.values()))
                self.assertEqual(r["adopt"], not has_regression and gain >= 1.0)
                self.assertEqual(r["score"], -1.0 if has_regression else gain)

    def test_serializable_result(self):
        json.dumps(score(self.b, self.c), allow_nan=False)
        json.dumps(score(self.b, run_trusted_demo(regressing)), allow_nan=False)


if __name__ == "__main__":
    b = run_trusted_demo(old)
    for fn in (old, partial, good, regressing, mutating):
        c = run_trusted_demo(fn)
        result = score(b, c)
        print(f"{fn.__name__:>10}: {sum(c.outcomes.values())}/8 tasks; "
              f"score={result['score']:>5}; status={result['status']}", flush=True)
    unittest.main(argv=["self_iteration_score.py"], verbosity=1)
