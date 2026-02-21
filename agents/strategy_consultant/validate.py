"""
agents/strategy_consultant/validate.py
Validation suite — test every agent independently without running a full engagement.

Usage:
    python -m agents.strategy_consultant.validate           # test all agents
    python -m agents.strategy_consultant.validate intake    # test one agent
    python -m agents.strategy_consultant.validate --list    # show available agents
"""

import sys
import os
import time
import logging
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

logging.basicConfig(level=logging.WARNING)  # quiet during validation

from agents.strategy_consultant.agents import ALL_AGENTS

COLORS = {
    "green":  "\033[92m",
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}

def c(color, text):
    return f"{COLORS.get(color,'')}{text}{COLORS['reset']}"


def validate_agent(name: str, cls) -> dict:
    print(f"  Testing {c('cyan', name)}...", end=" ", flush=True)
    t0 = time.monotonic()
    try:
        agent = cls()
        result = agent.validate()
        elapsed = time.monotonic() - t0
        result["agent"] = name
        result["elapsed_ms"] = round(elapsed * 1000)
        if result.get("passed"):
            print(c("green", f"PASS") + f"  ({elapsed:.1f}s)")
        else:
            print(c("red", f"FAIL") + f"  ({elapsed:.1f}s)")
        return result
    except Exception as e:
        elapsed = time.monotonic() - t0
        print(c("red", f"ERROR") + f"  ({elapsed:.1f}s)  {e}")
        return {"agent": name, "passed": False, "output": "", "notes": str(e), "elapsed_ms": round(elapsed*1000)}


def run_all() -> list:
    print(f"\n{c('bold', '='*60)}")
    print(f"{c('bold', ' Strategy Consulting Agent Validation Suite')}")
    print(f"{c('bold', '='*60)}\n")
    results = []
    for name, cls in ALL_AGENTS.items():
        r = validate_agent(name, cls)
        results.append(r)

    # Summary
    passed  = sum(1 for r in results if r.get("passed"))
    failed  = len(results) - passed

    print(f"\n{c('bold', '='*60)}")
    print(f"Results: {c('green', str(passed))} passed  {c('red', str(failed))} failed  out of {len(results)} agents")
    print(f"{c('bold', '='*60)}\n")

    if failed:
        print(c("yellow", "Failed agents:"))
        for r in results:
            if not r.get("passed"):
                print(f"  {c('red', r['agent'])}: {r.get('notes', 'no details')}")

    print("\nDetailed outputs:")
    for r in results:
        status = c("green", "[PASS]") if r.get("passed") else c("red", "[FAIL]")
        print(f"\n{status} {c('bold', r['agent'])} ({r.get('elapsed_ms', 0)}ms)")
        print(f"  Notes:  {r.get('notes', '')}")
        if r.get("output"):
            preview = r["output"][:150].replace("\n", " ")
            print(f"  Output: {preview}...")

    return results


def run_one(agent_name: str) -> dict:
    cls = ALL_AGENTS.get(agent_name)
    if not cls:
        print(f"Unknown agent: {agent_name}. Available: {', '.join(ALL_AGENTS.keys())}")
        sys.exit(1)
    print(f"\nValidating agent: {c('bold', agent_name)}\n")
    result = validate_agent(agent_name, cls)
    print(f"\nNotes:  {result.get('notes','')}")
    print(f"Output:\n{result.get('output','')}")
    return result


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        print("Available agents:", ", ".join(ALL_AGENTS.keys()))
    elif args:
        run_one(args[0])
    else:
        results = run_all()
        sys.exit(0 if all(r.get("passed") for r in results) else 1)
