# tools/security_checker.py

import re

# ─────────────────────────────────────────
# Patterns de détection de sécurité
# ─────────────────────────────────────────

SECURITY_PATTERNS = [
    # Secrets & credentials
    {
        "id": "SEC001",
        "name": "Clé API / Token exposé",
        "pattern": r'(?i)(api_key|apikey|api_token|access_token|secret_key|private_key)\s*=\s*["\'][^"\']{8,}["\']',
        "severity": "CRITIQUE"
    },
    {
        "id": "SEC002",
        "name": "Mot de passe en dur",
        "pattern": r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']',
        "severity": "CRITIQUE"
    },
    {
        "id": "SEC003",
        "name": "Token JWT exposé",
        "pattern": r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
        "severity": "CRITIQUE"
    },
    {
        "id": "SEC004",
        "name": "Clé AWS exposée",
        "pattern": r'AKIA[0-9A-Z]{16}',
        "severity": "CRITIQUE"
    },

    # Injections
    {
        "id": "SEC005",
        "name": "Injection SQL possible",
        "pattern": r'(?i)(execute|query|cursor\.execute)\s*\(\s*["\'].*(%s|%d|\+|format|f")',
        "severity": "ÉLEVÉ"
    },
    {
        "id": "SEC006",
        "name": "Injection de commande shell",
        "pattern": r'(?i)(os\.system|subprocess\.call|subprocess\.run|eval|exec)\s*\(',
        "severity": "ÉLEVÉ"
    },
    {
        "id": "SEC007",
        "name": "XSS possible",
        "pattern": r'(?i)(innerHTML|document\.write|\.html\()\s*[^;]*\+',
        "severity": "ÉLEVÉ"
    },

    # Mauvaises pratiques
    {
        "id": "SEC008",
        "name": "Debug mode activé",
        "pattern": r'(?i)(DEBUG\s*=\s*True|debug\s*=\s*true)',
        "severity": "MOYEN"
    },
    {
        "id": "SEC009",
        "name": "Vérification SSL désactivée",
        "pattern": r'(?i)verify\s*=\s*False',
        "severity": "MOYEN"
    },
    {
        "id": "SEC010",
        "name": "TODO / FIXME sécurité",
        "pattern": r'(?i)#.*(todo|fixme|hack|security|vulnerable)',
        "severity": "FAIBLE"
    },
]


# ─────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────

def security_checker(files: list) -> dict:
    """
    Analyse une liste de fichiers modifiés (format github_fetcher)
    et détecte les problèmes de sécurité dans les diffs.
    
    Args:
        files: liste de dicts avec 'filename' et 'diff'
    
    Returns:
        dict avec la liste des problèmes détectés par fichier
    """
    report = {
        "total_issues": 0,
        "critique": 0,
        "eleve": 0,
        "moyen": 0,
        "faible": 0,
        "files": []
    }

    for f in files:
        filename = f.get("filename", "unknown")
        diff = f.get("diff", "")

        if not diff:
            continue

        file_issues = []

        # On analyse seulement les lignes ajoutées (commencent par +)
        added_lines = [
            (i + 1, line[1:])  # (numéro ligne, contenu sans le +)
            for i, line in enumerate(diff.splitlines())
            if line.startswith("+") and not line.startswith("+++")
        ]

        for line_num, line_content in added_lines:
            for rule in SECURITY_PATTERNS:
                if re.search(rule["pattern"], line_content):
                    file_issues.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "line": line_num,
                        "content": line_content.strip()[:120]  # max 120 chars
                    })

                    # Compteurs globaux
                    report["total_issues"] += 1
                    sev = rule["severity"]
                    if sev == "CRITIQUE":
                        report["critique"] += 1
                    elif sev == "ÉLEVÉ":
                        report["eleve"] += 1
                    elif sev == "MOYEN":
                        report["moyen"] += 1
                    else:
                        report["faible"] += 1

        if file_issues:
            report["files"].append({
                "filename": filename,
                "issues": file_issues
            })

    return report


def format_security_report(report: dict) -> str:
    """
    Formate le rapport de sécurité en texte lisible pour le LLM.
    """
    if report["total_issues"] == 0:
        return "✅ Aucun problème de sécurité détecté."

    output = f"""RAPPORT DE SÉCURITÉ
Total : {report['total_issues']} problème(s)
- CRITIQUE : {report['critique']}
- ÉLEVÉ    : {report['eleve']}
- MOYEN    : {report['moyen']}
- FAIBLE   : {report['faible']}

Détails :
"""
    for f in report["files"]:
        output += f"\n📄 {f['filename']}\n"
        for issue in f["issues"]:
            output += f"  [{issue['severity']}] {issue['rule_id']} — {issue['name']}\n"
            output += f"  Ligne {issue['line']} : {issue['content']}\n"

    return output