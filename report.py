"""Builds a single self-contained HTML report you can send to a client."""
from html import escape

CHECK_LABELS = {
    "intro_first": "Intro in 1st message",
    "no_repeated_questions": "No repeated questions",
    "booking": "Booking as expected",
}

CSS = """
body{font-family:system-ui,sans-serif;max-width:1000px;margin:24px auto;padding:0 16px;color:#1d2433;background:#fff}
h1{margin-bottom:4px} .sub{color:#667;margin-top:0}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0}
.card{border:1px solid #dde;border-radius:10px;padding:12px 16px;min-width:180px}
.card b{font-size:26px;display:block}
table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}
th,td{border-bottom:1px solid #eee;padding:8px;text-align:left;vertical-align:top}
.ok{color:#137a3a;font-weight:600} .bad{color:#b42318;font-weight:600}
details{border:1px solid #eee;border-radius:8px;padding:8px 12px;margin:8px 0}
.msg{padding:6px 10px;border-radius:10px;margin:4px 0;max-width:80%}
.lead{background:#f1f3f7} .bot{background:#e6f0ff;margin-left:auto}
.detail{color:#b42318;font-size:13px}
"""


def _mark(ok):
    return '<span class="ok">✔</span>' if ok else '<span class="bad">✘</span>'


def _summary(results):
    done = [r for r in results if "transcript" in r]
    passed = sum(r["passed"] for r in done)
    scores = [r["judge"]["score"] for r in done if "score" in r["judge"]]
    avg = sum(scores) / len(scores) if scores else 0
    return passed, len(results), avg


def write_report(path, all_results, cost):
    parts = [f"<!doctype html><meta charset='utf-8'><title>Chatbot Regression Report</title><style>{CSS}</style>"]
    parts.append("<h1>Chatbot Regression Report</h1>")
    parts.append(f"<p class='sub'>Simulated DM conversations, hard checks and an LLM judge · API cost ${cost:.4f}</p>")

    parts.append("<div class='cards'>")
    for name, results in all_results.items():
        passed, total, avg = _summary(results)
        parts.append(f"<div class='card'>{escape(name)}<b>{passed}/{total}</b>passed · judge avg {avg:.1f}/5</div>")
    parts.append("</div>")

    for name, results in all_results.items():
        parts.append(f"<h2>{escape(name)}</h2><table><tr><th>Scenario</th>")
        parts += [f"<th>{label}</th>" for label in CHECK_LABELS.values()]
        parts.append("<th>Re-asked known info</th><th>Score</th><th>Judge notes</th></tr>")
        for r in results:
            if "transcript" not in r:
                parts.append(f"<tr><td>{escape(r['scenario'])}</td><td colspan='7' class='bad'>error: {escape(r['error'])}</td></tr>")
                continue
            cells = [f"<td>{escape(r['scenario'])} #{r['run']}</td>"]
            for key in CHECK_LABELS:
                ok, detail = r["hard"][key]
                extra = f"<div class='detail'>{escape(detail)}</div>" if detail and not ok else ""
                cells.append(f"<td>{_mark(ok)}{extra}</td>")
            j = r["judge"]
            if "error" in j:
                cells.append(f"<td colspan='3' class='bad'>{escape(j['error'])}</td>")
            else:
                cells.append(f"<td>{_mark(not j['reasked_known_info'])}</td><td>{j['score']}</td><td>{escape(j['notes'])}</td>")
            parts.append("<tr>" + "".join(cells) + "</tr>")
        parts.append("</table>")

        for r in results:
            if "transcript" not in r:
                continue
            status = "PASS" if r["passed"] else "FAIL"
            parts.append(f"<details><summary>{escape(r['scenario'])} #{r['run']} — {status}</summary>")
            for t in r["transcript"]:
                parts.append(f"<div class='msg {t['role']}'><b>{t['role'].upper()}:</b> {escape(t['text'])}</div>")
            parts.append("</details>")

    path.write_text("\n".join(parts), encoding="utf-8")
