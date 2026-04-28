import logging
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from ai_utils import get_ai_number_story
from logic_utils import (
    DIFFICULTY_CONFIG,
    build_range_from_history,
    build_win_note,
    calculate_score,
    evaluate_guess_submission,
    generate_secret,
    get_attempt_limit,
    get_range_for_difficulty,
    is_loss,
    is_win,
    new_stats,
    now_ts,
    read_json_file,
    update_stats,
    write_json_file,
)

st.set_page_config(page_title="AI Number Story Coach", page_icon="🎯", layout="centered")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATS_FILE = Path(".game_stats.json")
HISTORY_FILE = Path(".game_history.json")
PREFS_FILE = Path(".ui_prefs.json")


def load_stats():
    return read_json_file(STATS_FILE, new_stats())


def save_stats(stats):
    write_json_file(STATS_FILE, stats)


def load_history():
    return read_json_file(HISTORY_FILE, [])


def save_history(history):
    write_json_file(HISTORY_FILE, history)


def load_prefs():
    return read_json_file(PREFS_FILE, {"theme": "light"})


def save_prefs(prefs):
    write_json_file(PREFS_FILE, prefs)


def sync_local_storage_theme(theme: str) -> None:
    # Best-effort browser persistence for localStorage while Python-side fallback stays in .ui_prefs.json.
    components.html(
        f"""
        <script>
        localStorage.setItem('number_game_theme', '{theme}');
        </script>
        """,
        height=0,
    )


def init_state():
    if "phase" not in st.session_state:
        st.session_state.phase = "start"
    if "difficulty" not in st.session_state:
        st.session_state.difficulty = "Medium"
    if "secret" not in st.session_state:
        st.session_state.secret = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "guess_values" not in st.session_state:
        st.session_state.guess_values = []
    if "attempts_used" not in st.session_state:
        st.session_state.attempts_used = 0
    if "hint_uses" not in st.session_state:
        st.session_state.hint_uses = 0
    if "started_at" not in st.session_state:
        st.session_state.started_at = now_ts()
    if "last_score" not in st.session_state:
        st.session_state.last_score = 0
    if "last_story" not in st.session_state:
        st.session_state.last_story = None
    if "stats" not in st.session_state:
        st.session_state.stats = load_stats()
    if "game_history" not in st.session_state:
        st.session_state.game_history = load_history()
    if "prefs" not in st.session_state:
        st.session_state.prefs = load_prefs()
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Play"
    if "specialization_mode" not in st.session_state:
        st.session_state.specialization_mode = "Coach"


def start_game(difficulty: str):
    st.session_state.difficulty = difficulty
    st.session_state.secret = generate_secret(difficulty)
    st.session_state.history = []
    st.session_state.guess_values = []
    st.session_state.attempts_used = 0
    st.session_state.hint_uses = 0
    st.session_state.started_at = now_ts()
    st.session_state.last_story = None
    st.session_state.phase = "playing"
    logger.info("difficulty selected=%s", difficulty)
    logger.info("game started difficulty=%s", difficulty)


def finalize_game(won: bool):
    elapsed = now_ts() - st.session_state.started_at
    score = calculate_score(
        difficulty=st.session_state.difficulty,
        attempts_used=st.session_state.attempts_used,
        hint_uses=st.session_state.hint_uses,
        elapsed_seconds=elapsed,
        won=won,
    )
    st.session_state.last_score = score
    st.session_state.stats = update_stats(
        st.session_state.stats,
        won=won,
        score=score,
        attempts_used=st.session_state.attempts_used,
    )
    save_stats(st.session_state.stats)

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "difficulty": st.session_state.difficulty,
        "target_number": int(st.session_state.secret),
        "result": "win" if won else "loss",
        "attempts_used": st.session_state.attempts_used,
        "guesses_made": list(st.session_state.guess_values),
        "score": score,
        "hint_uses": st.session_state.hint_uses,
    }
    st.session_state.game_history = [record] + st.session_state.game_history
    save_history(st.session_state.game_history)

    st.session_state.phase = "won" if won else "lost"
    logger.info("game won") if won else logger.info("game lost")


def feedback_color(badge: str, theme: str) -> str:
    palette = {
        "light": {"Correct": "#6aaa64", "Very Close": "#c9b458", "Too High": "#d46a6a", "Too Low": "#7d8ea8"},
        "dark": {"Correct": "#538d4e", "Very Close": "#b59f3b", "Too High": "#a14f4f", "Too Low": "#4f6d8a"},
    }
    return palette[theme].get(badge, "#777")


init_state()

theme = st.session_state.prefs.get("theme", "light")
bg = "#f8fafc" if theme == "light" else "#0f172a"
fg = "#0f172a" if theme == "light" else "#e2e8f0"
card_bg = "#ffffff" if theme == "light" else "#111827"
muted = "#64748b" if theme == "light" else "#94a3b8"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;700&family=Exo+2:wght@400;500;700&display=swap');
    :root {{
      --ng-bg: {bg};
      --ng-fg: {fg};
      --ng-card: {card_bg};
      --ng-muted: {muted};
      --ng-border: #33415533;
      --ng-input-bg: {"#ffffff" if theme == "light" else "#1f2937"};
      --ng-input-border: {"#cbd5e1" if theme == "light" else "#475569"};
      --ng-button-bg: {"#0f172a" if theme == "light" else "#334155"};
      --ng-button-fg: {"#f8fafc" if theme == "light" else "#e2e8f0"};
    }}
    .stApp {{
      background:
        radial-gradient(1000px 460px at 8% -10%, {"#67e8f955" if theme == "light" else "#22d3ee55"}, transparent 55%),
        radial-gradient(850px 360px at 88% 6%, {"#f472b655" if theme == "light" else "#f472b655"}, transparent 60%),
        radial-gradient(900px 380px at 50% 110%, {"#a78bfa44" if theme == "light" else "#a78bfa33"}, transparent 65%),
        linear-gradient(140deg, {"#f8fafc" if theme == "light" else "#030712"} 0%, var(--ng-bg) 52%, {"#eef2ff" if theme == "light" else "#0f172a"} 100%);
      color: var(--ng-fg);
      font-family: 'Exo 2', var(--st-font), sans-serif;
    }}
    .stMarkdown, .stText, .stCaption, p, label {{
      color: var(--ng-fg);
    }}
    [data-testid="stHeader"] {{
      background: {"#f8fafcee" if theme == "light" else "#020617ee"} !important;
      border-bottom: 1px solid {"#94a3b844" if theme == "light" else "#38bdf833"};
      backdrop-filter: blur(6px);
    }}
    [data-testid="stToolbar"] button,
    [data-testid="stToolbar"] svg,
    [data-testid="stToolbar"] path {{
      color: {"#0f172a" if theme == "light" else "#e2e8f0"} !important;
      fill: {"#0f172a" if theme == "light" else "#e2e8f0"} !important;
    }}
    .main .block-container {{
      max-width: 980px;
      padding-top: 1.4rem;
      padding-bottom: 2.4rem;
    }}
    [data-testid="stMetricLabel"] *, [data-testid="stMetricValue"] * {{
      color: var(--ng-fg) !important;
    }}
    [data-testid="stMetric"] {{
      background: linear-gradient(180deg, {"#ffffffcc" if theme == "light" else "#0f172ab8"} 0%, {"#f1f5f9cc" if theme == "light" else "#111827b8"} 100%);
      border: 1px solid var(--ng-border);
      border-radius: 12px;
      padding: 0.45rem 0.55rem;
      box-shadow: 0 10px 24px {"#64748b22" if theme == "light" else "#00000055"};
    }}
    [data-testid="stProgressBar"] > div > div {{
      background: linear-gradient(90deg, #22c55e 0%, #16a34a 50%, #14b8a6 100%);
    }}
    [data-testid="stTextInputRootElement"] input {{
      background: var(--ng-input-bg) !important;
      color: var(--ng-fg) !important;
      border: 1px solid var(--ng-input-border) !important;
      border-radius: 10px !important;
    }}
    [data-testid="stTextInputRootElement"] input::placeholder {{
      color: var(--ng-muted) !important;
    }}
    [data-testid="stRadio"] label, [data-testid="stRadio"] span {{
      color: var(--ng-fg) !important;
    }}
    [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {{
      background: linear-gradient(135deg, {"#0f172a" if theme == "light" else "#1e293b"} 0%, {"#1e293b" if theme == "light" else "#334155"} 100%) !important;
      color: var(--ng-button-fg) !important;
      border: 1px solid {"#33415588" if theme == "light" else "#93c5fd55"} !important;
      border-radius: 12px !important;
      box-shadow: 0 8px 20px {"#33415533" if theme == "light" else "#00000066"} !important;
      transition: transform 120ms ease, box-shadow 120ms ease;
    }}
    [data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-primary"]:hover {{
      transform: translateY(-1px);
      box-shadow: 0 12px 26px {"#33415544" if theme == "light" else "#00000088"} !important;
    }}
    [data-testid="stBaseButton-secondary"] *,
    [data-testid="stBaseButton-primary"] * {{
      color: var(--ng-button-fg) !important;
      fill: var(--ng-button-fg) !important;
    }}
    [data-testid="stForm"] {{
      background: linear-gradient(180deg, {"#ffffffd9" if theme == "light" else "#0f172ad9"} 0%, {"#f8fafcd9" if theme == "light" else "#111827d9"} 100%);
      border: 1px solid var(--ng-border);
      border-radius: 12px;
      padding: 0.6rem;
      box-shadow: inset 0 1px 0 {"#ffffffaa" if theme == "light" else "#93c5fd22"};
    }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
      border-color: transparent;
    }}
    .main-title {{
      text-align:center;
      font-size:2.3rem;
      font-family:'Orbitron', var(--st-font), sans-serif;
      letter-spacing: 0.5px;
      font-weight:700;
      margin-bottom:0.2rem;
      text-shadow:
        0 0 8px {"#22d3ee99" if theme == "light" else "#22d3eecc"},
        0 0 22px {"#a78bfa66" if theme == "light" else "#a78bfaaa"};
    }}
    .sub {{ text-align:center; color:var(--ng-muted); margin-bottom:0.8rem; }}
    .story-card {{
      background: linear-gradient(160deg, {"#ffffffde" if theme == "light" else "#0b1221de"} 0%, {"#eef2ffde" if theme == "light" else "#111827de"} 100%);
      border:1px solid {"#22d3ee99" if theme == "light" else "#22d3ee88"};
      border-radius:14px;
      padding:0.9rem;
      margin-top:0.5rem;
      color: var(--ng-fg);
      box-shadow:
        0 0 0 1px {"#f472b633" if theme == "light" else "#f472b633"},
        0 12px 30px {"#0ea5e933" if theme == "light" else "#0ea5e922"};
    }}
    .guess-card {{
      border-radius:12px;
      color:white;
      padding:0.7rem;
      margin:0.35rem 0;
      font-weight:700;
      border: 1px solid #ffffff30;
      box-shadow: 0 8px 18px #00000033;
      animation: guessPop 180ms ease;
    }}
    .panel {{
      background: linear-gradient(180deg, {"#ffffffdb" if theme == "light" else "#0b1221db"} 0%, {"#f8fafcdb" if theme == "light" else "#111827db"} 100%);
      border:1px solid var(--ng-border);
      border-radius:14px;
      padding:0.8rem;
      margin-top:0.6rem;
      color: var(--ng-fg);
      box-shadow: 0 10px 26px {"#33415522" if theme == "light" else "#00000055"};
    }}
    @keyframes guessPop {{
      from {{ transform: scale(0.98); opacity: 0.65; }}
      to {{ transform: scale(1); opacity: 1; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">AI Number Story Coach</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Wordle-inspired number game with strategic AI guidance</div>', unsafe_allow_html=True)

col_t1, col_t2 = st.columns([4, 1])
with col_t2:
    if st.button("Toggle Theme"):
        new_theme = "dark" if st.session_state.prefs.get("theme") == "light" else "light"
        st.session_state.prefs["theme"] = new_theme
        save_prefs(st.session_state.prefs)
        sync_local_storage_theme(new_theme)
        logger.info("theme changed=%s", new_theme)
        st.rerun()

if st.session_state.phase == "start":
    st.write("Guess the hidden number in limited attempts. AI coach gives facts, safe clues, and strategy after each valid guess.")
    selected = st.radio("Difficulty", ["Easy", "Medium", "Hard"], horizontal=True, index=1)
    cfg = DIFFICULTY_CONFIG[selected]
    st.caption(f"Range {cfg['low']} to {cfg['high']} | Attempts: {cfg['attempts']}")
    if st.button("Start Game", type="primary", use_container_width=True):
        start_game(selected)
        st.rerun()
    st.stop()

selected_tab = st.radio("", ["Play", "History", "Stats"], horizontal=True, index=["Play", "History", "Stats"].index(st.session_state.active_tab))
if selected_tab != st.session_state.active_tab:
    st.session_state.active_tab = selected_tab
    logger.info("tab changed=%s", selected_tab)

if selected_tab == "Play":
    low, high = get_range_for_difficulty(st.session_state.difficulty)
    attempt_limit = get_attempt_limit(st.session_state.difficulty)
    attempts_left = attempt_limit - st.session_state.attempts_used
    over = st.session_state.phase in {"won", "lost"}

    current_min, current_max = build_range_from_history(low, high, st.session_state.history)

    a, b, c = st.columns(3)
    a.metric("Difficulty", st.session_state.difficulty)
    b.metric("Attempts Left", max(attempts_left, 0))
    c.metric("Possible Range", f"{current_min}-{current_max}")
    st.progress(st.session_state.attempts_used / attempt_limit)
    s1, s2 = st.columns(2)
    with s1:
        st.session_state.specialization_mode = st.selectbox(
            "Coach Style",
            ["Coach", "Analyst", "Arcade"],
            index=["Coach", "Analyst", "Arcade"].index(st.session_state.specialization_mode),
        )
    with s2:
        show_trace = st.checkbox("Show Agent Trace", value=True)

    with st.form("guess_form", clear_on_submit=True):
        raw_guess = st.text_input("Enter guess", placeholder=f"{low} - {high}", disabled=over)
        submitted = st.form_submit_button("Submit Guess", disabled=over, use_container_width=True)

    if submitted:
        result = evaluate_guess_submission(raw_guess, int(st.session_state.secret), low, high, st.session_state.guess_values)
        if not result["valid"]:
            logger.info("invalid guess raw=%s", raw_guess)
            st.toast(str(result["message"]), icon="⚠️")
        elif result["repeated"]:
            logger.info("repeated guess=%s", result["guess"])
            st.toast(str(result["message"]), icon="🔁")
        else:
            st.session_state.attempts_used += 1
            guess = int(result["guess"])
            st.session_state.guess_values.append(guess)
            row = {
                "attempt": st.session_state.attempts_used,
                "guess": guess,
                "badge": result["badge"],
                "message": result["message"],
            }
            st.session_state.history.append(row)
            logger.info("guess submitted guess=%s", guess)

            st.session_state.hint_uses += 1
            story = get_ai_number_story(
                difficulty=st.session_state.difficulty,
                guess=guess,
                secret=int(st.session_state.secret),
                low=low,
                high=high,
                attempts_left=max(0, attempt_limit - st.session_state.attempts_used),
                history=st.session_state.history,
                specialization=st.session_state.specialization_mode,
                mode="enhanced",
            )
            st.session_state.last_story = story

            won = is_win(result)
            lost = is_loss(st.session_state.attempts_used, attempt_limit, won)
            if won:
                finalize_game(True)
            elif lost:
                finalize_game(False)

    if st.session_state.last_story:
        s = st.session_state.last_story
        st.markdown(
            f"""
            <div class="story-card">
            <b>AI Number Story Coach</b><br><br>
            <b>Number fact:</b> {s['numberFact']}<br>
            <b>Direction:</b> {s['direction']}<br>
            <b>Range advice:</b> {s['rangeAdvice']}<br>
            <b>Target clue:</b> {s['targetClue']}<br>
            <b>Next strategy:</b> {s['nextStrategy']}<br>
            <b>Confidence:</b> {s['confidence']}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if show_trace:
            with st.expander("Agent Trace and Retrieval"):
                st.write("Specialization:", s.get("specialization", "unknown"))
                st.write("Retrieval sources:", s.get("retrievalSources", []))
                for i, step in enumerate(s.get("agentTrace", []), start=1):
                    st.write(f"{i}. {step}")

    if st.session_state.history:
        st.markdown('<div class="panel"><b>Guess History</b></div>', unsafe_allow_html=True)
        for row in reversed(st.session_state.history):
            color = feedback_color(row["badge"], st.session_state.prefs.get("theme", "light"))
            st.markdown(
                f'<div class="guess-card" style="background:{color};">Attempt {row["attempt"]}: '
                f'{row["guess"]} • {row["badge"]} • {row["message"]}</div>',
                unsafe_allow_html=True,
            )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Play Again", use_container_width=True):
            start_game(st.session_state.difficulty)
            st.rerun()
    with c2:
        if st.button("Reset", use_container_width=True):
            st.session_state.phase = "start"
            st.session_state.secret = None
            st.rerun()

    if st.session_state.phase == "won":
        st.success(build_win_note(st.session_state.difficulty, st.session_state.attempts_used, st.session_state.hint_uses))
        st.info(f"Score: {st.session_state.last_score}")
    elif st.session_state.phase == "lost":
        st.error(f"Out of attempts. Target number was {st.session_state.secret}. Score: {st.session_state.last_score}")

elif selected_tab == "History":
    st.subheader("Previous Games")
    if not st.session_state.game_history:
        st.info("No completed games yet.")
    else:
        for g in st.session_state.game_history[:30]:
            st.markdown(
                f"""
                <div class="panel">
                <b>{g['timestamp']}</b><br>
                Difficulty: {g['difficulty']}<br>
                Target: {g['target_number']}<br>
                Result: {g['result']}<br>
                Attempts: {g['attempts_used']}<br>
                Guesses: {g['guesses_made']}<br>
                Score: {g['score']}
                </div>
                """,
                unsafe_allow_html=True,
            )

else:
    st.subheader("Stats")
    s = st.session_state.stats
    r1, r2, r3 = st.columns(3)
    r1.metric("Games Played", int(s["games_played"]))
    r2.metric("Wins", int(s["wins"]))
    r3.metric("Losses", int(s["losses"]))

    r4, r5, r6 = st.columns(3)
    r4.metric("Win %", f"{s['win_percentage']}%")
    r5.metric("Current Streak", int(s["current_streak"]))
    r6.metric("Best Streak", int(s["best_streak"]))

    r7, r8 = st.columns(2)
    r7.metric("Best Score", int(s["best_score"]))
    r8.metric("Average Attempts", s["average_attempts"])
