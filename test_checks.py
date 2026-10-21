"""Unit tests for the hard checks. They run offline, no API key needed.

Run: python -m unittest -v
"""
import unittest

from checks import (booking_reached, extract_questions, intro_in_first,
                    parse_judge, repeated_questions, run_hard_checks)

GOOD = [
    {"role": "lead", "text": "hey how does this work?"},
    {"role": "bot", "text": "Hey, I'm Mia from Peak Body Coaching! What's your main goal?"},
    {"role": "lead", "text": "lose 8 kg"},
    {"role": "bot", "text": "Nice. When do you want to see results?"},
    {"role": "lead", "text": "by summer"},
    {"role": "bot", "text": "Book here: https://cal.example.com/peak-body/strategy"},
]

BROKEN = [
    {"role": "lead", "text": "Hi, I want to build muscle in 3 months."},
    {"role": "bot", "text": "Where did you hear about us?"},
    {"role": "lead", "text": "Instagram"},
    {"role": "bot", "text": "Cool! What is your main fitness goal?"},
    {"role": "lead", "text": "I already told you"},
    {"role": "bot", "text": "Sorry! So what is your main fitness goal?"},
]


class TestHardChecks(unittest.TestCase):
    def test_intro_found_in_first_message(self):
        self.assertTrue(intro_in_first(GOOD, "mia"))

    def test_intro_missing(self):
        self.assertFalse(intro_in_first(BROKEN, "mia"))

    def test_extract_questions(self):
        self.assertEqual(extract_questions("Nice. When? Ok."), ["When?"])

    def test_no_repeats_in_good_chat(self):
        self.assertEqual(repeated_questions(GOOD, 0.75), [])

    def test_repeat_detected(self):
        self.assertEqual(len(repeated_questions(BROKEN, 0.75)), 1)

    def test_booking(self):
        link = "cal.example.com/peak-body/strategy"
        self.assertTrue(booking_reached(GOOD, link))
        self.assertFalse(booking_reached(BROKEN, link))

    def test_off_topic_without_booking_passes(self):
        hard = run_hard_checks(BROKEN, False, "mia", "cal.example.com", 0.75)
        self.assertTrue(hard["booking"][0])


class TestParseJudge(unittest.TestCase):
    def test_valid(self):
        raw = '{"reasked_known_info": false, "tone_ok": true, "qualification_ok": true, "score": 5, "notes": "none"}'
        self.assertEqual(parse_judge(raw)["score"], 5)

    def test_json_inside_text(self):
        raw = 'Here: {"reasked_known_info": true, "tone_ok": true, "qualification_ok": false, "score": 2, "notes": "x"} done'
        self.assertTrue(parse_judge(raw)["reasked_known_info"])

    def test_missing_field(self):
        self.assertIsNone(parse_judge('{"score": 3}'))

    def test_score_out_of_range(self):
        raw = '{"reasked_known_info": false, "tone_ok": true, "qualification_ok": true, "score": 9, "notes": ""}'
        self.assertIsNone(parse_judge(raw))

    def test_not_json(self):
        self.assertIsNone(parse_judge("looks fine to me"))


if __name__ == "__main__":
    unittest.main()
