import json

from narrative_priors import format_matched_narratives_for_prompt
from editorial_templates import EDITORIAL_TEMPLATES


WORLDVIEW_SYSTEM_IDENTITY = """
You are a sharp strategic analyst with persistent worldview frameworks.

You do NOT invent insight from scratch or make vague, ungrounded futurist claims.
Instead, you ACTIVATE existing narrative priors and FILL structural editorial templates using evidence from the article.

Optimize for: compressed strategic interpretation grounded in mechanism.
NOT: maximum abstraction, hype, or synthetic "systems thinking."

Every claim must pass: "Can this reasonably be inferred from the source material?"

You avoid:
- fake-deep abstraction, futurism, paradigm language
- unsupported macro claims and deterministic predictions
- smart jargon without causal mechanism
- motivational tone and AI hype
- exclamation points, emojis, hashtags

Writing style:
- compressed, understated, mechanism-visible
- one abstraction layer above the headline (not five)
- epistemic restraint when evidence is thin (phrase as tension or question)
- no hashtags, no emojis, low emotion
""".strip()

BANNED_OUTPUT_PHRASES = """
Never use, emulate, or paraphrase:
- "the future of"
- "ultimate"
- "paradigm"
- "revolution"
- "everything is shifting"
- "signals the next era"
- "the AI era's"
- "entire industry will"
- "ultimate value layer"
- "paradigm shift"
- "everything is changing"
""".strip()

# Backward compatibility
MASTER_SYSTEM_IDENTITY = WORLDVIEW_SYSTEM_IDENTITY


def _article_block(context):
    full_article = context.get("full_article", "")
    if not (full_article and full_article.strip()):
        full_article = "ARTICLE_BODY_UNAVAILABLE_USE_TITLE_AND_SUMMARY_ONLY"

    narrative_block = format_matched_narratives_for_prompt(
        context.get("narrative_match", {})
    )

    return f"""
ARTICLE TITLE:
{context.get("title", "")}

ARTICLE SUMMARY:
{context.get("summary", "")}

ARTICLE URL:
{context.get("link", "")}

FULL ARTICLE:
{full_article}

{narrative_block}
""".strip()


def _rejected_block(context):
    return json.dumps(context.get("rejected_patterns", []), ensure_ascii=True)


def _get_recommended_templates_block(context):
    matched_templates = context.get("narrative_match", {}).get("recommended_templates", [])
    if not matched_templates:
        # fallback templates
        matched_templates = ["shift_not_x_but_y", "competing_on_y_not_x", "moat_moving_x_to_y"]
    
    lines = ["RECOMMENDED EDITORIAL TEMPLATES TO ACTIVATE:"]
    for t_id in matched_templates:
        for t in EDITORIAL_TEMPLATES:
            if t["id"] == t_id:
                lines.append(f"- Template ID: {t['id']}")
                lines.append(f"  Name: {t['template_name']}")
                lines.append(f"  Structure: {t['core_structure']}")
                lines.append(f"  Editorial Pattern: {t['editorial_pattern']}")
                lines.append(f"  Avoid: {', '.join(t['avoid'])}")
                lines.append("")
                break
    return "\n".join(lines)


def build_tension_extraction_prompt(context):
    """Stage 2: extract editorial tension through activated narrative priors."""
    narrative_match = json.dumps(context.get("narrative_match", {}), ensure_ascii=True)
    return f"""
{WORLDVIEW_SYSTEM_IDENTITY}

{BANNED_OUTPUT_PHRASES}

The narrative priors below are PRE-EXISTING strategic frameworks.
Your job is to find where THIS article creates tension within or against them.

Do NOT manufacture a new worldview.
Do NOT summarize the headline.

Ask:
- what assumption weakens? (this will fill the 'expectation_violation' slot)
- what operational shift occurs? (this will fill the 'operational_shift' slot)
- what incentive changes?
- what contradiction emerges?

Every field must be inferable from the source material.

Narrative match data:
{narrative_match}

{_article_block(context)}

Return ONLY JSON.

Format:
{{
  "activated_narrative_ids": [],
  "broken_assumption": "What superficial assumption is broken by this signal?",
  "observable_driver": "The concrete trigger in the story (metric, event, product, policy)",
  "incentive_change": "Who gains, who loses, and why?",
  "contradiction": "The core operational contradiction in the signal",
  "expectation_violation": "The 'not_x' component: what superficial view or expectation gets broken?",
  "operational_shift": "The 'but_y' component: the concrete change in workflows, costs, distribution, or pricing",
  "editorial_tension": "The core tension arising from the signal",
  "missed_by_most_people": "What is the counter-intuitive implication missed by casual readers?"
}}
""".strip()


def build_implication_refinement_prompt(context):
    """Stage 3: refine believable implications — no grand macro theories."""
    tension = json.dumps(context.get("tension_output", {}), ensure_ascii=True)
    narrative_match = json.dumps(context.get("narrative_match", {}), ensure_ascii=True)
    return f"""
{WORLDVIEW_SYSTEM_IDENTITY}

{BANNED_OUTPUT_PHRASES}

Refine implications from activated narratives + extracted tension.

Rules:
- stay ONE abstraction layer above observable facts (do NOT invent new macro theories)
- each implication must show mechanism (because -> therefore -> consequence)
- if evidence is thin, phrase as tension or question — not certainty
- prefer operational consequences: workflows, pricing, hiring, distribution, unit economics

Activated narratives and tension:
{narrative_match}

Tension extraction:
{tension}

Generate:
1. refined_implications — short mechanism-grounded observations
2. operational_consequences — near-term measurable effects (pricing, workflows, headcount)
3. contrarian_angle — inversion grounded in the article facts
4. product_operator_lessons — what builders should adjust (if supported)

Return ONLY JSON.

Format:
{{
  "refined_implications": [],
  "operational_consequences": [],
  "contrarian_angle": "",
  "product_operator_lessons": [],
  "claim_supportability_note": ""
}}
""".strip()


def build_compressed_expression_prompt(context):
    """Stage 4: Fill strategic slots into the activated templates."""
    implication = json.dumps(context.get("implication_output", {}), ensure_ascii=True)
    tension = json.dumps(context.get("tension_output", {}), ensure_ascii=True)
    templates_block = _get_recommended_templates_block(context)

    return f"""
{WORLDVIEW_SYSTEM_IDENTITY}

{BANNED_OUTPUT_PHRASES}

Compress refined implications by filling the strategic slots of the recommended editorial templates below.

{templates_block}

Instructions:
- Take the recommended template structures and populate their slots ({'{not_x}'} and {'{but_y}'}) using the mechanisms, tensions, and implications in the context.
- Keep the writing understated, sober, and low-emotion.
- Expose the causal driver and operational mechanism in the filled structures.
- Put the filled template texts into the "hooks" array.

Tension:
{tension}

Implication refinement:
{implication}

Avoid:
{_rejected_block(context)}

Return ONLY JSON.

Format:
{{
  "hooks": ["Filled Template 1 Text", "Filled Template 2 Text"],
  "compressed_beats": ["Supporting mechanism beat 1", "Supporting mechanism beat 2"],
  "closing_insight": "Understated closing insight showing operational consequence"
}}
""".strip()


def build_final_post_prompt(context):
    """Stage 5: final compressed posts."""
    narrative_match = json.dumps(context.get("narrative_match", {}), ensure_ascii=True)
    tension = json.dumps(context.get("tension_output", {}), ensure_ascii=True)
    implication = json.dumps(context.get("implication_output", {}), ensure_ascii=True)
    expression = json.dumps(context.get("expression_output", {}), ensure_ascii=True)
    tweet_history = json.dumps(context.get("tweet_history", []), ensure_ascii=True)

    return f"""
{WORLDVIEW_SYSTEM_IDENTITY}

{BANNED_OUTPUT_PHRASES}

Generate 3 X/Twitter post drafts by consolidating the filled templates, hooks, and beats.

Hard rules:
- ~280 characters each when possible
- Mechanism must be visible (why, not just that)
- Cite observable driver from the article when possible
- Understate when evidence is thin (epistemic restraint)
- Absolutely NO exclamation marks, hashtags, or emojis
- Absolutely no futurism phrases (e.g. "will inevitably", "in the era of")

Bad pattern (do NOT emulate - too high abstraction and hype):
"The AI era's ultimate product is not the intelligent model, but the controlled environment..."

Good pattern (emulate - grounded, mechanism-visible, template-filled structure):
"Companies are no longer competing on raw model benchmarks. They're competing on workflow persistence and failure recovery, which shifts complexity to the orchestration layer."

Narrative priors:
{narrative_match}

Tension:
{tension}

Implications:
{implication}

Compressed beats & filled templates:
{expression}

Previous drafts (do not repeat):
{tweet_history}

Avoid:
{_rejected_block(context)}

Return ONLY JSON.

Format:
{{
  "posts": ["Draft 1", "Draft 2", "Draft 3"]
}}

Important:
- Return ONLY valid JSON
- Do not wrap in markdown code fences
- posts must be an array of plain strings
""".strip()


# --- Backward compatibility aliases (old stage names) ---

def build_signal_analysis_prompt(context):
    return build_tension_extraction_prompt(context)


def build_thesis_generation_prompt(context):
    return build_implication_refinement_prompt(context)


def build_narrative_compression_prompt(context):
    return build_compressed_expression_prompt(context)
