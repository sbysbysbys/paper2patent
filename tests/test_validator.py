"""Tests for patent validator."""

import pytest
from paper2patent.ir import PatentIR, PatentClaim, PatentSection
from paper2patent.validator.patent_validator import PatentValidator


def make_valid_patent():
    return PatentIR(
        title="一种测试方法",
        patent_type="cn",
        abstract="本发明提供一种测试方法，包括：接收数据；处理数据；输出结果。本发明提高了效率。",
        claims=[
            PatentClaim(number=1, claim_type="independent", category="method",
                       text="一种测试方法，其特征在于，包括：步骤S110和步骤S120。"),
            PatentClaim(number=2, claim_type="dependent", category="method",
                       text="根据权利要求1所述的方法，其特征在于，参数为0.5。",
                       depends_on=[1]),
        ],
        sections=[
            PatentSection(heading="【技术领域】", content="测试领域"),
            PatentSection(heading="【背景技术】", content="背景"),
            PatentSection(heading="【发明内容】", content="发明内容"),
            PatentSection(heading="【附图说明】", content="附图说明"),
            PatentSection(heading="【具体实施方式】", content="具体实施方式"),
        ],
    )


class TestValidator:
    def test_valid_patent_passes(self):
        patent = make_valid_patent()
        validator = PatentValidator()
        report = validator.validate(patent)
        assert "✓" in report or "未发现问题" in report

    def test_missing_section_detected(self):
        patent = make_valid_patent()
        patent.sections = patent.sections[:2]  # Only 2 of 5 required
        validator = PatentValidator()
        report = validator.validate(patent)
        assert "缺少必选章节" in report or "问题" in report

    def test_abstract_too_long_warns(self):
        patent = make_valid_patent()
        patent.abstract = "本发明" * 200  # ~600 chars
        validator = PatentValidator()
        report = validator.validate(patent)
        assert "300" in report

    def test_multi_dependency_detected(self):
        patent = make_valid_patent()
        patent.claims = [
            PatentClaim(number=1, claim_type="independent", category="method",
                       text="一种方法。"),
            PatentClaim(number=2, claim_type="dependent", category="method",
                       text="根据权利要求1所述的方法，其特征在于，...",
                       depends_on=[1]),
            PatentClaim(number=3, claim_type="dependent", category="method",
                       text="根据权利要求1或2所述的方法...",
                       depends_on=[1, 2]),
            PatentClaim(number=4, claim_type="dependent", category="method",
                       text="根据权利要求3所述的方法...",
                       depends_on=[3]),  # 3 is multi-dependent → 多引多
        ]
        validator = PatentValidator()
        report = validator.validate(patent)
        assert "多引多" in report

    def test_forbidden_terms_detected(self):
        patent = make_valid_patent()
        patent.claims[0].text = "一种方法，其特征在于，所述参数约为0.5等等。"
        validator = PatentValidator()
        report = validator.validate(patent)
        assert any(t in report for t in ["约", "等等"])
