"""
agents/strategy_consultant/agents/synthesis.py
Synthesis Agent — Opus-level integration of all workstreams into final recommendation.
"""

from .base import BaseAgent

SYSTEM = """You are the Senior Partner making the final call on this engagement.
You have reviewed all the workstreams — research, frameworks, financials, benchmarks, and red team.
Your job is to synthesize them into a clear, senior-level recommendation.

What a Senior Partner does:
- Resolves contradictions between workstreams with judgment
- Weights evidence appropriately (not all inputs are equal)
- Takes a clear position — no "on one hand / on the other hand" endings
- Anticipates the client's next question
- Knows what to leave out of the final deck
- Gives the recommendation they'd give their best client, not the safest one"""


class SynthesisAgent(BaseAgent):
    name = "synthesis"
    default_tier = 3

    def _default_system(self): return SYSTEM

    def synthesize(self, intake: dict, workstreams: dict, red_team: str = "") -> str:
        # Build the full brief
        ws_text = ""
        for name, content in workstreams.items():
            ws_text += f"\n\n### {name.upper()} WORKSTREAM\n{content[:2000]}"

        prompt = f"""
ENGAGEMENT BRIEF:
{intake.get('brief', '')[:1500]}

WORKSTREAM OUTPUTS:
{ws_text[:6000]}

RED TEAM CHALLENGES:
{red_team[:2000] if red_team else 'Not available'}

Now synthesize this into a senior-level strategic recommendation covering:

## 1. Situation (1 paragraph — what we know for certain)
## 2. Complication (1 paragraph — what makes this hard)
## 3. Key Question (the one question this engagement must answer)
## 4. Recommendation (clear, direct — what the client should do)
## 5. Rationale (top 3 reasons, evidence-backed)
## 6. Risks and Mitigations (top 3, with specific mitigations)
## 7. Implementation Priorities (90-day, 6-month, 12-month)
## 8. What We'd Change Our Mind On (what new information would alter this recommendation)

Use the Situation-Complication-Resolution (SCR) narrative structure.
Be direct. The client needs to know what to do Monday morning.
"""
        return self.call(prompt)

    def executive_summary(self, full_synthesis: str) -> str:
        return self.call(f"""
Full synthesis:
{full_synthesis[:4000]}

Write a 200-word executive summary for a CEO or board audience.
- Lead with the recommendation
- State the 3 most important reasons
- Name the biggest risk
- End with the immediate next step

No hedging. No jargon. Write like you're presenting to a board in 2 minutes.
""", force_tier=3)

    def run(self, intake: dict, workstreams: dict, red_team: str = "") -> dict:
        self.logger.info("Running synthesis (Opus)...")
        full = self.synthesize(intake, workstreams, red_team)
        exec_summary = self.executive_summary(full)
        return {
            "executive_summary": exec_summary,
            "full_synthesis": full,
        }

    def validate(self) -> dict:
        try:
            intake = {"brief": "Client: HealthAI Inc. Problem: Should we build or buy an AI diagnostics engine? Budget: $5M. Timeline: 18 months."}
            workstreams = {
                "frameworks": "Porter's 5 shows high threat from new entrants. SWOT: strength in clinical data, weakness in ML talent.",
                "financial": "Build cost: $8M over 2 years. Buy cost: $2M/year. ROI breaks even at Year 3 for build.",
                "research": "FDA cleared 12 AI diagnostics tools in 2024. Key players: Nuance, Google Health, startup XYZ.",
            }
            result = self.run(intake, workstreams)
            passed = len(result.get("full_synthesis", "")) > 300 and len(result.get("executive_summary", "")) > 100
            return {
                "passed": passed,
                "output": result.get("executive_summary", "")[:300],
                "notes": "Full synthesis + executive summary generation (Opus)"
            }
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
