from article_fetcher import fetch_full_article
from llm_clients import (
    model_json,
    groq_json,
    normalize_string_list,
    fallback_lines,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GROQ_MODEL,
)
from prompts import (
    build_tension_extraction_prompt,
    build_implication_refinement_prompt,
    build_compressed_expression_prompt,
    build_final_post_prompt,
)
from storage import default_post_context, save_post_context

# Cognition routing (worldview-first pipeline)
STAGE_TENSION_MODEL = DEFAULT_GEMINI_MODEL
STAGE_IMPLICATION_MODEL = DEFAULT_GROQ_MODEL
STAGE_EXPRESSION_MODEL = DEFAULT_GEMINI_MODEL
STAGE_POST_MODEL = DEFAULT_GROQ_MODEL

# Legacy aliases
STAGE_1_SIGNAL_MODEL = STAGE_TENSION_MODEL
STAGE_2_THESIS_MODEL = STAGE_IMPLICATION_MODEL
STAGE_3_NARRATIVE_MODEL = STAGE_EXPRESSION_MODEL
STAGE_4_POST_MODEL = STAGE_POST_MODEL


def build_post_context(selected):
    context = default_post_context()
    context["title"] = selected.get("title", "")
    context["summary"] = selected.get("summary", "")
    context["link"] = selected.get("link", "")
    if selected.get("narrative_candidate"):
        context["narrative_candidate"] = selected["narrative_candidate"]
    return context


def _default_narrative_match():
    return {
        "matched_narratives": [],
        "confidence": 0.0,
        "supporting_mechanisms": [],
        "expectation_violations": [],
        "editorial_tension": [],
        "recommended_templates": [],
        "primary_narrative_id": "",
    }


def _default_tension_output():
    return {
        "activated_narrative_ids": [],
        "broken_assumption": "",
        "observable_driver": "",
        "incentive_change": "",
        "contradiction": "",
        "expectation_violation": "",
        "operational_shift": "",
        "editorial_tension": "",
        "missed_by_most_people": "",
    }


def _default_implication_output():
    return {
        "refined_implications": [],
        "operational_consequences": [],
        "contrarian_angle": "",
        "product_operator_lessons": [],
        "claim_supportability_note": "",
    }


def _default_expression_output():
    return {
        "hooks": [],
        "compressed_beats": [],
        "closing_insight": "",
    }


def _default_signal_analysis():
    """Backward compatibility shape."""
    return {
        "core_signal": "",
        "broken_assumption": "",
        "observable_driver": "",
        "causal_mechanism": "",
        "operational_shift": "",
        "incentive_change": "",
        "expectation_violation": "",
        "operational_consequences": [],
        "second_order_effects": [],
        "startup_opportunities": [],
        "hidden_implications": [],
        "missed_by_most_people": "",
        "market_shift": "",
    }


def _default_thesis_output():
    return {
        "theses": [],
        "contrarian_views": [],
        "operational_implications": [],
        "long_term_implications": [],
        "product_lessons": [],
        "market_dynamics": [],
    }


def _default_narrative_output():
    return {
        "hooks": [],
        "compressed_narratives": [],
        "ending_insights": [],
    }


def _sync_legacy_context(context):
    """Map worldview-first outputs to legacy keys for downstream consumers."""
    tension = context.get("tension_output", {})
    implication = context.get("implication_output", {})
    expression = context.get("expression_output", {})
    match = context.get("narrative_match", {})
    mechanisms = match.get("supporting_mechanisms", [])

    signal = _default_signal_analysis()
    signal.update({
        "core_signal": tension.get("editorial_tension", ""),
        "broken_assumption": tension.get("broken_assumption", ""),
        "observable_driver": tension.get("observable_driver", ""),
        "causal_mechanism": mechanisms[0] if mechanisms else "",
        "operational_shift": tension.get("operational_shift", ""),
        "incentive_change": tension.get("incentive_change", ""),
        "expectation_violation": tension.get("expectation_violation", ""),
        "operational_consequences": implication.get("operational_consequences", []),
        "hidden_implications": implication.get("refined_implications", []),
        "missed_by_most_people": tension.get("missed_by_most_people", ""),
        "market_shift": tension.get("operational_shift", "") or (mechanisms[0] if mechanisms else ""),
    })
    context["signal_analysis"] = signal
    context["analysis_output"] = signal

    thesis = _default_thesis_output()
    thesis.update({
        "theses": implication.get("refined_implications", []),
        "contrarian_views": [implication.get("contrarian_angle", "")] if implication.get("contrarian_angle") else [],
        "operational_implications": implication.get("operational_consequences", []),
        "product_lessons": implication.get("product_operator_lessons", []),
    })
    context["thesis_output"] = thesis

    narrative = _default_narrative_output()
    narrative.update({
        "hooks": expression.get("hooks", []),
        "compressed_narratives": expression.get("compressed_beats", []),
        "ending_insights": [expression.get("closing_insight", "")] if expression.get("closing_insight") else [],
    })
    context["narrative_output"] = narrative


def _extract_posts_from_payload(payload):
    posts = normalize_string_list(payload.get("posts"))

    if posts:
        return posts

    alternative_fields = [
        payload.get("post_1"),
        payload.get("post_2"),
        payload.get("post_3"),
        payload.get("tweet_1"),
        payload.get("tweet_2"),
        payload.get("tweet_3"),
        payload.get("operational_insight"),
        payload.get("market_insight"),
        payload.get("founder_insight"),
        payload.get("ecosystem_insight"),
    ]
    return [item.strip() for item in alternative_fields if isinstance(item, str) and item.strip()]


def get_current_posts(context):
    posts = context.get("final_posts", [])
    if posts:
        return posts
    return context.get("final_tweets", [])


def run_narrative_matching(context):
    # 1. Use pre-computed narrative match if present in context (e.g. from GitHub Actions main.py run)
    if "narrative_match" in context and context["narrative_match"].get("matched_narratives"):
        return context["narrative_match"]

    # 2. Otherwise, check if we can run it locally (e.g. during local tests where torch is available)
    try:
        import torch
        import sentence_transformers
        from narrative_priors import match_narrative_priors

        article = {
            "title": context.get("title", ""),
            "summary": context.get("summary", ""),
            "link": context.get("link", ""),
        }
        result = match_narrative_priors(article)
        if result and result.get("matched_narratives"):
            return result
    except ImportError:
        pass

    return _default_narrative_match()


def run_tension_extraction(context):
    payload, _raw_text = model_json(
        build_tension_extraction_prompt(context),
        model=STAGE_TENSION_MODEL,
    )
    if not payload:
        return _default_tension_output()

    result = _default_tension_output()
    result.update(payload)
    if not result["activated_narrative_ids"] and context.get("narrative_match"):
        result["activated_narrative_ids"] = [
            n["id"] for n in context["narrative_match"].get("matched_narratives", [])
        ]
    return result


def run_implication_refinement(context):
    payload, _raw_text = groq_json(
        build_implication_refinement_prompt(context),
        model=STAGE_IMPLICATION_MODEL,
    )
    if not payload:
        return _default_implication_output()

    result = _default_implication_output()
    result.update(payload)
    return result


def run_compressed_expression(context):
    payload, _raw_text = model_json(
        build_compressed_expression_prompt(context),
        model=STAGE_EXPRESSION_MODEL,
    )
    if not payload:
        return _default_expression_output()

    result = _default_expression_output()
    result.update(payload)
    return result


def run_final_post_generation(context):
    payload, raw_text = groq_json(
        build_final_post_prompt(context),
        model=STAGE_POST_MODEL,
    )

    posts = _extract_posts_from_payload(payload)

    if not posts:
        posts = fallback_lines(raw_text)[:3]

    if not posts:
        posts = ["Could not generate post drafts."]

    return posts


# --- Backward compatibility aliases ---

def run_signal_analysis(context):
    if not context.get("narrative_match"):
        context["narrative_match"] = run_narrative_matching(context)
    return run_tension_extraction(context)


def run_thesis_generation(context):
    return run_implication_refinement(context)


def run_narrative_compression(context):
    return run_compressed_expression(context)


def generate_final_tweets_v2(context):
    return run_final_post_generation(context)


def run_generation_pipeline(selected):
    context = build_post_context(selected)

    context["full_article"] = fetch_full_article(context["link"])
    context["full_article_fetch_failed"] = not bool(context["full_article"])
    save_post_context(context)

    # 1. Narrative prior matching (embedding — primary cognition layer)
    context["narrative_match"] = run_narrative_matching(context)
    save_post_context(context)

    # 2. Tension extraction (LLM — through activated priors)
    context["tension_output"] = run_tension_extraction(context)
    save_post_context(context)

    # 3. Implication refinement (LLM — grounded, not invented macro theory)
    context["implication_output"] = run_implication_refinement(context)
    save_post_context(context)

    # 4. Compressed expression (LLM — post-ready beats)
    context["expression_output"] = run_compressed_expression(context)
    _sync_legacy_context(context)
    save_post_context(context)

    context.setdefault("tweet_history", [])
    context.setdefault("rejected_patterns", [])

    # 5. Final posts
    posts = run_final_post_generation(context)
    context["final_posts"] = posts
    context["final_tweets"] = posts
    context["tweet_history"].append(posts)
    _sync_legacy_context(context)
    save_post_context(context)

    return context


def format_drafts_message(context):
    lines = []
    for idx, post in enumerate(get_current_posts(context), 1):
        lines.append(f"{idx}. {post}")

    posts_block = "\n\n".join(lines) if lines else "No posts generated."

    priors = context.get("narrative_match", {}).get("matched_narratives", [])
    prior_line = ""
    if priors:
        names = ", ".join(p["name"] for p in priors[:2])
        prior_line = f"\n🧭 Activated narratives: {names}\n"

    return (
        f"📰 {context.get('title', '')}\n\n"
        f"🔗 {context.get('link', '')}\n"
        f"{prior_line}\n"
        f"Generated X Drafts:\n\n"
        f"{posts_block}\n\n"
        f"Reply with: APPROVE <number> to approve one draft OR REGEN to generate fresh drafts."
    )
