# rag/best_practices.py

import chromadb

BEST_PRACTICES = [
    "Ne jamais stocker des mots de passe en clair. Utiliser bcrypt ou argon2 pour le hachage.",
    "Ne jamais exposer des clés API ou tokens dans le code source. Utiliser des variables d'environnement.",
    "Toujours valider et assainir les entrées utilisateur avant de les utiliser dans une requête SQL.",
    "Utiliser des requêtes préparées (prepared statements) pour éviter les injections SQL.",
    "Désactiver le mode DEBUG en production. Ne jamais laisser DEBUG=True en production.",
    "Toujours vérifier les certificats SSL. Ne jamais utiliser verify=False en production.",
    "Utiliser HTTPS pour toutes les communications.",
    "Implémenter une gestion des erreurs qui ne révèle pas les détails internes du système.",
    "Les fonctions doivent faire une seule chose (principe de responsabilité unique - SRP).",
    "Une fonction ne doit pas dépasser 50 lignes. Si c'est le cas, la découper en sous-fonctions.",
    "Les noms de variables et fonctions doivent être descriptifs et explicites.",
    "Éviter l'imbrication profonde (plus de 3-4 niveaux). Utiliser des early returns.",
    "Supprimer le code mort et les commentaires inutiles. Utiliser Git pour l'historique.",
    "Remplacer les print() de debug par un système de logging.",
    "Toujours écrire des docstrings pour les fonctions et classes publiques.",
    "Utiliser des types hints en Python pour améliorer la lisibilité.",
    "Séparer la logique métier de la logique de présentation.",
    "Utiliser des variables d'environnement pour toute configuration.",
    "Écrire des tests unitaires pour chaque fonction critique.",
    "Appliquer le principe DRY — éviter la duplication de code.",
    "Les dépendances doivent être déclarées dans requirements.txt.",
    "Éviter les requêtes N+1 en base de données.",
    "Utiliser la pagination pour les listes longues.",
    "Une PR ne doit pas dépasser 400 lignes de changement.",
    "Ne jamais committer directement sur la branche main ou master.",
]


def init_rag() -> chromadb.Collection:
    """Initialise ChromaDB avec l'embedding par défaut (pas de sentence-transformers)."""
    client = chromadb.PersistentClient(path="./rag/chroma_db")

    # Utilise l'embedding par défaut de ChromaDB (pas de transformers)
    collection = client.get_or_create_collection(name="best_practices")

    if collection.count() == 0:
        print("📚 Initialisation de la base RAG...")
        collection.add(
            documents=BEST_PRACTICES,
            ids=[f"bp_{i}" for i in range(len(BEST_PRACTICES))]
        )
        print(f"✅ {len(BEST_PRACTICES)} bonnes pratiques indexées.")

    return collection


def query_best_practices(query: str, n_results: int = 3) -> list:
    """Recherche les bonnes pratiques les plus pertinentes."""
    collection = init_rag()
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0] if results["documents"] else []


def format_rag_results(practices: list) -> str:
    if not practices:
        return "Aucune bonne pratique trouvée."
    output = "BONNES PRATIQUES PERTINENTES :\n"
    for i, practice in enumerate(practices, 1):
        output += f"{i}. {practice}\n"
    return output