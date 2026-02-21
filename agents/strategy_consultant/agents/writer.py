"""
agents/strategy_consultant/agents/writer.py
Writer Agent — produces polished PDF strategy report and slide outline.
"""

import os
import re
import textwrap
from pathlib import Path
from datetime import datetime
from .base import BaseAgent

SYSTEM = """You are a senior communications expert who writes consulting deliverables.
Your writing is precise, structured, and executive-ready.
No filler. No passive voice where active works. No hedging.
Every sentence earns its place."""


def _safe(text: str) -> str:
    replacements = {"\u2013":"-","\u2014":"-","\u2018":"'","\u2019":"'",
                    "\u201c":'"',"\u201d":'"',"\u2026":"...","\u2022":"*",
                    "\u2192":"->","\u00d7":"x","\u00b7":"*","\u00ae":"(R)","\u2122":"(TM)"}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def generate_pdf(engagement_title: str, client: str, date: str,
                 exec_summary: str, sections: dict, output_path: str) -> str:
    from fpdf import FPDF, XPos, YPos

    C_ACCENT  = (30, 64, 175)   # deep blue
    C_DARK    = (17, 24, 39)
    C_MID     = (75, 85, 99)
    C_LIGHT   = (156, 163, 175)
    C_WHITE   = (255, 255, 255)
    C_DIVIDER = (229, 231, 235)
    C_BG      = (248, 249, 250)

    class ReportPDF(FPDF):
        def header(self):
            self.set_fill_color(*C_ACCENT)
            self.rect(0, 0, 210, 12, "F")
            self.set_y(2.5)
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*C_WHITE)
            self.cell(0, 7, "STRATEGY CONSULTING | CONFIDENTIAL", align="L")
            self.cell(0, 7, date, align="R")
            self.set_y(14)
            self.set_text_color(*C_DARK)

        def footer(self):
            self.set_y(-11)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(*C_LIGHT)
            self.cell(0, 5, f"Confidential | {client} | Page {self.page_no()}", align="C")

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(16, 16, 16)

    # Cover page
    pdf.add_page()
    pdf.set_fill_color(*C_BG)
    pdf.rect(0, 12, 210, 60, "F")
    pdf.set_y(28)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*C_ACCENT)
    for line in textwrap.wrap(_safe(engagement_title), 40):
        pdf.cell(0, 11, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*C_MID)
    pdf.cell(0, 8, f"Prepared for: {_safe(client)}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 8, date, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(12)

    # Executive Summary
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*C_ACCENT)
    pdf.cell(0, 8, "Executive Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(*C_ACCENT)
    pdf.line(16, pdf.get_y(), 194, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*C_DARK)
    for line in textwrap.wrap(_safe(exec_summary), 90):
        pdf.cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)

    # Sections
    for title, content in sections.items():
        if pdf.get_y() > 240:
            pdf.add_page()
        # Section header
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(*C_ACCENT)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(0, 8, f"  {_safe(title)}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_DARK)

        # Render content with basic markdown handling
        for raw_line in _safe(content).split("\n"):
            line = raw_line.strip()
            if not line:
                pdf.ln(2)
                continue
            if line.startswith("## "):
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, line[3:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", "", 9)
            elif line.startswith("### "):
                pdf.set_font("Helvetica", "BI", 9)
                pdf.cell(0, 5, line[4:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", "", 9)
            elif line.startswith("**") and line.endswith("**"):
                pdf.set_font("Helvetica", "B", 9)
                for w in textwrap.wrap(line.strip("**"), 88):
                    pdf.cell(0, 5, w, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_font("Helvetica", "", 9)
            elif line.startswith("- ") or line.startswith("* "):
                for w in textwrap.wrap(line[2:], 86):
                    pdf.cell(4, 5, "")
                    pdf.cell(0, 5, f"- {w}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                for w in textwrap.wrap(line, 90):
                    pdf.cell(0, 5, w, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(4)
        pdf.set_draw_color(*C_DIVIDER)
        pdf.line(16, pdf.get_y(), 194, pdf.get_y())
        pdf.ln(4)

    pdf.output(output_path)
    return output_path


class WriterAgent(BaseAgent):
    name = "writer"
    default_tier = 2

    def _default_system(self): return SYSTEM

    def slide_outline(self, synthesis: str, title: str) -> str:
        return self.call(f"""
Strategy synthesis:
{synthesis[:3000]}

Create a 12-15 slide presentation outline for a CEO/board audience.
Format each slide as:
**Slide N: [Title]**
- Key point 1
- Key point 2
- Suggested visual/chart

Follow the Situation-Complication-Resolution structure.
Slide 1 = title. Slide 2 = agenda. Slides 3-4 = situation. Slides 5-6 = complication/findings.
Slides 7-10 = recommendation + rationale. Slides 11-12 = risks + mitigations. Slide 13 = next steps.
""")

    def run(self, engagement_state, synthesis_result: dict) -> str:
        """Generate full PDF report and slide outline. Returns PDF path."""
        title = engagement_state.title
        client = engagement_state.client_name or "Client"
        date = datetime.now().strftime("%B %d, %Y")
        exec_summary = synthesis_result.get("executive_summary", "")
        full_synthesis = synthesis_result.get("full_synthesis", "")

        # Build sections from workstreams
        ws = engagement_state.all_workstreams()
        sections = {}
        if ws.get("research"):
            sections["Research & Market Intelligence"] = ws["research"][:2500]
        if ws.get("frameworks"):
            sections["Strategic Framework Analysis"] = ws["frameworks"][:2500]
        if ws.get("financial"):
            sections["Financial Analysis"] = ws["financial"][:2500]
        if ws.get("benchmarks"):
            sections["External Benchmarks"] = ws["benchmarks"][:2000]
        if ws.get("redteam"):
            sections["Risk & Red Team Review"] = ws["redteam"][:2000]
        sections["Recommendation & Implementation"] = full_synthesis[:3000]

        # Slide outline
        slide_outline = self.slide_outline(full_synthesis, title)
        sections["Presentation Outline"] = slide_outline

        # Generate PDF
        pdf_path = str(engagement_state.dir / "final_report.pdf")
        generate_pdf(title, client, date, exec_summary, sections, pdf_path)

        # Also save slide outline as markdown
        (engagement_state.dir / "slide_outline.md").write_text(slide_outline, encoding="utf-8")

        return pdf_path

    def validate(self) -> dict:
        try:
            result = self.slide_outline(
                "Recommendation: Enter the enterprise healthcare AI market via a partnerships-first strategy, targeting radiology departments. TAM $8B, SAM $1.2B, 3-year SOM $180M.",
                "Healthcare AI Market Entry"
            )
            passed = len(result) > 200 and "slide" in result.lower()
            return {"passed": passed, "output": result[:300], "notes": "Slide outline generation test"}
        except Exception as e:
            return {"passed": False, "output": "", "notes": str(e)}
