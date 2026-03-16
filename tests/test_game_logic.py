from logic_utils import check_guess

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win.
    result = check_guess(50, 50)
    assert result == ("Win", "Correct!")

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High".
    result = check_guess(60, 50)
    assert result == ("Too High", "Go LOWER!")

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low".
    result = check_guess(40, 50)
    assert result == ("Too Low", "Go HIGHER!")

def test_numeric_string_secret_does_not_use_lexicographic_comparison():
    # Regression test: "10" used to compare as text, so 9 was incorrectly treated as too high.
    result = check_guess(9, "10")
    assert result == ("Too Low", "Go HIGHER!")
