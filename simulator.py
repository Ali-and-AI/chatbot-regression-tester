"""Runs one conversation: an AI lead talks to the bot under test, then a judge grades it."""
import os

import anthropic
from dotenv import load_dotenv

import config
from checks import parse_judge

load_dotenv(override=True)
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

LEAD_RULES = (
    "You are role-playing a person messaging a business on Instagram. Stay in character. "
    "Write short, casual DMs (1-2 sentences). Never mention you are an AI. "
    "When the assistant sends a booking link, reply with a short thanks and then write exactly END. "
    "If you want to stop the chat, write exactly END."
)

JUDGE_PROMPT = """You are a strict QA reviewer of sales DM bots.
Read the conversation between LEAD and BOT and answer in JSON only:
{{"reasked_known_info": true/false,   // did the BOT ask for information the LEAD had already given?
  "tone_ok": true/false,              // friendly, short, natural DM tone, no pressure
  "qualification_ok": true/false,     // learned goal, timeline, what they tried, commitment (or ended politely if off-topic)
  "score": 1-5,                       // overall quality
  "notes": "one or two sentences: the most important problem, or 'none'"}}

Conversation:
{conversation}"""

class EmptyReplyError(Exception):
    pass


# Usage counter: model -> [input_tokens, output_tokens]
usage = {}


def _call(model, system, messages, max_tokens=4000, attempts=3):
    # max_tokens covers the model's hidden thinking too, so it must be generous,
    # otherwise replies come back cut off or empty. Retry if that still happens.
    for _ in range(attempts):
        response = client.messages.create(
            model=model, system=system, messages=messages, max_tokens=max_tokens
        )
        counts = usage.setdefault(model, [0, 0])
        counts[0] += response.usage.input_tokens
        counts[1] += response.usage.output_tokens
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if text and response.stop_reason != "max_tokens":
            return text
    raise EmptyReplyError(f"{model} returned no text {attempts} times in a row")


def _as_messages(transcript, me):
    """Turn the transcript into API messages from one side's point of view."""
    messages = [
        {"role": "assistant" if t["role"] == me else "user", "content": t["text"]}
        for t in transcript
    ]
    # The API needs the first message to come from "user".
    if messages and messages[0]["role"] == "assistant":
        messages.insert(0, {"role": "user", "content": "(You open the DM chat.)"})
    return messages


def run_conversation(bot_prompt, scenario):
    transcript = [{"role": "lead", "text": scenario["opening"]}]
    for _ in range(config.MAX_TURNS):
        bot_reply = _call(config.BOT_MODEL, bot_prompt, _as_messages(transcript, "bot"))
        transcript.append({"role": "bot", "text": bot_reply})

        lead_reply = _call(
            config.LEAD_MODEL,
            LEAD_RULES + "\n\n" + scenario["persona"],
            _as_messages(transcript, "lead"),
        )
        if lead_reply.strip().endswith("END"):
            goodbye = lead_reply.replace("END", "").strip()
            if goodbye:
                transcript.append({"role": "lead", "text": goodbye})
            break
        transcript.append({"role": "lead", "text": lead_reply})
    return transcript


def judge(transcript):
    conversation = "\n".join(f'{t["role"].upper()}: {t["text"]}' for t in transcript)
    try:
        raw = _call(
            config.JUDGE_MODEL,
            "You output valid JSON only.",
            [{"role": "user", "content": JUDGE_PROMPT.format(conversation=conversation)}],
        )
    except (anthropic.APIError, EmptyReplyError) as error:
        return {"error": f"judge call failed: {error}"}
    return parse_judge(raw) or {"error": "judge returned unusable JSON", "raw": raw}


def cost_usd():
    total = 0.0
    for model, (inp, out) in usage.items():
        price_in, price_out = config.PRICES[model]
        total += inp / 1e6 * price_in + out / 1e6 * price_out
    return total
