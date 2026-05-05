"""
app.py
Gradio UI for the AI Content Creator (CyberContent).
Run with: python app.py
"""

import sys
import os
import io
from pathlib import Path
from contextlib import redirect_stdout

try:
    import gradio as gr
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "No module named 'gradio'. Install the project dependencies with "
        "'python -m pip install -r requirements.txt' in the same Python "
        "environment you use to run src/app.py."
    ) from exc

# Ensure src/ is on the path
sys.path.insert(0, str(Path(__file__).parent))

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TEMPLATE_CHOICES = [
    "blog_post_ciso",
    "blog_post_analyst",
    "linkedin_thought_leadership",
    "content_brief",
    "iterate_and_refine",
    "monitor_trends",
]

TEMPLATE_DESCRIPTIONS = {
    "blog_post_ciso":              "Long-form blog post aimed at CISOs and security leaders",
    "blog_post_analyst":           "Technical deep-dive for security analysts and practitioners",
    "linkedin_thought_leadership": "Short punchy LinkedIn post for thought leadership",
    "content_brief":               "Structured brief to plan content before writing",
    "iterate_and_refine":          "Iteratively improve an existing draft",
    "monitor_trends":              "Trend-monitoring report on a topic",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _read_latest_md(output_dir: str) -> str:
    """Return the content of the most-recently-modified .md file in output_dir."""
    p = Path(output_dir)
    if not p.exists():
        return ""
    files = sorted(p.glob("**/*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return ""
    return files[0].read_text(encoding="utf-8")


def _capture_stdout(fn, *args, **kwargs):
    """Run fn and capture its stdout, returning (result, captured_text)."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


# ── pipeline actions ───────────────────────────────────────────────────────────

# Stage 1: generate draft (always skips internal human_review so WE control it)
def generate_draft(topic, template, word_count, skip_monitor, kb_path, output_dir):
    if not topic.strip():
        # status, logs, draft_md, review_row visible, final_row visible
        return "⚠️ Please enter a topic.", "", "", gr.update(visible=False), gr.update(visible=False)

    try:
        from content_pipeline import ContentPipeline
    except ImportError as e:
        return f"❌ Import error: {e}", "", "", gr.update(visible=False), gr.update(visible=False)

    try:
        pipeline = ContentPipeline(
            knowledge_base_path=kb_path,
            output_dir=output_dir,
            auto_save=True,
        )
        published, logs = _capture_stdout(
            pipeline.run,
            topic=topic,
            template_name=template,
            word_count=int(word_count),
            skip_monitor=skip_monitor,
            human_review=False,   # we handle review in the UI
        )
        md_content = _read_latest_md(output_dir)
        status = f"✅ Draft ready — review below or approve to finish."
        return (
            status,
            logs.strip(),
            md_content,
            gr.update(visible=True),   # show review panel
            gr.update(visible=False),  # hide final panel until decided
        )
    except Exception as e:
        return f"❌ Error: {e}", "", "", gr.update(visible=False), gr.update(visible=False)


# Stage 2a: approve — surface the draft as final
# FIX: return value order matches outputs=[run_status, final_output, review_panel, final_panel]
# and final_panel must receive gr.update(visible=True, value=...) so the Markdown renders.
def approve_draft(draft_md, output_dir):
    return (
        "✅ Content approved and saved.",
        draft_md,                       # → final_output (gr.Markdown)
        gr.update(visible=False),       # hide review panel
        gr.update(visible=True),        # show final panel
    )


# Stage 2b: skip review — same as approve
def skip_review(draft_md, output_dir):
    return (
        "⏭ Review skipped. Draft saved as-is.",
        draft_md,                       # → final_output (gr.Markdown)
        gr.update(visible=False),
        gr.update(visible=True),
    )


# Stage 2c: revise — re-run pipeline with feedback injected into topic
def revise_draft(topic, template, word_count, feedback, draft_md, kb_path, output_dir):
    if not feedback.strip():
        return (
            "⚠️ Please enter feedback before revising.",
            draft_md,
            gr.update(visible=True),
            gr.update(visible=False),
        )

    try:
        from content_pipeline import ContentPipeline
    except ImportError as e:
        return f"❌ Import error: {e}", draft_md, gr.update(visible=True), gr.update(visible=False)

    try:
        pipeline = ContentPipeline(
            knowledge_base_path=kb_path,
            output_dir=output_dir,
            auto_save=True,
        )
        revised_topic = (
            f"{topic}\n\n"
            f"--- REVISION INSTRUCTIONS ---\n"
            f"Previous draft was reviewed. Apply this feedback:\n{feedback}\n"
            f"--- PREVIOUS DRAFT ---\n{draft_md}"
        )
        published, logs = _capture_stdout(
            pipeline.run,
            topic=revised_topic,
            template_name=template,
            word_count=int(word_count),
            skip_monitor=True,   # no need to re-monitor for a revision
            human_review=False,
        )
        md_content = _read_latest_md(output_dir)
        return (
            f"✅ Revision complete — saved to `{published.output_file}`",
            md_content,                 # → final_output (gr.Markdown)
            gr.update(visible=False),
            gr.update(visible=True),
        )
    except Exception as e:
        return f"❌ Error: {e}", draft_md, gr.update(visible=True), gr.update(visible=False)


def run_monitor(kb_path, output_dir):
    try:
        from content_pipeline import ContentPipeline
    except ImportError as e:
        return f"❌ Import error: {e}", ""

    try:
        pipeline = ContentPipeline(knowledge_base_path=kb_path, output_dir=output_dir)
        response, logs = _capture_stdout(pipeline.monitor)
        return response.content, logs.strip()
    except Exception as e:
        return f"❌ Error: {e}", ""


def run_brief(topic, kb_path, output_dir):
    if not topic.strip():
        return "⚠️ Please enter a topic.", ""

    try:
        from content_pipeline import ContentPipeline
    except ImportError as e:
        return f"❌ Import error: {e}", ""

    try:
        pipeline = ContentPipeline(knowledge_base_path=kb_path, output_dir=output_dir)
        brief, logs = _capture_stdout(pipeline.brief, topic=topic)
        return brief.raw_brief, logs.strip()
    except Exception as e:
        return f"❌ Error: {e}", ""


def get_kb_status(kb_path):
    try:
        from knowledge_base import KnowledgeBase
    except ImportError as e:
        return f"❌ Import error: {e}"

    try:
        kb = KnowledgeBase(base_path=kb_path)
        state = kb.monitor_knowledge_state()
        lines = [
            f"**Total Documents:** {state['total_documents']}",
            f"**Total Words:** {state['total_words']:,}",
            "",
            f"**Primary KB** ({state['primary_count']} docs): {', '.join(state['primary_categories'])}",
            f"**Secondary KB** ({state['secondary_count']} docs): {', '.join(state['secondary_categories'])}",
            "",
            "### Documents",
        ]
        for doc in state["documents"]:
            lines.append(f"- `[{doc['kb_type'].upper()}]` **{doc['filename']}** — {doc['word_count']:,} words")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error: {e}"


def list_templates():
    lines = ["### Available Templates\n"]
    for name, desc in TEMPLATE_DESCRIPTIONS.items():
        lines.append(f"**`{name}`**  \n{desc}\n")
    return "\n".join(lines)


def update_template_description(template):
    return TEMPLATE_DESCRIPTIONS.get(template, "")


def load_latest_output(output_dir):
    md = _read_latest_md(output_dir)
    if not md:
        return "_(No output files found yet)_"
    return md


# ── UI ────────────────────────────────────────────────────────────────────────

css = """
/* ── global ── */
body, .gradio-container {
    font-family: 'IBM Plex Mono', 'Courier New', monospace !important;
    /* FIX: changed background from dark navy #0a0e17 to light blue */
    background: #ddeeff !important;
    color: #1a2a3a !important;
}

/* Remove Gradio's default white bg from main content area */
.gradio-container > .main, .gradio-container .contain {
    background: transparent !important;
}

/* ── header banner ── */
.cyber-header {
    background: linear-gradient(135deg, #b8d8f0 0%, #cce4f8 50%, #aecde8 100%);
    border: 1px solid #7ab0d8;
    border-radius: 8px;
    padding: 28px 36px;
    margin-bottom: 8px;
    position: relative;
    overflow: hidden;
}
.cyber-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #0080cc, #0050aa, transparent);
}
.cyber-header h1 {
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #0a2a4a !important;
    margin: 0 0 4px 0;
    text-transform: uppercase;
}
.cyber-header p {
    color: #2a6090 !important;
    font-size: 0.82rem;
    letter-spacing: 0.06em;
    margin: 0;
}

/* ── tabs ── */
.tab-nav button {
    background: #c8e0f4 !important;
    border: 1px solid #7ab0d8 !important;
    color: #1a4a70 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    border-radius: 4px 4px 0 0 !important;
    padding: 8px 18px !important;
}
.tab-nav button.selected {
    background: #e8f4ff !important;
    border-bottom-color: #e8f4ff !important;
    color: #0050aa !important;
    border-top: 2px solid #0080cc !important;
}

/* ── panels ── */
.panel-box {
    background: #c8e0f4;
    border: 1px solid #7ab0d8;
    border-radius: 6px;
    padding: 20px;
}

/* ── inputs ── */
label {
    font-size: 0.75rem !important;
    letter-spacing: 0.07em !important;
    color: #1a4a70 !important;
    text-transform: uppercase !important;
}
input[type=text], input[type=number], textarea, .gr-text-input, .gr-box {
    background: #f0f8ff !important;
    border: 1px solid #7ab0d8 !important;
    color: #0a2a4a !important;
    border-radius: 4px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
}
input[type=text]:focus, textarea:focus {
    border-color: #0080cc !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(0,128,204,0.15) !important;
}

/* ── dropdown ── */
.gr-dropdown select, select {
    background: #f0f8ff !important;
    border: 1px solid #7ab0d8 !important;
    color: #0a2a4a !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── buttons ── */
button.primary-btn, .gr-button-primary {
    background: linear-gradient(135deg, #0060a0, #0080cc) !important;
    border: 1px solid #0070b8 !important;
    color: #ffffff !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
    transition: all 0.2s ease !important;
}
button.primary-btn:hover, .gr-button-primary:hover {
    background: linear-gradient(135deg, #0080cc, #00a0e8) !important;
    border-color: #0090d0 !important;
    box-shadow: 0 0 12px rgba(0,128,204,0.3) !important;
}
.gr-button-secondary {
    background: #c8e0f4 !important;
    border: 1px solid #7ab0d8 !important;
    color: #1a4a70 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
}

/* ── markdown output ── */
.output-markdown, .gr-markdown {
    background: #f0f8ff !important;
    border: 1px solid #7ab0d8 !important;
    border-radius: 6px !important;
    padding: 20px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.85rem !important;
    color: #0a2a4a !important;
    line-height: 1.7 !important;
}
.output-markdown h1, .output-markdown h2, .output-markdown h3 {
    color: #0050aa !important;
    border-bottom: 1px solid #7ab0d8;
    padding-bottom: 4px;
}
.output-markdown code, .output-markdown pre {
    background: #ddeeff !important;
    border: 1px solid #7ab0d8 !important;
    color: #003a80 !important;
    border-radius: 3px;
}
.output-markdown strong { color: #003a80 !important; }
.output-markdown a { color: #0060c0 !important; }

/* ── status badge ── */
.status-text textarea, .gr-textbox textarea {
    background: #f0f8ff !important;
    color: #003a80 !important;
    border-color: #7ab0d8 !important;
    font-size: 0.82rem !important;
}

/* ── log box ── */
.log-box textarea {
    background: #e0eef8 !important;
    color: #1a4a30 !important;
    font-size: 0.72rem !important;
    border-color: #7ab0c8 !important;
}

/* ── checkbox / slider ── */
input[type=range] { accent-color: #0080cc; }
input[type=checkbox] { accent-color: #0080cc; }

/* ── divider ── */
hr { border-color: #7ab0d8 !important; }
"""

head_html = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&display=swap" rel="stylesheet">
"""

with gr.Blocks(css=css, head=head_html, title="CyberContent AI") as demo:

    gr.HTML("""
    <div class="cyber-header">
        <h1>⬡ CyberContent AI</h1>
        <p>AI-POWERED CYBERSECURITY CONTENT PIPELINE · MDR / SOC / THREAT INTELLIGENCE</p>
    </div>
    """)

    # ── shared settings (collapsed) ──────────────────────────────────────────
    with gr.Accordion("⚙  Pipeline Settings", open=False):
        with gr.Row():
            kb_path   = gr.Textbox(value="knowledge_base", label="Knowledge Base Path", scale=2)
            output_dir = gr.Textbox(value="output",         label="Output Directory",    scale=2)

    # ── tabs ─────────────────────────────────────────────────────────────────
    with gr.Tabs():

        # ── RUN ──────────────────────────────────────────────────────────────
        with gr.TabItem("🚀  Run Pipeline"):

            # — Stage 1: inputs —
            with gr.Row():
                with gr.Column(scale=2):
                    topic_run = gr.Textbox(
                        label="Topic / Angle",
                        placeholder="e.g. Why alert fatigue is a leadership problem",
                        lines=2,
                    )
                    template = gr.Dropdown(
                        choices=TEMPLATE_CHOICES,
                        value="blog_post_ciso",
                        label="Template",
                    )
                    tmpl_desc = gr.Markdown(
                        value=TEMPLATE_DESCRIPTIONS["blog_post_ciso"],
                        elem_classes=["output-markdown"],
                    )
                    template.change(update_template_description, template, tmpl_desc)

                    word_count   = gr.Slider(400, 3000, value=1600, step=100, label="Target Word Count")
                    skip_monitor = gr.Checkbox(label="Skip market monitoring stage", value=False)
                    gen_btn      = gr.Button("▶  Generate Draft", variant="primary")

                with gr.Column(scale=3):
                    run_status = gr.Textbox(label="Status", lines=2, interactive=False,
                                            elem_classes=["status-text"])
                    run_logs   = gr.Textbox(label="Pipeline Logs", lines=5, interactive=False,
                                            elem_classes=["log-box"])

            gr.Markdown("### 📄 Draft Output")
            draft_output = gr.Markdown(elem_classes=["output-markdown"])

            # — Stage 2: review panel (hidden until draft is ready) —
            with gr.Group(visible=False) as review_panel:
                gr.HTML("""
                <div style="
                    border: 1px solid #5aaa80;
                    background: linear-gradient(135deg, #d0f0e0, #e0f8ec);
                    border-radius: 6px;
                    padding: 16px 20px;
                    margin: 12px 0 8px 0;
                    position: relative;
                ">
                <div style="position:absolute;top:0;left:0;right:0;height:2px;
                    background:linear-gradient(90deg,transparent,#00bb66,transparent)"></div>
                <span style="color:#006633;font-family:'IBM Plex Mono',monospace;
                    font-size:0.78rem;letter-spacing:0.1em;text-transform:uppercase;font-weight:700;">
                    ◈ Human Review Required
                </span>
                <p style="color:#2a7a50;font-family:'IBM Plex Mono',monospace;
                    font-size:0.78rem;margin:6px 0 0 0;">
                    Review the draft above, then choose an action below.
                    Feedback revision is a one-time operation.
                </p>
                </div>
                """)
                with gr.Row():
                    approve_btn = gr.Button("✅  1. Approve & Continue", variant="primary", scale=1)
                    skip_btn    = gr.Button("⏭  3. Skip Review",         variant="secondary", scale=1)

                feedback_box = gr.Textbox(
                    label="2. Provide Feedback for Revision",
                    placeholder="e.g. Make the tone more technical, add a section on detection engineering, shorten the intro...",
                    lines=3,
                )
                revise_btn = gr.Button("🔄  Submit Feedback & Revise", variant="primary")

            # — Stage 3: final output (hidden until review is done) —
            # FIX: final_output is declared INSIDE the Group so gr.update(visible=True)
            # on final_panel also causes the Markdown child to render correctly.
            with gr.Group(visible=False) as final_panel:
                gr.HTML("""
                <div style="border:1px solid #7ab0d8;background:#e8f4ff;border-radius:6px;
                    padding:12px 20px;margin:12px 0 8px 0;">
                <span style="color:#0050aa;font-family:'IBM Plex Mono',monospace;
                    font-size:0.78rem;letter-spacing:0.1em;text-transform:uppercase;">
                    ◈ Final Output
                </span>
                </div>
                """)
                final_output = gr.Markdown(elem_classes=["output-markdown"])

            # — wiring —
            gen_btn.click(
                generate_draft,
                inputs=[topic_run, template, word_count, skip_monitor, kb_path, output_dir],
                outputs=[run_status, run_logs, draft_output, review_panel, final_panel],
            )
            # FIX: outputs list now includes final_output explicitly so the
            # Markdown component receives its value when the panel becomes visible.
            approve_btn.click(
                approve_draft,
                inputs=[draft_output, output_dir],
                outputs=[run_status, final_output, review_panel, final_panel],
            )
            skip_btn.click(
                skip_review,
                inputs=[draft_output, output_dir],
                outputs=[run_status, final_output, review_panel, final_panel],
            )
            revise_btn.click(
                revise_draft,
                inputs=[topic_run, template, word_count, feedback_box, draft_output, kb_path, output_dir],
                outputs=[run_status, final_output, review_panel, final_panel],
            )

        # ── BRIEF ────────────────────────────────────────────────────────────
        with gr.TabItem("📋  Content Brief"):
            topic_brief = gr.Textbox(
                label="Topic",
                placeholder="e.g. AI-powered phishing threats in 2025",
                lines=2,
            )
            brief_btn  = gr.Button("Generate Brief", variant="primary")
            brief_logs = gr.Textbox(label="Logs", lines=3, interactive=False,
                                    elem_classes=["log-box"])
            brief_out  = gr.Markdown(elem_classes=["output-markdown"])

            brief_btn.click(
                run_brief,
                inputs=[topic_brief, kb_path, output_dir],
                outputs=[brief_out, brief_logs],
            )

        # ── MONITOR ──────────────────────────────────────────────────────────
        with gr.TabItem("📊  Market Monitor"):
            monitor_btn  = gr.Button("▶  Run Monitor Analysis", variant="primary")
            monitor_logs = gr.Textbox(label="Logs", lines=3, interactive=False,
                                      elem_classes=["log-box"])
            monitor_out  = gr.Markdown(elem_classes=["output-markdown"])

            monitor_btn.click(
                run_monitor,
                inputs=[kb_path, output_dir],
                outputs=[monitor_out, monitor_logs],
            )

        # ── LATEST OUTPUT ────────────────────────────────────────────────────
        with gr.TabItem("📁  Latest Output"):
            refresh_btn = gr.Button("🔄  Refresh", variant="secondary")
            latest_out  = gr.Markdown(
                value="_(Click refresh to load the most recent generated file)_",
                elem_classes=["output-markdown"],
            )
            refresh_btn.click(load_latest_output, inputs=[output_dir], outputs=[latest_out])

        # ── KB STATUS ────────────────────────────────────────────────────────
        with gr.TabItem("🗂  Knowledge Base"):
            kb_btn  = gr.Button("Show KB Status", variant="secondary")
            kb_out  = gr.Markdown(elem_classes=["output-markdown"])
            kb_btn.click(get_kb_status, inputs=[kb_path], outputs=[kb_out])

        # ── TEMPLATES ────────────────────────────────────────────────────────
        with gr.TabItem("📚  Templates"):
            gr.Markdown(list_templates(), elem_classes=["output-markdown"])


# FIX: removed the broken `"""""` triple-quote that swallowed the second
# demo.launch() call, making only share=True run and ignoring server_name/port.
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_error=True, share=True)