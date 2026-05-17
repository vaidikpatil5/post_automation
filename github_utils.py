import requests
from config import get_env


GITHUB_TOKEN = get_env("GITHUB_TOKEN")
GITHUB_OWNER = get_env("GITHUB_OWNER")
GITHUB_REPO = get_env("GITHUB_REPO")
GITHUB_WORKFLOW_FILE = get_env("GITHUB_WORKFLOW_FILE")


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
        "Accept": "application/vnd.github+json",
    }

    payload = {"ref": "master"}

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 204:
            return True, "Fresh news refresh triggered successfully."

        return False, f"GitHub API error: {response.text}"
    except Exception as e:
        return False, str(e)
