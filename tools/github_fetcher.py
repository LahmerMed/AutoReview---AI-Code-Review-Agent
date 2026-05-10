# tools/github_fetcher.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def github_fetcher(url: str) -> dict:
    """
    Fetches the list of changed files and their diffs from a GitHub Pull Request URL.
    Example URL: https://github.com/owner/repo/pull/42
    """
    try:
        # Nettoyage de l'URL
        url = url.strip().rstrip("/")
        parts = url.replace("https://github.com/", "").split("/")

        if len(parts) < 4 or parts[2] != "pull":
            return {"error": "URL invalide. Format attendu : https://github.com/owner/repo/pull/NUMBER"}

        owner = parts[0]
        repo = parts[1]
        pr_number = parts[3]

        # Infos générales de la PR
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        pr_response = requests.get(pr_url, headers=headers)

        if pr_response.status_code != 200:
            return {"error": f"PR introuvable : {pr_response.json().get('message', 'Erreur inconnue')}"}

        pr_data = pr_response.json()
        pr_info = {
            "title": pr_data.get("title", ""),
            "description": pr_data.get("body", ""),
            "author": pr_data.get("user", {}).get("login", ""),
            "base_branch": pr_data.get("base", {}).get("ref", ""),
            "head_branch": pr_data.get("head", {}).get("ref", ""),
            "state": pr_data.get("state", ""),
        }

        # Fichiers modifiés + diffs
        files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
        files_response = requests.get(files_url, headers=headers)

        if files_response.status_code != 200:
            return {"error": files_response.json()}

        files = files_response.json()

        result = {
            "pr_info": pr_info,
            "files": []
        }

        for f in files:
            result["files"].append({
                "filename": f.get("filename", "unknown"),
                "status": f.get("status", ""),        # added / modified / removed
                "additions": f.get("additions", 0),
                "deletions": f.get("deletions", 0),
                "diff": f.get("patch", "")            # le vrai diff ligne par ligne
            })

        return result

    except Exception as e:
        return {"error": str(e)}    