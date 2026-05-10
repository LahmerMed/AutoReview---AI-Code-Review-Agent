# tools/context_analyzer.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def context_analyzer(owner: str, repo: str) -> dict:
    """
    Analyse le contexte global d'un repo GitHub.
    Récupère : langages, structure des fichiers, README, description.
    
    Args:
        owner: propriétaire du repo
        repo: nom du repo
    
    Returns:
        dict avec les infos contextuelles du projet
    """
    try:
        context = {}

        # 1. Infos générales du repo
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        repo_resp = requests.get(repo_url, headers=headers)

        if repo_resp.status_code != 200:
            return {"error": f"Repo introuvable : {repo_resp.json().get('message')}"}

        repo_data = repo_resp.json()
        context["repo"] = {
            "name": repo_data.get("name"),
            "description": repo_data.get("description", ""),
            "language": repo_data.get("language", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
        }

        # 2. Langages utilisés
        langs_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
        langs_resp = requests.get(langs_url, headers=headers)
        if langs_resp.status_code == 200:
            context["languages"] = langs_resp.json()

        # 3. Structure racine du repo (fichiers/dossiers)
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD"
        tree_resp = requests.get(tree_url, headers=headers)
        if tree_resp.status_code == 200:
            tree = tree_resp.json().get("tree", [])
            context["structure"] = [
                {"name": item["path"], "type": item["type"]}
                for item in tree[:30]  # max 30 éléments
            ]

        # 4. README (100 premières lignes)
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        readme_resp = requests.get(readme_url, headers=headers)
        if readme_resp.status_code == 200:
            import base64
            readme_data = readme_resp.json()
            content = base64.b64decode(readme_data.get("content", "")).decode("utf-8", errors="ignore")
            lines = content.splitlines()[:100]
            context["readme"] = "\n".join(lines)

        return context

    except Exception as e:
        return {"error": str(e)}


def format_context_report(context: dict) -> str:
    """
    Formate le contexte du repo en texte lisible pour le LLM.
    """
    if "error" in context:
        return f"Erreur : {context['error']}"

    repo = context.get("repo", {})
    langs = context.get("languages", {})
    structure = context.get("structure", [])
    readme = context.get("readme", "")

    output = f"""CONTEXTE DU PROJET
Nom        : {repo.get('name')}
Description: {repo.get('description') or 'Aucune'}
Langage    : {repo.get('language')}
Stars      : {repo.get('stars')} | Forks : {repo.get('forks')}

Langages détectés : {', '.join(langs.keys()) if langs else 'N/A'}

Structure racine :
"""
    for item in structure:
        icon = "📁" if item["type"] == "tree" else "📄"
        output += f"  {icon} {item['name']}\n"

    if readme:
        output += f"\nREADME (extrait) :\n{readme[:500]}...\n"

    return output