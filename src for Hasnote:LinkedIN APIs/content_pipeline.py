"""
content_pipeline.py
Implements the full content creation workflow:
Document → Monitor → Brief → Publish → Iterate

Each stage produces structured outputs that feed into the next.
"""

import json
import time
import os
from dataclasses import dataclass, field
from typing import Optional

from knowledge_base import KnowledgeBase
from prompt_templates import get_template, list_templates
from llm_integration import LLMClient, LLMResponse
from publish_hashnode import publish_to_hashnode
from publish_linkedin import publish_to_linkedin


@dataclass
class ContentBrief:
    """Structured output of the Brief stage."""
    topic: str
    raw_brief: str
    recommended_template: str = "blog_post_ciso"
    audience: str = "ciso"
    urgency: str = "medium"
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class PublishedContent:
    """Structured output of the Publish stage."""
    brief: ContentBrief
    content: str
    template_used: str
    model: str
    tokens_used: int
    output_file: str = ""
    published_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    feedback: list[str] = field(default_factory=list)
    iterations: int = 0


class ContentPipeline:
    """
    Orchestrates the five-stage content creation workflow.

    Stages:
    1. Document  — Load and validate knowledge bases
    2. Monitor   — Analyze market context, identify opportunities
    3. Brief     — Generate a structured content brief
    4. Publish   — Create final content from the brief
    5. Iterate   — Refine based on feedback
    """

    def __init__(
        self,
        knowledge_base_path: str = "knowledge_base",
        output_dir: str = "output",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        auto_save: bool = True,
    ):
        self.output_dir = output_dir
        self.auto_save = auto_save
        os.makedirs(output_dir, exist_ok=True)

        print("\n" + "="*60)
        print("  AI CONTENT CREATOR — IronVeil Security")
        print("="*60)

        # Stage 1: Document — Initialize knowledge base
        print("\n[STAGE 1: DOCUMENT] Loading knowledge bases...")
        self.kb = KnowledgeBase(base_path=knowledge_base_path)
        self.llm = LLMClient(api_key=api_key, model=model)

        state = self.kb.monitor_knowledge_state()
        print(f"  ✓ {state['total_documents']} documents loaded")
        print(f"  ✓ Primary KB: {state['primary_count']} docs | Secondary KB: {state['secondary_count']} docs")
        print(f"  ✓ Total knowledge: {state['total_words']:,} words\n")

    # ──────────────────────────────────────────────
    # STAGE 2: MONITOR
    # ──────────────────────────────────────────────

    def monitor(self) -> LLMResponse:
        """
        Stage 2: Monitor — Analyze market trends and identify content opportunities.
        Uses both knowledge bases to surface relevant topics.
        """
        print("[STAGE 2: MONITOR] Analyzing market context and content opportunities...")

        market_context = self.kb.get_market_trends()
        competitor_context = self.kb.get_competitor_insights()
        performance_context = self.kb.get_past_performance()

        template = get_template("monitor_trends")
        system_prompt, user_prompt = template.render(
            market_context=market_context,
            competitor_context=competitor_context,
            performance_context=performance_context,
        )

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            template_name="monitor_trends",
            topic="market_monitor",
            max_tokens=2000,
            temperature=0.6,
        )

        if self.auto_save:
            response.save(self.output_dir)

        print("  ✓ Monitor report generated\n")
        return response

    # ──────────────────────────────────────────────
    # STAGE 3: BRIEF
    # ──────────────────────────────────────────────

    def brief(
        self,
        topic: str,
        template_name: str = "blog_post_ciso",
    ) -> ContentBrief:
        """
        Stage 3: Brief — Generate a structured content brief for a given topic.
        Pulls context from both knowledge bases.
        """
        print(f"[STAGE 3: BRIEF] Generating content brief for: '{topic}'")

        kb_context = self.kb.build_full_context(topic=topic)
        template = get_template("content_brief")

        system_prompt, user_prompt = template.render(
            topic=topic,
            kb_context=kb_context,
        )

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            template_name="content_brief",
            topic=topic,
            max_tokens=1500,
            temperature=0.65,
        )

        if self.auto_save:
            response.save(self.output_dir)

        brief = ContentBrief(
            topic=topic,
            raw_brief=response.content,
            recommended_template=template_name,
        )

        print("  ✓ Content brief generated\n")
        return brief

    # ──────────────────────────────────────────────
    # STAGE 4: PUBLISH
    # ──────────────────────────────────────────────

    def publish(
        self,
        brief: ContentBrief,
        template_name: Optional[str] = None,
        word_count: int = 1600,
        human_review: bool = True,
    ) -> PublishedContent:
        """
        Stage 4: Publish — Create final content from a content brief.
        Optionally prompts for human review before saving.
        """
        chosen_template = template_name or brief.recommended_template
        print(f"[STAGE 4: PUBLISH] Creating content | Template: {chosen_template}")

        kb_context = self.kb.build_full_context(topic=brief.topic)
        template = get_template(chosen_template)

        extra_vars = {
            "content_brief": brief.raw_brief,
            "word_count": word_count,
        }

        system_prompt, user_prompt = template.render(
            topic=brief.topic,
            kb_context=kb_context,
            **extra_vars,
        )

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            template_name=chosen_template,
            topic=brief.topic,
            max_tokens=4096,
            temperature=0.72,
        )

        output_file = ""
        if self.auto_save:
            output_file = response.save(self.output_dir)

        published = PublishedContent(
            brief=brief,
            content=response.content,
            template_used=chosen_template,
            model=response.model,
            tokens_used=response.total_tokens,
            output_file=output_file,
        )

        print("  ✓ Content created\n")

        # Human-in-the-loop review
        if human_review:
            published = self._human_review_step(published)

        return published

    # ──────────────────────────────────────────────
    # STAGE 5: ITERATE
    # ──────────────────────────────────────────────

    def iterate(
        self,
        published: PublishedContent,
        feedback: Optional[str] = None,
    ) -> PublishedContent:
        """
        Stage 5: Iterate — Refine published content based on feedback.
        Feedback can be provided directly or collected interactively.
        """
        if not feedback:
            print("[STAGE 5: ITERATE] Enter feedback for refinement (or press Enter to skip):")
            feedback = input("  Feedback: ").strip()

        if not feedback:
            print("  [ITERATE] No feedback provided. Skipping iteration.")
            return published

        print(f"[STAGE 5: ITERATE] Refining content based on feedback...")

        brand_context = self.kb.get_brand_voice()
        template = get_template("iterate_and_refine")

        system_prompt, user_prompt = template.render(
            topic=published.brief.topic,
            kb_context=brand_context,
            original_content=published.content,
            feedback=feedback,
            brand_context=brand_context,
        )

        response = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            template_name="iterate_and_refine",
            topic=published.brief.topic,
            max_tokens=4096,
            temperature=0.6,
        )

        published.content = response.content
        published.feedback.append(feedback)
        published.iterations += 1

        if self.auto_save:
            output_file = response.save(self.output_dir)
            published.output_file = output_file

        print(f"  ✓ Iteration {published.iterations} complete\n")
        return published

    # ──────────────────────────────────────────────
    # FULL PIPELINE RUN
    # ──────────────────────────────────────────────

    def run(
        self,
        topic: str,
        template_name: str = "blog_post_ciso",
        word_count: int = 1600,
        skip_monitor: bool = False,
        human_review: bool = True,
    ) -> PublishedContent:
        """
        Run the complete content creation pipeline for a given topic.

        Args:
            topic: The content topic or title angle
            template_name: Which content template to use (see prompt_templates.py)
            word_count: Target word count for the final piece
            skip_monitor: Skip the market monitoring stage
            human_review: Whether to prompt for human review before publishing

        Returns:
            PublishedContent object with final content and metadata
        """
        print(f"\n🚀 Starting pipeline for topic: '{topic}'\n")

        if not skip_monitor:
            self.monitor()

        content_brief = self.brief(topic=topic, template_name=template_name)
        published = self.publish(
            brief=content_brief,
            template_name=template_name,
            word_count=word_count,
            human_review=human_review,
        )

        print("\n" + "="*60)
        print("  PIPELINE COMPLETE")
        print("="*60)
        print(f"  Topic:      {topic}")
        print(f"  Template:   {template_name}")
        print(f"  Tokens:     {published.tokens_used:,}")
        print(f"  Iterations: {published.iterations}")
        print(f"  Output:     {published.output_file}")
        print("="*60 + "\n")

        return published

    # ──────────────────────────────────────────────
    # HUMAN-IN-THE-LOOP
    # ──────────────────────────────────────────────

    def _human_review_step(self, published: PublishedContent) -> PublishedContent:
        """
        Human-in-the-loop review step.
        Presents content for approval and collects feedback.
        """
        print("\n" + "-"*60)
        print("  HUMAN REVIEW STEP")
        print("-"*60)
        print(f"\n📄 GENERATED CONTENT PREVIEW:\n")
        preview = published.content[:800] + ("..." if len(published.content) > 800 else "")
        print(preview)
        print(f"\n[Full content saved to: {published.output_file}]")
        
        print("\nOptions:")
        print("  [1] Approve and publish to Hashnode")
        print("  [2] Approve and publish to LinkedIn")
        print("  [3] Provide feedback for revision")
        print("  [4] Skip review")

        choice = input("\nYour choice [1/2/3/4]: ").strip()

        if choice == "1":
            publish_to_hashnode(published.brief.topic, published.content)
        elif choice == "2":
            publish_to_linkedin(published.content)
        elif choice == "3":
            feedback = input("Enter your feedback: ").strip()
            if feedback:
                published = self.iterate(published, feedback=feedback)
        elif choice == "4":
            print("  [Review] Skipped.")

        return published  