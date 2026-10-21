# Chatbot Regression Tester

Automated QA for AI sales and support bots. It holds real multi-turn conversations with your bot, checks them with hard rules and an LLM judge, and shows exactly what broke after a prompt change, before it reaches a customer.

## The problem
A client asks for "one small change" to their bot, like adding a question. Suddenly the bot re-asks things the lead already said, skips its intro or never gets to the booking. Single-reply tests don't catch this, because the bug only shows up across a whole conversation.

## How it works
1. **Simulated leads:** an LLM plays realistic personas (a cooperative lead, a lead who gives everything up front, a price-first skeptic, an off-topic visitor).
2. **Multi-turn conversations** with the bot under test, up to a turn limit.
3. **Hard checks (plain Python):**
   - intro in the first message;
   - the same question never asked twice;
   - the booking link sent when expected (and not sent to off-topic leads).
4. **LLM judge:** did the bot re-ask information it already had? Is the tone right? Is the qualification complete? Gives a score from 1 to 5 with notes.
5. **Regression mode:** runs the same scenarios against the old and new prompt and writes an HTML report you can send to a client.

## Example: catching a real regression
`bots/setter_v1.md` is a working DM appointment setter. `bots/setter_v2.md` is the same bot after a typical client edit ("add *where did you hear about us*, always ask it first, never skip a script question").

| Version | Passed | Intro in 1st message | Re-asked known info (judge) |
|---|---|---|---|
| setter_v1 (baseline) | 2/4 | 3/4 | 1/4 |
| setter_v2 (after edit) | **0/4** | **0/4** | 1/4, plus it never collected timeline or commitment for the price-first lead |

The tester showed that the edit removed the intro in every conversation and made the bot ask irrelevant questions to an off-topic lead. It also found two weak spots that were already in v1: a missing intro when the lead opens with a long message, and one re-asked goal. A single-reply test would have missed both. One full comparison costs about $0.04.

LLM conversations vary from run to run, so use `--runs 3` (or more) before trusting a pass rate.

## Run it
```bash
pip install -r requirements.txt
# put ANTHROPIC_API_KEY=... into a .env file
python run_tests.py setter_v1 setter_v2           # compare two versions
python run_tests.py setter_v1 --runs 3            # test one version, 3 runs per scenario
python -m unittest -v                             # offline tests for the checks
```
Reports are saved to `reports/` (HTML plus raw JSON).

## Adapt it to your bot
- Put your system prompt into `bots/your_bot.md`.
- Write your own personas in `scenarios.json` (`expect_booking` sets whether the conversation should end in a booking).
- Change the models, the intro phrase, the booking link and the repeat threshold in `config.py`.

## Files
| File | What it does |
|---|---|
| `simulator.py` | runs conversations (bot vs simulated lead) and the LLM judge; tracks API cost |
| `checks.py` | hard checks and validation of the judge's JSON |
| `run_tests.py` | runs everything and saves the report |
| `report.py` | builds the HTML report |
| `test_checks.py` | 12 offline unit tests |

Built by Alina Kremenchutska · [Ali & AI](https://ali-and-ai.com)
