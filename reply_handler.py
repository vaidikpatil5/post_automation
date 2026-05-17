import os
import json
import re
import requests
from telegram_bot import send_message
from google import genai
from flask import Flask, request
from config import get_env
from storage import (
    load_articles,
    save_articles,
    load_post_context,
    save_post_context,
    default_post_context,
)

BOT_TOKEN = get_env("BOT_TOKEN")
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
GITHUB_TOKEN = get_env("GITHUB_TOKEN")
GITHUB_OWNER = get_env("GITHUB_OWNER")
GITHUB_REPO = get_env("GITHUB_REPO")
GITHUB_WORKFLOW_FILE = get_env("GITHUB_WORKFLOW_FILE")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY. Set it in .env.")

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

STYLE_EXAMPLES = [
    "Most social apps don't die because of competition.\nThey die because they stop being fun.",
    "The biggest businesses often look stupid in year 1.",
    "Distribution problems often disguise themselves as product problems.",
    "People underestimate how much trust matters in financial products.",
]

STYLE_CONTEXT = {
    "tone": "sharp, concise, operator-minded, slightly contrarian",
    "patterns": [
        "strong first line",
        "short punchy sentences",
        "second-order thinking",
        "avoid summarizing headlines",
        "focus on business implications"
    ]
}


def _extract_json_payload(raw_text):
    if not raw_text:
        return {}

    text = raw_text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    code_block_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return {}


def _model_json(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    raw_text = response.text or ""
    payload = _extract_json_payload(raw_text)
    return payload, raw_text


def trigger_github_workflow():
    if not all([GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, GITHUB_WORKFLOW_FILE]):
        return False, "GitHub workflow config missing."

    url = (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/"
        f"{GITHUB_WORKFLOW_FILE}/dispatches"
    )

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "ref": "master"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 204:
            return True, "Fresh news refresh triggered successfully."

        return False, f"GitHub API error: {response.text}"

    except Exception as e:
        return False, str(e)


def _normalize_string_list(values):
    if not isinstance(values, list):
        return []

    normalized = []
    for value in values:
        if isinstance(value, str) and value.strip():
            normalized.append(value.strip())
    return normalized


def _fallback_lines(raw_text):
    if not raw_text:
        return []

    lines = []
    for line in raw_text.splitlines():
        cleaned = line.strip().strip("-").strip()
        if cleaned:
            lines.append(cleaned)
    return lines


def _build_post_context(selected):
    context = default_post_context()
    context["title"] = selected.get("title", "")
    context["summary"] = selected.get("summary", "")
    context["link"] = selected.get("link", "")
    context["style_examples"] = STYLE_EXAMPLES[:]
    return context


def _extract_core_angle(context):
    prompt = f"""
You are identifying the SINGLE strongest business narrative from a news article.

Title:
{context['title']}

Summary:
{context['summary']}

Choose only ONE dominant angle from:
- startup growth
- business model shift
- market trend
- product strategy
- AI infrastructure
- founder lesson
- competition
- monetization

Rules:
- pick only one angle
- avoid generic summaries
- explain why this angle matters in one sharp sentence

Return JSON:
{{
  \"angle\": \"\",
  \"why_this_angle_matters\": \"\"
}}
"""

    payload, raw_text = _model_json(prompt)

    angle = payload.get("angle", "")
    why = payload.get("why_this_angle_matters", "")

    if not angle:
        angle = "market trend"

    if not why:
        why = "This story signals a broader business shift most people are missing."

    return {
        "angle": angle,
        "why_this_angle_matters": why
    }


def _generate_insights(context):
    prompt = f"""
Article:
{context['title']}

Summary:
{context['summary']}

Core angle:
{context.get('angle', '')}

Why it matters:
{context.get('why_this_angle_matters', '')}

Generate exactly 5 punchy insights.

Rules:
- each insight under 20 words
- sound like sharp business observations
- avoid repeating article facts
- avoid corporate jargon
- focus on implications

Return JSON format:
{{
  \"insights\": []
}}
"""

    payload, raw_text = _model_json(prompt)
    insights = _normalize_string_list(payload.get("insights"))

    if not insights:
        insights = _fallback_lines(raw_text)[:5]

    return insights


def _generate_hooks(context):
    prompt = f"""
Based on these insights:
{json.dumps(context['insights'], ensure_ascii=True)}

Generate exactly 5 hooks:
1 shocking data hook
1 contrarian hook
1 investor hook
1 founder hook
1 prediction hook

Rules:
- max 12 words
- no clickbait
- no emojis
- no hashtags
- no generic startup fluff

Return JSON:
{{
  \"hooks\": []
}}
"""

    payload, raw_text = _model_json(prompt)
    hooks = _normalize_string_list(payload.get("hooks"))

    if not hooks:
        hooks = _fallback_lines(raw_text)[:5]

    return hooks


def _generate_final_tweets(context, style_context):
    prompt = f"""
You are writing tweets for ambitious startup/product/business audiences.

Article:
{context['title']}

Summary:
{context['summary']}

Core angle:
{context.get('angle', '')}

Insights:
{json.dumps(context['insights'], ensure_ascii=True)}

Hooks:
{json.dumps(context['hooks'], ensure_ascii=True)}

Writing style:
{json.dumps(style_context, ensure_ascii=True)}

Generate exactly 4 tweets:
1 contrarian take
1 investor take
1 founder lesson
1 prediction take

Rules:
- max 280 chars
- strong first line
- no headline summary
- no repeating article title wording
- no generic AI phrases
- no emojis
- no hashtags
- sound native to X

Return JSON:
{{
  \"final_tweets\": []
}}
"""

    payload, raw_text = _model_json(prompt)

    tweets = _normalize_string_list(
        payload.get("final_tweets")
    )

    if not tweets:
        tweets = _fallback_lines(raw_text)[:4]

    if not tweets:
        tweets = [
            "Couldn't generate clean drafts for this article. Try REGEN or select another story."
        ]

    return tweets


def _run_generation_pipeline(selected):
    context = _build_post_context(selected)
    angle_data = _extract_core_angle(context)
    context.update(angle_data)
    save_post_context(context)

    context["insights"] = _generate_insights(context)
    save_post_context(context)

    context["hooks"] = _generate_hooks(context)
    save_post_context(context)

    context["style_context"] = STYLE_CONTEXT
    save_post_context(context)

    context["final_tweets"] = _generate_final_tweets(context, STYLE_CONTEXT)
    save_post_context(context)

    return context


def _format_drafts_message(context):
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


def _handle_approval_command(user_reply):
    match = re.match(r"^\s*approve\s+(\d+)\s*$", user_reply, flags=re.IGNORECASE)
    if not match:
        return False

    approved_index = int(match.group(1))
    context = load_post_context()
    tweets = context.get("final_tweets", [])

    if approved_index < 1 or approved_index > len(tweets):
        send_message("Invalid approval number. Reply with APPROVE <number> from the latest drafts.")
        return True

    approved_tweet = tweets[approved_index - 1]
    context["approved_tweet"] = approved_tweet
    save_post_context(context)

    send_message(
        "✅ Draft approved.\n\n"
        f"{approved_tweet}"
    )
    print(f"Tweet draft approved: index={approved_index}")
    return True

def _handle_regen_command(user_reply):
    if user_reply.strip().lower() not in ["regen", "/regen"]:
        return False

    context = load_post_context()

    if not context.get("title"):
        send_message("No active article context found. Select a story first.")
        return True

    context["final_tweets"] = _generate_final_tweets(
        context,
        context.get("style_context", STYLE_CONTEXT)
    )
    save_post_context(context)

    send_message("♻️ Regenerated drafts:\n\n" + _format_drafts_message(context))
    return True

def _handle_refresh_command(user_reply):
    if user_reply.strip().lower() != "/refresh":
        return False

    send_message("🔄 Fetching fresh news... This may take 2–3 minutes.")

    success, message = trigger_github_workflow()

    if success:
        print("GitHub workflow triggered successfully")
    else:
        send_message(f"Refresh failed: {message}")
        print(message)

    return True


def handle_reply(user_reply):
    print(f"Received Telegram reply: {user_reply}")

    if not user_reply:
        print("No reply found")
        return

    if _handle_approval_command(user_reply):
        return

    if _handle_regen_command(user_reply):
        return

    if _handle_refresh_command(user_reply):
        return

    if not user_reply.isdigit():
        print("Invalid reply")
        send_message("Reply with a story number, or APPROVE <number> after drafts are generated.")
        return

    choice = int(user_reply)
    articles = load_articles()

    if choice < 1 or choice > len(articles):
        print("Choice out of range")
        send_message("Selected story number is out of range. Please choose a valid number.")
        return

    selected = articles[choice - 1]
    context = _run_generation_pipeline(selected)
    send_message(_format_drafts_message(context))
    print("Drafts sent!")

@app.route('/update-articles', methods=['POST'])
def update_articles():
    data = request.json
    print("Received ranked articles update from main.py")

    save_articles(data or [])

    return {"status": "articles updated successfully"}, 200

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    data = request.json
    print("Webhook hit from Telegram")
    print(data)

    if not data or "message" not in data:
        return {"status": "ignored"}, 200

    user_reply = data["message"].get("text", "")

    handle_reply(user_reply)

    return {"status": "success"}, 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    print(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
