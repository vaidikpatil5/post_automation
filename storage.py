import json
import os

FILE_NAME = "ranked_articles.json"
POST_CONTEXT_FILE = "post_context.json"
APPROVED_POSTS_FILE = "approved_posts.json"


def default_post_context():
    return {
        "title": "",
        "summary": "",
        "link": "",
        "full_article": "",
        "full_article_fetch_failed": False,
        "narrative_match": {},
        "tension_output": {},
        "implication_output": {},
        "expression_output": {},
        "signal_analysis": {},
        "thesis_output": {},
        "narrative_output": {},
        "final_posts": [],
        "analysis_output": {},
        "insights": [],
        "hooks": [],
        "style_examples": [],
        "style_context": {},
        "final_tweets": [],
        "tweet_history": [],
        "rejected_patterns": [],
        "approved_tweet": "",
        "approved_index": None,
    }


def save_articles(articles):
    with open(FILE_NAME, "w") as f:
        json.dump(articles, f)


def load_articles():
    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_post_context(context):
    with open(POST_CONTEXT_FILE, "w") as f:
        json.dump(context, f, indent=2)


def load_post_context():
    if not os.path.exists(POST_CONTEXT_FILE):
        return default_post_context()

    with open(POST_CONTEXT_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return default_post_context()

    merged = default_post_context()
    merged.update(data if isinstance(data, dict) else {})
    return merged


def save_approved_post(post_data):
    posts = load_approved_posts()
    posts.append(post_data)

    with open(APPROVED_POSTS_FILE, "w") as f:
        json.dump(posts, f, indent=2)


def load_approved_posts():
    if not os.path.exists(APPROVED_POSTS_FILE):
        return []

    with open(APPROVED_POSTS_FILE, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
