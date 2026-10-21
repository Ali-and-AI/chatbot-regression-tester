"""Run every scenario against one or two bot versions and write an HTML report.

Usage:
    python run_tests.py setter_v1                 # test one version
    python run_tests.py setter_v1 setter_v2       # compare: baseline vs new version
    python run_tests.py setter_v1 setter_v2 --runs 3
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

import config
import simulator
from checks import run_hard_checks
from report import write_report

ROOT = Path(__file__).parent


def test_version(name, scenarios, runs):
    prompt = (ROOT / "bots" / f"{name}.md").read_text(encoding="utf-8")
    results = []
    for scenario in scenarios:
        for run in range(1, runs + 1):
            print(f"  {name} | {scenario['id']} | run {run} ...", end=" ", flush=True)
            try:
                transcript = simulator.run_conversation(prompt, scenario)
            except (simulator.anthropic.APIError, simulator.EmptyReplyError) as error:
                print(f"API error: {error}")
                results.append({"scenario": scenario["id"], "run": run, "error": str(error)})
                continue
            hard = run_hard_checks(
                transcript, scenario["expect_booking"], config.INTRO_PHRASE,
                config.BOOKING_LINK, config.REPEAT_SIMILARITY,
            )
            verdict = simulator.judge(transcript)
            passed = all(ok for ok, _ in hard.values()) and verdict.get("reasked_known_info") is False
            print("PASS" if passed else "FAIL")
            results.append({
                "scenario": scenario["id"], "run": run, "transcript": transcript,
                "hard": hard, "judge": verdict, "passed": passed,
            })
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("versions", nargs="+", help="bot prompt names in bots/ (1 or 2)")
    parser.add_argument("--runs", type=int, default=1, help="runs per scenario (LLMs vary)")
    args = parser.parse_args()

    scenarios = json.loads((ROOT / "scenarios.json").read_text(encoding="utf-8"))
    all_results = {}
    for name in args.versions[:2]:
        print(f"Testing {name}")
        all_results[name] = test_version(name, scenarios, args.runs)

    print()
    for name, results in all_results.items():
        ok = sum(r.get("passed", False) for r in results)
        print(f"{name}: {ok}/{len(results)} conversations passed")
    print(f"API cost: ${simulator.cost_usd():.4f}")

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    out = ROOT / "reports" / f"report_{stamp}.html"
    write_report(out, all_results, simulator.cost_usd())
    (ROOT / "reports" / f"results_{stamp}.json").write_text(
        json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Report: {out}")


if __name__ == "__main__":
    main()
