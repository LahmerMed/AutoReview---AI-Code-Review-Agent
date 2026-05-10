# ui/app.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import gradio as gr
from main import run_agent, run_agent_stream

# ─────────────────────────────────────────
# Fonctions
# ─────────────────────────────────────────
def analyze_pr(url, history, session_id):
    if not url.strip():
        history.append({"role": "assistant", "content": "⚠️ Veuillez entrer une URL de Pull Request GitHub."})
        yield history, ""
        return

    history.append({"role": "user", "content": f"Analyse cette Pull Request : {url.strip()}"})
    history.append({"role": "assistant", "content": "⏳ L'agent analyse la PR, veuillez patienter..."})
    yield history, ""

    try:
        full_text = ""
        started = False

        for chunk in run_agent_stream(
            f"Analyse cette Pull Request : {url.strip()}",
            session_id=session_id
        ):
            if not started:
                # Efface le message "en cours..." dès que le vrai contenu arrive
                history[-1] = {"role": "assistant", "content": ""}
                started = True

            full_text += chunk

            # Mise à jour mot par mot
            history[-1] = {"role": "assistant", "content": full_text}
            yield history, ""

    except Exception as e:
        history[-1] = {"role": "assistant", "content": f"❌ Erreur : {str(e)}"}
        yield history, ""


def chat_followup(message, history, session_id):
    if not message.strip():
        yield history, ""
        return

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": "⏳ Réflexion en cours..."})
    yield history, ""

    try:
        full_text = ""
        started = False

        for chunk in run_agent_stream(message, session_id=session_id):
            if not started:
                history[-1] = {"role": "assistant", "content": ""}
                started = True

            full_text += chunk
            history[-1] = {"role": "assistant", "content": full_text}
            yield history, ""

    except Exception as e:
        history[-1] = {"role": "assistant", "content": f"❌ Erreur : {str(e)}"}
        yield history, ""
def clear_chat():
    initial = [{"role": "assistant", "content":
        "👋 Bonjour ! Je suis **AutoReview**, votre agent de code review.\n\n"
        "Collez une URL de Pull Request GitHub et je vais :\n"
        "1. 🔍 Analyser le contexte du projet\n"
        "2. 📂 Récupérer les fichiers modifiés\n"
        "3. 🔒 Vérifier la sécurité du code\n"
        "4. ✅ Évaluer la qualité et le style\n"
        "5. 📚 Recommander des bonnes pratiques\n"
        "6. 📊 Générer un rapport avec note **/10**"
    }]
    return initial, str(uuid.uuid4())


CSS = """
.header-box {
    background: linear-gradient(135deg, #1E3A5F 0%, #2E75B6 100%);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
    text-align: center;
    color: white;
}
.btn-example {
    border-radius: 6px !important;
    font-size: 12px !important;
    background: #F0F4FA !important;
    border: 1px solid #2E75B6 !important;
    color: #1E3A5F !important;
}
"""

EXAMPLES = [
    "https://github.com/LahmerMed/redboostfinal/pull/1",
    "https://github.com/pallets/flask/pull/5537",
    "https://github.com/django/django/pull/18820",
]

INITIAL_MESSAGES = [{"role": "assistant", "content":
    "👋 Bonjour ! Je suis **AutoReview**, votre agent de code review.\n\n"
    "Collez une URL de Pull Request GitHub et je vais :\n"
    "1. 🔍 Analyser le contexte du projet\n"
    "2. 📂 Récupérer les fichiers modifiés\n"
    "3. 🔒 Vérifier la sécurité du code\n"
    "4. ✅ Évaluer la qualité et le style\n"
    "5. 📚 Recommander des bonnes pratiques\n"
    "6. 📊 Générer un rapport avec note **/10**"
}]

# ─────────────────────────────────────────
# Interface
# ─────────────────────────────────────────

with gr.Blocks(title="AutoReview — Agent IA de Code Review") as demo:

    session_id = gr.State(value=str(uuid.uuid4()))

    # Header
    gr.HTML("""
    <div class="header-box">
        <h1 style="margin:0; font-size:2em; color:white;">🤖 AutoReview</h1>
        <p style="margin:8px 0 0 0; font-size:1.1em; opacity:0.9; color:white;">
            Agent IA de Code Review automatique pour Pull Requests GitHub
        </p>
        <p style="margin:4px 0 0 0; font-size:0.85em; opacity:0.7; color:white;">
            LangGraph • Groq LLaMA 3.3 • ChromaDB RAG • GitHub API
        </p>
    </div>
    """)

    with gr.Row():

        # Colonne gauche
        with gr.Column(scale=3):

            chatbot = gr.Chatbot(
                label="",
                height=500,
                show_label=False,
                value=INITIAL_MESSAGES
            )

            with gr.Row():
                url_input = gr.Textbox(
                    placeholder="https://github.com/owner/repo/pull/42",
                    label="URL de la Pull Request GitHub",
                    lines=1,
                    scale=5
                )
                analyze_btn = gr.Button("🔍 Analyser", variant="primary", scale=1)

            gr.HTML("<div style='text-align:center; color:#888; margin:4px 0; font-size:13px;'>— ou posez une question de suivi —</div>")

            with gr.Row():
                chat_input = gr.Textbox(
                    placeholder="Ex: Explique le problème SEC002 en détail...",
                    label="",
                    lines=1,
                    scale=5,
                    show_label=False
                )
                send_btn = gr.Button("💬 Envoyer", scale=1)

            clear_btn = gr.Button("🗑️ Nouvelle conversation", variant="secondary")

        # Colonne droite
        with gr.Column(scale=1):

            gr.HTML("<h3 style='color:#1E3A5F; margin-bottom:8px;'>⚡ Exemples rapides</h3>")
            for ex in EXAMPLES:
                short = ex.split("github.com/")[1]
                ex_btn = gr.Button(f"📎 {short}", size="sm")
                ex_btn.click(fn=lambda e=ex: e, outputs=url_input)

            gr.HTML("""
            <div style='margin-top:20px;'>
                <h3 style='color:#1E3A5F; margin-bottom:8px;'>🛠️ Tools actifs</h3>
                <div style='background:#F0F4FA; border-radius:8px; padding:12px; font-size:13px;'>
                    <div style='margin:4px 0;'>🔗 <b>github_fetcher</b><br><span style='color:#666; font-size:11px;'>Récupère les diffs</span></div>
                    <hr style='border:none; border-top:1px solid #ddd; margin:6px 0;'>
                    <div style='margin:4px 0;'>🏗️ <b>context_analyzer</b><br><span style='color:#666; font-size:11px;'>Analyse le repo</span></div>
                    <hr style='border:none; border-top:1px solid #ddd; margin:6px 0;'>
                    <div style='margin:4px 0;'>🔒 <b>security_checker</b><br><span style='color:#666; font-size:11px;'>Détecte les failles</span></div>
                    <hr style='border:none; border-top:1px solid #ddd; margin:6px 0;'>
                    <div style='margin:4px 0;'>✅ <b>style_reviewer</b><br><span style='color:#666; font-size:11px;'>Évalue la qualité</span></div>
                    <hr style='border:none; border-top:1px solid #ddd; margin:6px 0;'>
                    <div style='margin:4px 0;'>📚 <b>search_best_practices</b><br><span style='color:#666; font-size:11px;'>Base RAG ChromaDB</span></div>
                </div>
            </div>

            <div style='margin-top:16px;'>
                <h3 style='color:#1E3A5F; margin-bottom:8px;'>📋 Rapport généré</h3>
                <div style='background:#F0F4FA; border-radius:8px; padding:12px; font-size:13px; color:#444; line-height:1.8;'>
                    📌 Résumé<br>
                    🏗️ Contexte du projet<br>
                    🔒 Problèmes de sécurité<br>
                    ✅ Qualité du code<br>
                    📚 Bonnes pratiques<br>
                    💡 Suggestions<br>
                    ⭐ Note globale /10
                </div>
            </div>
            """)

    gr.HTML("""
    <div style='text-align:center; color:#888; font-size:12px; margin-top:8px;'>
        AutoReview — LangGraph + Groq LLaMA 3.3 + ChromaDB RAG + GitHub API | 100% Gratuit
    </div>
    """)

    # Events
    analyze_btn.click(
        fn=analyze_pr,
        inputs=[url_input, chatbot, session_id],
        outputs=[chatbot, url_input]
    )
    url_input.submit(
        fn=analyze_pr,
        inputs=[url_input, chatbot, session_id],
        outputs=[chatbot, url_input]
    )
    send_btn.click(
        fn=chat_followup,
        inputs=[chat_input, chatbot, session_id],
        outputs=[chatbot, chat_input]
    )
    chat_input.submit(
        fn=chat_followup,
        inputs=[chat_input, chatbot, session_id],
        outputs=[chatbot, chat_input]
    )
    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot, session_id]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7865,
        show_error=True
    ) 