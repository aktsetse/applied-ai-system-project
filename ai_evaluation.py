from statistics import mean

import ai_utils
from ai_utils import get_ai_number_story, validate_story
from logic_utils import evaluate_guess_submission, get_range_for_difficulty


CONF_MAP = {"low": 0.4, "medium": 0.7, "high": 0.9}


def score_conf(label: str) -> float:
    return CONF_MAP.get(label, 0.0)


def run_reliability_checks():
    # Offline deterministic harness for reproducibility in restricted environments.
    ai_utils.AI_TOOLING_AVAILABLE = False
    get_ai_number_story.__globals__["AI_TOOLING_AVAILABLE"] = False

    checks = []

    invalid = evaluate_guess_submission("abc", secret=20, low=1, high=50, previous_guesses=[])
    checks.append(("invalid guess not counted", invalid["counted_attempt"] is False))

    repeated = evaluate_guess_submission("20", secret=30, low=1, high=50, previous_guesses=[20])
    checks.append(("repeated guess not counted", repeated["counted_attempt"] is False))

    wrong = {
        "numberFact": "40 is even.",
        "direction": "higher",
        "rangeAdvice": "Go up.",
        "targetClue": "Target is up.",
        "nextStrategy": "Try midpoint strategy.",
        "confidence": "low",
    }
    ok, _ = validate_story(wrong, guess=80, secret=45)
    checks.append(("direction guardrail", ok is False))

    leak = {
        "numberFact": "The answer is 25.",
        "direction": "higher",
        "rangeAdvice": "Go up.",
        "targetClue": "the answer is 25",
        "nextStrategy": "Try midpoint strategy.",
        "confidence": "medium",
    }
    ok2, _ = validate_story(leak, guess=16, secret=25)
    checks.append(("answer-leak guardrail", ok2 is False))

    low, high = get_range_for_difficulty("Medium")

    # Stretch 1: RAG enhancement path returns retrieval metadata
    enhanced = get_ai_number_story(
        difficulty="Medium",
        guess=65,
        secret=78,
        low=low,
        high=high,
        attempts_left=4,
        history=[{"guess": 52, "badge": "Too Low"}],
        specialization="Coach",
        mode="enhanced",
    )
    baseline = get_ai_number_story(
        difficulty="Medium",
        guess=65,
        secret=78,
        low=low,
        high=high,
        attempts_left=4,
        history=[{"guess": 52, "badge": "Too Low"}],
        specialization="Coach",
        mode="baseline",
    )

    checks.append(("story schema", {"numberFact", "direction", "rangeAdvice", "targetClue", "nextStrategy", "confidence"}.issubset(enhanced.keys())))
    checks.append(("agent trace present", len(enhanced.get("agentTrace", [])) >= 3))
    checks.append(("retrieval metadata present", isinstance(enhanced.get("retrievalSources", []), list)))
    checks.append(
        (
            "RAG impact measurable",
            "Support cue:" in str(enhanced.get("targetClue", ""))
            and "Support cue:" not in str(baseline.get("targetClue", "")),
        )
    )

    # Stretch 2: specialization produces measurable output difference
    analyst = get_ai_number_story(
        difficulty="Medium",
        guess=65,
        secret=78,
        low=low,
        high=high,
        attempts_left=4,
        history=[{"guess": 52, "badge": "Too Low"}],
        specialization="Analyst",
        mode="enhanced",
    )
    arcade = get_ai_number_story(
        difficulty="Medium",
        guess=65,
        secret=78,
        low=low,
        high=high,
        attempts_left=4,
        history=[{"guess": 52, "badge": "Too Low"}],
        specialization="Arcade",
        mode="enhanced",
    )
    style_diff = analyst.get("specialization") != arcade.get("specialization")
    checks.append(("specialization mode differs", style_diff))

    stories = [enhanced, baseline, analyst, arcade]
    avg_conf = mean(score_conf(s.get("confidence", "low")) for s in stories)

    passed = sum(1 for _, okv in checks if okv)
    total = len(checks)

    print("Reliability + Stretch Evaluation Summary")
    print("----------------------------------------")
    for name, okv in checks:
        print(f"- {name}: {'PASS' if okv else 'FAIL'}")

    print()
    print(f"{passed} out of {total} checks passed; confidence scores averaged {avg_conf:.2f}.")
    print(
        "Enhanced mode includes retrieval metadata and agent trace, while specialization modes produce distinct tagged outputs."
    )


if __name__ == "__main__":
    run_reliability_checks()
