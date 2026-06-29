#!/usr/bin/env python3
"""Parse 100+ CN patent PDFs and extract writing patterns for skill improvement.

Extracts:
1. Claims structure (independent vs dependent, typical phrasing)
2. Section headings and transitions
3. High-frequency terminology
4. Embodiment structures
5. Boilerplate phrases

Outputs:
- data/patents/analysis/claims_patterns.json
- data/patents/analysis/terminology_freq.json
- data/patents/analysis/section_patterns.json
- data/patents/analysis/boilerplate_phrases.json
"""

import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

import fitz  # PyMuPDF

PDF_DIR = Path.home() / "paper2patent" / "data" / "patents" / "pdfs"
OUT_DIR = Path.home() / "paper2patent" / "data" / "patents" / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Load manifest for patent metadata
MANIFEST = json.loads(
    (Path.home() / "paper2patent" / "data" / "patents" / "manifest.json").read_text()
)


class PatentAnalyzer:
    def __init__(self):
        self.claims_data = []           # per-patent claim structures
        self.claim_openers = Counter()  # independent claim opening phrases
        self.dep_claim_patterns = Counter()  # dependent claim patterns
        self.section_headings = Counter()
        self.terminology = Counter()
        self.boilerplate = Counter()
        self.embodiment_patterns = []
        self.tech_field_patterns = Counter()
        self.transitions = Counter()

    def analyze_all(self, limit: int = 100):
        pdfs = sorted(PDF_DIR.glob("*.pdf"))[:limit]
        print(f"Analyzing {len(pdfs)} patent PDFs...")

        for i, pdf_path in enumerate(pdfs):
            pid = pdf_path.stem
            title = MANIFEST.get("patents", {}).get(pid, "")
            try:
                text = self._extract_text(pdf_path)
                if len(text) < 500:
                    continue
                self._analyze_one(pid, title, text)
            except Exception as e:
                pass

            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(pdfs)}] processed")

        print(f"\nDone: {i+1} patents analyzed")
        self._save_results()

    def _extract_text(self, pdf_path: Path) -> str:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _analyze_one(self, pid: str, title: str, text: str):
        # ── Split into major sections ──
        sections = self._split_sections(text)

        # ── Claims ──
        claims_text = sections.get("claims", "")
        if claims_text:
            claims_info = self._parse_claims(pid, title, claims_text)
            self.claims_data.append(claims_info)

        # ── Description sections ──
        desc_text = sections.get("description", "")
        if desc_text:
            self._extract_section_headings(desc_text)
            self._extract_boilerplate_phrases(desc_text)
            self._extract_tech_field(desc_text)
            self._extract_embodiments(desc_text)

        # ── Terminology ──
        self._extract_key_terminology(text)

    def _split_sections(self, text: str) -> dict:
        """Split patent text into major sections."""
        sections = {}

        # Remove extra whitespace in common markers
        text_clean = re.sub(r'(权)\s+(利)\s+(要)\s+(求)', r'\1\2\3\4', text)
        text_clean = re.sub(r'(说)\s+(明)\s+(书)', r'\1\2\3', text_clean)

        # Claims section — find "权利要求书" page header to end or "说明书" start
        claims_match = re.search(
            r'权利要求书.*?\n(.*?)(?=\n\s*(?:说明书|说\s*明\s*书|技术领域|技\s*术\s*领\s*域))',
            text_clean, re.DOTALL
        )
        if claims_match:
            sections["claims"] = claims_match.group(1)
        else:
            # Try alternative: everything from first claim number to 说明书
            alt = re.search(
                r'((?:(?:^\d+[\.\s、）)]|^\s*\d+[\.\s、）)])[\s\S]{50,5000}?)(?=\n\s*(?:技术领域|背景技术|发明内容|具体实施方式))',
                text, re.MULTILINE | re.DOTALL
            )
            if alt:
                sections["claims"] = alt.group(1)

        # Description — from 技术领域 to end
        desc_match = re.search(
            r'(?:技术领域|技\s*术\s*领\s*域)([\s\S]*?)(?=\n\s*(?:说明书附图|附图说明|图\s*\d|\Z))',
            text_clean, re.DOTALL
        )
        if desc_match:
            sections["description"] = "技术领域" + desc_match.group(1)
        elif claims_match:
            # Fallback: everything after claims
            end_of_claims = claims_match.end()
            sections["description"] = text_clean[end_of_claims:]

        return sections

    def _parse_claims(self, pid: str, title: str, claims_text: str) -> dict:
        """Parse individual claims from claims section."""
        # Split into individual claims (numbered)
        claim_parts = re.split(r'\n\s*(?=\d+[\.\s、])', claims_text)

        independent = []
        dependent = []
        claim_texts = []

        for cp in claim_parts:
            cp = cp.strip()
            if not cp or len(cp) < 10:
                continue

            claim_texts.append(cp)

            # Detect independent claims
            if re.search(r'(?:一种|一种|其特征在于)', cp[:80]):
                independent.append(cp[:500])
                # Extract opening phrase
                opener = self._extract_claim_opener(cp)
                if opener:
                    self.claim_openers[opener] += 1

            # Detect dependent claims
            if re.search(r'(?:根据权利要求|如权利要求)', cp[:80]):
                dependent.append(cp[:500])
                # Extract dependency pattern
                pattern = self._extract_dep_pattern(cp)
                if pattern:
                    self.dep_claim_patterns[pattern] += 1

        return {
            "pid": pid,
            "title": title,
            "total_claims": len(claim_texts),
            "independent": len(independent),
            "dependent": len(dependent),
            "sample_independent": independent[:3],
            "sample_dependent": dependent[:3],
        }

    def _extract_claim_opener(self, claim_text: str) -> str | None:
        """Extract the opening phrase of an independent claim.
        e.g. '一种...方法，其特征在于，包括：'
        """
        # Method claims
        m = re.match(
            r'(一种[^，,。.]*(?:方法|系统|装置|设备|介质|产品|程序)[^，,。.]*(?:其特征在于|包括|包含|由)[^，,。.]*)',
            claim_text
        )
        if m:
            return m.group(1)[:120]
        # Generic
        m = re.match(r'(一种[^，]{10,60})', claim_text)
        if m:
            return m.group(1)
        return None

    def _extract_dep_pattern(self, claim_text: str) -> str | None:
        """Categorize dependent claim pattern.
        e.g. '根据权利要求1所述的方法，其特征在于，所述...'
        """
        m = re.match(
            r'((?:根据权利要求\d+(?:或\d+)*(?:至\d+)?(?:任一项)?所述(?:的)?(?:方法|系统|装置|设备|介质))[^，,]*)',
            claim_text
        )
        if m:
            return m.group(1)[:100]
        return None

    def _extract_section_headings(self, desc_text: str):
        """Extract section headings from description — handles both 【】 and plain formats."""
        headings = re.findall(r'【([^】]+)】', desc_text)
        for h in headings:
            self.section_headings["【" + h + "】"] += 1

        # Also detect plain section markers (older format)
        plain_sections = [
            "技术领域", "背景技术", "发明内容", "附图说明",
            "具体实施方式", "技术问题", "技术方案", "有益效果",
        ]
        for ps in plain_sections:
            count = len(re.findall(ps, desc_text))
            if count > 0:
                self.section_headings[ps] += count

    def _extract_boilerplate_phrases(self, desc_text: str):
        """Extract common boilerplate phrases."""
        patterns = [
            r'(本发明涉及[^。]{5,80}技术领域[^。]*。)',
            r'(本(?:发明|申请|公开|实施例)[^，]{5,60}提供[^。]*。)',
            r'(应当[^，]{3,30}理解[^。]*。)',
            r'(以上所述[^。]*仅为本[^。]*。)',
            r'(凡[^，]{5,30}之内[^。]*。)',
            r'(显然[^，]{5,40}本[^。]*。)',
            r'(本领域[^，]{5,40}技术人员[^。]*。)',
            r'(需要说明的是[^。]*。)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, desc_text)
            for m in matches:
                if len(m) > 10:
                    self.boilerplate[m[:120]] += 1

    def _extract_tech_field(self, desc_text: str):
        """Extract technical field descriptions."""
        # Find 【技术领域】section
        field_match = re.search(
            r'【技术领域】(.*?)(?:【|\Z)',
            desc_text, re.DOTALL
        )
        if field_match:
            field_text = field_match.group(1).strip()
            # Extract key phrases
            phrases = re.findall(r'(?:涉及|属于|应用于|用于)([^，。]{5,40})', field_text)
            for p in phrases:
                self.tech_field_patterns[p.strip()] += 1

    def _extract_embodiments(self, desc_text: str):
        """Extract embodiment structures."""
        # Find embodiment sections
        emb_matches = re.findall(
            r'((?:实施例\d+|【实施例\d+】|实施方式\d+)[^【]{20,800})',
            desc_text
        )
        for emb in emb_matches[:50]:
            self.embodiment_patterns.append(emb[:300])

    def _extract_key_terminology(self, text: str):
        """Extract technical Chinese patent terminology."""
        # Patent-specific transition words
        transition_patterns = [
            r'(可选地[^，。]*)',
            r'(优选地[^，。]*)',
            r'(进一步[^，地]{2,15})',
            r'(具体地[^，。]*)',
            r'(示例性地[^，。]*)',
            r'(在一些实施例中[^，。]*)',
            r'(在一个实施例中[^，。]*)',
            r'(在可能的实现方式中[^，。]*)',
        ]
        for pattern in transition_patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                if 3 < len(m) < 50:
                    self.transitions[m] += 1

        # Patent-specific compound terms (3-6 chars, high technical content)
        compounds = re.findall(
            r'((?:特征|处理|获取|确定|生成|计算|识别|检测|预测|估计|优化|训练|推理|融合|编码|解码|压缩|量化|迁移|蒸馏|对齐|增强|重建|分割|分类|聚类|匹配|跟踪|定位|规划|控制)(?:模块|单元|器|装置|网络|模型|方法|步骤|过程|流程|系统))',
            text
        )
        for c in compounds:
            self.terminology[c] += 1

        # Method-step verbs
        step_verbs = re.findall(
            r'(?:步骤S\d+[：:]\s*)([^，。；;]{8,60})',
            text
        )
        for sv in step_verbs[:200]:
            # Extract the first verb phrase
            verb = re.match(r'([通过利用采用根据基于将对待][^，]{10,50})', sv)
            if verb:
                self.terminology[verb.group(1)[:60]] += 1

    def _save_results(self):
        """Save all extracted patterns to JSON files."""
        # Claims patterns
        (OUT_DIR / "claims_patterns.json").write_text(json.dumps({
            "total_patents_analyzed": len(self.claims_data),
            "avg_claims_per_patent": sum(d["total_claims"] for d in self.claims_data) / max(len(self.claims_data), 1),
            "top_independent_openers": self.claim_openers.most_common(30),
            "top_dependent_patterns": self.dep_claim_patterns.most_common(30),
            "sample_patents": self.claims_data[:10],
        }, ensure_ascii=False, indent=2))

        # Section patterns
        (OUT_DIR / "section_patterns.json").write_text(json.dumps({
            "section_headings": self.section_headings.most_common(50),
            "tech_field_patterns": self.tech_field_patterns.most_common(30),
            "embodiment_samples": self.embodiment_patterns[:30],
        }, ensure_ascii=False, indent=2))

        # Terminology
        (OUT_DIR / "terminology_freq.json").write_text(json.dumps({
            "compound_terms": self.terminology.most_common(100),
            "transitions": self.transitions.most_common(50),
        }, ensure_ascii=False, indent=2))

        # Boilerplate
        (OUT_DIR / "boilerplate_phrases.json").write_text(json.dumps({
            "phrases": self.boilerplate.most_common(50),
        }, ensure_ascii=False, indent=2))

        print(f"\nResults saved to {OUT_DIR}/")
        for f in sorted(OUT_DIR.glob("*.json")):
            print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    analyzer = PatentAnalyzer()
    analyzer.analyze_all(limit=limit)
