"""
agents/strategy_consultant/orchestrator.py
Engagement Partner — the master orchestrator.
Manages the full engagement lifecycle from intake to final PDF delivery.
"""

import logging
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE))

from .config import ProjectType, Proactivity, ENGAGEMENTS_DIR
from .state import EngagementState, search_engagements
from .cost_estimator import estimate, format_estimate, confirm
from .status_reporter import StatusReporter
from .agents import (
    IntakeAgent, DataProcessorAgent, ResearchAgent, FrameworksAgent,
    FinancialAgent, BenchmarkingAgent, RedTeamAgent, SynthesisAgent,
    WriterAgent, CommunicationsAgent,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("consultant.partner")


class EngagementPartner:
    """
    The Engagement Partner orchestrates all agents.
    Entry points:
      - start_engagement(problem, ...)   → runs full engagement
      - run_validation()                 → tests all agents
    """

    def __init__(self):
        self.intake_agent    = IntakeAgent()
        self.data_agent      = DataProcessorAgent()
        self.research_agent  = ResearchAgent()
        self.frameworks_agent= FrameworksAgent()
        self.financial_agent = FinancialAgent()
        self.benchmark_agent = BenchmarkingAgent()
        self.redteam_agent   = RedTeamAgent()
        self.synthesis_agent = SynthesisAgent()
        self.writer_agent    = WriterAgent()
        self.comms_agent     = CommunicationsAgent()

    # ── Full engagement lifecycle ──────────────────────────────────────────────

    def start_engagement(
        self,
        problem: str,
        title: str = None,
        client_name: str = "",
        proactivity: Proactivity = Proactivity.MEDIUM,
        data_files: list = None,
        competitors: list = None,
        channels: list = None,
        answers: dict = None,
        skip_cost_confirm: bool = False,
        auto_approve_under: float = None,
    ) -> dict:
        """
        Run a full consulting engagement end-to-end.
        Returns engagement_id and path to final PDF.
        """
        # ── 0. Cost estimate gate ─────────────────────────────────────────────
        cost_est = estimate(
            proactivity=proactivity.value,
            has_data_files=bool(data_files),
            n_competitors=len(competitors or []),
        )
        logger.info(format_estimate(cost_est))

        if not skip_cost_confirm:
            approved = confirm(cost_est, auto_approve_under=auto_approve_under)
            if not approved:
                logger.info("Engagement cancelled by user.")
                return {"error": "cancelled", "reason": "User declined after cost estimate."}

        # ── 0b. Start status reporter ─────────────────────────────────────────
        tg_target = "8296787175"
        if channels:
            tg_ch = next((c for c in channels if c.get("type") == "telegram"), None)
            if tg_ch:
                tg_target = tg_ch.get("to", tg_target)

        reporter = StatusReporter(
            chat_id=tg_target,
            title=title or problem[:60],
            interval_s=300,  # every 5 minutes
        )
        reporter.start()

        # ── 1. Check for relevant prior engagements ───────────────────────────
        prior = search_engagements(query=problem[:30])
        if prior:
            logger.info(f"Found {len(prior)} prior related engagements: {[p['title'] for p in prior[:3]]}")

        # ── 2. Intake ──────────────────────────────────────────────────────────
        logger.info("=== PHASE 1: INTAKE ===")
        reporter.set_phase("intake", ["intake"])
        intake_result = self.intake_agent.run(problem=problem, answers=answers, proactivity=proactivity.value)
        project_type = intake_result["project_type"]
        reporter.complete_workstream("intake")
        logger.info(f"Project type: {project_type}")

        # ── 3. Create engagement state ─────────────────────────────────────────
        state = EngagementState.create(
            title=title or problem[:60],
            project_type=ProjectType(project_type),
            proactivity=proactivity,
            client_name=client_name,
        )
        state.save_intake(intake_result)
        state.write_workstream("intake", intake_result.get("brief", ""))
        logger.info(f"Engagement created: {state.engagement_id}")
        logger.info(f"Folder: {state.dir}")

        # ── 4. Data processing ─────────────────────────────────────────────────
        data_summary = ""
        reporter.set_phase("data", ["data_processing"] if data_files else [])
        if data_files:
            logger.info("=== PHASE 2: DATA PROCESSING ===")
            # Copy files to engagement data dir
            import shutil
            for f in data_files:
                src = Path(f)
                if src.exists():
                    shutil.copy(src, state.data_dir() / src.name)
            data_results = self.data_agent.run(data_dir=state.data_dir())
            data_summary = "\n\n".join(f"**{k}**\n{v}" for k, v in data_results.items())
            state.write_workstream("data", data_summary)
            state.append_context("Data & Files Processed", data_summary[:2000])
            logger.info(f"Processed {len(data_results)} files")

        # ── 5. Build full context for analysis agents ─────────────────────────
        context = f"""
Engagement: {state.title}
Client: {client_name or 'undisclosed'}
Project Type: {project_type}
Proactivity: {proactivity.value}

Problem Statement:
{problem}

Intake Brief:
{intake_result.get('brief', '')[:2000]}

Data Extracted:
{data_summary[:1500] if data_summary else 'No data files provided'}

Prior Engagements:
{str([p['title'] for p in prior[:3]]) if prior else 'None'}
""".strip()

        # ── 6. Parallel analysis workstreams ──────────────────────────────────
        logger.info("=== PHASE 3: PARALLEL ANALYSIS ===")
        state.set_status("analysis")
        reporter.set_phase("analysis", ["research", "frameworks", "financial", "benchmarks"])

        def run_research():
            r = self.research_agent.run(
                topic=problem[:100],
                competitors=competitors or [],
                include_papers=("ai" in project_type or "tech" in problem.lower())
            )
            state.write_workstream("research", r)
            reporter.complete_workstream("research")
            return "research", r

        def run_frameworks():
            r = self.frameworks_agent.run(context=context, project_type=project_type)
            state.write_workstream("frameworks", r)
            reporter.complete_workstream("frameworks")
            return "frameworks", r

        def run_financial():
            r = self.financial_agent.run(
                context=context, project_type=project_type, data_extracted=data_summary
            )
            state.write_workstream("financial", r)
            reporter.complete_workstream("financial")
            return "financial", r

        def run_benchmarks():
            r = self.benchmark_agent.run(
                context=context, industry="technology", metrics=["revenue growth", "NRR", "CAC/LTV"],
                peers=competitors or []
            )
            state.write_workstream("benchmarks", r)
            reporter.complete_workstream("benchmarks")
            return "benchmarks", r

        workstream_results = {}
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = [
                ex.submit(run_research),
                ex.submit(run_frameworks),
                ex.submit(run_financial),
                ex.submit(run_benchmarks),
            ]
            for fut in as_completed(futures):
                name, result = fut.result()
                workstream_results[name] = result
                logger.info(f"  Workstream complete: {name} ({len(result)} chars)")

        # ── 7. Red Team ───────────────────────────────────────────────────────
        logger.info("=== PHASE 4: RED TEAM ===")
        reporter.set_phase("red_team", ["red_team"])
        redteam = self.redteam_agent.run(workstreams=workstream_results)
        state.write_workstream("redteam", redteam)
        reporter.complete_workstream("red_team")

        # ── 8. Synthesis (Opus) ───────────────────────────────────────────────
        logger.info("=== PHASE 5: SYNTHESIS ===")
        state.set_status("synthesis")
        reporter.set_phase("synthesis", ["synthesis"])
        synthesis = self.synthesis_agent.run(
            intake=intake_result,
            workstreams=workstream_results,
            red_team=redteam,
        )
        state.write_workstream("synthesis", synthesis.get("full_synthesis", ""))
        reporter.complete_workstream("synthesis")

        # ── 9. Write PDF ───────────────────────────────────────────────────────
        logger.info("=== PHASE 6: WRITING REPORT ===")
        state.set_status("writing")
        reporter.set_phase("writing", ["writer"])
        self.writer_agent.state = state
        pdf_path = self.writer_agent.run(state, synthesis)
        reporter.complete_workstream("writer")
        logger.info(f"PDF generated: {pdf_path}")

        # ── 10. Deliver ────────────────────────────────────────────────────────
        logger.info("=== PHASE 7: DELIVERY ===")
        state.set_status("delivered")
        reporter.set_phase("delivered")
        comms_results = self.comms_agent.run(
            engagement_state=state,
            synthesis_result=synthesis,
            pdf_path=pdf_path,
            channels=channels or [{"type": "telegram", "to": "8296787175"}],
        )
        reporter.stop()

        logger.info(f"=== ENGAGEMENT COMPLETE: {state.engagement_id} ===")
        return {
            "engagement_id": state.engagement_id,
            "pdf_path": pdf_path,
            "folder": str(state.dir),
            "summary": synthesis.get("executive_summary", ""),
            "delivery": comms_results,
        }

    # ── Questions-first mode ───────────────────────────────────────────────────

    def get_intake_questions(self, problem: str) -> dict:
        """Return intake questions without running the full engagement."""
        result = self.intake_agent.run(problem=problem)
        return {
            "project_type": result["project_type"],
            "questions": result["questions"],
        }

    # ── Prior engagement search ────────────────────────────────────────────────

    def find_prior_engagements(self, query: str = "") -> list:
        return search_engagements(query)
