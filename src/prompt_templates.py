"""
prompt_templates.py
Advanced, reusable prompt engineering templates for AI content creation.
Designed to produce distinctive, brand-aligned outputs — not generic AI content.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ContentFormat(Enum):
    BLOG_POST = "blog_post"
    LINKEDIN_POST = "linkedin_post"
    EXECUTIVE_BRIEF = "executive_brief"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    EMAIL_NEWSLETTER = "email_newsletter"
    CONTENT_BRIEF = "content_brief"


class AudienceType(Enum):
    CISO = "ciso"
    SOC_ANALYST = "soc_analyst"
    EXECUTIVE_BOARD = "executive_board"
    IT_MANAGER = "it_manager"


@dataclass
class PromptTemplate:
    name: str
    system_prompt: str
    user_prompt_template: str
    format: ContentFormat
    audience: AudienceType
    notes: str = ""

    def render(self, **kwargs) -> tuple[str, str]:
        """Return (system_prompt, rendered_user_prompt) tuple."""
        return self.system_prompt, self.user_prompt_template.format(**kwargs)


# ──────────────────────────────────────────────────────────────
# SYSTEM PROMPTS — Define the AI's persona and constraints
# ──────────────────────────────────────────────────────────────

BRAND_PERSONA_SYSTEM = """You are the senior content strategist for a cybersecurity company
serving mid-market enterprises. You write with deep technical credibility but always translate
complexity into operational clarity.

Your writing rules:
1. NEVER open with "In today's digital landscape" or any generic scene-setting.
2. NEVER use these phrases: "robust", "cutting-edge", "next-generation", "game-changing", "leverage" (as a verb), "utilize", "seamlessly".
3. ALWAYS lead with the reader's specific pain or context, not the product.
4. ALWAYS include at least one concrete data point from a recognized source.
5. NEVER make claims you can't substantiate. If uncertain, say "research suggests" or cite ranges.
6. Write like a knowledgeable colleague, not a marketing brochure.
7. Prefer short sentences when making a key point. Use longer sentences for context.
8. End with something actionable — a question, a next step, or a challenge to the reader.

Tone: Authoritative, pragmatic, occasionally dry-humored. The expert in the room who doesn't need to prove it.
"""

SOC_ANALYST_SYSTEM = """You are writing for SOC analysts and security engineers — practitioners who
work hands-on with security tooling every day. They are deeply skeptical of vendor marketing.

Your writing rules:
1. Be technically precise. Vague claims will lose this audience instantly.
2. Acknowledge the operational constraints analysts face (understaffing, alert fatigue, tool sprawl).
3. Use specific tool names, protocols, and frameworks when relevant (MITRE ATT&CK, SIEM, EDR, etc.).
4. Don't talk down to the reader. They know more than most vendors give them credit for.
5. Include "war stories" framing — what happens at 2am when things break.
6. Avoid corporate language entirely. Write like a practitioner, for practitioners.
7. NEVER use the passive voice to hide uncertainty (e.g., "It is believed that..." → just say what you know).
"""

EXECUTIVE_SYSTEM = """You are writing for CISOs and C-suite executives who consume content in 5-minute windows.
They make strategic decisions, not technical ones.

Your writing rules:
1. Lead with business impact: revenue risk, regulatory exposure, or operational resilience.
2. Translate technical threats into financial and reputational language.
3. No acronyms without explanation on first use.
4. Structure for skimmability: key insight in the first sentence of every paragraph.
5. Respect their time — every sentence must earn its place.
6. Connect security decisions to board-level priorities: M&A risk, cyber insurance, ESG reporting.
7. End with a clear, specific recommendation they can act on or delegate.
"""

# ──────────────────────────────────────────────────────────────
# CONTENT BRIEF TEMPLATE
# ──────────────────────────────────────────────────────────────

CONTENT_BRIEF_TEMPLATE = PromptTemplate(
    name="content_brief",
    format=ContentFormat.CONTENT_BRIEF,
    audience=AudienceType.CISO,
    system_prompt=BRAND_PERSONA_SYSTEM,
    user_prompt_template="""Generate a detailed content brief for a cybersecurity article based on the context below.

TOPIC: {topic}

KNOWLEDGE BASE CONTEXT:
{kb_context}

Output the brief in this exact structure:
---
TITLE OPTIONS (3 alternatives):
1. [Option 1]
2. [Option 2]
3. [Option 3]

RECOMMENDED TITLE: [Your pick and why]

TARGET AUDIENCE: [Specific role and seniority]

CORE ARGUMENT (one sentence): [The central claim this piece makes]

WHY NOW: [Why this topic is timely — market conditions, recent events, regulatory changes]

KEY POINTS TO COVER:
1. [Point 1 — with supporting data or example]
2. [Point 2 — with supporting data or example]
3. [Point 3 — with supporting data or example]

DATA POINTS TO INCLUDE: [3-5 specific statistics with sources]

COMPETITIVE DIFFERENTIATION: [How this piece positions us differently from competitors]

CALL TO ACTION: [Specific action for the reader]

CONTENT WARNINGS (what to avoid): [Common pitfalls for this topic]

SUGGESTED FORMAT: [Blog, LinkedIn post, email, etc. with estimated word count]
---

Be specific and actionable. Reference the knowledge base context where relevant.""",
    notes="Use for planning stage. Output feeds into blog/LinkedIn templates."
)

# ──────────────────────────────────────────────────────────────
# BLOG POST TEMPLATE
# ──────────────────────────────────────────────────────────────

BLOG_POST_CISO_TEMPLATE = PromptTemplate(
    name="blog_post_ciso",
    format=ContentFormat.BLOG_POST,
    audience=AudienceType.CISO,
    system_prompt=BRAND_PERSONA_SYSTEM,
    user_prompt_template="""Write a {word_count}-word blog post for CISOs based on this brief and context.

CONTENT BRIEF:
{content_brief}

KNOWLEDGE BASE CONTEXT:
{kb_context}

STRUCTURAL REQUIREMENTS:
- Opening: 2-3 sentences that state a specific, uncomfortable truth or overlooked reality
- Body: 3-4 sections with H2 headers (no generic headers like "Introduction" or "Conclusion")
- Each section: 150-200 words with at least one concrete example or data point
- Closing: A challenge or reframe — give the reader something to think or do differently

STYLE REQUIREMENTS:
- First person plural ("We've seen...", "Most CISOs we work with...") to create intimacy
- One analogy per piece (make it non-tech but precise)
- One counterintuitive point that challenges conventional wisdom
- Active voice throughout

OUTPUT FORMAT: Full article text with markdown formatting (## for headers, **bold** for key terms).
Include a 50-word meta description at the end, prefixed with META:""",
    notes="Primary blog format for CISO audience. ~1500-2000 words optimal."
)

BLOG_POST_ANALYST_TEMPLATE = PromptTemplate(
    name="blog_post_analyst",
    format=ContentFormat.BLOG_POST,
    audience=AudienceType.SOC_ANALYST,
    system_prompt=SOC_ANALYST_SYSTEM,
    user_prompt_template="""Write a {word_count}-word technical blog post for SOC analysts and security engineers.

TOPIC: {topic}

KNOWLEDGE BASE CONTEXT:
{kb_context}

STRUCTURAL REQUIREMENTS:
- Opening: Describe a specific scenario from the analyst's perspective (the 2am moment)
- Include: MITRE ATT&CK technique references where relevant
- Include: At least one detection logic snippet or workflow description
- Include: A "what this looks like in your SIEM" section
- Closing: A practical, immediately actionable recommendation

STYLE REQUIREMENTS:
- Technical but not academic
- First-person ("You're looking at your dashboard...")
- Name specific tools and technologies
- Acknowledge the messy reality (alerts, false positives, resource constraints)

OUTPUT FORMAT: Full article text with markdown formatting.""",
    notes="Technical depth format for practitioner audience."
)

# ──────────────────────────────────────────────────────────────
# LINKEDIN POST TEMPLATE
# ──────────────────────────────────────────────────────────────

LINKEDIN_THOUGHT_LEADERSHIP = PromptTemplate(
    name="linkedin_thought_leadership",
    format=ContentFormat.LINKEDIN_POST,
    audience=AudienceType.CISO,
    system_prompt=BRAND_PERSONA_SYSTEM,
    user_prompt_template="""Write a LinkedIn post for a senior cybersecurity leader (CISO/VP Security) to share.

TOPIC/ANGLE: {topic}

KNOWLEDGE BASE CONTEXT:
{kb_context}

LINKEDIN FORMAT RULES:
- First line: Bold claim or counterintuitive observation (stops the scroll — no more than 12 words)
- NO hashtag spam (max 3 relevant hashtags at the end)
- Use line breaks generously — LinkedIn readers scan, not read
- Length: 150-250 words maximum
- End with a question to drive comments

CONTENT RULES:
- Personal voice — this is a person sharing an insight, not a brand broadcasting
- Reference a real-world pattern or observation, not a generic trend
- Include one data point or specific example
- Avoid sounding like an advertisement

TONE: Confident, slightly provocative, collegial — not corporate.

Output only the post text, ready to paste.""",
    notes="High-engagement format. Avoid posting more than 3x/week."
)

# ──────────────────────────────────────────────────────────────
# ITERATION / REFINEMENT TEMPLATE
# ──────────────────────────────────────────────────────────────

ITERATE_TEMPLATE = PromptTemplate(
    name="iterate_and_refine",
    format=ContentFormat.BLOG_POST,
    audience=AudienceType.CISO,
    system_prompt=BRAND_PERSONA_SYSTEM,
    user_prompt_template="""Refine the following content based on the feedback provided.

ORIGINAL CONTENT:
{original_content}

FEEDBACK:
{feedback}

BRAND CONTEXT:
{brand_context}

REFINEMENT INSTRUCTIONS:
1. Address every piece of feedback specifically
2. Do NOT make changes beyond what the feedback requests (preserve what's working)
3. Flag any feedback that conflicts with brand guidelines (and explain why)
4. If the feedback asks for something generic or clichéd, offer an alternative that achieves the same goal more distinctively

Output:
- CHANGES MADE: [Bullet list of what was changed and why]
- FLAGGED CONFLICTS: [Any feedback that conflicts with brand guidelines]
- REFINED CONTENT: [The full revised piece]""",
    notes="Use in the Iterate stage of the pipeline."
)

# ──────────────────────────────────────────────────────────────
# MONITOR / TREND ANALYSIS TEMPLATE
# ──────────────────────────────────────────────────────────────

MONITOR_TEMPLATE = PromptTemplate(
    name="monitor_trends",
    format=ContentFormat.CONTENT_BRIEF,
    audience=AudienceType.CISO,
    system_prompt=BRAND_PERSONA_SYSTEM,
    user_prompt_template="""Analyze the current market context and identify content opportunities for IronVeil Security.

MARKET RESEARCH DATA:
{market_context}

COMPETITOR CONTEXT:
{competitor_context}

PAST CONTENT PERFORMANCE:
{performance_context}

Identify and rank 5 content opportunities based on:
1. Timeliness (is this trending or emerging?)
2. Differentiation (can we own this angle vs. competitors?)
3. Audience relevance (does this match CISO/SOC analyst pain points?)
4. Business alignment (does this connect to our product areas?)

OUTPUT FORMAT:
For each opportunity:
OPPORTUNITY #[N]: [Descriptive title]
RATIONALE: [2-3 sentences on why this is an opportunity now]
ANGLE: [Our specific take — what's the counterintuitive or differentiated angle?]
FORMAT RECOMMENDATION: [Blog, LinkedIn, email, etc.]
URGENCY: [High/Medium/Low with explanation]
---""",
    notes="Run weekly to keep content pipeline fresh and market-aligned."
)

# ──────────────────────────────────────────────────────────────
# TEMPLATE REGISTRY
# ──────────────────────────────────────────────────────────────

TEMPLATE_REGISTRY: dict[str, PromptTemplate] = {
    "content_brief": CONTENT_BRIEF_TEMPLATE,
    "blog_post_ciso": BLOG_POST_CISO_TEMPLATE,
    "blog_post_analyst": BLOG_POST_ANALYST_TEMPLATE,
    "linkedin_thought_leadership": LINKEDIN_THOUGHT_LEADERSHIP,
    "iterate_and_refine": ITERATE_TEMPLATE,
    "monitor_trends": MONITOR_TEMPLATE,
}


def get_template(name: str) -> PromptTemplate:
    """Retrieve a template by name."""
    if name not in TEMPLATE_REGISTRY:
        raise ValueError(f"Template '{name}' not found. Available: {list(TEMPLATE_REGISTRY.keys())}")
    return TEMPLATE_REGISTRY[name]


def list_templates() -> list[dict]:
    """List all available templates with metadata."""
    return [
        {
            "name": t.name,
            "format": t.format.value,
            "audience": t.audience.value,
            "notes": t.notes,
        }
        for t in TEMPLATE_REGISTRY.values()
    ]