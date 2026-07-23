"""Tests for the family-neutral answer-presence ladder (absent_matchers)."""

from __future__ import annotations

from wigtnocr_radp.evaluation.absent_matchers import (
    LADDER,
    l0_exact,
    l1_normalized,
    l2_numeric,
    l3_token_recall,
    l4_fuzzy_lcs,
)


def test_ladder_is_monotone_more_permissive():
    """Anything present at a stricter rung stays present at a looser rung."""
    # A page whose content matches the answer only after loosening.
    answer = "예산 1,234억 원"
    page = "본 사업의 총 예산은 1234 억 원 규모이다."  # comma dropped, spaced
    rungs = [l0_exact, l1_normalized, l2_numeric, l3_token_recall, l4_fuzzy_lcs]
    results = [m(answer, page) for m in rungs]
    # once true, stays true down the ladder (allow the strict end to be false)
    seen_true = False
    for r in results:
        if r:
            seen_true = True
        elif seen_true:
            raise AssertionError(f"non-monotone ladder: {results}")


def test_l0_exact_is_strict():
    assert l0_exact("abc", "xx abc yy")
    assert not l0_exact("a b c", "abc")  # whitespace counts at L0


def test_l1_ignores_markdown_and_whitespace():
    assert l1_normalized("**Total: 42**", "the total   :42 here")
    assert not l1_normalized("missing value", "unrelated text")


def test_l2_neutralises_digit_separators():
    assert not l1_normalized("1,234,567", "sum is 1234567 won")  # comma blocks L1
    assert l2_numeric("1,234,567", "sum is 1234567 won")         # L2 recovers it


def test_l3_token_recall_is_order_free():
    assert l3_token_recall("alpha beta gamma", "gamma then beta and alpha")
    assert not l3_token_recall("alpha beta gamma", "only alpha here")


def test_l4_fuzzy_tolerates_ocr_noise():
    # one substituted char in a long span still leaves a long common run
    assert l4_fuzzy_lcs("서울특별시 종로구 세종대로", "주소: 서울특별시 종로구 세종내로 1")
    assert not l4_fuzzy_lcs("completely different", "nothing alike whatsoever")


def test_empty_answer_never_present():
    for m in LADDER.values():
        assert not m("", "any page text")
        assert not m("   ", "any page text")
