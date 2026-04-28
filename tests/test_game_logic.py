from pathlib import Path

from ai_utils import get_number_fact, validate_story
from logic_utils import (
    evaluate_guess_submission,
    generate_secret,
    get_attempt_limit,
    get_range_for_difficulty,
    is_loss,
    is_win,
    new_stats,
    read_json_file,
    update_stats,
    write_json_file,
)


def test_target_number_generated_within_range():
    for difficulty in ["Easy", "Medium", "Hard"]:
        low, high = get_range_for_difficulty(difficulty)
        for _ in range(50):
            n = generate_secret(difficulty)
            assert low <= n <= high


def test_invalid_guess_does_not_count():
    out = evaluate_guess_submission("abc", secret=20, low=1, high=50, previous_guesses=[])
    assert out["counted_attempt"] is False


def test_repeated_guess_does_not_count():
    out = evaluate_guess_submission("20", secret=30, low=1, high=50, previous_guesses=[20])
    assert out["counted_attempt"] is False


def test_correct_win_detection():
    out = evaluate_guess_submission("30", secret=30, low=1, high=50, previous_guesses=[])
    assert is_win(out) is True


def test_correct_loss_detection():
    assert is_loss(attempts_used=get_attempt_limit("Easy"), attempt_limit=get_attempt_limit("Easy"), won=False) is True


def test_history_saves_correctly(tmp_path: Path):
    p = tmp_path / "history.json"
    payload = [{"difficulty": "Easy", "result": "win"}]
    write_json_file(p, payload)
    loaded = read_json_file(p, [])
    assert loaded == payload


def test_stats_update_correctly():
    stats = new_stats()
    stats = update_stats(stats, won=True, score=88, attempts_used=4)
    assert stats["games_played"] == 1
    assert stats["wins"] == 1
    assert stats["best_score"] == 88
    assert stats["average_attempts"] == 4.0


def test_theme_preference_saves_correctly(tmp_path: Path):
    p = tmp_path / "prefs.json"
    payload = {"theme": "dark"}
    write_json_file(p, payload)
    loaded = read_json_file(p, {"theme": "light"})
    assert loaded["theme"] == "dark"


def test_ai_response_does_not_reveal_target_number():
    payload = {
        "numberFact": "16 is a power of two.",
        "direction": "higher",
        "rangeAdvice": "Look above 16.",
        "targetClue": "The value sits in the upper half.",
        "nextStrategy": "Try midpoint of remaining range.",
        "confidence": "high",
    }
    ok, _ = validate_story(payload, guess=16, secret=25)
    assert ok is True


def test_ai_response_gives_correct_direction():
    payload = {
        "numberFact": "80 is divisible by 10.",
        "direction": "lower",
        "rangeAdvice": "Go below 80.",
        "targetClue": "Target is in lower side.",
        "nextStrategy": "Use midpoint from current lower band.",
        "confidence": "medium",
    }
    ok, _ = validate_story(payload, guess=80, secret=45)
    assert ok is True


def test_fallback_triggered_when_validation_fails():
    bad = {
        "numberFact": "The answer is 25",
        "direction": "higher",
        "rangeAdvice": "",
        "targetClue": "The answer is 25",
        "nextStrategy": "",
        "confidence": "low",
    }
    ok, reason = validate_story(bad, guess=16, secret=25)
    assert ok is False
    assert reason in {"target_revealed", "answer_phrase", "weak_strategy"}


def test_local_fact_lookup_uses_stored_fact():
    assert get_number_fact(65) == "65 is the product of 5 and 13."
    assert get_number_fact(89) == "89 is a prime number and also a Fibonacci number."


def test_local_fact_lookup_uses_math_fallback():
    assert get_number_fact(46) == "46 can be written as 2 x 23."
