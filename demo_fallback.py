#!/usr/bin/env python3
"""
Demo script to showcase the enhanced fallback AI insights without API keys.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ai_utils import simple_fallback_advice, NUMBER_INSIGHTS, GENERAL_STRATEGIES
from collections import namedtuple

# Mock Document for testing
Document = namedtuple("Document", ["page_content", "metadata"])

def demo_fallback_insights():
    """Demonstrate the enhanced fallback AI insights."""

    print("🎯 Enhanced AI Fallback Insights Demo")
    print("=" * 50)

    # Test cases with different numbers and outcomes
    test_cases = [
        (15, "Win", "Mentor"),
        (7, "Too High", "Coach"),
        (23, "Too Low", "Wizard"),
        (42, "Too High", "Mentor"),  # Number not in insights (fallback case)
    ]

    mock_docs = [Document("Sample math fact", {})]

    for secret, outcome, style in test_cases:
        guess = secret + (1 if outcome == "Too Low" else -1)  # Simulate a guess
        advice = simple_fallback_advice(guess, secret, outcome, mock_docs, style)

        print(f"\n🎲 Secret: {secret} | Guess: {guess} | Outcome: {outcome} | Style: {style}")
        print(f"💡 AI Insight: {advice}")

    print("\n" + "=" * 50)
    print("📚 Available Number Insights:", len(NUMBER_INSIGHTS))
    print("🎯 General Strategies:", len(GENERAL_STRATEGIES))
    print("\n✅ All insights work without external API keys!")

if __name__ == "__main__":
    demo_fallback_insights()