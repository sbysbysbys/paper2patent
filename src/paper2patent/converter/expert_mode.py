"""Patent Writing Expert — knowledge-driven patent writing guidance.

Powered by analysis of 300+ real Chinese invention patents across 21 domains.
Loads the expert knowledge base and provides writing guidance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_EXPERT_KB: Optional[dict] = None


def load_expert_kb() -> dict:
    """Load the patent writing expert knowledge base."""
    global _EXPERT_KB
    if _EXPERT_KB is not None:
        return _EXPERT_KB

    kb_path = Path.home() / "paper2patent" / "data" / "patents" / "expert_knowledge" / "patent_expert_kb.json"
    if kb_path.exists():
        _EXPERT_KB = json.loads(kb_path.read_text(encoding="utf-8"))
        return _EXPERT_KB

    # Fallback: compact built-in expert knowledge
    _EXPERT_KB = _builtin_expert()
    return _EXPERT_KB


def _builtin_expert() -> dict:
    """Built-in compact expert knowledge (when full KB not available)."""
    return {
        "expert_profile": {
            "name": "Patent Writing Expert",
            "knowledge_source": "300+ CN invention patents across 21 domains",
        },
        "claims_writing_guide": {
            "independent_method_template": (
                "一种[技术主题]方法，其特征在于，包括：\n"
                "步骤S[110]：[动词][对象]，得到[结果]；\n"
                "步骤S[120]：对[结果]进行[操作]，输出[最终结果]。"
            ),
            "dependent_claim_variations": [
                "根据权利要求[1]所述的方法，其特征在于，所述[参数]的取值范围为[X]至[Y]。",
                "根据权利要求[1]所述的方法，其特征在于，所述[步骤]中[操作]使用[替代方案]。",
                "根据权利要求[1]至[3]任一所述的方法，其特征在于，所述[特征]为[具体限定]。",
            ],
        },
        "section_writing_guide": {
            "cn_required_sections": [
                {"name": "技术领域", "purpose": "发明所属技术领域，1-2句话"},
                {"name": "背景技术", "purpose": "现有技术的不足之处"},
                {"name": "发明内容", "purpose": "技术问题+技术方案+有益效果"},
                {"name": "附图说明", "purpose": "逐图说明"},
                {"name": "具体实施方式", "purpose": "至少1个实施例"},
            ],
        },
        "boilerplate_bank": {
            "abstract": "本发明公开了一种[技术主题]，包括：[步骤]。本发明[有益效果]。",
            "tech_field": "本发明涉及[领域]技术领域，具体涉及一种[技术方案]。",
            "closing": "以上所述仅为本发明的优选实施例而已，并不用于限制本发明。",
        },
        "terminology_guide": {
            "forbidden_in_claims": ["等等", "最好是", "约", "接近", "诸如此类"],
        },
        "writing_checklist": [
            "权利要求是否为单句？",
            "是否包含全部5个必选章节？",
            "附图中引用号是否在说明书中全部出现？",
            "术语是否前后一致？",
        ],
    }


# ── Expert Guidance API ──

def get_claim_template(claim_type: str = "method") -> str:
    """Get a patent claim template from the expert KB."""
    kb = load_expert_kb()
    guide = kb.get("claims_writing_guide", {})
    if claim_type == "method":
        return guide.get("independent_method_template", "")
    elif claim_type == "device":
        return guide.get("independent_device_template", "")
    return ""


def get_dep_claim_variations() -> list[str]:
    """Get dependent claim variation templates."""
    kb = load_expert_kb()
    return kb.get("claims_writing_guide", {}).get("dependent_claim_variations", [])


def get_section_guide() -> list[dict]:
    """Get the required CN patent sections guide."""
    kb = load_expert_kb()
    return kb.get("section_writing_guide", {}).get("cn_required_sections", [])


def get_boilerplate(key: str) -> str:
    """Get a boilerplate phrase from the expert bank."""
    kb = load_expert_kb()
    return kb.get("boilerplate_bank", {}).get(key, "")


def get_forbidden_terms() -> list[str]:
    """Get terms forbidden in patent claims."""
    kb = load_expert_kb()
    return kb.get("terminology_guide", {}).get("forbidden_in_claims", [])


def get_writing_checklist() -> list[str]:
    """Get the patent writing quality checklist."""
    kb = load_expert_kb()
    return kb.get("writing_checklist", [])


def get_domain_insights() -> dict:
    """Get domain-specific patent writing insights."""
    kb = load_expert_kb()
    return kb.get("domain_specific_insights", {})


def get_expert_profile() -> dict:
    """Get the expert profile metadata."""
    kb = load_expert_kb()
    return kb.get("expert_profile", {})


def get_top_claim_patterns(n: int = 10) -> list:
    """Get top claim opening patterns from real patents."""
    kb = load_expert_kb()
    return kb.get("claims_writing_guide", {}).get("top_claim_openers_from_patents", [])[:n]


def get_top_boilerplate(n: int = 10) -> list:
    """Get top real boilerplate phrases."""
    kb = load_expert_kb()
    return kb.get("boilerplate_bank", {}).get("top_real_boilerplate", [])[:n]


# ── Expert system prompt for LLM-guided writing ──

EXPERT_SYSTEM_PROMPT = """你是一位资深的中国专利撰写专家（Patent Writing Expert）。你的知识来源于对300+件中国发明专利的系统分析，涵盖21个技术领域。

## 核心撰写原则

### 权利要求书
1. 独立权利要求必须包含"前序部分 + 其特征在于 + 特征部分"
2. 方法独立权利要求格式："一种...方法，其特征在于，包括：步骤SXX：..."
3. 装置独立权利要求格式："一种...装置，其特征在于，包括：模块A(10)，用于...；模块B(20)，用于..."
4. 每个权利要求是一个单句（仅句末一个。）
5. 从属权利要求："根据权利要求X所述的方法，其特征在于，..."
6. 禁止多引多
7. 权利要求的每一个技术特征都应在说明书中找到依据

### 说明书
1. 五部分：【技术领域】【背景技术】【发明内容】【附图说明】【具体实施方式】
2. 背景技术只写现有技术的局限性，不要赞扬现有技术
3. 发明内容 = 技术问题 + 技术方案概述 + 有益效果
4. 实施例要详细到"本领域技术人员能够实施"
5. 附图中的每个标记在说明书中至少出现一次

### 术语规范
1. 全文术语一致——不能同一个概念用不同词汇
2. 使用"所述"指代前述元件（不是"该"或"此"）
3. 权利要求禁用：等等、最好是、约、接近、诸如此类
4. 用"可以"代替"可能"，用"用于"代替"是用来"

### 格式规范（CNIPA）
- A4纸，上/左25mm，下/右15mm
- 正文宋体12pt，标题黑体14pt
- 1.5倍行距，首行缩进2字符
"""
