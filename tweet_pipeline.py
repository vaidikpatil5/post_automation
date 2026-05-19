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
    build_signal_analysis_prompt,
    build_thesis_generation_prompt,
    build_narrative_compression_prompt,
    build_final_post_prompt,
)
from storage import default_post_context, save_post_context


STAGE_1_SIGNAL_MODEL = DEFAULT_GEMINI_MODEL
STAGE_2_THESIS_MODEL = DEFAULT_GROQ_MODEL
STAGE_3_NARRATIVE_MODEL = DEFAULT_GEMINI_MODEL
STAGE_4_POST_MODEL = DEFAULT_GROQ_MODEL


def build_post_context(selected):
    context = default_post_context()
    context["title"] = selected.get("title", "")
    context["summary"] = selected.get("summary", "")
    context["link"] = selected.get("link", "")
    if selected.get("narrative_candidate"):
        context["narrative_candidate"] = selected["narrative_candidate"]
    return context


def _default_signal_analysis():
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
    }


def _default_thesis_output():
    return {
        "theses": [],
        "contrarian_views": [],
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


def run_signal_analysis(context):
    payload, _raw_text = model_json(
        build_signal_analysis_prompt(context),
        model=STAGE_1_SIGNAL_MODEL,
    )
    if not payload:
        return _default_signal_analysis()

    result = _default_signal_analysis()
    result.update(payload)
    return result


def run_thesis_generation(context):
    payload, _raw_text = groq_json(
        build_thesis_generation_prompt(context),
        model=STAGE_2_THESIS_MODEL,
    )
    if not payload:
        return _default_thesis_output()

    result = _default_thesis_output()
    result.update(payload)
    return result


def run_narrative_compression(context):
    payload, _raw_text = model_json(
        build_narrative_compression_prompt(context),
        model=STAGE_3_NARRATIVE_MODEL,
    )
    if not payload:
        return _default_narrative_output()

    result = _default_narrative_output()
    result.update(payload)
    return result


def run_final_post_generation(context):
    payload, raw_text = groq_json(
        build_final_post_prompt(context),
        model=STAGE_4_POST_MODEL,
    )

    posts = _extract_posts_from_payload(payload)

    if not posts:
        posts = fallback_lines(raw_text)[:3]

    if not posts:
        posts = ["Could not generate post drafts."]

    return posts


def generate_final_tweets_v2(context):
    return run_final_post_generation(context)


def run_generation_pipeline(selected):
    context = build_post_context(selected)

    context["full_article"] = fetch_full_article(context["link"])
    context["full_article_fetch_failed"] = not bool(context["full_article"])
    save_post_context(context)

    context["signal_analysis"] = run_signal_analysis(context)
    context["analysis_output"] = context["signal_analysis"]
    # Backward compatibility for consumers expecting market_shift key.
    if not context["signal_analysis"].get("market_shift"):
        context["signal_analysis"]["market_shift"] = (
            context["signal_analysis"].get("operational_shift")
            or context["signal_analysis"].get("causal_mechanism")
            or ""
        )
    save_post_context(context)

    context["thesis_output"] = run_thesis_generation(context)
    save_post_context(context)

    context["narrative_output"] = run_narrative_compression(context)
    save_post_context(context)

    context.setdefault("tweet_history", [])
    context.setdefault("rejected_patterns", [])

    posts = run_final_post_generation(context)
    context["final_posts"] = posts
    context["final_tweets"] = posts
    context["tweet_history"].append(posts)
    save_post_context(context)

    return context


def format_drafts_message(context):
    lines = []
    for idx, post in enumerate(get_current_posts(context), 1):
        lines.append(f"{idx}. {post}")

    posts_block = "\n\n".join(lines) if lines else "No posts generated."
    return (
        f"📰 {context.get('title', '')}\n\n"
        f"🔗 {context.get('link', '')}\n\n"
        f"Generated X Drafts:\n\n"
        f"{posts_block}\n\n"
        f"Reply with: APPROVE <number> to approve one draft OR REGEN to generate fresh drafts."
    )
