"""Map PaperAnalysis → patent sections (CN format).

Produces PatentIR with populated sections following CNIPA structure.
"""

from __future__ import annotations

from paper2patent.ir import (
    PaperIR, PaperAnalysis, PatentIR, PatentSection,
)
from paper2patent.converter.terminology import (
    academic_to_patent_phrase, boilerplate, translate_term, LEARNED_BOILERPLATE,
)
from paper2patent.converter.expert_mode import (
    get_boilerplate as expert_boilerplate,
    get_section_guide,
)

# Re-export expert system prompt for external use
from paper2patent.converter.expert_mode import EXPERT_SYSTEM_PROMPT  # noqa: F401


class SectionMapper:
    """Convert paper analysis into structured patent sections."""

    def __init__(self, patent_type: str = "cn"):
        self.patent_type = patent_type

    def map(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> PatentIR:
        """Generate a PatentIR from paper analysis."""
        patent = PatentIR(
            title=self._make_patent_title(paper_ir.title, analysis),
            patent_type=self.patent_type,
        )

        patent.sections = [
            self._technical_field(paper_ir, analysis),
            self._background(paper_ir, analysis),
            self._invention_summary(paper_ir, analysis),
            self._drawing_brief(paper_ir, analysis),
            self._detailed_description(paper_ir, analysis),
        ]

        patent.abstract = self._abstract(paper_ir, analysis)

        return patent

    # ------------------------------------------------------------------
    # Section generators
    # ------------------------------------------------------------------

    def _make_patent_title(self, paper_title: str, analysis: PaperAnalysis) -> str:
        """Convert paper title to patent title format."""
        import re
        # Clean LaTeX/markdown formatting artifacts
        title = re.sub(r'\*{1,3}|_{1,3}|`{1,3}', '', paper_title.strip())
        # Remove colons and subtitles (patent titles are simpler)
        title = title.split(":")[0].strip()

        # Make it patent-like if not already
        if "方法" not in title and "装置" not in title and "系统" not in title:
            if analysis.is_method_invention and analysis.is_system_invention:
                title = f"一种{title}的方法和装置"
            elif analysis.is_method_invention:
                title = f"一种{title}的方法"
            elif analysis.is_system_invention:
                title = f"一种{title}的装置"
            else:
                title = f"一种{title}的方法和装置"

        if not title.startswith("一种"):
            title = "一种" + title

        return title

    def _technical_field(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> PatentSection:
        # Use expert boilerplate, fall back to analysis.technical_field
        if analysis.technical_field:
            content = analysis.technical_field
        else:
            content = LEARNED_BOILERPLATE.get("tech_field", "本发明涉及{field}技术领域，具体涉及一种{title}。").format(
                field="人工智能", title=paper_ir.title
            )
        return PatentSection(heading="【技术领域】", content=content)

    def _background(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> PatentSection:
        lines = []

        # Problem statement
        if analysis.technical_problem:
            lines.append(f"随着技术的发展，{analysis.technical_problem}成为一个亟待解决的问题。")
        else:
            lines.append("现有技术中，相关方法存在一定的局限性。")

        lines.append("")

        # Limitations of prior art (from paper sections)
        intro_related = ""
        for sec in paper_ir.sections:
            if any(kw in sec.heading.lower() for kw in ("introduction", "related work", "background", "引言", "相关工作", "背景")):
                intro_related += sec.content[:1000]
                break

        if intro_related:
            # Defensive summary: only mention limitations
            lines.append("现有技术的方法主要存在以下不足：")
            # Extract limitation-like sentences
            import re
            limit_sentences = re.findall(
                r'[^。.]*(?:然而|但是|但|不足|限制|局限|无法|不能|缺少|缺乏|难以|问题|缺点|缺陷)[^。.]*[。.]',
                intro_related
            )
            if limit_sentences:
                for ls in limit_sentences[:5]:
                    cleaned = academic_to_patent_phrase(ls.strip())
                    if cleaned:
                        lines.append(f"- {cleaned}")
            else:
                lines.append("- 现有技术的方法在处理效率和准确性方面仍有改进空间。")

        return PatentSection(heading="【背景技术】", content="\n".join(lines))

    def _invention_summary(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> PatentSection:
        lines = []

        # Invention purpose (发明目的)
        problem = analysis.technical_problem or "现有技术的不足"
        lines.append(f"本发明旨在解决{problem}的技术问题。")
        lines.append("")

        # Technical solution (技术方案) - summarize method steps
        lines.append("为实现上述目的，本发明采用如下技术方案：")
        lines.append("")

        if analysis.is_method_invention and analysis.method_steps:
            lines.append(f"一种{paper_ir.title}的方法，包括以下步骤：")
            for step in analysis.method_steps:
                lines.append(
                    f"步骤S{step.reference_num}：{step.description}；"
                )
        lines.append("")

        if analysis.is_system_invention and analysis.system_components:
            lines.append(f"一种{paper_ir.title}的装置，包括：")
            for comp in analysis.system_components:
                lines.append(
                    f"{comp.name}({comp.reference_num})，用于{comp.function}；"
                )
        lines.append("")

        # Beneficial effects (有益效果)
        lines.append("与现有技术相比，本发明具有以下有益效果：")
        if analysis.novelty_points:
            for i, np in enumerate(analysis.novelty_points, 1):
                lines.append(f"{i}. {np.description}。")
        else:
            lines.append("1. 通过上述技术方案，有效解决了现有技术中的技术问题。")

        return PatentSection(heading="【发明内容】", content="\n".join(lines))

    def _drawing_brief(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> PatentSection:
        """Brief description of drawings — populated after figures are extracted/generated."""
        lines = ["下面结合附图对本发明的具体实施方式作进一步详细的说明。", ""]

        # This will be updated after figures and diagrams are generated
        fig_num = 1
        if paper_ir.figures:
            for fig in paper_ir.figures:
                caption = fig.caption if fig.caption else f"图{fig_num}是本发明实施例的示意图"
                lines.append(f"图{fig_num} 是{caption}；")
                fig_num += 1

        if analysis.method_steps:
            lines.append(f"图{fig_num} 是本发明方法的流程示意图；")
            fig_num += 1

        if analysis.system_components:
            lines.append(f"图{fig_num} 是本发明系统的结构框图；")

        return PatentSection(heading="【附图说明】", content="\n".join(lines))

    def _detailed_description(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> PatentSection:
        """Generate detailed implementation description with embodiments."""
        lines = []

        # Embodiment 1: Main implementation (method)
        if analysis.method_steps:
            lines.append("【实施例1】")
            lines.append("")
            lines.append("在本实施例中，提供了一种具体的实施方式。")
            lines.append("")

            for step in analysis.method_steps:
                lines.append(
                    f"步骤S{step.reference_num}："
                    f"{step.actor + '对' if step.actor else ''}"
                    f"{step.input_data or '输入数据'}进行{step.description.split('对')[-1] if '对' in step.description else step.description}，"
                    f"{'得到' + step.output_data + '；' if step.output_data else '；'}"
                )

            lines.append("")
            # Add system components description
            if analysis.system_components:
                lines.append("其中，所述系统包括：")
                for comp in analysis.system_components:
                    lines.append(
                        f"{comp.name}({comp.reference_num})，"
                        f"用于{comp.function}。"
                    )

            lines.append("")

        # Embodiment 2: Variations (if any)
        if analysis.alternatives:
            lines.append("【实施例2】")
            lines.append("")
            lines.append("本实施例与实施例1的区别在于：")
            for alt in analysis.alternatives:
                lines.append(f"- {alt}")
            lines.append("")
            lines.append("其余部分与实施例1相同，在此不再赘述。")
            lines.append("")

        # Parameter ranges
        if analysis.key_parameters:
            lines.append("需要说明的是，上述实施例中的参数可以根据实际应用场景进行调整：")
            for param in analysis.key_parameters:
                name = param.get("name", "")
                value = param.get("value", "")
                context = param.get("context", "")
                lines.append(f"- {name}：可以设置为{value}；{context}")
            lines.append("")

        # Additional embodiments from paper sections
        method_sections_added = 0
        for sec in paper_ir.sections:
            if any(kw in sec.heading.lower() for kw in ("method", "approach", "model", "architecture", "implementation", "方法", "方案", "实施")):
                if method_sections_added == 0:
                    method_sections_added += 1
                    continue  # skip first (already used as Embodiment 1)

                if method_sections_added < 3:
                    lines.append(f"【实施例{method_sections_added + 2}】")
                    lines.append("")
                    content = sec.content[:1500]
                    lines.append(academic_to_patent_phrase(content))
                    lines.append("")
                    method_sections_added += 1

        # Closing boilerplate — from expert knowledge base
        closing = LEARNED_BOILERPLATE.get("closing",
            "以上所述仅为本发明的优选实施例而已，并不用于限制本发明。"
            "凡在本发明的精神和原则之内，所作的任何修改、等同替换、改进等，"
            "均应包含在本发明的保护范围之内。")
        lines.append(closing)

        return PatentSection(heading="【具体实施方式】", content="\n".join(lines))

    def _abstract(self, paper_ir: PaperIR, analysis: PaperAnalysis) -> str:
        """Generate CN patent abstract (< 300 chars) using expert boilerplate."""
        # Use expert abstract template
        template = LEARNED_BOILERPLATE.get("abstract_opening",
            "本发明公开了一种{title}，{core_idea}。")

        parts = []

        # Opening: what the invention is
        if analysis.is_method_invention:
            parts.append(f"本发明提供一种{paper_ir.title}的方法。")
        if analysis.is_system_invention:
            parts.append(f"本发明还提供一种{paper_ir.title}的装置。")

        # Core steps (abbreviated)
        if analysis.method_steps:
            steps_summary = []
            for step in analysis.method_steps[:3]:  # top 3 steps
                steps_summary.append(step.description)
            parts.append(f"该方法包括：{'；'.join(steps_summary)}。")

        # Benefits
        if analysis.novelty_points:
            parts.append(f"本发明{analysis.novelty_points[0].description}。")

        abstract = "".join(parts)

        # Truncate if over 300 chars (CN requirement)
        if len(abstract) > 300:
            abstract = abstract[:295] + "……"

        return abstract
