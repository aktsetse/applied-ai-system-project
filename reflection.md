# Reflection and Ethics

## Limitations and Biases
My system is reliable for game logic, but it still has limits. The AI hint quality depends on prompt behavior and available context, so hints can sometimes feel generic. The local number facts are deterministic, but they still reflect my design choices about what counts as a "special" fact, which introduces selection bias.

## Misuse Risks and Prevention
A possible misuse is trying to force the AI to reveal the secret number or produce unsafe/confusing hints. I reduce this risk with guardrails: schema checks, direction checks, answer-leak checks, and deterministic fallback hints. I also keep the game playable when AI fails, so users do not depend on unstable model outputs.

## Reliability Surprise
What surprised me most was how often reliability issues came from integration details, not core logic. For example, UI/theme CSS collisions and AI response formatting were bigger reliability risks than basic win/loss logic. The safety validator and fallback system made the app much more stable during these edge cases.

## Future Improvements
I would improve this system by adding richer retrieval documents, a stronger quantitative quality metric for hint usefulness, and an in-app evaluator dashboard so reliability trends are visible over time. I would also add optional multiplayer or challenge modes while keeping the same safety checks.

## Collaboration with AI
AI helped me move faster in implementation and debugging. A helpful suggestion was to enforce structured JSON for AI hints and validate it before rendering; this directly improved safety and consistency. A flawed suggestion happened when a generated change looked correct but broke expectations in tests (fact-priority mismatch and UI styling side effects), so I had to verify with tests and manually refine the result.
