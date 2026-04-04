import os
import requests

GITHUB_API = "https://api.github.com"
OWNER = "aslamlogic"


def trigger_workflow(repo: str):
    token = os.getenv("GITHUB_TOKEN_CUSTOM")

    url = f"{GITHUB_API}/repos/{OWNER}/{repo}/actions/workflows/run-meta.yml/dispatches"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "ref": "main"
    }

    response = requests.post(url, headers=headers, json=data)

    return {
        "status_code": response.status_code,
        "response": response.text
    }


def main(repo: str):
    result = trigger_workflow(repo)

    return {
        "message": f"Workflow triggered for {repo}",
        "github": result
    }
