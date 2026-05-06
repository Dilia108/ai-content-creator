# AI Content Creator — CyberContent

A Python automation framework for generating brand-aligned, non-generic cybersecurity content using LLM APIs and a two-tier knowledge base architecture.

* **Client:** IronVeil Security

---

## Project Overview

This system implements a five-stage content creation pipeline that produces content distinctly different from generic AI output by:

1. **Grounding every piece** in company-specific brand guidelines, product context, and historical performance data (Primary KB)
2. **Positioning content** within current market dynamics, competitor gaps, and regulatory trends (Secondary KB)
3. **Using advanced prompt templates** that enforce brand voice rules, forbid generic phrases, and vary structure by audience
4. **Including a human-in-the-loop** review and iteration step
5. **Iterating on feedback** using a dedicated refinement template

---

## Quick Start

```bash
# 1. Clone and enter the project
cd ai-content-creator

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the full pipeline
python src/main.py run --topic "Why alert fatigue is a leadership failure, not a tooling problem"

# 5. Or run individual stages
python src/main.py monitor          # Stage 2: market analysis
python src/main.py brief --topic "Zero trust for mid-market companies"  # Stage 3
python src/main.py kb-status        # Check knowledge base
python src/main.py list-templates   # See available templates

# 6. Launch the Gradio UI
python src/app.py
```

---

## Project Structure

```
ai-content-creator/
├── src/
│   ├── document_processor.py    # Markdown ingestion, parsing, section extraction
│   ├── knowledge_base.py        # Primary and secondary KB management + retrieval
│   ├── prompt_templates.py      # Advanced prompt templates with brand constraints
│   ├── content_pipeline.py      # Five-stage pipeline orchestration
│   ├── llm_integration.py       # OpenAI API client with retry + output management
│   └── main.py                  # CLI entry point
│   └── app.py                   # Gradio UI
├── knowledge_base/
│   ├── primary/                 # Company-specific documents
│   │   ├── brand_guidelines.md  # Voice, tone, approved terminology
│   │   ├── product_specs.md     # Product details and differentiators
│   │   └── past_content/
│   │       └── performance_data.md  # What content has worked historically
│   └── secondary/               # Industry research
│       ├── market_trends.md     # Current threat landscape and budget trends
│       └── competitor_analysis.md  # Competitive positioning and content gaps
├── templates/                   # (extend with custom template .md files)
├── config/
│   └── vscode_agent.json        # VSCode agent configuration
├── output/                      # Generated content (auto-created, timestamped)
├── requirements.txt
├── .env.example                 # Copy to .env and fill in API key
└── README.md
```

---

## The Five-Stage Pipeline

### Stage 1: Document
`DocumentProcessor` walks both knowledge base directories, loads all `.md` files, extracts H2 sections, and makes documents available for retrieval by type, category, or keyword.

### Stage 2: Monitor
Analyzes market trends, competitor positioning, and past content performance using the `monitor` template. Outputs 5 ranked content opportunities with rationale, angle, format recommendation, and urgency.

```bash
python src/main.py monitor
```

### Stage 3: Brief
Generates a structured content brief including: title options, core argument, why-now rationale, key points with data, competitive differentiation, and CTA. Feeds directly into Stage 4.

```bash
python src/main.py brief --topic "Your topic here"
```

### Stage 4: Publish
Uses the brief + full knowledge base context to generate final content via the selected template. Includes a **human review step** where you can approve, request revisions, or skip.

### Stage 5: Iterate
Takes feedback (from human review or provided directly) and produces a refined version using the `iterate` template, which explicitly tracks what changed and flags conflicts with brand guidelines.

---

## Content Templates

| Template | Audience | Format | Use Case |
|---|---|---|---|
| `blog_post_ciso` | CISO / Security Director | Blog post | Thought leadership, 1500–2000 words |
| `blog_post_analyst` | SOC Analyst / Engineer | Blog post | Technical deep-dives, practitioner focus |
| `linkedin_thought_leadership` | CISO / Security Leader | LinkedIn post | 150–250 word engagement posts |
| `content_brief` | Internal | Brief | Planning and scoping |
| `monitor_trends` | Internal | Report | Weekly market opportunity analysis |
| `iterate_and_refine` | Internal | Refinement | Feedback-driven content revision |

---

## Avoiding Generic AI Content

The system implements four anti-homogenization strategies:

**1. Hard-coded anti-patterns in system prompts:**
> "NEVER open with 'In today's digital landscape'... NEVER use: 'robust', 'cutting-edge', 'next-generation', 'leverage' (as verb)..."

**2. Knowledge base grounding:**
Every piece of content is generated with injected context from both knowledge bases, forcing specificity about company products, past performance, and market positioning.

**3. Structural constraints by audience:**
Each template enforces different structures — CISO posts require "one analogy per piece" and "one counterintuitive point"; SOC analyst posts require MITRE ATT&CK references and SIEM workflow descriptions.

**4. Human-in-the-loop and iteration:**
The pipeline stops for human review by default. Feedback is incorporated via a dedicated `iterate` template that explicitly surfaces conflicts with brand guidelines.

---

## Knowledge Base Management

### Adding Primary Documents
Drop `.md` files into `knowledge_base/primary/`. Subdirectories are supported (e.g., `primary/past_content/`). The `DocumentProcessor` auto-discovers them on next run.

### Adding Secondary Documents
Drop `.md` files into `knowledge_base/secondary/`. Update `market_trends.md` and `competitor_analysis.md` regularly (recommended: weekly).

### Checking KB Status
```bash
python src/main.py kb-status
```

---

## VSCode Agent Configuration

The `config/vscode_agent.json` defines:
- Custom instructions for the coding agent to understand project structure
- File inclusion/exclusion patterns for context
- Pre-built task definitions for common commands
- Workflow guidelines for how the agent should approach content generation requests

To use with VSCode, reference this config file in your workspace settings.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | — | Your OpenAI API key |
| `LLM_MODEL` | No | `gpt-4o-mini` | Override the default model |

---

## Example Usage

```bash
# Run full pipeline — CISO blog post on alert fatigue
python src/main.py run \
  --topic "Alert fatigue is a leadership problem, not a tooling problem" \
  --template blog_post_ciso \
  --word-count 1800

# Run full pipeline — SOC analyst post on lateral movement detection
python src/main.py run \
  --topic "Detecting lateral movement in Microsoft environments" \
  --template blog_post_analyst \
  --no-review

# Quick LinkedIn post
python src/main.py run \
  --topic "The hidden cost of your current SIEM setup" \
  --template linkedin_thought_leadership \
  --skip-monitor \
  --no-review

# Generate content brief only
python src/main.py brief --topic "AI-augmented phishing attacks in 2025"

# Run market monitoring report
python src/main.py monitor
```

---

## Output Files

All generated content is saved to `output/` with the naming convention:
```
YYYYMMDD_HHMMSS_{template_name}_{topic_slug}.md
```

Each file includes a header comment with generation timestamp, model used, and token count.

---

## Extending the System

**Add a new template:**
1. Define a `PromptTemplate` in `src/prompt_templates.py`
2. Register it in `TEMPLATE_REGISTRY`
3. Add it as a CLI option in `src/main.py`

**Add a new knowledge base source:**
1. Create a `.md` file in the appropriate KB directory
2. Run `python src/main.py kb-status` to verify it's loaded

**Add a new pipeline stage:**
1. Add a method to `ContentPipeline` in `src/content_pipeline.py`
2. Update the `run()` method to call it at the appropriate stage
3. Update the CLI in `src/main.py`
