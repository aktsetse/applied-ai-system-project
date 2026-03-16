# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
The game run just fine when I run it. However, after entering my guess, it kept asking me to go higher even when I entered a hundred. Also, it did similar for my second try and kept asking me to go lower till I entered 0. Looks like the limit set doesn't work. Even when I entered a value out of range, it didn't signal me. 

- List at least two concrete bugs you noticed at the start  
  (for example: "the secret number kept changing" or "the hints were backwards").
  Kept asking me to go higher after entering the highest possible value(100).
  Didn't let me start a new game even when I guessed the number right.

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- I used Claude as the AI tool on this project. I used it like a teammate to inspect the code, suggest where bugs might be, and help me test whether the app behavior matched the code. It was useful for narrowing down likely problem areas faster than I could on my own.
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- One correct AI suggestion was that the comparison logic in `check_guess()` was wrong. The AI suggested that the code was returning the wrong hint direction, because a guess above the secret should tell the player to go lower, not higher. That suggestion was correct. I verified it by looking at the code in `check_guess()` and then running the game and entering guesses like 100, where the app clearly gave the wrong feedback.
- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).
- One incorrect or misleading AI suggestion was the idea that the app was basically fine just because it launched and let me play. That was misleading because the app still had logic bugs even though there were no startup errors. I verified that by testing the game directly and also by checking the code, where I found the reversed hint logic and the broken new game reset behavior.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- I decided a bug was really fixed only after I tested it in the app and saw the correct behavior more than once. I did not want to assume the repair worked just because the code changed. I used both the running game and the test file to verify that the fixes were actually working.
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- One manual test I ran was entering a very high guess when the secret number was lower. After the fix, the game correctly told me to go lower instead of higher, which showed that the `check_guess()` repair worked in the actual app. I also ran `python -m pytest` and used the regression test in `tests/test_game_logic.py`, which confirmed that the bug with comparing `9` to `"10"` was fixed in the code.
- Did AI help you design or understand any tests? How?
- Yes, AI helped me design the tests by pointing me toward the exact logic that was risky and by suggesting a regression test for the comparison bug. That helped me check both the player experience in the game and the logic in the test file. It made my testing more focused because I was verifying the exact bug instead of just clicking around randomly.

---

## 4. What did you learn about Streamlit and state?

- In your own words, explain why the secret number kept changing in the original app.
- The secret number can seem to change when Streamlit reruns the script and the value is not handled carefully in session state. Since Streamlit re-executes the app often, any value that is not stored the right way can act unpredictably. That made me realize state management matters a lot even in a small app.
- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?
- I would say Streamlit reruns are like the app rereading the whole script every time the user interacts with something. Session state is what helps the app remember important values like the secret number, score, and attempts between those reruns. Without session state, the game would keep forgetting where it was.
- What change did you make that finally gave the game a stable secret number?
- The main change was making sure the secret number stayed in `st.session_state.secret` and was reused during the game instead of getting replaced during normal play. That gave the app one stable number to compare guesses against. It made the behavior much easier to understand and debug.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- One habit I want to keep using is testing the app from the user side before trusting the code. Running the app and trying obvious edge cases helped me find bugs faster than just reading the file. I also want to keep using AI to narrow down where a bug might be before I start editing.
- What is one thing you would do differently next time you work with AI on a coding task?
- Next time, I would verify the AI suggestions earlier and more often. I learned that even if the code looks polished, the logic can still be wrong. I would rather test each small change right away than wait until the end.
- In one or two sentences, describe how this project changed the way you think about AI generated code.
- This project changed the way I think about AI-generated code because now I see that working code is not the same as correct code. AI can be really helpful, but I still need to test everything carefully and think through the logic myself.
