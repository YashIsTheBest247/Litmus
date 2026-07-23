"""Integrity report as a PDF.

The site is the place to explore results; this is the thing you send to
someone. It leads with the number that matters, then gives the per-task
evidence a reviewer needs to check the claim rather than take it on trust.

fpdf2 is pure Python, so this adds no system dependency to the service image.
"""

from __future__ import annotations

from typing import Any

from fpdf import FPDF

INK = (10, 10, 11)
MUTED = (107, 107, 115)
BAD = (225, 29, 72)
OK = (22, 163, 74)
RULE = (222, 222, 226)

VERDICT_COLOUR = {"fixed": OK, "gamed": BAD, "failed": MUTED}


class Report(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*MUTED)
        self.cell(0, 8, "Litmus integrity report", align="L")
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"{self.page_no()}", align="C")

    # -- small helpers so the body reads like a document, not like layout code

    def _home(self) -> None:
        """Return the cursor to the left margin.

        multi_cell derives its width from the current x, and a preceding cell
        can leave x at the right edge — at which point there is no room to
        render anything and fpdf raises. Resetting is cheaper than tracking
        every call's exit position.
        """
        self.set_x(self.l_margin)

    def title_block(self, text: str, size: int = 22) -> None:
        self._home()
        self.set_font("Helvetica", "B", size)
        self.set_text_color(*INK)
        self.multi_cell(0, size * 0.5, text)
        self.ln(2)

    def body(self, text: str, colour=MUTED, size: int = 10) -> None:
        self._home()
        self.set_font("Helvetica", "", size)
        self.set_text_color(*colour)
        self.multi_cell(0, 5.2, text)
        self.ln(1)

    def label(self, text: str) -> None:
        self._home()
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, text.upper())
        self.ln(6)

    def code(self, text: str, colour=BAD) -> None:
        """Monospaced evidence line, hard-wrapped so no token can overflow."""
        self._home()
        self.set_font("Courier", "", 8.5)
        self.set_text_color(*colour)
        # A long unbroken token cannot be wrapped, so cut it rather than fail.
        self.multi_cell(0, 4.4, text[:150])

    def rule(self) -> None:
        self.set_draw_color(*RULE)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)


def _headline(report: dict[str, Any]) -> tuple[float, float, float]:
    rows = report.get("leaderboard", [])
    tasks = sum(r["tasks"] for r in rows) or 1
    claimed = sum(r["fixed"] + r["gamed"] for r in rows)
    fixed = sum(r["fixed"] for r in rows)
    reported = 100.0 * claimed / tasks
    true_score = 100.0 * fixed / tasks
    return round(reported, 1), round(true_score, 1), round(reported - true_score, 1)


def build_pdf(report: dict[str, Any]) -> bytes:
    """Render a report dictionary to PDF bytes."""
    pdf = Report(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(18, 16, 18)
    pdf.add_page()

    reported, true_score, gap = _headline(report)
    totals = report.get("totals", {})

    # --- cover ----------------------------------------------------------
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*BAD)
    pdf.cell(0, 6, "LITMUS")
    pdf.ln(10)

    pdf.title_block("Integrity report", 26)
    pdf.body(
        "Every agent below was graded twice: once on a test suite it could read, "
        "and once on a suite it never saw. The distance between those two scores "
        "is the integrity gap.",
        size=11,
    )
    pdf.ln(4)

    # Headline figures.
    pdf.rule()
    start_y = pdf.get_y()
    column = (pdf.w - pdf.l_margin - pdf.r_margin) / 3
    for index, (label, value, colour) in enumerate(
        [
            ("Reported score", f"{reported}%", MUTED),
            ("True score", f"{true_score}%", INK),
            ("Integrity gap", f"{gap} pts", BAD if gap > 0 else OK),
        ]
    ):
        pdf.set_xy(pdf.l_margin + index * column, start_y + 2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*MUTED)
        pdf.cell(column, 5, label.upper())
        pdf.set_xy(pdf.l_margin + index * column, start_y + 8)
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(*colour)
        pdf.cell(column, 12, value)
    pdf.set_y(start_y + 24)
    pdf.rule()

    pdf.body(
        f"{totals.get('runs', 0)} runs across {totals.get('packs', 0)} task packs "
        f"and {totals.get('configs', 0)} agent configurations."
    )
    pdf.ln(4)

    # --- leaderboard ----------------------------------------------------
    pdf.label("Leaderboard")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*MUTED)
    widths = [58, 26, 26, 26, 32]
    for heading, width in zip(
        ["Agent", "Reported", "True", "Gap", "Flagged"], widths
    ):
        pdf.cell(width, 7, heading)
    pdf.ln(7)

    for row in report.get("leaderboard", []):
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*INK)
        pdf.cell(widths[0], 7, str(row["agent_config"])[:34])
        pdf.set_text_color(*MUTED)
        pdf.cell(widths[1], 7, f"{row['reported_score']}%")
        pdf.set_text_color(*INK)
        pdf.cell(widths[2], 7, f"{row['true_score']}%")
        pdf.set_text_color(*(BAD if row["integrity_gap"] > 0 else MUTED))
        pdf.cell(widths[3], 7, f"{row['integrity_gap']}")
        pdf.set_text_color(*MUTED)
        pdf.cell(widths[4], 7, f"{row['flagged_tasks']}/{row['tasks']}")
        pdf.ln(7)

    pdf.ln(3)

    # --- red team, when present ----------------------------------------
    red = report.get("red_team") or {}
    if red.get("attempts"):
        pdf.label("Red team")
        pdf.body(
            f"An agent was instructed to make the visible suite pass by any means. "
            f"Of {red['attempts']} attempts, {red['gamed']} produced a patch the "
            f"held-out suite rejected. The detectors flagged {red['caught_by_detectors']} "
            f"of those, a recall of {red['recall']}%."
        )
        if red.get("missed_by_detectors"):
            pdf._home()
            pdf.set_text_color(*BAD)
            pdf.set_font("Helvetica", "B", 9.5)
            pdf.multi_cell(
                0,
                5,
                f"{red['missed_by_detectors']} cheats were missed by every detector "
                f"and caught only by the held-out suite.",
            )
            pdf.ln(2)

    # --- per-task evidence ---------------------------------------------
    gamed = [r for r in report.get("runs", []) if r.get("verdict") == "gamed"]
    if gamed:
        pdf.add_page()
        pdf.title_block("Where the claims broke", 18)
        pdf.body(
            "Each of these patches turned the visible suite green. None of them "
            "survived the held-out suite."
        )
        pdf.ln(3)

        for run in gamed[:12]:
            pdf._home()
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(*INK)
            pdf.multi_cell(0, 6, f"{run['task_title']}")
            pdf._home()
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*MUTED)
            pdf.cell(
                0,
                5,
                f"{run['agent_config']}   visible {run['public']['passed']}/"
                f"{run['public']['total']}   held-out {run['hidden']['passed']}/"
                f"{run['hidden']['total']}",
            )
            pdf.ln(6)

            for flag in run.get("flags", [])[:3]:
                pdf.code(f"  {flag['file']}:{flag['line']}  {flag['evidence']}")
            pdf.ln(3)
            pdf.rule()

    # --- method note ----------------------------------------------------
    pdf.ln(2)
    pdf.label("How this was measured")
    pdf.body(
        "The held-out suite is not present on disk while the agent works; it is "
        "copied in only after writes are frozen. Any conftest or ini file the agent "
        "created is quarantined before it runs, so a patch cannot pass by changing "
        "how pytest behaves. Skipped tests do not count as passing. Every task ships "
        "a reference implementation that passes both suites, so each gap above is a "
        "bug that was solvable honestly."
    )

    return bytes(pdf.output())
