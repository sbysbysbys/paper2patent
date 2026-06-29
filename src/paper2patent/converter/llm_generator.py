"""LLM-driven patent content generator — replaces all rule-based generators.

Uses a single comprehensive prompt to generate the full patent document:
abstract + claims + all 5 description sections — all from the paper content.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from paper2patent.ir import (
    PaperIR, PaperAnalysis, PatentIR, PatentSection, PatentClaim,
    MethodStep, SystemComponent, NoveltyPoint,
)
from paper2patent.converter.expert_mode import EXPERT_SYSTEM_PROMPT

# ═══════════════════════════════════════════════════════════════
# Comprehensive LLM prompt for full patent generation
# ═══════════════════════════════════════════════════════════════

FULL_PATENT_PROMPT = """你是资深中国专利代理人。请根据以下论文内容，撰写一份完整的中国发明专利。

## 撰写要求

### 格式规范
- 正文使用"本申请"或"本技术"指代发明，严禁使用"本发明"
- 权利要求每项一个自然段，编号从1开始
- 说明书五个必选部分：【技术领域】【背景技术】【发明内容】【附图说明】【具体实施方式】
- 附图说明格式："图X是本申请实施例提供的...示意图"

### 内容要求
- 【背景技术】要详细描述现有技术及其局限性（3-5段），引用论文中提到的问题
- 【发明内容】包含技术问题、技术方案（分步骤详述）、有益效果（至少3点）
- 【具体实施方式】至少写3个实施例，每个实施例不少于2段，包含具体步骤和参数范围
- 权利要求不少于8条，包含方法独立权利要求、装置独立权利要求、至少4条从属权利要求
- 每条从属权利要求对应一个具体的技术特征限定
- 保留论文中的数学公式，用中文描述每个符号的含义
- 总字数不少于3000字

### 权利要求格式
- 独立权利要求（方法）："一种...方法，其特征在于，包括：步骤S110...；步骤S120...；"
- 独立权利要求（装置）："一种...装置，其特征在于，包括：模块A(10)，用于...；模块B(20)，用于...；"
- 从属权利要求："根据权利要求X所述的方法，其特征在于，..."

## 论文内容

{paper_text}

## 输出格式

请严格按以下JSON格式输出（只返回JSON，不要其他解释）：

```json
{{
  "title": "一种...的方法和装置",
  "abstract": "本申请公开了一种...（不超过300字）",
  "claims": [
    {{"number": 1, "text": "一种...方法，其特征在于，包括：\\n步骤S110：...；\\n步骤S120：...。"}},
    {{"number": 2, "text": "一种...装置，其特征在于，包括：\\n模块A(10)，用于...。", "depends_on": []}},
    {{"number": 3, "text": "根据权利要求1所述的方法，其特征在于，...。", "depends_on": [1]}}
  ],
  "sections": [
    {{"heading": "【技术领域】", "content": "本申请涉及...技术领域，具体涉及一种...。（1-2段）"}},
    {{"heading": "【背景技术】", "content": "详细描述现有技术及局限性，3-5段，引用论文中的相关工作。"}},
    {{"heading": "【发明内容】", "content": "技术问题 + 技术方案（分步骤，保留公式） + 有益效果（至少3点）。"}},
    {{"heading": "【附图说明】", "content": "逐图说明：图1是...示意图；图2是...流程图；等。"}},
    {{"heading": "【具体实施方式】", "content": "至少3个实施例，每个包含具体步骤、参数范围。公式用中文描述各符号。"}}
  ]
}}
```

重要：Background和Detailed Description要写详细，不要简短。每个section至少300-500字。"""


class LLMGenerator:
    """Generate full PatentIR from PaperIR using LLM (Claude).

    Replaces paper_analyzer + section_mapper + claims_generator
    with a single comprehensive LLM call.
    """

    def __init__(self, backend: str = "claude", verbose: bool = False):
        self.backend = backend
        self.verbose = verbose

    def generate(self, paper_ir: PaperIR) -> PatentIR:
        """Generate complete patent from paper content.

        Uses LLM for content generation, with rules-based fallback.
        """
        paper_text = self._build_paper_text(paper_ir)

        # Try LLM
        try:
            result_json = self._call_llm(paper_text)
            patent_ir = self._parse_patent(result_json, paper_ir)
            if self.verbose:
                print(f"[green]LLM generated: {len(patent_ir.claims)} claims, "
                      f"{len(patent_ir.sections)} sections, "
                      f"{sum(len(s.content) for s in patent_ir.sections)} chars total[/green]")
            return patent_ir
        except Exception as e:
            if self.verbose:
                print(f"[yellow]LLM generation failed ({e}), using expert rules[/yellow]")
            return self._fallback_generate(paper_ir)

    # ══════════════════════════════════════════════════════════
    # Paper text builder
    # ══════════════════════════════════════════════════════════

    def _build_paper_text(self, paper_ir: PaperIR) -> str:
        """Build comprehensive paper text for the LLM prompt."""
        parts = []

        if paper_ir.title:
            parts.append(f"# {paper_ir.title}")

        if paper_ir.abstract:
            parts.append(f"## 摘要\n{paper_ir.abstract}")

        # Sections with content
        for sec in paper_ir.sections:
            if sec.heading:
                parts.append(f"## {sec.heading}")
            if sec.content:
                # Include full content (no truncation for LLM)
                parts.append(sec.content)

        # Equations
        if paper_ir.equations:
            parts.append("## 数学公式")
            for eq in paper_ir.equations:
                parts.append(f"公式{eq.index}: {eq.latex}")
                if eq.context:
                    parts.append(f"上下文: {eq.context}")

        # Citations
        if paper_ir.citations:
            parts.append("## 参考文献")
            for cite in paper_ir.citations:
                parts.append(f"[{cite.key}] {cite.authors} ({cite.year}). {cite.title}. {cite.venue}")

        return "\n\n".join(parts)

    # ══════════════════════════════════════════════════════════
    # LLM call
    # ══════════════════════════════════════════════════════════

    def _call_llm(self, paper_text: str) -> dict:
        """Call LLM backend to generate patent content."""
        if self.backend == "claude":
            return self._call_claude(paper_text)
        elif self.backend == "openai":
            return self._call_openai(paper_text)
        raise ValueError(f"Unknown LLM backend: {self.backend}")

    def _call_claude(self, paper_text: str) -> dict:
        """Use Anthropic Claude."""
        import anthropic
        client = anthropic.Anthropic()

        prompt = FULL_PATENT_PROMPT.format(paper_text=paper_text[:80000])

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._extract_json(message.content[0].text)

    def _call_openai(self, paper_text: str) -> dict:
        """Use OpenAI."""
        import openai
        client = openai.OpenAI()

        prompt = FULL_PATENT_PROMPT.format(paper_text=paper_text[:80000])

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response."""
        # Direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # ```json ... ``` block
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if m:
            return json.loads(m.group(1))
        # Raw {...}
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            return json.loads(m.group(0))
        raise ValueError(f"Cannot parse LLM response as JSON: {text[:500]}")

    # ══════════════════════════════════════════════════════════
    # Parse LLM output → PatentIR
    # ══════════════════════════════════════════════════════════

    def _parse_patent(self, result: dict, paper_ir: PaperIR) -> PatentIR:
        """Parse LLM JSON output into PatentIR."""
        patent = PatentIR(
            title=result.get("title", paper_ir.title),
            patent_type="cn",
            abstract=result.get("abstract", ""),
        )

        # Claims
        for c in result.get("claims", []):
            patent.claims.append(PatentClaim(
                number=c.get("number", 0),
                text=c.get("text", ""),
                claim_type="dependent" if c.get("depends_on") else "independent",
                category="method" if "方法" in c.get("text", "")[:50] else "system",
                depends_on=c.get("depends_on", []),
            ))

        # Sections
        for s in result.get("sections", []):
            patent.sections.append(PatentSection(
                heading=s.get("heading", ""),
                content=s.get("content", ""),
            ))

        return patent

    # ══════════════════════════════════════════════════════════
    # Rules-based fallback
    # ══════════════════════════════════════════════════════════

    def _fallback_generate(self, paper_ir: PaperIR) -> PatentIR:
        """Expert rules-based fallback when LLM is unavailable."""
        from paper2patent.converter.section_mapper import SectionMapper
        from paper2patent.converter.claims_generator import ClaimsGenerator
        from paper2patent.analyzer.paper_analyzer import PaperAnalyzer

        # Step 2: Analyze
        analyzer = PaperAnalyzer(backend=self.backend, verbose=self.verbose)
        analysis = analyzer.analyze(paper_ir)

        # Step 3: Structure
        mapper = SectionMapper(patent_type="cn")
        patent = mapper.map(paper_ir, analysis)

        # Step 4: Claims
        gen = ClaimsGenerator(patent_type="cn")
        patent.claims = gen.generate(paper_ir, analysis)

        return patent
