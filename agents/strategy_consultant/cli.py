"""
agents/strategy_consultant/cli.py
CLI interface for the strategy consulting multi-agent system.

Usage:
    python -m agents.strategy_consultant.cli engage "Should we build our own LLM or use APIs?"
    python -m agents.strategy_consultant.cli questions "We're considering entering Southeast Asia"
    python -m agents.strategy_consultant.cli history
    python -m agents.strategy_consultant.cli validate
    python -m agents.strategy_consultant.cli validate intake
"""

import argparse
import json
import sys
import logging
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s", datefmt="%H:%M:%S")


def cmd_engage(args):
    from agents.strategy_consultant.orchestrator import EngagementPartner
    from agents.strategy_consultant.config import Proactivity

    proactivity = Proactivity(args.proactivity)
    competitors = args.competitors.split(",") if args.competitors else []
    data_files  = args.data.split(",") if args.data else []
    channels    = json.loads(args.channels) if args.channels else None

    ep = EngagementPartner()
    result = ep.start_engagement(
        problem=args.problem,
        title=args.title or args.problem[:60],
        client_name=args.client or "",
        proactivity=proactivity,
        data_files=data_files,
        competitors=competitors,
        channels=channels,
        skip_cost_confirm=getattr(args, "yes", False),
        auto_approve_under=getattr(args, "auto_approve_under", None),
    )

    print(f"\n{'='*60}")
    print(f"ENGAGEMENT COMPLETE")
    print(f"ID:     {result['engagement_id']}")
    print(f"Folder: {result['folder']}")
    print(f"PDF:    {result['pdf_path']}")
    print(f"{'='*60}")
    print(f"\nEXECUTIVE SUMMARY:\n{result.get('summary','')}")
    print(f"\nDELIVERY: {result.get('delivery',{})}")


def cmd_questions(args):
    from agents.strategy_consultant.orchestrator import EngagementPartner
    ep = EngagementPartner()
    result = ep.get_intake_questions(args.problem)
    print(f"\nProject Type: {result['project_type']}")
    print(f"\nIntake Questions ({len(result['questions'])}):")
    for i, q in enumerate(result['questions'], 1):
        print(f"  {i}. {q}")


def cmd_history(args):
    from agents.strategy_consultant.state import search_engagements
    results = search_engagements(query=args.query or "")
    if not results:
        print("No engagements found.")
        return
    print(f"\n{len(results)} engagement(s):")
    for e in results:
        print(f"  [{e['created_at'][:10]}] {e['title']}  ({e['project_type']})  client={e.get('client','?')}")


def cmd_estimate(args):
    from agents.strategy_consultant.cost_estimator import estimate, format_estimate
    competitors = args.competitors.split(",") if args.competitors else []
    data_files  = args.data.split(",") if args.data else []
    est = estimate(
        proactivity=args.proactivity,
        has_data_files=bool(data_files),
        n_competitors=len(competitors),
    )
    print(format_estimate(est))


def cmd_validate(args):
    if args.agent:
        from agents.strategy_consultant.validate import run_one
        run_one(args.agent)
    else:
        from agents.strategy_consultant.validate import run_all
        run_all()


def main():
    parser = argparse.ArgumentParser(prog="strategy-consultant", description="AI Strategy Consulting System")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # engage
    ep = sub.add_parser("engage", help="Run a full engagement")
    ep.add_argument("problem", help="Problem statement")
    ep.add_argument("--title",       default="", help="Engagement title")
    ep.add_argument("--client",      default="", help="Client name")
    ep.add_argument("--proactivity", default="medium", choices=["high","medium","low"])
    ep.add_argument("--data",        default="", help="Comma-separated file paths to upload")
    ep.add_argument("--competitors", default="", help="Comma-separated competitor names")
    ep.add_argument("--channels",          default="",   help='JSON: [{"type":"telegram","to":"..."}]')
    ep.add_argument("--yes",               action="store_true", help="Skip cost confirmation prompt")
    ep.add_argument("--auto-approve-under",type=float, default=None, dest="auto_approve_under",
                    help="Auto-approve if estimated cost is under this amount (USD)")

    # questions
    qp = sub.add_parser("questions", help="Get intake questions for a problem (no full run)")
    qp.add_argument("problem", help="Problem statement")

    # history
    hp = sub.add_parser("history", help="List past engagements")
    hp.add_argument("query", nargs="?", default="", help="Search keyword")

    # estimate
    estp = sub.add_parser("estimate", help="Show cost estimate without running")
    estp.add_argument("--proactivity", default="medium", choices=["high","medium","low"])
    estp.add_argument("--competitors",  default="", help="Comma-separated competitor names")
    estp.add_argument("--data",         default="", help="Comma-separated data files")

    # validate
    vp = sub.add_parser("validate", help="Validate agents")
    vp.add_argument("agent", nargs="?", default="", help="Agent name (omit to test all)")

    args = parser.parse_args()
    {
        "engage":    cmd_engage,
        "questions": cmd_questions,
        "history":   cmd_history,
        "validate":  cmd_validate,
        "estimate":  cmd_estimate,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
