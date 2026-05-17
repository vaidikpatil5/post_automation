import json
from article_fetcher import fetch_full_article
from llm_clients import (
    model_json,
    groq_json,
    normalize_string_list,
    fallback_lines,
)
from storage import default_post_context, save_post_context


STYLE_EXAMPLES = [
    "Most social apps don't die because of competition.\nThey die because they stop being fun.",
    "The biggest businesses often look stupid in year 1.",
    "Distribution problems often disguise themselves as product problems.",
    "People underestimate how much trust matters in financial products.",
]


def build_post_context(selected):
    context = default_post_context()
    context["title"] = selected.get("title", "")
    context["summary"] = selected.get("summary", "")
    context["link"] = selected.get("link", "")
    context["style_examples"] = STYLE_EXAMPLES[:]
    return context


def analyze_full_article(context):
    full_article = context.get("full_article", "")
    full_article_available = bool(full_article and full_article.strip())

    prompt = f"""
You are an elite startup/business analyst.

ARTICLE TITLE:
{context['title']}

ARTICLE SUMMARY:
{context['summary']}

ARTICLE URL:
{context['link']}

FULL ARTICLE:
{full_article if full_article_available else "JINA_FETCH_FAILED_OR_EMPTY"}

If FULL ARTICLE is missing, use ARTICLE URL + title + summary to analyze.

Your job:
- identify the real story beneath the headline
- extract the 3 most tweet-worthy numbers/statistics from the article
- prioritize numbers that create strong tweet hooks
- ignore vanity metrics
- explain why each important number matters
- hidden implications
- second-order effects
- competitive implications
- one contrarian insight
- 5 tweet-worthy angles

Do NOT summarize article.

Return JSON:
{{
  \"core_angle\": \"\",
  \"hook_stats\": [
    {{
      \"stat\": \"\",
      \"why_it_matters\": \"\"
    }}
  ],
  \"hidden_implications\": [],
  \"second_order_effects\": [],
  \"contrarian_take\": \"\",
  \"tweet_angles\": []
}}
"""

    payload, _raw_text = model_json(prompt)

    if not payload:
        return {
            "core_angle": "market shift",
            "hook_stats": [],
            "hidden_implications": [],
            "second_order_effects": [],
            "contrarian_take": "Most people are missing the deeper business implication.",
            "tweet_angles": [],
        }

    return payload


def generate_final_tweets_v2(context):
    rejected_patterns = context.get("rejected_patterns", [])
    tweet_history = context.get("tweet_history", [])

    prompt = f"""
You write elite startup Twitter content.

Examples of good tone:
"Distribution problems often disguise themselves as product problems."

"The biggest businesses often look stupid in year 1."

"AI startups are becoming infrastructure companies disguised as software companies."

Reasoning framework:
Step 1: Identify the most interesting fact/stat/observation from the article
Step 2: Ask:
"What behavior changes because of this?"
Step 3: Ask:
"What second-order business implication emerges?"
Step 4: Convert that into ONE sharp insight
Step 5: Write it in a clean, readable X format
Good transformation examples:
Example 1:
Fact: Anthropic hit $30B revenue
Insight: AI labs are becoming infrastructure-heavy businesses
Tweet: "The best model may not win. The company with the best compute access might."
Example 2:
Fact: India has $141B in listed tech market cap
Insight: founders now face public market discipline
Tweet: "Public markets reward operational discipline. Different game."
Example 3:
Fact: startup employees are getting liquidity
Insight: talent becomes more willing to join startups
Tweet: "Visible startup wealth creation changes talent behavior."

Audience:
- founders
- product people
- MBA audience
- operators
- investors

ARTICLE TITLE:
{context['title']}

ARTICLE SUMMARY:
{context['summary']}

ANALYSIS OUTPUT:
{json.dumps(context['analysis_output'], ensure_ascii=True)}

PREVIOUS DRAFTS:
{json.dumps(tweet_history, ensure_ascii=True)}

AVOID THESE ISSUES:
{json.dumps(rejected_patterns, ensure_ascii=True)}

Generate exactly 4 tweets:
1 operational insight
1 market insight
1 founder insight
1 ecosystem insight

Rules:
- each tweet should focus on ONE clear idea
- start with either:
  a strong stat
  OR a sharp observation
- explain why it matters
- end with a memorable takeaway
- use short paragraphs for readability
- 120-260 characters preferred
- no vague slogans
- no headline rewrites
- no fake predictions
- no fabricated numbers
- no fabricated acquisitions or outcomes
- no corporate language
- no generic startup motivation content
- no essay-style writing
- only make claims grounded in article + analysis
- optimize for clarity over sounding clever
- each tweet should feel complete and logically grounded

Return JSON:
{{
  \"tweets\": []
}}

Important:
- Return ONLY valid JSON
- Do not wrap in markdown code fences
- tweets must be an array of plain strings
"""

    payload, raw_text = groq_json(prompt)

    tweets = normalize_string_list(payload.get("tweets"))

    if not tweets:
        alternative_fields = [
            payload.get("operational_insight"),
            payload.get("market_insight"),
            payload.get("founder_insight"),
            payload.get("ecosystem_insight"),
            payload.get("tweet_1"),
            payload.get("tweet_2"),
            payload.get("tweet_3"),
            payload.get("tweet_4"),
        ]
        tweets = [item.strip() for item in alternative_fields if isinstance(item, str) and item.strip()]

    if not tweets:
        tweets = fallback_lines(raw_text)[:4]

    if not tweets:
        tweets = ["Could not generate tweet drafts."]

    return tweets


def run_generation_pipeline(selected):
    context = build_post_context(selected)

    context["full_article"] = fetch_full_article(context["link"])
    context["full_article_fetch_failed"] = not bool(context["full_article"])
    save_post_context(context)

    context["analysis_output"] = analyze_full_article(context)
    save_post_context(context)

    context.setdefault("tweet_history", [])
    context.setdefault("rejected_patterns", [])

    tweets = generate_final_tweets_v2(context)
    context["final_tweets"] = tweets
    context["tweet_history"].append(tweets)

    save_post_context(context)

    return context


def format_drafts_message(context):
    lines = []
    for idx, tweet in enumerate(context.get("final_tweets", []), 1):
        lines.append(f"{idx}. {tweet}")

    tweets_block = "\n\n".join(lines) if lines else "No tweets generated."
    return (
        f"📰 {context.get('title', '')}\n\n"
        f"🔗 {context.get('link', '')}\n\n"
        f"Generated X Drafts:\n\n"
        f"{tweets_block}\n\n"
        f"Reply with: APPROVE <number> to approve one draft OR REGEN to generate fresh drafts."
    )
