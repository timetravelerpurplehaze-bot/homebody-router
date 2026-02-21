import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from router.config import TIERS, all_available_models, RouterConfig
from router.classifier import classify, _heuristic_tier
from router.router import ModelRouter, RouteResult

print("Imports OK\n")

print("Tier definitions:")
for t, models in TIERS.items():
    print(f"  Tier {t}: {models}")
print()

tests = [
    ("What is the capital of France?", 1),
    ("Write a Python function to parse JSON with error handling", 2),
    ("Design a scalable distributed caching architecture for a global e-commerce platform", 3),
    ("Hi", 1),
    ("Analyze and compare the architectural tradeoffs between microservices and monoliths for a 50-engineer team", 3),
]

print("Heuristic classifier tests:")
all_pass = True
for q, expected in tests:
    got = _heuristic_tier(q)
    status = "OK" if got == expected else f"MISMATCH (expected {expected})"
    if got != expected:
        all_pass = False
    print(f"  [{status}] Tier {got} — {q[:70]}")

print()
print("Available models (requires API keys in .env):")
avail = all_available_models()
for t, ms in avail.items():
    label = ms if ms else ["(none — add API keys to .env)"]
    print(f"  Tier {t}: {label}")

print()
print("All heuristic tests passed!" if all_pass else "Some tests mismatched (may need tuning).")
