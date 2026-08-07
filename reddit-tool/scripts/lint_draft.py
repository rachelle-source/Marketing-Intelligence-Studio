"""
Lint a Reddit comment draft for tone, brand-voice, and Reddit-style issues.

Lower scores are better. A score of 0 means no issues detected.
The default threshold is 40 — drafts at or above that fail the lint and
should be redrafted.

Rule sources:
- Common Reddit-voice rules from the vo2max-reddit-growth skill (curious
  practitioner voice, mandatory question, no emojis, no CTAs).
- 8MSolar brand voice (no em dashes, banned word list).
- KORR brand voice (never call equipment "portable", never conflate
  VO2 max with RMR, no fear-based framing).
- McFie brand voice (no promised returns, no hype language).

Usage as CLI:
    python scripts/lint_draft.py 8msolar "Draft text here"
    cat draft.txt | python scripts/lint_draft.py 8msolar -

Usage as module:
    from scripts.lint_draft import lint_draft
    result = lint_draft(text, client_name="8MSolar")
    # result.score, result.passed, result.warnings, result.has_question, ...
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field

DEFAULT_THRESHOLD = 40

# Hype / marketing language that breaks the "real redditor" voice.
COMMON_HYPE_WORDS = [
    "amazing", "revolutionary", "game-changer", "game changer",
    "incredible", "transformative", "paradigm shift", "cutting-edge",
    "life-changing", "groundbreaking", "next-level", "next level",
    "world-class", "best-in-class", "state of the art", "state-of-the-art",
]

# Marketing tropes pulled from the 8MSolar banned word list and the KORE
# Wireless skill's "do not sound like" list.
COMMON_MARKETING_TROPES = [
    "leverage", "delve", "embark", "unlock", "holistic", "robust",
    "seamlessly", "illuminate", "navigate the world of",
    "in today's fast-paced", "in this article", "let's dive in",
    "yearn", "unearth", "synergy", "disruptive",
]

# Calls-to-action that betray brand voice on Reddit.
COMMON_CTA_PHRASES = [
    "let me know if", "feel free to", "happy to discuss",
    "happy to chat", "dm me", "message me", "reach out",
    "don't hesitate", "looking forward to hearing",
]

# Coaching language — vo2max skill explicitly bans this in favour of
# peer-to-peer practitioner voice.
COACHING_PHRASES = [
    "you should", "you need to", "you must", "you have to",
    "you've got to", "you ought to", "you gotta",
]

# Crude emoji detector — catches the common Unicode emoji ranges.
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U00002600-\U000026FF"  # misc symbols
    "]+",
    flags=re.UNICODE,
)

# Per-client extensions. Keys are normalised slugs (lowercase, hyphenated).
PER_CLIENT_RULES: dict[str, dict] = {
    "8msolar": {
        "no_em_dashes": True,
        "extra_banned_words": [],
        "brand_aliases": ["8msolar", "8m solar"],
    },
    "solartime-usa": {
        "no_em_dashes": False,
        "extra_banned_words": [],
        "brand_aliases": ["solartime", "solartime usa"],
    },
    "mcfie-insurance": {
        "no_em_dashes": False,
        "extra_banned_words": [
            "paramount", "myriad", "meticulously", "beacon", "imperative",
        ],
        "brand_aliases": ["mcfie", "mcfie insurance"],
        "no_promised_returns": True,
        "no_dave_ramsey_attack": True,
    },
    "korr": {
        "no_em_dashes": False,
        "extra_banned_words": [],
        "brand_aliases": ["korr"],
        "no_portable_claim": True,
        "no_conflate_tests": True,
    },
    "kore-wireless": {
        "no_em_dashes": False,
        "extra_banned_words": [],
        "brand_aliases": ["kore", "kore wireless"],
    },
}


def _normalise_slug(name: str) -> str:
    """Map any client name form to the slug used in PER_CLIENT_RULES."""
    return name.strip().lower().replace(" ", "-")


@dataclass
class LintResult:
    score: int  # 0-100, lower is better
    passed: bool  # score < threshold
    warnings: list[str] = field(default_factory=list)
    brand_mention_count: int = 0
    has_question: bool = False
    word_count: int = 0

    def summary(self) -> str:
        verdict = "PASS" if self.passed else "FAIL"
        return (
            f"Lint {verdict} — score {self.score}/100, "
            f"{self.word_count} words, "
            f"question={'yes' if self.has_question else 'no'}, "
            f"brand mentions={self.brand_mention_count}"
        )


def lint_draft(
    text: str,
    client_name: str = "",
    threshold: int = DEFAULT_THRESHOLD,
) -> LintResult:
    warnings: list[str] = []
    score = 0
    text_lower = text.lower()
    word_count = len(text.split())
    has_question = "?" in text

    # Length: Reddit comments work best at 50-150 words.
    if word_count < 30:
        warnings.append(f"Short ({word_count} words) — Reddit comments work best at 50-150 words")
        score += 5
    elif word_count > 220:
        warnings.append(f"Long ({word_count} words) — Reddit comments work best at 50-150 words")
        score += 5

    # Mandatory question (vo2max skill pattern, applies broadly).
    if not has_question:
        warnings.append("No question — strong Reddit pattern is to end with an open-ended question")
        score += 10

    # No emojis.
    if EMOJI_PATTERN.search(text):
        warnings.append("Contains emojis — not authentic Reddit voice")
        score += 15

    # Hype words.
    for word in COMMON_HYPE_WORDS:
        if word in text_lower:
            warnings.append(f"Hype word: '{word}'")
            score += 8

    # Marketing tropes.
    for trope in COMMON_MARKETING_TROPES:
        if trope in text_lower:
            warnings.append(f"Marketing trope: '{trope}'")
            score += 8

    # CTA phrases.
    for cta in COMMON_CTA_PHRASES:
        if cta in text_lower:
            warnings.append(f"CTA phrase: '{cta}' — sounds like a brand, not a redditor")
            score += 10

    # Coaching language.
    for phrase in COACHING_PHRASES:
        if phrase in text_lower:
            warnings.append(f"Coaching language: '{phrase}' — peer voice preferred")
            score += 5

    # Per-client rules.
    rules = PER_CLIENT_RULES.get(_normalise_slug(client_name), {})

    if rules.get("no_em_dashes") and ("—" in text or "–" in text):
        warnings.append(f"Em or en dash present — {client_name} hard rule")
        score += 20

    for banned in rules.get("extra_banned_words", []):
        if banned.lower() in text_lower:
            warnings.append(f"Client-banned word: '{banned}'")
            score += 8

    if rules.get("no_portable_claim") and "portable" in text_lower:
        warnings.append("Word 'portable' — KORR rule: never call metabolic testing equipment portable")
        score += 12

    if rules.get("no_conflate_tests"):
        # Cheap heuristic: both terms used in close proximity.
        if "vo2" in text_lower and "rmr" in text_lower:
            window = re.search(r"vo2.{0,40}rmr|rmr.{0,40}vo2", text_lower)
            if window:
                warnings.append("VO2 max and RMR mentioned in close proximity — verify they aren't being conflated")
                score += 8

    if rules.get("no_promised_returns"):
        if re.search(r"\b\d+(\.\d+)?\s?%\s+(return|guaranteed|growth|gain)\b", text_lower):
            warnings.append("Specific return percentage promised — McFie rule: no promised returns")
            score += 20

    if rules.get("no_dave_ramsey_attack"):
        # Flag clearly negative framings of Dave Ramsey.
        attack_patterns = [r"dave ramsey is wrong", r"dave ramsey doesn'?t know", r"dave ramsey is (a )?(scam|liar|fraud|idiot)"]
        for p in attack_patterns:
            if re.search(p, text_lower):
                warnings.append("Negative framing of Dave Ramsey — McFie rule: address respectfully")
                score += 15
                break

    # Brand mention count.
    brand_count = 0
    for alias in rules.get("brand_aliases", [client_name.strip()]):
        if not alias:
            continue
        brand_count += len(re.findall(re.escape(alias), text, flags=re.IGNORECASE))
    if brand_count > 1:
        warnings.append(f"Brand mentioned {brand_count} times — keep to 0-1 unless directly asked")
        score += 10 * (brand_count - 1)

    score = min(score, 100)

    return LintResult(
        score=score,
        passed=score < threshold,
        warnings=warnings,
        brand_mention_count=brand_count,
        has_question=has_question,
        word_count=word_count,
    )


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Lint a Reddit draft")
    parser.add_argument("client", help="Client name or slug (e.g. 8msolar, 'McFie Insurance')")
    parser.add_argument("text", nargs="?", default=None,
                        help="Draft text, '-' for stdin, or omit when using --file")
    parser.add_argument("--file", dest="file_path", default=None,
                        help="Path to a text file containing the draft")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                        help=f"Pass/fail threshold (default {DEFAULT_THRESHOLD})")
    args = parser.parse_args()

    if args.file_path:
        text = open(args.file_path, encoding="utf-8").read()
    elif args.text == "-":
        text = sys.stdin.read()
    elif args.text:
        text = args.text
    else:
        parser.error("Provide draft text, '-' for stdin, or --file <path>")
    result = lint_draft(text, client_name=args.client, threshold=args.threshold)

    print(result.summary())
    if result.warnings:
        print("\nWarnings:")
        for w in result.warnings:
            print(f"  - {w}")
    else:
        print("\nNo warnings.")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    _cli()
