from scripts.lint_draft import lint_draft, LintResult


def test_clean_draft_passes():
    text = (
        "I had a similar setup on a 1,800 sqft home in NC. After two years, "
        "production stayed within 4% of the modeled estimate, even through summer haze. "
        "Curious how your panels performed during the winter ice storms?"
    )
    result = lint_draft(text, client_name="8MSolar")
    assert isinstance(result, LintResult)
    assert result.passed is True
    assert result.has_question is True
    assert result.score < 40


def test_em_dash_fails_for_8msolar():
    text = (
        "Solar payback is usually 5 to 8 years — depending on Duke Energy rates and roof orientation. "
        "Have you checked PowerPair eligibility for your address?"
    )
    result = lint_draft(text, client_name="8MSolar")
    assert any("em" in w.lower() or "dash" in w.lower() for w in result.warnings)
    assert result.score >= 20


def test_em_dash_does_not_fail_for_solartime_usa():
    text = (
        "Solar payback in DFW is typically 5 to 8 years — depending on whether you bundle a battery for grid resilience. "
        "Have you priced Oncor's TDU charges into your savings model?"
    )
    result = lint_draft(text, client_name="SolarTime USA")
    # solartime-usa allows em dashes
    assert not any("em or en dash" in w.lower() for w in result.warnings)


def test_no_question_flagged():
    text = (
        "I had a similar setup on a 1,800 sqft home in NC. After two years, "
        "production stayed within 4% of the modeled estimate, even through summer haze."
    )
    result = lint_draft(text, client_name="8MSolar")
    assert result.has_question is False
    assert any("question" in w.lower() for w in result.warnings)


def test_emoji_flagged():
    text = "Solar is amazing for cutting bills 💸 What's your monthly usage?"
    result = lint_draft(text, client_name="8MSolar")
    assert any("emoji" in w.lower() for w in result.warnings)


def test_hype_words_flagged():
    text = (
        "Solar is a game-changer for homeowners and the technology is truly revolutionary. "
        "What's your average monthly bill?"
    )
    result = lint_draft(text, client_name="8MSolar")
    assert any("hype" in w.lower() for w in result.warnings)


def test_marketing_tropes_flagged():
    text = (
        "Let's delve into how solar can leverage your roof space and unlock real savings. "
        "What's your roof orientation?"
    )
    result = lint_draft(text, client_name="8MSolar")
    flagged = " ".join(result.warnings).lower()
    assert "delve" in flagged
    assert "leverage" in flagged
    assert "unlock" in flagged


def test_cta_phrase_flagged():
    text = (
        "Most NC homeowners save $15-30k over 25 years. Feel free to DM me if you want details. "
        "What's your monthly usage like?"
    )
    result = lint_draft(text, client_name="8MSolar")
    assert any("cta" in w.lower() for w in result.warnings)


def test_coaching_language_flagged():
    text = (
        "You should get three quotes before signing anything. You need to check Duke Energy's net metering policy too. "
        "What state are you in?"
    )
    result = lint_draft(text, client_name="8MSolar")
    assert any("coaching" in w.lower() for w in result.warnings)


def test_korr_portable_word_flagged():
    text = (
        "The CardioCoach is a portable metabolic system that fits in a small studio. "
        "What kind of clients are you testing?"
    )
    result = lint_draft(text, client_name="KORR")
    assert any("portable" in w.lower() for w in result.warnings)


def test_mcfie_promised_returns_flagged():
    text = (
        "Whole life policies build cash value with a 10% return guaranteed every year, "
        "which is a strong foundation for the Perpetual Wealth Code. "
        "Have you reviewed your current policy structure?"
    )
    result = lint_draft(text, client_name="McFie Insurance")
    assert any("return" in w.lower() and "promised" in w.lower() for w in result.warnings)


def test_mcfie_dave_ramsey_attack_flagged():
    text = (
        "Dave Ramsey is wrong about whole life insurance and most people who follow his advice end up worse off. "
        "Have you compared net cost over 30 years?"
    )
    result = lint_draft(text, client_name="McFie Insurance")
    assert any("dave ramsey" in w.lower() for w in result.warnings)


def test_brand_mention_count_excessive_flagged():
    text = (
        "8MSolar installs panels in NC. 8MSolar is licensed by Duke Energy. "
        "8MSolar offers PowerPair eligibility checks too. What's your zip code?"
    )
    result = lint_draft(text, client_name="8MSolar")
    assert result.brand_mention_count >= 3
    assert any("brand mentioned" in w.lower() for w in result.warnings)


def test_too_short_flagged():
    text = "Try Qcells. What's your roof size?"
    result = lint_draft(text, client_name="8MSolar")
    assert any("short" in w.lower() for w in result.warnings)


def test_too_long_flagged():
    body = " ".join(["solar"] * 250)
    text = body + " What is your monthly usage?"
    result = lint_draft(text, client_name="8MSolar")
    assert any("long" in w.lower() for w in result.warnings)


def test_score_capped_at_100():
    # Stuff every possible failure into one draft.
    text = (
        "You should leverage the amazing — revolutionary — game-changing solar technology to "
        "delve into a holistic, robust, cutting-edge transformation 💸💸💸. "
        "Feel free to DM me. 8MSolar is the best. 8MSolar wins. 8MSolar is amazing."
    )
    result = lint_draft(text, client_name="8MSolar")
    assert result.score == 100
    assert result.passed is False


def test_summary_string():
    text = "Helpful answer with detail and a clear question at the end. What is your context?"
    result = lint_draft(text, client_name="8MSolar")
    summary = result.summary()
    assert "Lint" in summary
    assert "score" in summary
