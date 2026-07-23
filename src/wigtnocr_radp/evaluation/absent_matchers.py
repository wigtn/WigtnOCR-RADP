"""Family-neutral answer-presence matchers — a strictness ladder for the
coverage diagnostic (rebuttal to the "same-family artifact" concern).

The coverage diagnostic (`coverage.py`) calls an answer *absent* when the gold
span is not a substring of the parser's page output under `normalize_for_match`
(NFKC + lowercase + whitespace/markdown removal). A reviewer objected that the
gold spans come from a Qwen3-VL-30B reference, so a same-family parser (Prod =
Qwen3-VL-2B) reproduces the *surface form* and matches, whereas MinerU/PaddleOCR
carry the same *content* in a different surface form and are wrongly counted
absent — i.e. the parser gap could be a matching artifact, not real content loss.

This module answers that head-on. It defines a *ladder* of presence tests of
increasing permissiveness. Each rung neutralises one more class of surface-form
difference:

    L0_exact        raw substring (strictest; formatting counts)
    L1_normalized   `normalize_for_match` — the paper's current matcher
                    (markdown + whitespace + case + NFKC neutral)
    L2_numeric      + strip in-content punctuation / digit separators
                    (1,234 == 1234; parens, hyphens, dots dropped)
    L3_token_recall order-free: >= TAU_TOKEN of the answer's content tokens
                    appear anywhere on the page (beats reordering / insertions)
    L4_fuzzy_lcs    longest common substring covers >= TAU_LCS of the answer
                    (tolerates OCR character noise, stdlib only)

If the MinerU-minus-Prod absent gap were a surface-form artifact it would shrink
to ~0 as we climb the ladder. If it survives to L4 (and to the LLM-judge ceiling
in `absent_llm_judge.py`), the missing content is genuinely missing.

All matchers are pure, deterministic, and dependency-free (stdlib only).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from difflib import SequenceMatcher

from wigtnocr_radp.evaluation.types import normalize_for_match

#: A presence test: is `answer` recoverable from `page`? (page-level, chunker-free)
Matcher = Callable[[str, str], bool]

#: Fraction of answer content-tokens that must appear on the page for L3.
TAU_TOKEN = 0.90
#: Fraction of the answer that the longest common substring must cover for L4.
TAU_LCS = 0.80

# Punctuation / separators dropped at L2 on top of L1. These carry surface-form
# differences that are not content: thousands separators, decimal points,
# hyphenation, bracketing, slashes, percent/units glue.
_L2_PUNCT = re.compile(r"[,\.\-‐-―/()\[\]{}:;%·・､、。]")
# Word/number tokens for L3 (Latin, digits, Hangul syllables + jamo, CJK).
_TOKEN = re.compile(r"[0-9a-z가-힣㄰-㆏一-鿿]+")


def _nfkc_lower(s: str) -> str:
    return unicodedata.normalize("NFKC", s).lower()


def l0_exact(answer: str, page: str) -> bool:
    """Raw substring — formatting and whitespace count."""
    answer = answer.strip()
    return bool(answer) and answer in page


def l1_normalized(answer: str, page: str) -> bool:
    """The paper's current matcher: markdown/whitespace/case/NFKC-neutral."""
    span = normalize_for_match(answer)
    return bool(span) and span in normalize_for_match(page)


def l2_numeric(answer: str, page: str) -> bool:
    """L1 plus in-content punctuation and digit-separator neutralisation."""
    strip = lambda s: _L2_PUNCT.sub("", normalize_for_match(s))
    span = strip(answer)
    return bool(span) and span in strip(page)


def _tokens(s: str) -> list[str]:
    return _TOKEN.findall(_nfkc_lower(s))


def l3_token_recall(answer: str, page: str, tau: float = TAU_TOKEN) -> bool:
    """Order-free: at least `tau` of the answer's content tokens are on the page.

    Robust to word reordering, glue words, and localised insertions/deletions
    that defeat a contiguous substring test but preserve the content.
    """
    ans = _tokens(answer)
    if not ans:
        return False
    page_set = set(_tokens(page))
    hit = sum(1 for t in ans if t in page_set)
    return hit / len(ans) >= tau


def l4_fuzzy_lcs(answer: str, page: str, tau: float = TAU_LCS) -> bool:
    """Longest common substring covers >= `tau` of the (normalised) answer.

    Tolerates OCR character noise: a few substituted/dropped characters still
    leave a long shared run. Stdlib `difflib`; pages are short (~1.4k chars) so
    the O(n*m) match is cheap.
    """
    a = normalize_for_match(answer)
    p = normalize_for_match(page)
    if not a:
        return False
    if a in p:
        return True
    block = SequenceMatcher(None, a, p, autojunk=False).find_longest_match(0, len(a), 0, len(p))
    return block.size / len(a) >= tau


#: The ordered ladder, strict -> permissive. Keys are stable output labels.
LADDER: dict[str, Matcher] = {
    "L0_exact": l0_exact,
    "L1_normalized": l1_normalized,
    "L2_numeric": l2_numeric,
    "L3_token_recall": l3_token_recall,
    "L4_fuzzy_lcs": l4_fuzzy_lcs,
}
