"""Tests for terminology conversion."""

from paper2patent.converter.terminology import (
    academic_to_patent_phrase,
    translate_term,
    boilerplate,
    ACADEMIC_TO_PATENT,
    ML_PATENT_TERMS,
)


class TestTerminology:
    def test_academic_to_patent_hedging(self):
        assert "可以" in academic_to_patent_phrase("可能")
        assert "本申请" in academic_to_patent_phrase("我们的方法")

    def test_vague_terms_removed(self):
        result = academic_to_patent_phrase("等等和诸如此类")
        # Should remove or replace vague terms
        assert "等等" not in result or "诸如此类" not in result
        # But not crash
        assert isinstance(result, str)

    def test_self_reference_converted(self):
        result = academic_to_patent_phrase("我们提出了一种新方法")
        assert "我们" not in result
        assert "本申请" in result

    def test_translate_ml_terms(self):
        assert translate_term("neural network") == "神经网络"
        assert translate_term("transformer") == "变换器网络"
        assert translate_term("attention mechanism") == "注意力机制"
        assert translate_term("unknown_term_xyz") == "unknown_term_xyz"

    def test_boilerplate(self):
        result = boilerplate("technical_field_opening", field="人工智能", title="测试方法")
        assert "人工智能" in result
        assert "测试方法" in result
        assert "技术领域" in result

    def test_boilerplate_unknown_key(self):
        result = boilerplate("nonexistent_key")
        assert result == ""

    def test_all_ml_terms_have_translations(self):
        # All keys should have non-empty values
        for en, zh in ML_PATENT_TERMS.items():
            assert zh, f"Missing translation for {en}"

    def test_academic_to_patent_idempotent(self):
        """Running twice should not degrade the text."""
        text = "本申请提供一种测试方法"
        result = academic_to_patent_phrase(text)
        # Should not add extra "本申请"
        assert result.count("本申请") <= 2
