"""Validate a patent document for CNIPA compliance."""

from __future__ import annotations

import re
from typing import Optional

from paper2patent.ir import PatentIR, PatentClaim


class PatentValidator:
    """Validate a PatentIR against CN patent rules."""

    def __init__(self, patent_type: str = "cn"):
        self.patent_type = patent_type
        self.issues: list[str] = []
        self.warnings: list[str] = []

    def validate(self, patent: PatentIR) -> str:
        """Run all validations and return a report string."""
        self.issues = []
        self.warnings = []

        self._check_claims_single_sentence(patent.claims)
        self._check_claims_multi_dependency(patent.claims)
        self._check_abstract_length(patent.abstract)
        self._check_required_sections(patent.sections)
        self._check_figure_reference_cross(patent)
        self._check_claims_forbidden_terms(patent.claims)
        self._check_overuse_of_benfaming(patent)

        return self._build_report()

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def _check_claims_single_sentence(self, claims: list[PatentClaim]) -> None:
        """Each claim must be a single sentence (only one 。at the end for CN)."""
        for claim in claims:
            # Count periods that are not inside parentheses
            text_without_parens = re.sub(r'\([^)]*\)', '', claim.text)
            # Remove the final period
            body = text_without_parens.rstrip("。；;")
            # Check for internal periods or Chinese full stops
            internal_periods = body.count("。")
            internal_semicolons = body.count("；")

            if internal_periods > 0:
                self.issues.append(
                    f"权利要求{claim.number}：单句中包含{internal_periods}个句号（。）。"
                    f"每项权利要求的正文中间不能使用句号，只能有一个句号在结尾。"
                )

            # For CN claims, internal semicolons (；) are also problematic
            # But claim elements are separated by ； in practice... this is a relaxed check
            # Strict interpretation says only 、and ，are allowed
            # We warn rather than error
            if internal_semicolons > 0 and self.patent_type == "cn":
                self.warnings.append(
                    f"权利要求{claim.number}：包含{internal_semicolons}个分号（；）。"
                    f"在严格解释下，CN权利要求内部只允许逗号和枚举逗号。"
                )

    def _check_claims_multi_dependency(self, claims: list[PatentClaim]) -> None:
        """No claim may depend on a claim that is itself multi-dependent (多引多)."""
        multi_dep_claims = set()

        for claim in claims:
            if len(claim.depends_on) > 1:
                multi_dep_claims.add(claim.number)

        for claim in claims:
            for dep in claim.depends_on:
                if dep in multi_dep_claims:
                    self.issues.append(
                        f"权利要求{claim.number}：引用了权利要求{dep}，但权利要求{dep}引用了多项权利要求（多引多）。"
                        f"CN审查指南禁止多引多。"
                    )

    def _check_abstract_length(self, abstract: str) -> None:
        """CN invention patent abstract must be <= 300 characters."""
        if not abstract:
            self.issues.append("摘要内容为空。")
            return

        # Count actual characters (excluding whitespace prefix/suffix)
        char_count = len(abstract.strip())
        if char_count > 300:
            self.warnings.append(
                f"摘要长度{char_count}字，超过300字的建议上限。"
                f"请精简摘要内容。"
            )

    def _check_required_sections(self, sections) -> None:
        """Check that all 5 mandatory CN 【】sections are present."""
        required_headings = [
            "【技术领域】",
            "【背景技术】",
            "【发明内容】",
            "【附图说明】",
            "【具体实施方式】",
        ]

        found_headings = {s.heading for s in sections}

        for required in required_headings:
            if required not in found_headings:
                self.issues.append(f"缺少必选章节：{required}。CN说明书必须包含5个必选章节。")

    def _check_figure_reference_cross(self, patent: PatentIR) -> None:
        """Check that all reference numerals in figures appear in the description."""
        # Collect reference numbers from figures
        figure_ref_nums = set()
        for fig in patent.figures:
            for rn in fig.get("ref_nums", []):
                figure_ref_nums.add(rn)
        for diag in patent.diagrams:
            for rn in diag.get("ref_nums", []):
                figure_ref_nums.add(rn)

        # Collect reference numbers from claims and description
        text_ref_nums = set()
        # Claims
        for claim in patent.claims:
            text_ref_nums.update(claim.reference_nums)
        # Description sections
        for section in patent.sections:
            # Extract (数字) patterns
            found = re.findall(r'\((\d+)\)', section.content)
            text_ref_nums.update(int(n) for n in found)

        # Cross-check
        if figure_ref_nums and text_ref_nums:
            missing_in_text = figure_ref_nums - text_ref_nums
            if missing_in_text:
                self.warnings.append(
                    f"附图中的引用号{missing_in_text}未在说明书或权利要求中出现。"
                    f"CN规定所有附图中的标记必须在说明书中提及。"
                )

    def _check_claims_forbidden_terms(self, claims: list[PatentClaim]) -> None:
        """Check for forbidden vague terms in claims."""
        forbidden = ["等等", "最好是", "约", "接近", "大致", "诸如此类"]
        for claim in claims:
            for term in forbidden:
                if term in claim.text:
                    self.warnings.append(
                        f"权利要求{claim.number}：使用了模糊用语'{term}'。"
                        f"CN权利要求中应避免使用这些不确定的表述。"
                    )
                    break  # One warning per claim

    def _check_overuse_of_benfaming(self, patent: PatentIR) -> None:
        """Warn about overuse of '本发明' which can limit scope."""
        count = 0
        for section in patent.sections:
            count += section.content.count("本发明")

        if count > 5:
            self.warnings.append(
                f"说明书中使用了{count}次'本发明'。建议替换为'本申请'、'本实施例'或"
                f"'在本公开的一个方面'，以避免不当限制保护范围。"
            )

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def _build_report(self) -> str:
        lines = []

        lines.append("=" * 50)
        lines.append("专利校验报告")
        lines.append("=" * 50)
        lines.append("")

        if not self.issues and not self.warnings:
            lines.append("✓ 校验通过，未发现问题。")
        else:
            if self.issues:
                lines.append(f"## 问题 ({len(self.issues)}项) — 需要修改")
                lines.append("")
                for i, issue in enumerate(self.issues, 1):
                    lines.append(f"  [{i}] {issue}")
                lines.append("")

            if self.warnings:
                lines.append(f"## 警告 ({len(self.warnings)}项) — 建议关注")
                lines.append("")
                for i, warning in enumerate(self.warnings, 1):
                    lines.append(f"  [{i}] {warning}")
                lines.append("")

        lines.append("=" * 50)
        return "\n".join(lines)
