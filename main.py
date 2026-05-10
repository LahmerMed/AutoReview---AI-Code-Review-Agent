# main.py

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from tools.github_fetcher import github_fetcher
from tools.security_checker import security_checker, format_security_report
from tools.context_analyzer import context_analyzer, format_context_report
from tools.style_reviewer import style_reviewer, format_style_report
from rag.best_practices import query_best_practices, format_rag_results

load_dotenv()

# ─────────────────────────────────────────
# 1. LLM — Groq
# ─────────────────────────────────────────
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.2
)

# ─────────────────────────────────────────
# 2. Tools de l'agent
# ─────────────────────────────────────────
@tool
def fetch_pull_request(url: str) -> str:
    """
    Fetches the content of a GitHub Pull Request given its URL.
    Returns the PR title, author, description and all changed files with their diffs.
    Use this tool first whenever the user provides a GitHub PR URL.
    """
    result = github_fetcher(url)
    if "error" in result:
        return f"Erreur : {result['error']}"

    pr = result["pr_info"]
    output = f"""
PR : {pr['title']}
Auteur : {pr['author']}
Branche : {pr['head_branch']} → {pr['base_branch']}
Description : {pr['description'] or 'Aucune description'}

Fichiers modifiés ({len(result['files'])}) :
"""
    total_chars = len(output)
    MAX_CHARS = 6000

    for f in result["files"]:
        file_header = f"\n--- {f['filename']} [{f['status']}] +{f['additions']} -{f['deletions']}\n"
        diff = ""
        if f["diff"]:
            diff_lines = f["diff"].splitlines()[:80]
            diff = "\n".join(diff_lines) + "\n"

        chunk = file_header + diff
        if total_chars + len(chunk) > MAX_CHARS:
            output += f"\n--- {f['filename']} [tronqué — trop grand]\n"
            break

        output += chunk
        total_chars += len(chunk)

    return output


@tool
def check_security(url: str) -> str:
    """
    Analyzes the security of a GitHub Pull Request.
    Detects exposed secrets, SQL injections, shell injections,
    disabled SSL, debug mode and other security issues.
    Use this after fetching the PR to detect security vulnerabilities.
    """
    result = github_fetcher(url)
    if "error" in result:
        return f"Erreur : {result['error']}"

    report = security_checker(result["files"])
    return format_security_report(report)


@tool
def analyze_repo_context(url: str) -> str:
    """
    Analyzes the global context of the GitHub repository of a PR.
    Returns the repo description, languages used, file structure and README.
    Use this to understand what the project is about before reviewing the code.
    """
    try:
        parts = url.strip().rstrip("/").replace("https://github.com/", "").split("/")
        owner = parts[0]
        repo = parts[1]
        context = context_analyzer(owner, repo)
        return format_context_report(context)
    except Exception as e:
        return f"Erreur : {str(e)}"


@tool
def review_code_style(url: str) -> str:
    """
    Reviews the code style and quality of a GitHub Pull Request.
    Detects long lines, deep nesting, debug prints, generic exceptions,
    missing docstrings and other style issues.
    Use this to evaluate code quality after fetching the PR.
    """
    result = github_fetcher(url)
    if "error" in result:
        return f"Erreur : {result['error']}"

    report = style_reviewer(result["files"])
    return format_style_report(report)


@tool
def search_best_practices(query: str) -> str:
    """
    Searches the knowledge base for relevant coding best practices.
    Use this to find best practices related to a specific issue found in the PR.
    Example queries: 'SQL injection', 'password storage', 'function too long'
    """
    practices = query_best_practices(query, n_results=3)
    return format_rag_results(practices)

def run_agent_stream(user_input: str, session_id: str = "default"):
    """
    Version streaming — yield chunk par chunk
    """
    config = {"configurable": {"thread_id": session_id}}

    full_response = ""

    for chunk in agent.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="values"
    ):
        messages = chunk.get("messages", [])
        if messages:
            last = messages[-1]
            if (
                hasattr(last, "content")
                and last.content
                and not getattr(last, "tool_calls", None)
            ):
                if last.content != full_response:
                    new_text = last.content[len(full_response):]
                    full_response = last.content
                    yield new_text


# ─────────────────────────────────────────
# 3. Prompt système
# ─────────────────────────────────────────
SYSTEM_PROMPT = """Tu es AutoReview, un agent expert en code review.

Ton rôle est d'analyser des Pull Requests GitHub et de produire un rapport structuré.

Quand tu reçois une URL de PR, tu dois TOUJOURS suivre ces étapes dans l'ordre :
1. analyze_repo_context  → comprendre le projet
2. fetch_pull_request    → récupérer les fichiers modifiés
3. check_security        → détecter les failles de sécurité
4. review_code_style     → évaluer la qualité du code
5. search_best_practices → chercher les bonnes pratiques pertinentes
6. Synthétiser et produire le rapport final

Format de ton rapport final :
## Résumé
## Contexte du projet
## Problèmes de sécurité
## Qualité du code
## Bonnes pratiques recommandées
## Suggestions d'amélioration
## Note globale /10
"""

# ─────────────────────────────────────────
# 4. Agent LangGraph avec mémoire
# ─────────────────────────────────────────
tools = [
    fetch_pull_request,
    check_security,
    analyze_repo_context,
    review_code_style,
    search_best_practices
]
memory = MemorySaver()

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
    checkpointer=memory
)

# ─────────────────────────────────────────
# 5. Fonction principale
# ─────────────────────────────────────────
def run_agent(user_input: str, session_id: str = "default") -> str:
    config = {"configurable": {"thread_id": session_id}}
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config
    )
    return result["messages"][-1].content


if __name__ == "__main__":
    print("=== AutoReview Agent ===\n")
    url = input("Colle une URL de PR GitHub : ")
    result = run_agent(f"Analyse cette Pull Request : {url}")
    print("\n" + result)