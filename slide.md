# Presentation Slides (5-7 minutes)

## Slide 1: Title
**AI Number Story Coach: Building a Reliable Applied AI Game System**

- Course: Project 4 - Applied AI System
- Presenter: [Your Name]
- Tech: Python, Streamlit, OpenAI API, Local Retrieval, Pytest

**Speaker notes (20-30 sec):**
This project extends my original Number Guessing Game into an AI-assisted system with safety guardrails, local retrieval, evaluation scripts, and a polished game-style interface.

---

## Slide 2: Original Project and Motivation
**Original project (Modules 1-3): Number Guessing Game**

- Basic gameplay: guess a hidden number
- Feedback: too high / too low
- Win/loss after limited attempts

**Why extend it:**
- Turn a simple game into a reliable AI product
- Add meaningful strategy guidance, not random tips
- Demonstrate production-style AI safeguards

**Speaker notes (35-45 sec):**
I wanted to show that applied AI is not only about generating text. It is about building a complete system: input handling, reasoning, validation, fallback behavior, observability, and testing.

---

## Slide 3: What I Built
**Key upgrades**

- AI Number Story Coach after every valid guess
- Wordle-style visual feedback and progress tracking
- Difficulty modes and score model
- Play / History / Stats tabs
- Light/dark theme with persistence
- Local number facts for 1-500 with special-fact priority

**Speaker notes (35-45 sec):**
The AI is embedded in the main gameplay loop. Each guess triggers structured coaching that includes a number fact, directional strategy, and next-step guidance.

---

## Slide 4: System Architecture
**Architecture highlights**

- Input -> Validator -> State Engine
- Local Fact Retrieval + Optional Doc Retrieval (RAG-enhanced mode)
- AI Story Generator
- Safety Checker (schema, direction, no-answer-leak)
- Output UI + Persistence + Logs
- Feedback loop from tests and human review

**Diagrams to show:**
- `number-game-architecture-light.svg.png`
- `number-game-architecture-dark.svg.png`

**Speaker notes (45-55 sec):**
The architecture separates concerns: game logic, AI generation, safety validation, and persistence. This reduces brittle behavior and makes reliability measurable.

---

## Slide 5: Live Demo Plan
**Demo script (2-3 minutes)**

1. Start game on Medium mode
2. Submit invalid guess -> show toast + no attempt consumed
3. Submit repeated guess -> blocked + no attempt consumed
4. Submit valid guess -> show AI Story card
5. Open Agent Trace expander -> show intermediate steps and retrieval sources
6. Switch Coach Style (Coach -> Analyst -> Arcade)
7. Show History and Stats tabs updating

**Speaker notes:**
Narrate why each behavior matters for reliability, not just UX.

---

## Slide 6: Reliability and Evaluation
**Guardrails implemented**

- Direction correctness check
- Answer leakage check
- Schema validation for AI output
- Fallback hint when AI fails or is unsafe
- Logging for failures and key decisions

**Validation results**
- `pytest`: 13 passed
- `ai_evaluation.py`: 9/9 checks passed
- Confidence average: 0.70

**Speaker notes (45-55 sec):**
I tested both normal gameplay behavior and AI-specific failure paths. The fallback system keeps the app usable even when API access is unavailable.

---

## Slide 7: Stretch Features Implemented
**Completed stretch features**

- RAG enhancement: local facts + support docs, measurable impact
- Agentic workflow: observable `agentTrace` steps
- Specialization behavior: Coach / Analyst / Arcade output modes
- Evaluation harness: predefined scenarios + pass/fail summary

**Speaker notes (35-45 sec):**
I focused on features that are visible, testable, and directly connected to the gameplay loop rather than isolated experiments.

---

## Slide 8: Reflection and What I Learned
**What I learned**

- Reliability issues often come from integration details, not core logic
- Guardrails + fallback are essential for trust
- Clear architecture makes debugging and iteration faster

**Limitations and next steps**

- Add richer retrieval corpus and better quality metrics
- Add in-app evaluation dashboard
- Expand multiplayer/challenge modes while preserving safety checks

**Speaker notes (40-50 sec):**
The biggest takeaway is that responsible AI systems need both intelligence and control layers. Good AI UX comes from combining both.

---

## Optional Q&A Backup Slide
**If asked about technical depth**

- `ai_utils.py`: generation, retrieval, validation, fallback
- `logic_utils.py`: deterministic game rules and scoring
- `tests/test_game_logic.py`: logic and guardrail tests
- `ai_evaluation.py`: reliability summary harness

