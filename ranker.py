from config import get_env
from editorial_intelligence import (
    EXPECTATION_VIOLATION_MARKERS,
    EDITORIAL_SHORTLIST_SIZE,
    TENSION_MARKERS,
    attach_narrative_convergence_stub,
    build_article_text,
    build_editorial_decision_reason,
    build_narrative_candidate_prompt,
    cosine_scores,
    default_narrative_candidate,
    encode_texts,
    get_audience_alignment_score,
    score_abstraction_penalty,
    score_claim_supportability,
    score_contradiction,
    score_elite_signal,
    score_epistemic_restraint,
    score_expectation_violation,
    score_hookability,
    score_implication,
    score_mechanism_visibility,
    score_source_prestige,
)


GEMINI_AVAILABLE = bool(get_env("GEMINI_API_KEY"))


def _article_key(article):
    return article.get("content_fingerprint") or article.get("link") or article.get("title", "")


def _safe_score_0_to_10(value):
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(10, int(round(numeric))))


def _theme_frequency(articles):
    counts = {}
    for article in articles:
        for match in article.get("theme_matches", []):
            theme = match["theme"]
            counts[theme] = counts.get(theme, 0) + 1
    return counts


def _extract_marker_hits(text, markers):
    lowered = text.lower()
    return [marker for marker in markers if marker in lowered]


def _score_novelty(index, similarity_matrix):
    if len(similarity_matrix) <= 1:
        return 1.0

    other_similarities = [
        float(score)
        for peer_index, score in enumerate(similarity_matrix[index])
        if peer_index != index
    ]

    max_peer_similarity = max(other_similarities) if other_similarities else 0.0
    return max(0.0, 1.0 - max_peer_similarity)


def _score_narrative_momentum(article, theme_counts, total_articles):
    matched_themes = article.get("theme_matches", [])
    if not matched_themes or total_articles <= 1:
        return 0.0

    normalized_support = 0.0
    for theme in matched_themes[:2]:
        normalized_support += theme_counts.get(theme["theme"], 1) / total_articles

    return min(1.0, normalized_support / 2.0)


def _score_signal_richness(scores):
    return min(
        1.0,
        0.22 * scores["implication_score"]
        + 0.18 * scores["expectation_violation_score"]
        + 0.18 * scores["mechanism_visibility_score"]
        + 0.16 * scores["claim_supportability_score"]
        + 0.14 * scores["contradiction_score"]
        + 0.12 * scores["epistemic_restraint_score"],
    )


def _score_editorial_value(scores):
    base = (
        0.14 * scores["expectation_violation_score"]
        + 0.12 * scores["mechanism_visibility_score"]
        + 0.12 * scores["claim_supportability_score"]
        + 0.10 * scores["epistemic_restraint_score"]
        + 0.10 * scores["implication_score"]
        + 0.08 * scores["contradiction_score"]
        + 0.08 * scores["hookability_score"]
        + 0.07 * scores["relevance_score"]
        + 0.06 * scores["novelty_score"]
        + 0.05 * scores["audience_alignment_score"]
        + 0.04 * scores["elite_signal_score"]
        + 0.02 * scores["narrative_momentum_score"]
        + 0.02 * scores["source_prestige_score"]
    )

    # Heavy penalty for weak grounding and fake-deep abstraction.
    if scores["claim_supportability_score"] < 0.35:
        base -= 0.14
    if scores["abstraction_penalty"] >= 0.45:
        base -= 0.10 * scores["abstraction_penalty"]
    if scores["mechanism_visibility_score"] < 0.25:
        base -= 0.08

    return max(0.0, base)


def _compute_article_scores(article, article_texts, article_embeddings, similarity_matrix, theme_counts, total_articles, article_index_map):
    text = build_article_text(article)
    index = article_index_map[_article_key(article)]
    article_embedding = article_embeddings[index:index + 1]

    scores = {
        "relevance_score": float(article.get("theme_similarity_score", 0.0)),
        "contradiction_score": score_contradiction(text),
        "expectation_violation_score": score_expectation_violation(text),
        "hookability_score": score_hookability(text),
        "implication_score": score_implication(text),
        "mechanism_visibility_score": score_mechanism_visibility(text),
        "epistemic_restraint_score": score_epistemic_restraint(text),
        "claim_supportability_score": score_claim_supportability(text, article),
        "abstraction_penalty": score_abstraction_penalty(text),
        "novelty_score": _score_novelty(index, similarity_matrix),
        "elite_signal_score": score_elite_signal(article),
        "narrative_momentum_score": _score_narrative_momentum(article, theme_counts, total_articles),
        "source_prestige_score": score_source_prestige(article),
        "audience_alignment_score": get_audience_alignment_score(article_embedding),
    }

    narrative_candidate = article.get("narrative_candidate") or {}
    llm_audience = float(narrative_candidate.get("audience_relevance", 0) or 0) / 10.0
    llm_implication = float(narrative_candidate.get("implication_strength", 0) or 0) / 10.0
    llm_support = float(narrative_candidate.get("claim_supportability", 0) or 0) / 10.0
    llm_mechanism = float(narrative_candidate.get("mechanism_visibility", 0) or 0) / 10.0
    llm_restraint = float(narrative_candidate.get("epistemic_restraint", 0) or 0) / 10.0
    llm_expectation = 0.0
    if narrative_candidate.get("expectation_violation", "").strip():
        llm_expectation = min(1.0, 0.55 + llm_support * 0.25)

    if llm_audience:
        scores["audience_alignment_score"] = max(scores["audience_alignment_score"], llm_audience)
    if llm_implication:
        scores["implication_score"] = max(scores["implication_score"], llm_implication * 0.85)
    if llm_support:
        scores["claim_supportability_score"] = max(scores["claim_supportability_score"], llm_support)
    if llm_mechanism:
        scores["mechanism_visibility_score"] = max(scores["mechanism_visibility_score"], llm_mechanism)
    if llm_restraint:
        scores["epistemic_restraint_score"] = max(scores["epistemic_restraint_score"], llm_restraint)
        scores["abstraction_penalty"] = 1.0 - scores["epistemic_restraint_score"]
    if llm_expectation:
        scores["expectation_violation_score"] = max(scores["expectation_violation_score"], llm_expectation)

    scores["signal_richness_score"] = _score_signal_richness(scores)
    return scores


def _populate_heuristic_scores(articles, article_texts, article_embeddings, similarity_matrix, theme_counts, total_articles, article_index_map):
    for index, article in enumerate(articles):
        text = article_texts[index]
        tension_hits = _extract_marker_hits(text, TENSION_MARKERS)
        expectation_hits = _extract_marker_hits(text, EXPECTATION_VIOLATION_MARKERS)

        scores = _compute_article_scores(
            article,
            article_texts,
            article_embeddings,
            similarity_matrix,
            theme_counts,
            total_articles,
            article_index_map,
        )

        article["scores"] = scores
        article["signal_richness"] = scores["signal_richness_score"]
        article["audience_alignment"] = scores["audience_alignment_score"]
        article["editorial_score"] = _score_editorial_value(scores)
        article["score"] = article["editorial_score"]
        article["editorial_decision_reason"] = build_editorial_decision_reason(
            scores,
            article.get("theme_matches", []),
        )

        article.setdefault("editorial_metadata", {})
        article["editorial_metadata"]["ranking"] = {
            "tension_markers": tension_hits,
            "expectation_markers": expectation_hits,
            "theme_counts": {
                match["theme"]: theme_counts.get(match["theme"], 1)
                for match in article.get("theme_matches", [])
            },
            "llm_shortlisted": False,
        }


def _extract_shortlist_narratives(articles):
    if not GEMINI_AVAILABLE or not articles:
        return

    try:
        from llm_clients import model_json
    except Exception as exc:
        print(f"Skipping shortlist implication extraction: {exc}")
        return

    shortlist = articles[:EDITORIAL_SHORTLIST_SIZE]

    for article in shortlist:
        candidate = default_narrative_candidate()
        extraction_error = ""

        try:
            payload, _raw_text = model_json(build_narrative_candidate_prompt(article))
            if isinstance(payload, dict):
                candidate.update(payload)
        except Exception as exc:
            extraction_error = str(exc)
            print(f"Shortlist implication extraction failed for '{article.get('title', '')}': {exc}")

        candidate["audience_relevance"] = _safe_score_0_to_10(candidate.get("audience_relevance", 0))
        candidate["implication_strength"] = _safe_score_0_to_10(candidate.get("implication_strength", 0))
        candidate["claim_supportability"] = _safe_score_0_to_10(candidate.get("claim_supportability", 0))
        candidate["mechanism_visibility"] = _safe_score_0_to_10(candidate.get("mechanism_visibility", 0))
        candidate["epistemic_restraint"] = _safe_score_0_to_10(candidate.get("epistemic_restraint", 0))

        if not candidate.get("hidden_implication") and candidate.get("operational_consequence"):
            candidate["hidden_implication"] = candidate["operational_consequence"]

        article["narrative_candidate"] = candidate
        attach_narrative_convergence_stub(article)
        article.setdefault("editorial_metadata", {})
        article["editorial_metadata"].setdefault("ranking", {})
        article["editorial_metadata"]["ranking"]["llm_shortlisted"] = True
        article["editorial_metadata"]["ranking"]["llm_extraction_error"] = extraction_error


def _refresh_scores_after_shortlist(articles, article_texts, article_embeddings, similarity_matrix, theme_counts, total_articles, article_index_map):
    for article in articles:
        scores = _compute_article_scores(
            article,
            article_texts,
            article_embeddings,
            similarity_matrix,
            theme_counts,
            total_articles,
            article_index_map,
        )
        article["scores"] = scores
        article["signal_richness"] = scores["signal_richness_score"]
        article["audience_alignment"] = scores["audience_alignment_score"]
        article["editorial_score"] = _score_editorial_value(scores)
        article["score"] = article["editorial_score"]
        article["editorial_decision_reason"] = build_editorial_decision_reason(
            scores,
            article.get("theme_matches", []),
        )

        candidate = article.get("narrative_candidate", {})
        article.setdefault("editorial_metadata", {})
        article["editorial_metadata"].setdefault("ranking", {})
        article["editorial_metadata"]["ranking"]["narrative_cluster"] = candidate.get("narrative_cluster", "")
        article["editorial_metadata"]["ranking"]["causal_mechanism"] = candidate.get("causal_mechanism", "")
        article["editorial_metadata"]["ranking"]["hidden_implication"] = candidate.get("hidden_implication", "")
        article["editorial_metadata"]["ranking"]["why_it_matters"] = candidate.get("why_it_matters", "")
        article["editorial_metadata"]["ranking"]["claim_supportability"] = candidate.get("claim_supportability", 0)
        article["editorial_metadata"]["ranking"]["mechanism_visibility"] = candidate.get("mechanism_visibility", 0)
        article["editorial_metadata"]["ranking"]["epistemic_restraint"] = candidate.get("epistemic_restraint", 0)
        attach_narrative_convergence_stub(article)


def rank_articles(articles):
    if not articles:
        return []

    article_texts = [build_article_text(article) for article in articles]
    article_embeddings = encode_texts(article_texts)
    similarity_matrix = cosine_scores(article_embeddings, article_embeddings)
    theme_counts = _theme_frequency(articles)
    total_articles = len(articles)
    article_index_map = {
        _article_key(article): index
        for index, article in enumerate(articles)
    }

    _populate_heuristic_scores(
        articles,
        article_texts,
        article_embeddings,
        similarity_matrix,
        theme_counts,
        total_articles,
        article_index_map,
    )

    articles.sort(
        key=lambda item: item["editorial_score"],
        reverse=True,
    )

    _extract_shortlist_narratives(articles)
    _refresh_scores_after_shortlist(
        articles,
        article_texts,
        article_embeddings,
        similarity_matrix,
        theme_counts,
        total_articles,
        article_index_map,
    )

    articles.sort(
        key=lambda item: item["editorial_score"],
        reverse=True,
    )

    return articles[:5]
