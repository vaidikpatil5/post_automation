import re
from urllib.parse import urlparse

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


THEMATIC_INTERESTS = [
    "AI economics",
    "market structure shifts",
    "infrastructure bottlenecks",
    "distribution advantage",
    "supply chain intelligence",
    "labor market compression",
    "automation economics",
    "measurement replacing intuition",
    "platform dependency",
    "operational leverage",
    "concentration dynamics",
    "pricing disruption",
]

AUDIENCE_PROFILE = """
startups
AI
product strategy
growth systems
fintech
business models
distribution advantage
market structure
incentive shifts
operational leverage
infrastructure transitions
""".strip()

IRRELEVANT_KEYWORDS = [
    "celebrity",
    "politics",
    "sports",
    "movie",
    "entertainment",
]

TENSION_MARKERS = [
    "despite",
    "while",
    "however",
    "yet",
    "but",
    "even though",
    "instead",
    "forcing",
    "collapse",
    "pressure",
    "saturation",
    "replacing",
    "shift",
]

EXPECTATION_VIOLATION_MARKERS = [
    "unexpected",
    "surprising",
    "surprisingly",
    "instead",
    "despite",
    "yet",
    "but",
    "however",
    "only",
    "even as",
    "even though",
]

# Jargon alone must not inflate quality; pair with mechanism markers for credit.
SMART_JARGON_MARKERS = [
    "orchestration",
    "market structure",
    "operational leverage",
    "platform dynamics",
    "infrastructure layer",
    "value shifting",
    "paradigm",
    "ecosystem lock-in",
]

OPERATIONAL_IMPLICATION_MARKERS = [
    "workflow",
    "hiring",
    "layoff",
    "margin",
    "pricing",
    "distribution",
    "adoption",
    "integration",
    "contract",
    "procurement",
    "compliance",
    "sales cycle",
    "unit economics",
    "cac",
    "churn",
    "inventory",
    "throughput",
    "headcount",
    "revenue",
    "profit",
    "cost",
    "spend",
    "deployment",
    "failure rate",
]

MECHANISM_MARKERS = [
    "because",
    "requires",
    "forces",
    "leads to",
    "due to",
    "when",
    "after",
    "before",
    "drives",
    "causes",
    "results in",
    "incentive",
    "tradeoff",
    "bottleneck",
    "latency",
    "failure",
    "recovery",
    "integration",
    "api",
    "workflow",
]

ABSTRACTION_INFLATION_PHRASES = [
    "the future of",
    "ultimate",
    "ultimate product",
    "paradigm",
    "revolution",
    "everything is shifting",
    "everything is changing",
    "signals the next era",
    "entire industry",
    "the era of",
    "the ai era",
    "ai era's",
    "will change everything",
    "next era",
    "fundamentally transforms",
    "not the intelligent model, but",
    "value is shifting",
    "value has shifted",
]

FUTURISM_PHRASES = [
    "will inevitably",
    "inevitably",
    "destined to",
    "soon all",
    "the next decade",
    "world where",
    "before long",
]

EXCESSIVE_CERTAINTY_PHRASES = [
    "clearly",
    "obviously",
    "undoubtedly",
    "certainly will",
    "always will",
    "no doubt",
    "guaranteed to",
]

EXPECTATION_INVERSION_PATTERNS = [
    r"\bdespite\b.+\b(grow|profit|revenue|surge|boom)\b",
    r"\bwhile\b.+\b(fall|slump|loss|decline|shrink)\b",
    r"\b(short|shorting)\b.+\b(nvidia|nvda)\b",
    r"\b(spend|spending|capex)\b.+\b(low|weak|slow)\b.+\badoption\b",
    r"\b(same|similar)\b.+\b(at|for)\b.+\b(lower|less|fraction)\b",
]

ELITE_SIGNAL_ENTITIES = [
    "anthropic",
    "openai",
    "nvidia",
    "microsoft",
    "amazon",
    "google",
    "meta",
    "apple",
    "tsmc",
    "sec",
    "federal reserve",
    "y combinator",
    "yc",
    "a16z",
]

SOURCE_PRESTIGE = {
    "sec.gov": 1.0,
    "ft.com": 0.95,
    "bloomberg.com": 0.95,
    "openai.com": 0.92,
    "anthropic.com": 0.92,
    "nvidia.com": 0.9,
    "techcrunch.com": 0.72,
    "inc42.com": 0.66,
    "yourstory.com": 0.62,
}

MODEL_NAME = "all-MiniLM-L6-v2"
FILTER_THEME_THRESHOLD = 0.24
FILTER_THEME_FLOOR = 0.20
EDITORIAL_SHORTLIST_SIZE = 8

_model = SentenceTransformer(MODEL_NAME)
_theme_embeddings = _model.encode(THEMATIC_INTERESTS)
_audience_embedding = _model.encode([AUDIENCE_PROFILE])


def build_article_text(article):
    return f"{article.get('title', '')} {article.get('summary', '')}".strip()


def encode_texts(texts):
    if not texts:
        return []
    return _model.encode(texts)


def cosine_scores(left_embeddings, right_embeddings):
    if len(left_embeddings) == 0 or len(right_embeddings) == 0:
        return []
    return cosine_similarity(left_embeddings, right_embeddings)


def normalize_domain(url):
    if not url:
        return ""
    domain = urlparse(url).netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def get_theme_matches(text):
    article_embedding = encode_texts([text])
    similarities = cosine_scores(article_embedding, _theme_embeddings)[0]

    ranked = sorted(
        (
            {
                "theme": theme,
                "score": float(score),
            }
            for theme, score in zip(THEMATIC_INTERESTS, similarities)
        ),
        key=lambda item: item["score"],
        reverse=True,
    )

    top_score = ranked[0]["score"] if ranked else 0.0
    matched = [
        item for item in ranked[:3]
        if item["score"] >= FILTER_THEME_FLOOR and item["score"] >= top_score - 0.05
    ]

    return {
        "theme_similarity_score": float(top_score),
        "matched_themes": matched,
    }


def get_audience_alignment_score(article_embedding):
    return float(cosine_scores(article_embedding, _audience_embedding)[0][0])


def score_contradiction(text):
    lowered = text.lower()
    hits = sum(lowered.count(marker) for marker in TENSION_MARKERS)
    bonus = 0.0

    if any(word in lowered for word in ("growth", "surge", "boom")) and any(
        word in lowered for word in ("pressure", "collapse", "layoff", "slowdown", "constraint")
    ):
        bonus += 0.2

    return min(1.0, hits * 0.16 + bonus)


def score_expectation_violation(text):
    lowered = text.lower()
    hits = sum(lowered.count(marker) for marker in EXPECTATION_VIOLATION_MARKERS)
    bonus = 0.0

    if re.search(r"\b(same|lower|higher|faster|slower|cheaper|costlier)\b", lowered):
        bonus += 0.15
    if re.search(r"\b\d+(\.\d+)?x\b", lowered):
        bonus += 0.2
    if re.search(r"\bdespite\b", lowered) and re.search(
        r"\b(grow|growth|profit|revenue|surge|rise|boom)\b", lowered
    ):
        bonus += 0.22
    if re.search(r"\bwhile\b", lowered) and re.search(
        r"\b(fall|slump|loss|decline|shrink|drop|pressure)\b", lowered
    ):
        bonus += 0.18
    if re.search(r"\b(short|shorting)\b", lowered) and "nvidia" in lowered:
        bonus += 0.25

    for pattern in EXPECTATION_INVERSION_PATTERNS:
        if re.search(pattern, lowered):
            bonus += 0.12

    return min(1.0, hits * 0.16 + bonus)


def score_hookability(text):
    lowered = text.lower()
    score = 0.0

    if re.search(r"\b\d[\d,.]*\b", text):
        score += 0.3
    if "%" in text or re.search(r"\b(billion|million|trillion|cr|crore|bn)\b", lowered):
        score += 0.2
    if any(token in lowered for token in ("vs", "versus", "same", "lower", "higher", "despite", "yet", "while")):
        score += 0.22
    if re.search(r"\b(despite|yet|but)\b", lowered) and re.search(
        r"\b(grow|profit|revenue|fall|slump|loss)\b", lowered
    ):
        score += 0.18

    return min(1.0, score)


def score_operational_implication(text):
    """Reward observable operational consequences, not jargon density."""
    lowered = text.lower()
    operational_hits = sum(
        1 for marker in OPERATIONAL_IMPLICATION_MARKERS if marker in lowered
    )
    mechanism_hits = sum(1 for marker in MECHANISM_MARKERS if marker in lowered)
    jargon_hits = sum(1 for marker in SMART_JARGON_MARKERS if marker in lowered)

    score = min(1.0, operational_hits * 0.14 + mechanism_hits * 0.08)
    if jargon_hits >= 2 and mechanism_hits == 0 and operational_hits == 0:
        score *= 0.45
    return score


def score_implication(text):
    """Compatibility alias — operational implication, not abstract jargon."""
    return score_operational_implication(text)


def score_epistemic_restraint(text):
    """Higher = more grounded, less fake-deep (1.0 is ideal restraint)."""
    lowered = text.lower()
    penalty = 0.0

    for phrase in ABSTRACTION_INFLATION_PHRASES:
        if phrase in lowered:
            penalty += 0.18
    for phrase in FUTURISM_PHRASES:
        if phrase in lowered:
            penalty += 0.14
    for phrase in EXCESSIVE_CERTAINTY_PHRASES:
        if phrase in lowered:
            penalty += 0.10

    jargon_hits = sum(1 for marker in SMART_JARGON_MARKERS if marker in lowered)
    mechanism_hits = sum(1 for marker in MECHANISM_MARKERS if marker in lowered)
    if jargon_hits >= 2 and mechanism_hits == 0:
        penalty += 0.28
    if re.search(r"\b(entire|whole)\s+(industry|market|ecosystem)\b", lowered):
        penalty += 0.15
    if re.search(r"\bnot\b.+\bbut\b", lowered) and mechanism_hits == 0:
        penalty += 0.12

    return max(0.0, 1.0 - min(1.0, penalty))


def score_mechanism_visibility(text):
    """Higher = causal/operational drivers are visible in the text."""
    lowered = text.lower()
    mechanism_hits = sum(1 for marker in MECHANISM_MARKERS if marker in lowered)
    operational_hits = sum(
        1 for marker in OPERATIONAL_IMPLICATION_MARKERS if marker in lowered
    )
    has_number = bool(re.search(r"\b\d[\d,.]*\b", text))
    has_entity = any(entity in lowered for entity in ELITE_SIGNAL_ENTITIES)

    score = min(1.0, mechanism_hits * 0.12 + operational_hits * 0.08)
    if has_number:
        score += 0.15
    if has_entity:
        score += 0.10
    if re.search(r"\b(because|requires|forces|due to|leads to)\b", lowered):
        score += 0.12

    jargon_only = (
        sum(1 for marker in SMART_JARGON_MARKERS if marker in lowered) >= 2
        and mechanism_hits == 0
        and operational_hits == 0
    )
    if jargon_only:
        score *= 0.35

    return min(1.0, score)


def score_claim_supportability(text, article=None):
    """Higher = claims appear anchored in observable source material."""
    lowered = text.lower()
    score = 0.25

    if re.search(r"\b\d[\d,.]*\b", text):
        score += 0.20
    if "%" in text or re.search(r"\b(billion|million|trillion|cr|crore|bn|q\d)\b", lowered):
        score += 0.18
    if any(entity in lowered for entity in ELITE_SIGNAL_ENTITIES):
        score += 0.12
    if re.search(r"\b(announced|reported|said|according|filed|launched|acquired)\b", lowered):
        score += 0.12
    if article and article.get("published_at"):
        score += 0.05

    for phrase in ABSTRACTION_INFLATION_PHRASES + FUTURISM_PHRASES:
        if phrase in lowered:
            score -= 0.12

    return max(0.0, min(1.0, score))


def score_abstraction_penalty(text):
    """Higher = more abstract / less grounded (used as penalty in ranking)."""
    return 1.0 - score_epistemic_restraint(text)


def score_source_prestige(article):
    domain = article.get("source_domain") or normalize_domain(article.get("link", ""))

    if domain in SOURCE_PRESTIGE:
        return float(SOURCE_PRESTIGE[domain])

    for known_domain, value in SOURCE_PRESTIGE.items():
        if domain.endswith(known_domain):
            return float(value)

    return 0.4


def score_elite_signal(article):
    text = build_article_text(article).lower()
    entity_hits = sum(1 for entity in ELITE_SIGNAL_ENTITIES if entity in text)
    source_bonus = score_source_prestige(article) * 0.35
    return min(1.0, entity_hits * 0.18 + source_bonus)


def build_editorial_decision_reason(scores, matched_themes):
    reasons = []

    if scores.get("expectation_violation_score", 0) >= 0.45:
        reasons.append("high expectation violation")
    if scores.get("mechanism_visibility_score", 0) >= 0.5:
        reasons.append("visible causal mechanism")
    if scores.get("claim_supportability_score", 0) >= 0.55:
        reasons.append("well-supported claims")
    if scores.get("epistemic_restraint_score", 0) >= 0.65:
        reasons.append("epistemically restrained")
    if scores.get("contradiction_score", 0) >= 0.45:
        reasons.append("high contradiction")
    if scores.get("hookability_score", 0) >= 0.5:
        reasons.append("high hookability")
    if scores.get("implication_score", 0) >= 0.45:
        reasons.append("operational implications")
    if scores.get("abstraction_penalty", 0) >= 0.45:
        reasons.append("abstraction-heavy (penalized)")
    if scores.get("elite_signal_score", 0) >= 0.55:
        reasons.append("elite signal")
    if scores.get("source_prestige_score", 0) >= 0.8:
        reasons.append("high-prestige source")

    for theme in matched_themes[:2]:
        reasons.append(f"theme match: {theme['theme']}")

    seen = set()
    deduped = []
    for reason in reasons:
        if reason not in seen:
            deduped.append(reason)
            seen.add(reason)

    return deduped[:5]


def default_narrative_convergence_object():
    """Placeholder for future multi-signal → single narrative clustering."""
    return {
        "cluster_label": "",
        "weak_signal_hooks": [],
        "convergence_ready": False,
    }


def attach_narrative_convergence_stub(article):
    article.setdefault("narrative_object", default_narrative_convergence_object())
    candidate = article.get("narrative_candidate") or {}
    hooks = candidate.get("weak_signal_hooks") or []
    if hooks:
        article["narrative_object"]["weak_signal_hooks"] = hooks
        article["narrative_object"]["cluster_label"] = candidate.get("narrative_cluster", "")
    return article


def default_narrative_candidate():
    return {
        "main_claim": "",
        "causal_mechanism": "",
        "operational_shift": "",
        "incentive_change": "",
        "observable_driver": "",
        "operational_consequence": "",
        "hidden_implication": "",
        "contradiction": "",
        "expectation_violation": "",
        "why_it_matters": "",
        "claim_supportability": 0,
        "mechanism_visibility": 0,
        "epistemic_restraint": 0,
        "audience_relevance": 0,
        "implication_strength": 0,
        "narrative_cluster": "",
        "weak_signal_hooks": [],
    }


def build_narrative_candidate_prompt(article):
    text = build_article_text(article)
    return f"""
You are a sharp editorial analyst ranking news for mechanism-grounded X/Twitter commentary.

Your job is NOT to summarize.
Your job is to extract whether this signal supports a compressed, believable analytical post.

Optimize for COMPRESSED MECHANISM-AWARE INSIGHT — not maximum abstraction.

Every field must be inferable from the source material below.
Ask: "Can this implication reasonably be inferred from the article?"

REQUIRE for strong scores:
- causal_mechanism: the how/why (not vibes)
- operational_shift: what changes in workflows, costs, hiring, distribution, pricing, adoption
- incentive_change: who gains/loses and why
- observable_driver: the concrete trigger in the story (metric, event, product, policy)

PENALIZE in your own scoring:
- unsupported macro claims
- vague futurism ("the era of", "everything will")
- deterministic predictions
- jargon without mechanism (orchestration, market structure, paradigm without specifics)
- abstraction leaps beyond the article

Article:
Title: {article.get("title", "")}
Summary: {article.get("summary", "")}
Source: {article.get("source_domain", "")}
Published: {article.get("published_at", "")}
Combined text: {text}

Return ONLY JSON.

Format:
{{
  "main_claim": "",
  "causal_mechanism": "",
  "operational_shift": "",
  "incentive_change": "",
  "observable_driver": "",
  "operational_consequence": "",
  "hidden_implication": "",
  "contradiction": "",
  "expectation_violation": "",
  "why_it_matters": "",
  "claim_supportability": 0,
  "mechanism_visibility": 0,
  "epistemic_restraint": 0,
  "audience_relevance": 0,
  "implication_strength": 0,
  "narrative_cluster": "",
  "weak_signal_hooks": []
}}

Scoring guidance (0 to 10 each):
- claim_supportability: how strongly the source supports the thesis
- mechanism_visibility: are causal drivers explicit and operational?
- epistemic_restraint: avoids overclaiming, futurism, and fake depth
- audience_relevance: useful to startup/AI/product operators
- implication_strength: operational consequence density (not abstraction density)

weak_signal_hooks: short tags for related signals (for future clustering), e.g. ["layoffs", "copilot adoption"]
""".strip()
