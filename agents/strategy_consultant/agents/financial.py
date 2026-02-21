"""
agents/strategy_consultant/agents/financial.py
Financial Modeler — TAM/SAM/SOM, ROI, unit economics, scenarios.
"""

from .base import BaseAgent

SYSTEM = """You are a financial modeling expert on a strategy consulting team.
Build models bottom-up where possible. Show your assumptions explicitly.
Run 3 scenarios (bear/base/bull). Be conservative on revenue, honest about costs.
Call out the 2-3 variables that most swing the outcome."""


class FinancialAgent(BaseAgent):
    name = "financial"
    default_tier = 2

    def _default_system(self): return SYSTEM

    def tam_sam_som(self, context: str) -> str:
        return self.call(f"""
Context: {context}

Build a TAM/SAM/SOM analysis:
1. TAM — total addressable market (top-down and bottom-up approaches)
2. SAM — serviceable addressable market given current capabilities/geography
3. SOM — realistic 3-year capture given go-to-market assumptions

Show calculations. State key assumptions. Flag data quality.
""")

    def roi_analysis(self, context: str, investment: str = "") -> str:
        return self.call(f"""
Context: {context}
Investment context: {investment or 'not specified'}

Build an ROI analysis:
- Cost structure (one-time + ongoing)
- Revenue/value impact (quantified where possible)
- Payback period
- 3-year NPV at 10% discount rate
- Sensitivity: which 3 assumptions most affect the outcome?
- Bear / Base / Bull scenarios

Show your work. Flag what's estimated vs. calculated.
""")

    def unit_economics(self, context: str) -> str:
        return self.call(f"""
Context: {context}

Model the unit economics:
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value) and LTV/CAC ratio
- Payback period
- Gross margin per unit/customer
- Contribution margin
- At what scale do the economics become attractive?

If data is insufficient, state what you'd need to model this properly.
""")

    def scenario_model(self, context: str, decision: str) -> str:
        return self.call(f"""
Context: {context}
Decision being modeled: {decision}

Build a 3-scenario financial model (Bear / Base / Bull):
For each scenario:
- Key assumptions that define it
- Year 1, Year 2, Year 3 P&L snapshot
- Cash position at end of Year 3
- Key risks that could push from Base to Bear

End with: "The decision is most sensitive to..." (top 3 variables)
""", force_tier=3)

    def run(self, context: str, project_type: str = "general", data_extracted: str = "") -> str:
        full_context = context
        if data_extracted:
            full_context += f"\n\nClient financial data:\n{data_extracted[:2000]}"

        parts = ["# Financial Analysis\n"]

        if project_type in ["market_entry", "go_to_market", "build_buy_partner"]:
            parts.append("## Market Sizing (TAM/SAM/SOM)\n" + self.tam_sam_som(full_context))

        parts.append("\n## ROI Analysis\n" + self.roi_analysis(full_context))

        if project_type in ["product_strategy", "market_entry", "go_to_market"]:
            parts.append("\n## Unit Economics\n" + self.unit_economics(full_context))

        parts.append("\n## Scenario Model\n" + self.scenario_model(
            full_context,
            decision=f"Proceed with {project_type.replace('_', ' ')} initiative"
        ))

        return "\n".join(parts)

    def validate(self) -> dict:
        try:
            context = "SaaS company, $5M ARR, 120% NRR, $2M CAC spend, 500 customers, $10K ACV, 3 year contracts."
            result = self.unit_economics(context)
            passed = len(result) > 150 and any(w in result.lower() for w in ["cac", "ltv", "payback", "margin"])
            return {"passed": passed, "output": result[:300], "notes": "Unit economics modeling test"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
