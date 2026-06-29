"""Patent claims generation — independent + dependent claims in CN format."""

from __future__ import annotations

from paper2patent.ir import PaperIR, PaperAnalysis, PatentClaim
from paper2patent.converter.terminology import boilerplate
from paper2patent.converter.expert_mode import (
    get_claim_template, get_dep_claim_variations, get_forbidden_terms,
)


class ClaimsGenerator:
    """Generate CN patent claims from PaperAnalysis — guided by Patent Expert KB."""

    def __init__(self, patent_type: str = "cn"):
        self.patent_type = patent_type
        self.forbidden_terms = get_forbidden_terms()

    def generate(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> list[PatentClaim]:
        """Generate the full claims set."""
        claims = []
        claim_num = 0

        # --- Independent Claim 1: Method ---
        if analysis.is_method_invention and analysis.method_steps:
            claim_num += 1
            method_claim = self._independent_method(claim_num, paper_ir, analysis)
            claims.append(method_claim)

        # --- Independent Claim 2: System ---
        if analysis.is_system_invention and analysis.system_components:
            claim_num += 1
            system_claim = self._independent_system(claim_num, paper_ir, analysis)
            claims.append(system_claim)

        # --- Dependent claims from parameters ---
        if analysis.method_steps and analysis.key_parameters:
            for param in analysis.key_parameters:
                claim_num += 1
                claims.append(self._dependent_parameter(
                    number=claim_num,
                    param=param,
                    parent_claim=1,
                    subject=self._subject(paper_ir, "方法"),
                ))

        # --- Dependent claims from alternatives ---
        if analysis.method_steps and analysis.alternatives:
            for i, alt in enumerate(analysis.alternatives[:5]):
                claim_num += 1
                claims.append(self._dependent_alternative(
                    number=claim_num,
                    alternative=alt,
                    parent_claim=1,
                    subject=self._subject(paper_ir, "方法"),
                ))

        # --- Dependent claims from novelty points ---
        if analysis.novelty_points:
            for np in analysis.novelty_points[1:4]:  # skip first (covered by indep. claim)
                claim_num += 1
                claims.append(PatentClaim(
                    number=claim_num,
                    claim_type="dependent",
                    category="method",
                    text=f"根据权利要求1所述的方法，其特征在于，{np.description}。",
                    depends_on=[1],
                ))

        # --- Learned from 109 real patents: electronic device + storage medium claims ---
        first_independent = claims[0].number if claims else 1
        last_independent = max(c.number for c in claims if c.claim_type == "independent") if claims else 1

        if analysis.is_method_invention:
            claim_num += 1
            claims.append(PatentClaim(
                number=claim_num,
                claim_type="independent",
                category="device",
                text=(
                    f"一种电子设备，包括：\n"
                    f"一个或多个处理器；\n"
                    f"存储装置，用于存储一个或多个程序；\n"
                    f"当所述一个或多个程序被所述一个或多个处理器执行时，使得所述一个或多个"
                    f"处理器实现如权利要求{first_independent}至{last_independent}中任一所述的方法。"
                ),
                depends_on=[],
            ))

            claim_num += 1
            claims.append(PatentClaim(
                number=claim_num,
                claim_type="independent",
                category="medium",
                text=(
                    f"一种计算机可读存储介质，其上存储有计算机程序，"
                    f"所述计算机程序被处理器执行时实现如权利要求{first_independent}至"
                    f"{last_independent}中任一所述的方法。"
                ),
                depends_on=[],
            ))

        return claims

    # ------------------------------------------------------------------
    # Independent claims
    # ------------------------------------------------------------------

    def _independent_method(
        self, num: int, paper_ir: PaperIR, analysis: PaperAnalysis
    ) -> PatentClaim:
        subject = self._subject(paper_ir, "方法")
        lines = [f"一种{subject}，其特征在于，包括："]

        for i, step in enumerate(analysis.method_steps):
            ref = step.reference_num
            desc = step.description.rstrip("；。，")
            sep = "。" if i == len(analysis.method_steps) - 1 else "；"
            lines.append(f"步骤S{ref}：{desc}{sep}")

        # Only final step gets full stop — CN single-sentence rule
        text = "\n".join(lines)

        return PatentClaim(
            number=num,
            claim_type="independent",
            category="method",
            text=text,
            reference_nums=[s.reference_num for s in analysis.method_steps],
        )

    def _independent_system(
        self, num: int, paper_ir: PaperIR, analysis: PaperAnalysis
    ) -> PatentClaim:
        subject = self._subject(paper_ir, "装置")
        lines = [f"一种{subject}，其特征在于，包括："]

        for i, comp in enumerate(analysis.system_components):
            ref = comp.reference_num
            sep = "。" if i == len(analysis.system_components) - 1 else "；"
            lines.append(f"{comp.name}({ref})，用于{comp.function}{sep}")

        text = "\n".join(lines)

        return PatentClaim(
            number=num,
            claim_type="independent",
            category="system",
            text=text,
            reference_nums=[c.reference_num for c in analysis.system_components],
        )

    # ------------------------------------------------------------------
    # Dependent claims
    # ------------------------------------------------------------------

    def _dependent_parameter(
        self, number: int, param: dict, parent_claim: int, subject: str
    ) -> PatentClaim:
        name = param.get("name", "参数")
        value = param.get("value", "预设范围")

        return PatentClaim(
            number=number,
            claim_type="dependent",
            category="method",
            text=f"根据权利要求{parent_claim}所述的{subject}，其特征在于，所述{name}的取值范围为{value}。",
            depends_on=[parent_claim],
        )

    def _dependent_alternative(
        self, number: int, alternative: str, parent_claim: int, subject: str
    ) -> PatentClaim:
        return PatentClaim(
            number=number,
            claim_type="dependent",
            category="method",
            text=f"根据权利要求{parent_claim}所述的{subject}，其特征在于，{alternative}。",
            depends_on=[parent_claim],
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _subject(self, paper_ir: PaperIR, suffix: str) -> str:
        """Extract a clean subject name from the paper title."""
        import re
        title = paper_ir.title or ""
        # Strip markdown formatting (**, __, etc.)
        title = re.sub(r'\*{1,3}|_{1,3}|`{1,3}', '', title)
        # Remove common prefixes
        for prefix in ["一种", "基于", "用于"]:
            if title.startswith(prefix):
                title = title[len(prefix):]
        # Remove subtitle after colon
        title = title.split(":")[0].strip()
        # Strip existing patent suffixes to avoid doubling
        for existing in ["的方法和装置", "的方法", "的装置", "的系统", "方法", "装置", "系统"]:
            if title.endswith(existing):
                title = title[:-len(existing)].strip()
        # Limit length
        if len(title) > 40:
            title = title[:40]
        return title + suffix if title else suffix
