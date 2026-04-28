import json
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DIFFICULTY_CONFIG: Dict[str, Dict[str, int]] = {
    "Easy": {"low": 1, "high": 50, "attempts": 8, "bonus": 0},
    "Medium": {"low": 1, "high": 100, "attempts": 7, "bonus": 10},
    "Hard": {"low": 1, "high": 500, "attempts": 10, "bonus": 25},
}

SAFE_FALLBACK_STORY = (
    "Your guess helped narrow the search. Use the higher/lower feedback and try a number "
    "near the middle of the remaining range."
)


def read_json_file(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json_file(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def now_ts() -> float:
    return time.time()


def get_range_for_difficulty(difficulty: str) -> Tuple[int, int]:
    cfg = DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["Medium"])
    return cfg["low"], cfg["high"]


def get_attempt_limit(difficulty: str) -> int:
    return DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["Medium"])["attempts"]


def get_difficulty_bonus(difficulty: str) -> int:
    return DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["Medium"])["bonus"]


def generate_secret(difficulty: str) -> int:
    low, high = get_range_for_difficulty(difficulty)
    return random.randint(low, high)


def parse_guess(raw: str, low: int, high: int) -> Tuple[bool, Optional[int], str]:
    if raw is None or raw.strip() == "":
        return False, None, "Enter a number first."
    try:
        guess = int(raw.strip())
    except ValueError:
        return False, None, "Invalid input. Please enter a whole number."
    if guess < low or guess > high:
        return False, None, f"Guess must be between {low} and {high}."
    return True, guess, ""


def get_badge(guess: int, secret: int) -> Tuple[str, str]:
    delta = abs(guess - secret)
    if guess == secret:
        return "Correct", "You nailed it."
    if delta <= 5:
        return "Very Close", "Very close. Adjust slightly."
    if guess < secret:
        return "Too Low", "Too low. Go higher."
    return "Too High", "Too high. Go lower."


def guess_direction(guess: int, secret: int) -> str:
    if guess == secret:
        return "correct"
    return "higher" if guess < secret else "lower"


def evaluate_guess_submission(raw_guess: str, secret: int, low: int, high: int, previous_guesses: List[int]) -> Dict[str, object]:
    ok, guess, err = parse_guess(raw_guess, low, high)
    if not ok:
        return {
            "valid": False,
            "counted_attempt": False,
            "repeated": False,
            "message": err,
            "guess": None,
            "badge": "Invalid",
            "direction": "",
        }

    assert guess is not None
    if guess in previous_guesses:
        return {
            "valid": True,
            "counted_attempt": False,
            "repeated": True,
            "message": f"You already guessed {guess}.",
            "guess": guess,
            "badge": "Repeated",
            "direction": "",
        }

    badge, msg = get_badge(guess, secret)
    return {
        "valid": True,
        "counted_attempt": True,
        "repeated": False,
        "message": msg,
        "guess": guess,
        "badge": badge,
        "direction": guess_direction(guess, secret),
    }


def is_win(guess_result: Dict[str, object]) -> bool:
    return guess_result.get("badge") == "Correct"


def is_loss(attempts_used: int, attempt_limit: int, won: bool) -> bool:
    return (not won) and attempts_used >= attempt_limit


def build_range_from_history(low: int, high: int, history: List[Dict[str, object]]) -> Tuple[int, int]:
    min_bound = low
    max_bound = high
    for row in history:
        guess = int(row["guess"])
        badge = str(row["badge"])
        if badge == "Too Low":
            min_bound = max(min_bound, guess + 1)
        elif badge == "Too High":
            max_bound = min(max_bound, guess - 1)
        elif badge == "Very Close":
            min_bound = max(min_bound, guess - 5)
            max_bound = min(max_bound, guess + 5)
    if min_bound > max_bound:
        return low, high
    return min_bound, max_bound


def fallback_story(min_bound: int, max_bound: int, direction: str, attempts_left: int) -> Dict[str, object]:
    midpoint = (min_bound + max_bound) // 2
    return {
        "numberFact": "Numbers become easier to solve when you keep shrinking the possible range.",
        "direction": direction,
        "rangeAdvice": f"Current practical range is {min_bound} to {max_bound}.",
        "targetClue": "The target is still hidden inside that range.",
        "nextStrategy": (
            f"You have {attempts_left} attempts left. Try near {midpoint}."
            if attempts_left <= 3
            else "Use midpoint strategy to split the remaining range efficiently."
        ),
        "confidence": "medium",
    }


def calculate_score(difficulty: str, attempts_used: int, hint_uses: int, elapsed_seconds: float, won: bool) -> int:
    if not won:
        return 0
    base = 100 + get_difficulty_bonus(difficulty)
    wrong_guess_penalty = max(0, attempts_used - 1) * 8
    hint_penalty = hint_uses * 4
    time_penalty = min(20, int(elapsed_seconds // 12))
    efficiency_bonus = max(0, (get_attempt_limit(difficulty) - attempts_used) * 2)
    return max(5, base - wrong_guess_penalty - hint_penalty - time_penalty + efficiency_bonus)


def new_stats() -> Dict[str, float]:
    return {
        "games_played": 0,
        "wins": 0,
        "losses": 0,
        "win_percentage": 0.0,
        "current_streak": 0,
        "best_streak": 0,
        "best_score": 0,
        "average_attempts": 0.0,
        "total_attempts": 0,
    }


def update_stats(stats: Dict[str, float], won: bool, score: int, attempts_used: int) -> Dict[str, float]:
    s = dict(stats)
    s["games_played"] += 1
    s["total_attempts"] += attempts_used
    if won:
        s["wins"] += 1
        s["current_streak"] += 1
        s["best_streak"] = max(s["best_streak"], s["current_streak"])
        s["best_score"] = max(s["best_score"], score)
    else:
        s["losses"] += 1
        s["current_streak"] = 0
    s["win_percentage"] = round((s["wins"] / s["games_played"]) * 100, 2) if s["games_played"] else 0.0
    s["average_attempts"] = round(s["total_attempts"] / s["games_played"], 2) if s["games_played"] else 0.0
    return s


def build_win_note(difficulty: str, attempts_used: int, hint_uses: int) -> str:
    hint_text = "without AI hints" if hint_uses == 0 else f"with {hint_uses} AI hint(s)"
    return (
        f"Excellent work! You guessed the number in {attempts_used} attempts on {difficulty} mode, {hint_text}. "
        "You used each clue to narrow the range and make smarter guesses. That is a strong strategy."
    )
