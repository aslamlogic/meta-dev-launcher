import os
import requests


def main(repo_name: str):
    """
    Trigger GitHub Actions workflow for a given repository
    """

    try:
        # --- CONFIG ---
        owner = "aslamlogic"
        workflow_file = "run-meta.yml"   # must match your repo
        branch = "main"

        # --- TOKEN (CRITICAL FIX) ---
        token = os.getenv("META_GITHUB_TOKEN")

        if not token:
            return {
                "status": "error",
                "error": "META_GITHUB_TOKEN not found in environment"
            }

        # --- API URL ---
        url = f"https://api.github.com/repos/{owner}/{repo_name}/actions/workflows/{workflow_file}/dispatches"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        payload = {
            "ref": branch
        }

        # --- REQUEST ---
        response = requests.post(url, json=payload, headers=headers)

        return {
            "status": "executed",
            "repo": repo_name,
            "result": {
                "message": f"Workflow triggered for {repo_name}",
                "github": {
                    "status_code": response.status_code,
                    "response": response.text
                }
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
