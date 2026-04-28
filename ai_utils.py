import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from logic_utils import build_range_from_history, fallback_story

load_dotenv()
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_TOOLING_AVAILABLE = bool(OPENAI_API_KEY and OpenAI is not None)

FALLBACK_TEXT = (
    "Your guess helped narrow the search. Use the higher/lower feedback and try a number near the middle of the remaining range."
)

DOC_DIR = Path("assets/docs")

SPECIALIZATION_MODES = {
    "Analyst": "Use concise analytical language with explicit ranges and midpoint strategy.",
    "Coach": "Use motivational but concise language and keep strategy actionable.",
    "Arcade": "Use playful game tone while keeping strategy clear and brief.",
}

SPECIAL_NUMBER_FACTS = {
    1: "1 is the only positive integer that is neither prime nor composite.",
    2: "2 is the only even prime number.",
    3: "3 is the first odd prime number.",
    4: "4 is the first nontrivial perfect square.",
    5: "5 is the number of fingers on one hand.",
    6: "6 is the smallest perfect number because 1 + 2 + 3 equals 6.",
    7: "7 is a prime number often called lucky.",
    8: "8 is 2 cubed.",
    9: "9 is the square of 3.",
    10: "10 is the base of the decimal number system.",
    11: "11 is the smallest two-digit prime number.",
    12: "12 is a highly composite number with six positive divisors.",
    13: "13 is a prime number often linked with superstition.",
    16: "16 is the square of 4.",
    18: "18 is the legal adult age in many countries.",
    20: "20 is the number of fingers and toes on a typical human body.",
    21: "21 is a Fibonacci number and a triangular number.",
    24: "24 is the number of hours in a day.",
    25: "25 is the square of 5.",
    27: "27 is 3 cubed.",
    28: "28 is a perfect number because 1 + 2 + 4 + 7 + 14 equals 28.",
    30: "30 is the number of days in several calendar months.",
    32: "32 equals 2 to the 5th power.",
    36: "36 is the square of 6.",
    40: "40 is common in periods of time, like 40 weeks of pregnancy.",
    42: "42 is popularly known as the answer to life in science fiction.",
    49: "49 is the square of 7.",
    50: "50 is exactly half of 100.",
    60: "60 is the base of historical time measurement for minutes and seconds.",
    64: "64 is both 8 squared and 2 to the 6th power.",
    65: "65 is the product of 5 and 13.",
    72: "72 has many divisors and appears in geometry and time cycles.",
    81: "81 is the square of 9.",
    88: "88 is often used as a symbol of good fortune in some cultures.",
    89: "89 is a prime number and also a Fibonacci number.",
    90: "90 is a right angle in degree measure.",
    96: "96 is divisible by 12 and 8, making it useful in fractions.",
    99: "99 is one less than 100 and has repeating digits.",
    100: "100 is the square of 10.",
}


def _is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _smallest_factor(n: int) -> int:
    i = 2
    while i * i <= n:
        if n % i == 0:
            return i
        i += 1
    return 0


def get_number_fact(n: int) -> str:
    fact = SPECIAL_NUMBER_FACTS.get(n)
    if fact:
        return fact

    root = int(n ** 0.5)
    if root * root == n:
        return f"{n} is a perfect square."
    if _is_prime(n):
        return f"{n} is a prime number."
    factor = _smallest_factor(n)
    if factor:
        return f"{n} can be written as {factor} x {n // factor}."
    if n % 2 == 0:
        return f"{n} is an even number."
    return f"{n} is an odd number."


def _load_docs() -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    if DOC_DIR.exists():
        for p in sorted(DOC_DIR.glob("*.txt")):
            try:
                content = p.read_text(encoding="utf-8").strip()
                if content:
                    docs.append({"source": p.name, "content": content})
            except Exception as exc:
                logger.warning("failed loading doc %s: %s", p, exc)
    return docs


def _simple_retrieve_docs(query_terms: List[str], k: int = 2) -> List[Dict[str, str]]:
    docs = _load_docs()
    scored: List[Tuple[int, Dict[str, str]]] = []
    for doc in docs:
        text = doc["content"].lower()
        score = sum(text.count(t) for t in query_terms)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [doc for score, doc in scored if score > 0][:k]
    if len(picked) < k:
        for _, doc in scored:
            if doc not in picked:
                picked.append(doc)
            if len(picked) >= k:
                break
    return picked


def _extract_json(text: str) -> Dict[str, object]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _expected_direction(guess: int, secret: int) -> str:
    if guess == secret:
        return "correct"
    return "higher" if guess < secret else "lower"


def _is_relevant_to_guess(payload: Dict[str, object], guess: int) -> bool:
    blob = " ".join(str(payload.get(k, "")) for k in ["numberFact", "rangeAdvice", "targetClue", "nextStrategy"]).lower()
    return str(guess) in blob or any(term in blob for term in ["range", "mid", "higher", "lower", "close", "number"])


def _has_useful_strategy(payload: Dict[str, object]) -> bool:
    text = str(payload.get("nextStrategy", "")).strip().lower()
    return len(text) >= 10 and any(k in text for k in ["try", "range", "mid", "higher", "lower", "strategy"])


def validate_story(payload: Dict[str, object], *, guess: int, secret: int) -> Tuple[bool, str]:
    needed = {"numberFact", "direction", "rangeAdvice", "targetClue", "nextStrategy", "confidence"}
    if not needed.issubset(payload):
        return False, "missing_keys"

    if payload.get("direction") not in {"higher", "lower", "correct"}:
        return False, "invalid_direction"

    if payload.get("direction") != _expected_direction(guess, secret):
        return False, "wrong_direction"

    if payload.get("confidence") not in {"low", "medium", "high"}:
        return False, "invalid_confidence"

    blob = " ".join(str(payload.get(k, "")) for k in needed).lower()
    if re.search(rf"\b{secret}\b", blob):
        return False, "target_revealed"
    if "the answer is" in blob:
        return False, "answer_phrase"

    if not _is_relevant_to_guess(payload, guess):
        return False, "not_relevant"

    if not _has_useful_strategy(payload):
        return False, "weak_strategy"

    return True, "ok"


def _safe_fallback(
    *,
    guess: int,
    low: int,
    high: int,
    attempts_left: int,
    history: List[Dict[str, object]],
    direction: str,
    specialization: str,
    mode: str,
) -> Dict[str, object]:
    min_bound, max_bound = build_range_from_history(low, high, history)
    base = fallback_story(min_bound, max_bound, direction, attempts_left)
    base["numberFact"] = get_number_fact(guess)
    base["targetClue"] = FALLBACK_TEXT
    base["confidence"] = "medium"
    base["agentTrace"] = [
        "Input validated and game range inferred.",
        "Local number fact retrieved.",
        f"Specialization mode selected: {specialization}.",
        "Safety fallback selected due to AI unavailability or validation block.",
    ]
    base["retrievalSources"] = ["local-number-facts", "fallback-logic", f"mode:{mode}"]
    base["specialization"] = specialization
    return base


def get_ai_number_story(
    *,
    difficulty: str,
    guess: int,
    secret: int,
    low: int,
    high: int,
    attempts_left: int,
    history: List[Dict[str, object]],
    specialization: str = "Coach",
    mode: str = "enhanced",  # enhanced | baseline
) -> Dict[str, object]:
    logger.info("AI story requested")
    direction = _expected_direction(guess, secret)
    local_fact = get_number_fact(guess)
    fallback = _safe_fallback(
        guess=guess,
        low=low,
        high=high,
        attempts_left=attempts_left,
        history=history,
        direction=direction,
        specialization=specialization,
        mode=mode,
    )

    min_bound, max_bound = build_range_from_history(low, high, history)
    query_terms = [str(guess), "strategy", "range", direction, difficulty.lower()]
    retrieved_docs = _simple_retrieve_docs(query_terms, k=2) if mode == "enhanced" else []
    doc_snippets = [d["content"][:180] for d in retrieved_docs]
    doc_sources = [d["source"] for d in retrieved_docs]
    if mode == "enhanced" and doc_snippets:
        cue = doc_snippets[0].split(".")[0].strip()
        if cue:
            fallback["targetClue"] = f"{FALLBACK_TEXT} Support cue: {cue}."
            fallback["confidence"] = "high" if attempts_left <= 3 else "medium"
            fallback["retrievalSources"] = ["local-number-facts"] + doc_sources + [f"mode:{mode}"]

    agent_trace = [
        "Validate guess context and compute direction.",
        "Retrieve local number fact and optional support docs.",
        "Generate structured strategy response in selected specialization mode.",
        "Run safety validator; fallback if blocked.",
    ]

    if direction == "correct":
        return {
            "numberFact": local_fact,
            "direction": "correct",
            "rangeAdvice": "No more narrowing needed, you solved it.",
            "targetClue": "You found the target exactly.",
            "nextStrategy": "Review the guesses that narrowed your range fastest and reuse that approach next game.",
            "confidence": "high",
            "agentTrace": agent_trace,
            "retrievalSources": ["local-number-facts"] + doc_sources,
            "specialization": specialization,
        }

    if not AI_TOOLING_AVAILABLE:
        logger.info("fallback hint used (AI unavailable)")
        return fallback

    system = (
        "You are the AI Number Story Coach in a number guessing game. "
        "Never reveal exact answer. Return strict JSON only with keys: "
        "numberFact, direction, rangeAdvice, targetClue, nextStrategy, confidence."
    )

    mode_instruction = SPECIALIZATION_MODES.get(specialization, SPECIALIZATION_MODES["Coach"])
    retrieval_note = "\n".join(doc_snippets) if doc_snippets else "No external docs in baseline mode."

    user = {
        "difficulty": difficulty,
        "guess": guess,
        "direction": direction,
        "attemptsLeft": attempts_left,
        "range": {"low": low, "high": high},
        "inferredRange": {"min": min_bound, "max": max_bound},
        "history": history,
        "clueStrength": "stronger" if attempts_left <= 3 else "gentle",
        "specializationMode": specialization,
        "specializationInstruction": mode_instruction,
        "retrievedSupport": retrieval_note,
        "instructions": [
            f"Use this exact one-sentence fact for numberFact: {local_fact}",
            "Provide directional feedback consistent with direction field.",
            "Provide range narrowing advice.",
            "Give safe clue about target pattern without revealing answer.",
            "Give next-step strategy.",
        ],
    }

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        res = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0.35,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user)},
            ],
        )
        parsed = _extract_json(res.output_text.strip())
        parsed["numberFact"] = local_fact
        ok, reason = validate_story(parsed, guess=guess, secret=secret)
        if not ok:
            logger.warning("AI story blocked by safety checker: %s", reason)
            logger.info("fallback hint used")
            return fallback

        parsed["agentTrace"] = agent_trace
        parsed["retrievalSources"] = ["local-number-facts"] + doc_sources
        parsed["specialization"] = specialization
        return parsed
    except Exception as exc:
        logger.exception("AI story request failed: %s", exc)
        logger.info("fallback hint used")
        return fallback
