"""Settings for the chatbot regression tester.

Prices are USD per 1 million tokens (input, output). Check them against
Anthropic's pricing page before publishing cost numbers.
"""

# The bot under test. In a real audit this is the client's model.
BOT_MODEL = "claude-haiku-5-5"

# Plays the lead. A cheap model is fine: it only needs to follow a persona.
LEAD_MODEL = "claude-haiku-5-5"

# Grades each finished conversation. A stronger model makes a fairer judge.
JUDGE_MODEL = "claude-sonnet-5-5"

PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}

# Hard limit so a looping bot can't burn the budget.
MAX_TURNS = 8

# Facts the hard checks look for.
INTRO_PHRASE = "mia"
BOOKING_LINK = "cal.example.com/peak-body/strategy"

# Two bot questions this similar (0-1) count as the same question asked twice.
REPEAT_SIMILARITY = 0.75
