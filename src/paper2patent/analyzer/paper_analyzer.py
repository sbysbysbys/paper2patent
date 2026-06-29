"""LLM-assisted paper analysis — extracts structured inventive content from PaperIR."""

from __future__ import annotations

import json
import os
from textwrap import dedent

from paper2patent.ir import PaperIR, PaperAnalysis, MethodStep, SystemComponent, NoveltyPoint
from paper2patent.converter.expert_mode import EXPERT_SYSTEM_PROMPT


ANALYSIS_PROMPT_CN = EXPERT_SYSTEM_PROMPT + """

## 本次任务：分析论文并提取专利撰写要素

请仔细分析以下学术论文，提取出可用于撰写中国发明专利的结构化信息。

## ⚠️ 重要
- 所有技术描述使用中文，**严禁使用"本发明"**，使用"本申请"替代
- technical_field 格式："本申请涉及...技术领域，具体涉及一种...的方法和装置"
- 方法步骤描述要详细，每个步骤10-30字中文描述

## 论文内容

{paper_text}

## 提取要求

请以 JSON 格式返回以下内容（只返回 JSON，不要其他解释）：

```json
{{
  "technical_field": "本申请涉及...技术领域，具体涉及一种...",
  "technical_problem": "论文试图解决的核心技术问题（1-2句话，用中文）",
  "method_steps": [
    {{
      "index": 1,
      "description": "按执行顺序描述的步骤（中文），用'通过...对...进行...得到...'的句式",
      "actor": "执行该步骤的系统组件名称",
      "input_data": "该步骤的输入",
      "output_data": "该步骤的输出"
    }}
  ],
  "system_components": [
    {{
      "index": 1,
      "name": "组件的中文名称",
      "function": "该组件的功能描述",
      "inputs": "输入数据/信号",
      "outputs": "输出数据/信号",
      "connections": []
    }}
  ],
  "novelty_points": [
    {{
      "description": "创新点的中文描述，强调与技术问题的因果关系"
    }}
  ],
  "key_parameters": [
    {{
      "name": "参数名（中文）",
      "value": "取值范围或典型值",
      "context": "该参数在方法中的作用"
    }}
  ],
  "alternatives": [
    "可选实施方式1的中文描述",
    "可选实施方式2的中文描述"
  ],
  "is_method_invention": true,
  "is_system_invention": true
}}
```

**重要提示：**
- 如果论文中包含性能数据（准确率、F1值、速度等），在提取时**忽略**这些数字，只提取方法步骤和系统结构
- 每个方法步骤尽量细化，理想情况下 3-8 个步骤
- 如果论文提出了一个新模型架构，将其分解为组成部分（编码器、解码器、注意力模块等）
- 对于深度学习方法，将前向传播过程描述为方法步骤，将模型组件描述为系统组件
"""


class PaperAnalyzer:
    """Use LLM to extract structured patent-ready analysis from a paper.

    Supports Claude (default) and OpenAI backends.
    """

    def __init__(self, backend: str = "claude", verbose: bool = False):
        self.backend = backend
        self.verbose = verbose

    def analyze(self, paper_ir: PaperIR) -> PaperAnalysis:
        """Analyze a PaperIR and return a PaperAnalysis.

        Requires LLM (Anthropic/OpenAI API key). No rules fallback.
        """
        paper_text = self._build_context(paper_ir)
        result_json = self._call_llm(paper_text, paper_ir.language)
        return self._parse_result(result_json)

    def _build_context(self, paper_ir: PaperIR) -> str:
        """Build a concise text representation for the LLM prompt."""
        parts = [f"## 标题: {paper_ir.title}"]
        if paper_ir.abstract:
            parts.append(f"## 摘要: {paper_ir.abstract}")
        for sec in paper_ir.sections:
            if sec.heading or sec.content:
                heading = sec.heading or "(未命名章节)"
                content = sec.content[:3000] if len(sec.content) > 3000 else sec.content
                parts.append(f"### {heading}\n{content}")
        return "\n\n".join(parts)

    def _call_llm(self, paper_text: str, language: str) -> dict:
        """Call the configured LLM backend."""
        if self.backend == "claude":
            return self._call_claude(paper_text)
        elif self.backend == "openai":
            return self._call_openai(paper_text)
        else:
            raise ValueError(f"Unknown LLM backend: {self.backend}")

    def _call_claude(self, paper_text: str) -> dict:
        """Use Anthropic Claude API for analysis."""
        try:
            import anthropic
            client = anthropic.Anthropic()

            prompt = ANALYSIS_PROMPT_CN.format(paper_text=paper_text[:50000])

            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            return self._extract_json(response_text)
        except (ImportError, Exception) as e:
            if self.verbose:
                print(f"[dim]Claude API unavailable: {e}[/dim]")
            raise

    def _call_openai(self, paper_text: str) -> dict:
        """Use OpenAI API for analysis."""
        try:
            import openai
            client = openai.OpenAI()

            prompt = ANALYSIS_PROMPT_CN.format(paper_text=paper_text[:50000])

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)
        except (ImportError, Exception) as e:
            if self.verbose:
                print(f"[dim]OpenAI API unavailable: {e}[/dim]")
            raise

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown code blocks."""
        # Try parsing the whole text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from ```json ... ``` block
        import re
        m = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass

        # Try { ... } extraction
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse LLM response as JSON: {text[:500]}")

    def _parse_result(self, result: dict) -> PaperAnalysis:
        """Parse LLM JSON result into PaperAnalysis."""
        return PaperAnalysis(
            technical_field=result.get("technical_field", ""),
            technical_problem=result.get("technical_problem", ""),
            method_steps=[
                MethodStep(
                    index=s.get("index", i + 1),
                    description=s.get("description", ""),
                    actor=s.get("actor", ""),
                    input_data=s.get("input_data", ""),
                    output_data=s.get("output_data", ""),
                    reference_num=110 + (s.get("index", i + 1) - 1) * 10,
                )
                for i, s in enumerate(result.get("method_steps", []))
            ],
            system_components=[
                SystemComponent(
                    index=c.get("index", i + 1),
                    name=c.get("name", ""),
                    function=c.get("function", ""),
                    inputs=c.get("inputs", ""),
                    outputs=c.get("outputs", ""),
                    connections=c.get("connections", []),
                    reference_num=10 + (c.get("index", i + 1) - 1) * 10,
                )
                for i, c in enumerate(result.get("system_components", []))
            ],
            novelty_points=[
                NoveltyPoint(description=n.get("description", ""))
                for n in result.get("novelty_points", [])
            ],
            key_parameters=result.get("key_parameters", []),
            alternatives=result.get("alternatives", []),
            is_method_invention=result.get("is_method_invention", True),
            is_system_invention=result.get("is_system_invention", False),
        )

    # All content generation is LLM-driven — no rules-based fallback.
