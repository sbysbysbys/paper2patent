"""Tests for claims generation."""

import pytest
from paper2patent.ir import PaperIR, PaperAnalysis, MethodStep, SystemComponent, NoveltyPoint
from paper2patent.converter.claims_generator import ClaimsGenerator


def make_basic_analysis():
    return PaperAnalysis(
        technical_field="本发明涉及人工智能技术领域",
        technical_problem="现有方法准确性不足",
        is_method_invention=True,
        is_system_invention=True,
        method_steps=[
            MethodStep(index=1, description="接收输入数据", actor="传感器", reference_num=110),
            MethodStep(index=2, description="对数据进行特征提取", actor="特征提取器", reference_num=120),
            MethodStep(index=3, description="输出分类结果", actor="分类器", reference_num=130),
        ],
        system_components=[
            SystemComponent(index=1, name="传感器", function="采集数据", reference_num=10),
            SystemComponent(index=2, name="处理器", function="处理数据", reference_num=20),
        ],
        novelty_points=[
            NoveltyPoint(description="提高了处理效率"),
            NoveltyPoint(description="降低了计算成本"),
        ],
        key_parameters=[
            {"name": "阈值", "value": "0.5-0.9", "context": "分类阈值"},
        ],
        alternatives=[
            "所述特征提取步骤中使用深度神经网络替代传统方法",
        ],
    )


class TestClaimsGenerator:
    def test_generates_independent_method_claim(self):
        gen = ClaimsGenerator()
        analysis = make_basic_analysis()
        paper = PaperIR(title="一种数据处理方法")
        claims = gen.generate(paper, analysis)

        method_claims = [c for c in claims if c.claim_type == "independent" and c.category == "method"]
        assert len(method_claims) >= 1
        assert "其特征在于" in method_claims[0].text or "包括" in method_claims[0].text

    def test_generates_independent_system_claim(self):
        gen = ClaimsGenerator()
        analysis = make_basic_analysis()
        paper = PaperIR(title="一种数据处理方法")
        claims = gen.generate(paper, analysis)

        system_claims = [c for c in claims if c.claim_type == "independent" and c.category == "system"]
        assert len(system_claims) >= 1
        assert "装置" in system_claims[0].text

    def test_generates_dependent_parameter_claim(self):
        gen = ClaimsGenerator()
        analysis = make_basic_analysis()
        paper = PaperIR(title="一种数据处理方法")
        claims = gen.generate(paper, analysis)

        dep_claims = [c for c in claims if c.claim_type == "dependent"]
        # Should have at least one parameter-dependent claim
        param_claims = [c for c in dep_claims if "阈值" in c.text]
        assert len(param_claims) >= 1
        assert param_claims[0].depends_on == [1]

    def test_no_multi_dependency_chain(self):
        gen = ClaimsGenerator()
        analysis = make_basic_analysis()
        paper = PaperIR(title="一种数据处理方法")
        claims = gen.generate(paper, analysis)

        multi_dep = [c.number for c in claims if len(c.depends_on) > 1]
        for claim in claims:
            for dep in claim.depends_on:
                assert dep not in multi_dep, f"Claim {claim.number} depends on multi-dependent claim {dep}"

    def test_method_only_paper(self):
        gen = ClaimsGenerator()
        analysis = PaperAnalysis(
            is_method_invention=True,
            is_system_invention=False,
            method_steps=[
                MethodStep(index=1, description="处理数据", reference_num=110),
            ],
        )
        paper = PaperIR(title="一种方法")
        claims = gen.generate(paper, analysis)

        # Method claim + electronic device claim + storage medium claim
        categories = {c.category for c in claims}
        assert "method" in categories
        assert "system" not in categories
        assert len(claims) >= 3  # method + device + medium
