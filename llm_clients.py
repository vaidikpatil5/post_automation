import json
import re
import requests
from google import genai
from config import get_env


GEMINI_API_KEY = get_env("GEMINI_API_KEY")
GROQ_API_KEY = get_env("GROQ_API_KEY")
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY. Set it in .env.")

_client = genai.Client(api_key=GEMINI_API_KEY)


def _try_json_load(candidate):
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _extract_balanced_json_objects(text):
    objects = []
    stack = []
    in_string = False
    escaped = False
    start_idx = None

    for idx, ch in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch == "{":
            if not stack:
                start_idx = idx
            stack.append(ch)
            continue

        if ch == "}" and stack:
            stack.pop()
            if not stack and start_idx is not None:
                objects.append(text[start_idx : idx + 1])
                start_idx = None

    return objects


def extract_json_payload(raw_text):
    if not raw_text:
        return {}

    text = raw_text.strip()

    direct = _try_json_load(text)
    if isinstance(direct, dict):
        return direct

    code_blocks = re.findall(
        r"```(?:json)?\s*([\s\S]*?)\s*```",
        text,
        flags=re.IGNORECASE,
    )
    for block in code_blocks:
        parsed = _try_json_load(block.strip())
        if isinstance(parsed, dict):
            return parsed

        for candidate in _extract_balanced_json_objects(block):
            parsed = _try_json_load(candidate)
            if isinstance(parsed, dict):
                return parsed

    for candidate in _extract_balanced_json_objects(text):
        parsed = _try_json_load(candidate)
        if isinstance(parsed, dict):
            return parsed

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = _try_json_load(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    return {}


def model_json(prompt, model=DEFAULT_GEMINI_MODEL):
    response = _client.models.generate_content(
        model=model,
        contents=prompt,
    )

    raw_text = response.text or ""
    payload = extract_json_payload(raw_text)
    return payload, raw_text


def groq_json(prompt, model=DEFAULT_GROQ_MODEL):
    if not GROQ_API_KEY:
        print("Missing GROQ_API_KEY")
        return {}, ""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.9,
            },
            timeout=30,
        )

        if response.status_code != 200:
            print(f"Groq error: {response.text}")
            return {}, ""

        raw_text = response.json()["choices"][0]["message"]["content"]
        payload = extract_json_payload(raw_text)
        return payload, raw_text
    except Exception as e:
        print(f"Groq request error: {e}")
        return {}, ""


def normalize_string_list(values):
    if not isinstance(values, list):
        return []

    normalized = []
    for value in values:
        if isinstance(value, str) and value.strip():
            normalized.append(value.strip())
            continue

        if isinstance(value, dict):
            for key in ("tweet", "text", "content", "draft", "value", "body"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    normalized.append(candidate.strip())
                    break
    return normalized


def fallback_lines(raw_text):
    if not raw_text:
        return []

    lines = []
    for line in raw_text.splitlines():
        cleaned = line.strip().strip("-").strip()
        if cleaned in {"```", "```json", "{", "}", "[", "]", '"tweets": ['}:
            continue
        if cleaned:
            lines.append(cleaned)
    return lines
