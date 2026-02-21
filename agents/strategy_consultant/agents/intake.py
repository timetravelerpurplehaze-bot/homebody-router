"""
agents/strategy_consultant/agents/intake.py
Intake Agent — acts as a senior partner conducting the initial client discovery.
Detects project type, asks domain-specific questions, requests documents.
"""

from .base import BaseAgent
from ..config import ProjectType, Proactivity

SYSTEM = """You are a Senior Partner at a top-tier strategy consulting firm (McKinsey/BCG level).
You are conducting the initial discovery call for a new engagement.
Your job is to extract maximum context from the client — problem statement, constraints, data,
prior work, stakeholders, success criteria, and anything that will let the team hit the ground running.

Ask sharp, specific questions. No generic consulting boilerplate.
If the client mentions a domain (AI, product, M&A), ask the specific questions that domain demands.
When you have enough context, summarize everything into a structured brief.
Be direct. Be thorough. Push back on vague answers."""

QUESTION_BANK = {
    ProjectType.BUILD_BUY_PARTNER: [
        "What specific capability gap is driving this decision right now?",
        "What's your current build capability — engineering headcount, AI/ML talent?",
        "Have you evaluated specific vendors or partners? What were the outcomes?",
        "What's the total budget envelope and ownership timeline?",
        "Is proprietary data or IP a constraint on the buy/partner path?",
        "What does 'good' look like in 12 months if you get this right?",
    ],
    ProjectType.MARKET_ENTRY: [
        "What's the specific market and segment — geography, customer type, use case?",
        "Do you have any existing customers, pilots, or LOIs in this market?",
        "Who are the top 3 incumbents and what's their current moat?",
        "What's your beachhead strategy — where do you win first?",
        "What regulatory or compliance constraints apply?",
        "What resources are committed — team, budget, timeline to first revenue?",
    ],
    ProjectType.AI_CAPABILITY: [
        "What's your current AI/ML stack — infra, models, tooling?",
        "Do you have proprietary data assets? What type, volume, quality?",
        "How many ML engineers and data scientists do you have?",
        "What AI initiatives have you attempted and what happened?",
        "What are your competitors doing in AI that you're watching closely?",
        "What business outcomes do you need AI to drive in the next 12 months?",
    ],
    ProjectType.MA_INVESTMENT: [
        "What is the strategic rationale — capability acquisition, market access, talent?",
        "Do you have a specific target or target profile in mind?",
        "What's your integration capacity and track record with prior acquisitions?",
        "What's the deal size envelope and preferred structure (asset, stock, merger)?",
        "What synergies are you underwriting and over what timeframe?",
        "Who has board/investment committee authority and what's the approval process?",
    ],
    ProjectType.PRODUCT_STRATEGY: [
        "What's the core problem your product solves and for whom?",
        "Have you built similar products before? What were the specs and outcomes?",
        "What are the must-have technical constraints or integrations?",
        "Who are the top 3 competing products and how do users describe the gap?",
        "What does your current roadmap look like and what's blocking it?",
        "What does product-market fit look like for you — metric, threshold, timeline?",
    ],
    ProjectType.COMPETITIVE_RESPONSE: [
        "What exactly did the competitor do and when did you learn about it?",
        "How is it affecting you — revenue, pipeline, churn, talent?",
        "What's your current competitive positioning and moat?",
        "What response options have you already considered internally?",
        "What's your speed constraint — how fast can you actually move?",
        "What's your relationship with the customers most at risk?",
    ],
    ProjectType.DIGITAL_TRANSFORMATION: [
        "What's driving this transformation — competitive pressure, cost, mandate?",
        "What's your current technology estate — core systems, tech debt level?",
        "What transformation efforts have you attempted? What stalled them?",
        "What's the org's change appetite — leadership alignment, culture?",
        "What's the budget and governance model for this program?",
        "What does success look like in Year 1 vs Year 3?",
    ],
    ProjectType.GENERAL: [
        "What is the specific decision you need to make, and by when?",
        "What do you already know and believe about this problem?",
        "What would change your mind or surprise you?",
        "Who are the key stakeholders and what do they each care about?",
        "What constraints are truly fixed vs. negotiable?",
        "What does a successful outcome look like in concrete terms?",
    ],
}

UNIVERSAL_QUESTIONS = [
    "Do you have any internal data — financials, product metrics, org charts, customer data — we should absorb?",
    "Any prior strategy decks, market studies, RFPs, or board materials relevant to this?",
    "Who are the key internal stakeholders and what do they each care about most?",
    "Are there any political landmines or organizational sensitivities we should know about?",
    "What's your timeline and key milestones for this engagement?",
]


def detect_project_type(problem: str) -> ProjectType:
    """Heuristic detection of project type from problem statement."""
    p = problem.lower()
    if any(x in p for x in ["build vs", "make vs buy", "build or buy", "vendor", "make-or-buy"]):
        return ProjectType.BUILD_BUY_PARTNER
    if any(x in p for x in ["market entry", "enter the market", "new market", "expansion", "go-to-market", "gtm"]):
        return ProjectType.MARKET_ENTRY
    if any(x in p for x in ["ai strategy", "ai capability", "ml capability", "ai roadmap", "llm", "model"]):
        return ProjectType.AI_CAPABILITY
    if any(x in p for x in ["acquire", "acquisition", "m&a", "merger", "invest", "due diligence", "target"]):
        return ProjectType.MA_INVESTMENT
    if any(x in p for x in ["product", "feature", "roadmap", "product-market", "launch"]):
        return ProjectType.PRODUCT_STRATEGY
    if any(x in p for x in ["competitor", "competitive", "threat", "response", "disruption"]):
        return ProjectType.COMPETITIVE_RESPONSE
    if any(x in p for x in ["transform", "digital", "moderniz", "legacy", "overhaul"]):
        return ProjectType.DIGITAL_TRANSFORMATION
    return ProjectType.GENERAL


class IntakeAgent(BaseAgent):
    name = "intake"
    default_tier = 2

    def _default_system(self): return SYSTEM

    def generate_questions(self, problem: str, project_type: ProjectType = None) -> list[str]:
        if project_type is None:
            project_type = detect_project_type(problem)
        domain_qs = QUESTION_BANK.get(project_type, QUESTION_BANK[ProjectType.GENERAL])
        return domain_qs + UNIVERSAL_QUESTIONS

    def run(self, problem: str, answers: dict = None, proactivity: str = "medium") -> dict:
        """
        Run the intake process.
        Returns: {project_type, questions, structured_brief}
        """
        project_type = detect_project_type(problem)
        questions = self.generate_questions(problem, project_type)

        brief_prompt = f"""
The client has presented the following problem:
"{problem}"

Project type detected: {project_type.value}

Answers collected so far:
{answers or '(none yet)'}

Write a structured intake brief with these sections:
1. Problem Statement (sharp, one paragraph)
2. Project Type & Framing
3. Key Questions Still Open
4. Data/Documents Requested from Client
5. Stakeholder Map
6. Success Criteria
7. Recommended Engagement Scope & Timeline

Be specific. Flag any red flags or contradictions in the client's framing.
"""
        brief = self.call(brief_prompt)

        return {
            "project_type": project_type.value,
            "questions": questions,
            "brief": brief,
            "answers": answers or {},
        }

    def validate(self) -> dict:
        try:
            result = self.run(
                problem="We need to decide whether to build our own AI summarization capability or use a third-party API.",
                proactivity="medium"
            )
            passed = (
                result.get("project_type") == ProjectType.BUILD_BUY_PARTNER.value
                and len(result.get("questions", [])) >= 5
                and len(result.get("brief", "")) > 100
            )
            return {
                "passed": passed,
                "output": f"Type: {result['project_type']} | Questions: {len(result['questions'])} | Brief: {len(result['brief'])} chars",
                "notes": "Project type detection + question generation + brief creation"
            }
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
