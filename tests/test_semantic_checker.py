"""
Tests for SemanticChecker (L3 Outcome/Semantic Evaluation)
"""

import os
import tempfile

import pytest

from termnet.claims_engine import SemanticChecker


@pytest.fixture
def temp_semantic_checker():
    """Create temporary semantic checker for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    checker = SemanticChecker(db_path)
    yield checker

    # Cleanup
    checker.close()
    os.unlink(db_path)


def test_good_answer_high_score(temp_semantic_checker):
    """Good answer with matching evidence should score >= 70"""
    checker = temp_semantic_checker

    answer = "The result is 42 based on Source A calculations. Source B confirms this figure. See (source)."
    evidence = [
        "Source A shows calculation result of 42",
        "Source B confirms the same figure of 42",
        "Mathematical analysis indicates 42 as correct"
    ]

    score = checker.score_answer(answer, evidence)

    assert score["final"] >= 70
    assert score["grounding"] > 0.5  # Good token overlap
    assert score["consistency"] == 1.0  # No uncertainty/contradictions
    assert score["style"] > 0.0  # Has citations


def test_poor_answer_low_score(temp_semantic_checker):
    """Poor answer with low overlap/contradictions should score < 50"""
    checker = temp_semantic_checker

    answer = "I'm not sure, maybe it's something. I made that up."
    evidence = [
        "The definitive result is 42",
        "Documentation clearly states 42",
    ]

    score = checker.score_answer(answer, evidence)

    assert score["final"] < 50
    assert score["grounding"] < 0.3  # Poor token overlap
    assert score["consistency"] < 0.8  # Penalty for uncertainty


def test_contradictory_answer_low_consistency(temp_semantic_checker):
    """Answer contradicting evidence should have low consistency"""
    checker = temp_semantic_checker

    answer = "The result is 99, but evidence shows 42. However evidence suggests otherwise."
    evidence = [
        "The result is clearly 42",
        "All calculations point to 42"
    ]

    score = checker.score_answer(answer, evidence)

    assert score["consistency"] < 0.5  # Heavy penalty for contradictions
    assert score["final"] < 60


def test_well_cited_answer_good_style(temp_semantic_checker):
    """Well-cited answer should have good style score"""
    checker = temp_semantic_checker

    answer = "According to Source A, the value is 100. The documentation (ref) confirms this result."
    evidence = [
        "Source A indicates value of 100",
        "Documentation confirms 100"
    ]

    score = checker.score_answer(answer, evidence)

    assert score["style"] >= 0.5  # Citations + multiple sentences
    assert score["final"] >= 65


def test_verbose_answer_style_penalty(temp_semantic_checker):
    """Overly verbose answer (>300 words) should get style penalty"""
    checker = temp_semantic_checker

    # Create a 350+ word answer
    verbose_answer = "The result is 50. " + "This is additional verbose content with many words. " * 60
    evidence = ["The result is 50"]

    score = checker.score_answer(verbose_answer, evidence)

    # Should have style penalty for verbosity
    assert len(verbose_answer.split()) > 300
    assert score["style"] < 0.8  # Penalty applied


def test_empty_answer(temp_semantic_checker):
    """Empty answer should return zero scores"""
    checker = temp_semantic_checker

    score = checker.score_answer("", ["Some evidence"])

    assert score["grounding"] == 0.0
    assert score["consistency"] == 0.0
    assert score["style"] == 0.0
    assert score["final"] == 0


def test_no_evidence_zero_grounding(temp_semantic_checker):
    """Answer with no evidence should have zero grounding"""
    checker = temp_semantic_checker

    score = checker.score_answer("Some answer here", [])

    assert score["grounding"] == 0.0


def test_score_persistence(temp_semantic_checker):
    """Test saving and retrieving semantic scores"""
    checker = temp_semantic_checker

    answer = "The result matches expectations according to sources."
    evidence = ["Sources confirm the result"]

    score = checker.score_answer(answer, evidence)
    checker.save_semantic_score("test-request-001", score)

    # Verify score was saved (would need DB query to fully test)
    # For now, just ensure no exceptions were raised
    assert score["final"] > 0


def test_llm_judge_stub(temp_semantic_checker):
    """Test LLM judge stub returns None"""
    checker = temp_semantic_checker

    result = checker.llm_judge("Some answer", "Some rubric")

    assert result is None


def test_grounding_calculation(temp_semantic_checker):
    """Test grounding score calculation edge cases"""
    checker = temp_semantic_checker

    # Perfect overlap
    answer = "apple banana cherry"
    evidence = ["apple banana cherry fruit"]
    score = checker.score_answer(answer, evidence)
    assert score["grounding"] == 1.0  # All answer tokens in evidence

    # Partial overlap
    answer = "apple banana orange"
    evidence = ["apple banana fruit"]
    score = checker.score_answer(answer, evidence)
    assert 0.6 <= score["grounding"] <= 0.7  # ~2/3 overlap

    # No overlap
    answer = "apple banana"
    evidence = ["cherry orange"]
    score = checker.score_answer(answer, evidence)
    assert score["grounding"] == 0.0


def test_consistency_phrases(temp_semantic_checker):
    """Test consistency scoring with various uncertainty phrases"""
    checker = temp_semantic_checker

    # Multiple uncertainty phrases
    answer = "I'm not sure, maybe it's unclear what the result could be"
    evidence = ["The result is definitive"]

    score = checker.score_answer(answer, evidence)
    assert score["consistency"] <= 0.4  # Multiple penalties


def test_deterministic_scoring(temp_semantic_checker):
    """Ensure scoring is deterministic (same input = same output)"""
    checker = temp_semantic_checker

    answer = "The final result is 42 according to the source."
    evidence = ["Source indicates result of 42"]

    score1 = checker.score_answer(answer, evidence)
    score2 = checker.score_answer(answer, evidence)

    assert score1 == score2  # Deterministic results