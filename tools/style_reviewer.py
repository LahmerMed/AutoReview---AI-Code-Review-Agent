# tools/style_reviewer.py

import re

# ─────────────────────────────────────────
# Règles de style et qualité de code
# ─────────────────────────────────────────

STYLE_RULES = [
    # Nommage
    {
        "id": "STY001",
        "name": "Variable à nom trop court",
        "pattern": r'^\s*(var|let|const)?\s*([a-z]{1,2})\s*=\s*[^=]',
        "severity": "FAIBLE",
        "suggestion": "Utilise un nom descriptif au lieu d'une variable d'une lettre"
    },
    {
        "id": "STY002",
        "name": "Fonction sans type de retour (Python)",
        "pattern": r'^def\s+\w+\([^)]*\)\s*:(?!\s*->)',
        "severity": "FAIBLE",
        "suggestion": "Ajoute un type hint de retour -> type"
    },
    {
        "id": "STY003",
        "name": "Classe sans docstring",
        "pattern": r'^class\s+\w+.*:\s*$',
        "severity": "FAIBLE",
        "suggestion": "Ajoute une docstring pour décrire la classe"
    },

    # Complexité
    {
        "id": "STY004",
        "name": "Fonction trop longue (>50 lignes)",
        "pattern": None,  # traité séparément
        "severity": "MOYEN",
        "suggestion": "Découpe la fonction en sous-fonctions"
    },
    {
        "id": "STY005",
        "name": "Imbrication trop profonde (>4 niveaux)",
        "pattern": r'^\s{16,}',  # 16 espaces = 4 niveaux
        "severity": "MOYEN",
        "suggestion": "Réduis l'imbrication avec des early returns"
    },
    {
        "id": "STY006",
        "name": "Ligne trop longue (>120 caractères)",
        "pattern": None,  # traité séparément
        "severity": "FAIBLE",
        "suggestion": "Coupe la ligne pour améliorer la lisibilité"
    },

    # Mauvaises pratiques
    {
        "id": "STY007",
        "name": "Print de debug laissé",
        "pattern": r'^\s*print\s*\(',
        "severity": "FAIBLE",
        "suggestion": "Remplace print() par un logger"
    },
    {
        "id": "STY008",
        "name": "Exception trop générique",
        "pattern": r'except\s*(\bException\b|\b\:\b|\s*:)',
        "severity": "MOYEN",
        "suggestion": "Capture une exception spécifique au lieu de Exception"
    },
    {
        "id": "STY009",
        "name": "Code commenté (dead code)",
        "pattern": r'^\s*#\s*(var|let|const|def|class|return|if|for|while)\s+',
        "severity": "FAIBLE",
        "suggestion": "Supprime le code commenté, utilise Git pour l'historique"
    },
    {
        "id": "STY010",
        "name": "Import global non utilisé possible",
        "pattern": r'^import\s+\w+\s*$',
        "severity": "FAIBLE",
        "suggestion": "Vérifie que cet import est bien utilisé"
    },
]


# ─────────────────────────────────────────
# Fonction principale
# ─────────────────────────────────────────

def style_reviewer(files: list) -> dict:
    """
    Analyse la qualité et le style du code dans les fichiers modifiés.

    Args:
        files: liste de dicts avec 'filename' et 'diff'

    Returns:
        dict avec les problèmes de style détectés
    """
    report = {
        "total_issues": 0,
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

        # Lignes ajoutées uniquement
        added_lines = [
            (i + 1, line[1:])
            for i, line in enumerate(diff.splitlines())
            if line.startswith("+") and not line.startswith("+++")
        ]

        for line_num, line_content in added_lines:
            # Ligne trop longue
            if len(line_content) > 120:
                file_issues.append({
                    "rule_id": "STY006",
                    "name": "Ligne trop longue (>120 caractères)",
                    "severity": "FAIBLE",
                    "suggestion": "Coupe la ligne pour améliorer la lisibilité",
                    "line": line_num,
                    "content": line_content.strip()[:120]
                })
                report["total_issues"] += 1
                report["faible"] += 1
                continue

            # Vérifie les patterns
            for rule in STYLE_RULES:
                if rule["pattern"] is None:
                    continue
                if re.search(rule["pattern"], line_content):
                    file_issues.append({
                        "rule_id": rule["id"],
                        "name": rule["name"],
                        "severity": rule["severity"],
                        "suggestion": rule["suggestion"],
                        "line": line_num,
                        "content": line_content.strip()[:120]
                    })
                    report["total_issues"] += 1
                    if rule["severity"] == "MOYEN":
                        report["moyen"] += 1
                    else:
                        report["faible"] += 1

        if file_issues:
            report["files"].append({
                "filename": filename,
                "issues": file_issues
            })

    return report


def format_style_report(report: dict) -> str:
    """
    Formate le rapport de style en texte lisible pour le LLM.
    """
    if report["total_issues"] == 0:
        return "✅ Aucun problème de style détecté."

    output = f"""RAPPORT DE QUALITÉ DE CODE
Total : {report['total_issues']} problème(s)
- MOYEN  : {report['moyen']}
- FAIBLE : {report['faible']}

Détails :
"""
    for f in report["files"]:
        output += f"\n📄 {f['filename']}\n"
        for issue in f["issues"]:
            output += f"  [{issue['severity']}] {issue['rule_id']} — {issue['name']}\n"
            output += f"  Ligne {issue['line']} : {issue['content']}\n"
            output += f"  💡 {issue['suggestion']}\n"

    return output