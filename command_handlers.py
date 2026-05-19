import re
from telegram_bot import send_message
from storage import load_post_context, save_post_context, save_approved_post
from tweet_pipeline import generate_final_tweets_v2, format_drafts_message, get_current_posts
from github_utils import trigger_github_workflow


def handle_approval_command(user_reply):
    match = re.match(r"^\s*approve\s+(\d+)\s*$", user_reply, flags=re.IGNORECASE)
    if not match:
        return False

    approved_index = int(match.group(1))
    context = load_post_context()
    tweets = get_current_posts(context)

    if approved_index < 1 or approved_index > len(tweets):
        send_message("Invalid approval number. Reply with APPROVE <number> from the latest drafts.")
        return True

    approved_tweet = tweets[approved_index - 1]
    context["approved_tweet"] = approved_tweet
    context["approved_index"] = approved_index
    save_post_context(context)
    save_approved_post(
        {
            "title": context.get("title", ""),
            "summary": context.get("summary", ""),
            "link": context.get("link", ""),
            "approved_tweet": approved_tweet,
            "approved_index": approved_index,
        }
    )

    send_message(
        "✅ Draft approved.\n\n"
        f"{approved_tweet}"
    )
    print(f"Tweet draft approved: index={approved_index}")
    return True


def handle_regen_command(user_reply):
    if user_reply.strip().lower() not in ["regen", "/regen"]:
        return False

    context = load_post_context()

    if not context.get("title"):
        send_message("No active article context found. Select a story first.")
        return True

    context.setdefault("rejected_patterns", [])
    context.setdefault("tweet_history", [])

    context["rejected_patterns"].append(
        "previous drafts were not engaging enough"
    )

    new_tweets = generate_final_tweets_v2(context)

    context["final_posts"] = new_tweets
    context["final_tweets"] = new_tweets
    context["tweet_history"].append(new_tweets)

    save_post_context(context)

    send_message("♻️ Regenerated drafts:\n\n" + format_drafts_message(context))
    return True


def handle_refresh_command(user_reply):
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
