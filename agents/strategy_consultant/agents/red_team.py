"""
agents/strategy_consultant/agents/red_team.py
Red Team Agent — adversarial review, stress-testing assumptions, devil's advocate.
"""

from .base import BaseAgent

SYSTEM = """You are the most skeptical person in the room. Your job is to stress-test every assumption,
challenge every conclusion, and find what everyone else missed.
You are NOT trying to be destructive — you are trying to make the work stronger.
Be specific. "This assumption is wrong because X" not "this might be wrong."
End every section with: "The team should address this by..."
If something is genuinely solid, say so. Don't manufacture objections."""


class RedTeamAgent(BaseAgent):
    name = "red_team"
    default_tier = 2

    def _default_system(self): return SYSTEM

    def challenge_assumptions(self, workstream_content: str) -> str:
        return self.call(f"""
Review the following analysis and identify every explicit and implicit assumption.
For each, rate it: SOLID / SHAKY / UNFOUNDED.

Analysis:
{workstream_content[:3000]}

Format:
**Assumption:** [state it clearly]
**Rating:** SOLID / SHAKY / UNFOUNDED
**Why:** [specific reason]
**Address by:** [what the team should do]
""")

    def steelman_opposition(self, recommendation: str, context: str) -> str:
        return self.call(f"""
Recommendation being made: {recommendation}
Context: {context[:2000]}

Build the strongest possible case AGAINST this recommendation.
This is not about being contrarian — find the genuine risks, flaws, and better alternatives.

Cover:
1. The strongest counterargument
2. What this recommendation gets wrong about the market/customer/competition
3. What could go catastrophically wrong
4. A better alternative approach

Be specific and evidence-based.
""", force_tier=3)

    def find_blind_spots(self, full_analysis: str) -> str:
        return self.call(f"""
You have reviewed a full strategy engagement analysis:
{full_analysis[:4000]}

What is this team NOT seeing?
- What question isn't being asked?
- What stakeholder isn't being considered?
- What market dynamic is being ignored?
- What historical analogy is relevant but absent?
- What execution risk is being glossed over?

List 5-7 blind spots with specific explanations.
""", force_tier=3)

    def stress_test_financials(self, financial_analysis: str) -> str:
        return self.call(f"""
Financial analysis to stress-test:
{financial_analysis[:3000]}

Challenge this financial model:
1. Which assumptions are the most heroic? What's a more conservative estimate?
2. What costs are missing or underestimated?
3. What's the realistic downside scenario vs. the stated bear case?
4. At what point does this become financially unviable?
5. What comparable situations (comps) suggest about likely outcomes?
""")

    def run(self, workstreams: dict, recommendation: str = "") -> str:
        parts = ["# Red Team Review\n"]
        parts.append("> *This section is intentionally adversarial. Its purpose is to strengthen the final recommendation.*\n")

        # Challenge each workstream
        if workstreams.get("frameworks"):
            parts.append("\n## Challenging the Framework Analysis\n" +
                         self.challenge_assumptions(workstreams["frameworks"]))

        if workstreams.get("financial"):
            parts.append("\n## Stress-Testing the Financials\n" +
                         self.stress_test_financials(workstreams["financial"]))

        if workstreams.get("research"):
            parts.append("\n## Challenging Research Assumptions\n" +
                         self.challenge_assumptions(workstreams["research"]))

        # Blind spots across everything
        combined = "\n\n".join(list(workstreams.values())[:3])
        parts.append("\n## Blind Spots\n" + self.find_blind_spots(combined))

        # Steelman the opposition
        if recommendation:
            parts.append("\n## Strongest Case Against the Recommendation\n" +
                         self.steelman_opposition(recommendation, combined))

        return "\n".join(parts)

    def validate(self) -> dict:
        try:
            analysis = "We recommend entering the healthcare AI market. TAM is $50B. Our product has 98% accuracy. Competitors are slow. We should move fast."
            result = self.challenge_assumptions(analysis)
            passed = len(result) > 200 and any(w in result.lower() for w in ["assumption", "shaky", "unfounded", "solid"])
            return {"passed": passed, "output": result[:300], "notes": "Assumption challenge on overconfident market analysis"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
