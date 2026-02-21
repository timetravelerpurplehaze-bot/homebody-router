"""
agents/strategy_consultant/agents/frameworks.py
Frameworks Analyst — applies strategic frameworks rigorously to the engagement context.
"""

from .base import BaseAgent

SYSTEM = """You are a senior strategy analyst expert in applying consulting frameworks.
Apply frameworks rigorously and with specificity — no generic templates.
Every cell, quadrant, or force must be grounded in the actual client context.
Call out where the framework reveals something non-obvious or counterintuitive."""


FRAMEWORK_PROMPTS = {
    "porters_5": """Apply Porter's Five Forces to the following context.
For each force, rate it (High/Medium/Low) and explain WHY with specific evidence.
End with: "The dominant forces are X and Y because..."

Context: {context}""",

    "swot": """Conduct a SWOT analysis for the following context.
Each cell must have 3-5 specific, evidence-backed points — not generic statements.
Conclude with the top 3 strategic implications.

Context: {context}""",

    "bcg_matrix": """Apply the BCG Matrix to the following portfolio/product context.
Map each item to a quadrant with revenue/growth justification.
Recommend: what to invest in, maintain, harvest, divest.

Context: {context}""",

    "wardley_map": """Create a Wardley Map analysis for the following context.
Identify: user needs at the top, then map the value chain components by evolution stage
(Genesis → Custom → Product → Commodity).
Identify strategic opportunities where components are misplaced vs. competitors.

Context: {context}""",

    "jobs_to_be_done": """Apply Jobs-to-be-Done framework.
Identify the functional, emotional, and social jobs the customer is hiring the product/service to do.
Identify underserved jobs — where current solutions fall short.
Recommend: what to build, improve, or stop.

Context: {context}""",

    "ansoff": """Apply the Ansoff Growth Matrix.
Evaluate Market Penetration, Market Development, Product Development, and Diversification.
Rank the options by risk/reward given the client's current position.

Context: {context}""",

    "value_chain": """Conduct a Value Chain Analysis.
Map primary activities (inbound logistics, operations, outbound, marketing, service)
and support activities (infrastructure, HR, technology, procurement).
Identify where the client has advantage, parity, or disadvantage vs. competitors.

Context: {context}""",
}


class FrameworksAgent(BaseAgent):
    name = "frameworks"
    default_tier = 2

    def _default_system(self): return SYSTEM

    def apply(self, framework: str, context: str) -> str:
        template = FRAMEWORK_PROMPTS.get(framework)
        if not template:
            return f"Unknown framework: {framework}"
        prompt = template.format(context=context[:3000])
        return self.call(prompt)

    def select_frameworks(self, project_type: str, context: str) -> list[str]:
        """Auto-select the most relevant frameworks for a given project type."""
        mapping = {
            "build_buy_partner":      ["porters_5", "value_chain", "ansoff"],
            "market_entry":           ["porters_5", "ansoff", "jobs_to_be_done"],
            "ai_capability_assessment":["wardley_map", "value_chain", "swot"],
            "ma_investment":           ["porters_5", "swot", "value_chain"],
            "product_strategy":        ["jobs_to_be_done", "ansoff", "bcg_matrix"],
            "competitive_response":    ["porters_5", "swot", "wardley_map"],
            "digital_transformation":  ["wardley_map", "value_chain", "swot"],
            "go_to_market":            ["jobs_to_be_done", "ansoff", "porters_5"],
        }
        return mapping.get(project_type, ["porters_5", "swot"])

    def run(self, context: str, project_type: str = "general", frameworks: list[str] = None) -> str:
        if not frameworks:
            frameworks = self.select_frameworks(project_type, context)

        self.logger.info(f"Running frameworks: {frameworks}")
        parts = [f"# Strategic Framework Analysis\n"]

        for fw in frameworks:
            fw_name = fw.replace("_", " ").title()
            self.logger.info(f"Applying {fw_name}...")
            result = self.apply(fw, context)
            parts.append(f"\n## {fw_name}\n{result}")

        # Cross-framework synthesis
        combined = "\n\n".join(parts)
        synthesis_prompt = (
            f"You have applied multiple strategic frameworks to this problem.\n\n{combined[:4000]}\n\n"
            "In 2-3 paragraphs: what are the most consistent and contradictory signals across frameworks? "
            "What strategic direction do they collectively point to?"
        )
        parts.append("\n## Cross-Framework Synthesis\n" + self.call(synthesis_prompt, force_tier=3))

        return "\n".join(parts)

    def validate(self) -> dict:
        try:
            context = "A B2B SaaS company selling AI-powered analytics to mid-market enterprises, considering entering the healthcare vertical."
            result = self.apply("porters_5", context)
            passed = len(result) > 200 and any(w in result.lower() for w in ["high", "medium", "low", "force", "bargaining"])
            return {"passed": passed, "output": result[:300], "notes": "Porter's 5 Forces on B2B SaaS context"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
