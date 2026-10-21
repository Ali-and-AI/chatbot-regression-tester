"""Hard checks: plain Python rules that don't need an AI to decide.

A transcript is a list of turns: {"role": "lead" or "bot", "text": "..."}.
"""
import json
import re
from difflib import SequenceMatcher


def bot_turns(transcript):
    return [t["text"] for t in transcript if t["role"] == "bot"]


def intro_in_first(transcript, phrase):
    """The bot's first message must introduce it (contain the phrase)."""
    turns = bot_turns(transcript)
    return bool(turns) and phrase.lower() in turns[0].lower()


def extract_questions(text):
    """Split a message into sentences and keep the ones that end with '?'."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip().endswith("?")]


def _normalize(question):
    return re.sub(r"[^a-z0-9 ]", "", question.lower()).strip()


def repeated_questions(transcript, threshold):
    """Questions the bot asked again in a later message.

    Returns a list of (earlier_question, later_question) pairs.
    """
    seen = []  # (turn_index, normalized, original)
    repeats = []
    for i, text in enumerate(bot_turns(transcript)):
        for q in extract_questions(text):
            norm = _normalize(q)
            for j, old_norm, old_q in seen:
                if j != i and SequenceMatcher(None, norm, old_norm).ratio() >= threshold:
                    repeats.append((old_q, q))
                    break
            seen.append((i, norm, q))
    return repeats


def booking_reached(transcript, link):
    return any(link in text for text in bot_turns(transcript))


def parse_judge(raw):
    """Read the judge's JSON reply. Returns None if it is not usable.

    Expected: {"reasked_known_info": bool, "tone_ok": bool,
               "qualification_ok": bool, "score": 1-5, "notes": str}
    """
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    needed = {"reasked_known_info", "tone_ok", "qualification_ok", "score", "notes"}
    if not needed.issubset(data):
        return None
    if not isinstance(data["score"], (int, float)) or not 1 <= data["score"] <= 5:
        return None
    return data


def run_hard_checks(transcript, expect_booking, intro_phrase, booking_link, repeat_threshold):
    """All hard checks for one conversation, as {check_name: (passed, detail)}."""
    repeats = repeated_questions(transcript, repeat_threshold)
    booked = booking_reached(transcript, booking_link)
    return {
        "intro_first": (intro_in_first(transcript, intro_phrase), ""),
        "no_repeated_questions": (
            not repeats,
            "; ".join(f'"{a}" -> "{b}"' for a, b in repeats),
        ),
        "booking": (
            booked == expect_booking,
            "booked" if booked else "no booking link",
        ),
    }
