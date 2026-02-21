"""
router/cli.py
Command-line interface for the model router.

Usage:
    python -m router.cli "Your query here"
    python -m router.cli --tier 2 "Your query here"
    python -m router.cli --backend heuristic --classify-only "Your query"
    python -m router.cli --status
"""

import argparse
import json
import sys
import os

# ensure workspace is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def cmd_status():
    from router.config import all_available_models, TIERS, PROVIDER_API_KEYS
    print("\n=== Model Router Status ===\n")
    available = all_available_models()
    for tier, models in TIERS.items():
        label = {1: "Tier 1 (Fast/Cheap)", 2: "Tier 2 (Balanced)", 3: "Tier 3 (Powerful)"}[tier]
        print(f"{label}:")
        for m in models:
            provider = m.split("/")[0]
            key = PROVIDER_API_KEYS.get(provider, "")
            has_key = "✓" if os.environ.get(key) else "✗ (no key)"
            avail = "available" if m in available[tier] else "unavailable"
            print(f"  {has_key}  {m}  [{avail}]")
        print()


def cmd_route(args):
    from router import route, classify
    from router.config import RouterConfig

    config = RouterConfig(
        classifier_backend=args.backend,
        allow_escalation=not args.no_escalation,
    )

    query = " ".join(args.query)

    if args.classify_only:
        tier = classify(query, config)
        print(f"Complexity tier: {tier}")
        return

    from router.router import ModelRouter
    r = ModelRouter(config)
    result = r.route(
        query,
        force_tier=args.tier,
        system_prompt=args.system,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Model : {result.model_used}")
        print(f"Tier  : {result.tier_requested} → {result.tier_used}")
        print(f"Time  : classify={result.classification_ms:.0f}ms  call={result.call_ms:.0f}ms")
        print(f"{'='*60}\n")
        print(result.content)
        if not result.success:
            print(f"\n[ERROR] {result.error}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="python -m router.cli",
        description="Complexity-aware LLM router"
    )
    sub = parser.add_subparsers(dest="cmd")

    # status
    sub.add_parser("status", help="Show available models and API key status")

    # route (default)
    rp = parser.add_argument_group("routing options")
    parser.add_argument("query", nargs="*", help="Query to route")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Force tier (skip classifier)")
    parser.add_argument("--backend", default="llm", choices=["llm", "heuristic", "routellm"],
                        help="Classifier backend (default: llm)")
    parser.add_argument("--classify-only", action="store_true", help="Only classify, don't call model")
    parser.add_argument("--no-escalation", action="store_true", help="Disable tier escalation on failure")
    parser.add_argument("--system", default=None, help="System prompt")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if args.cmd == "status":
        cmd_status()
    elif args.query:
        cmd_route(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
