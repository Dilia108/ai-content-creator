"""
knowledge_base.py
Primary and Secondary Knowledge Base management.
Provides structured, context-aware retrieval for the content pipeline.
"""

from document_processor import DocumentProcessor


class KnowledgeBase:
    """
    Wraps DocumentProcessor with higher-level retrieval methods
    tailored for content creation workflows.
    """

    def __init__(self, base_path: str = "knowledge_base"):
        self.processor = DocumentProcessor(base_path=base_path)

    # ──────────────────────────────────────────────
    # PRIMARY KNOWLEDGE BASE — Company-Specific
    # ──────────────────────────────────────────────

    def get_brand_voice(self) -> str:
        """Retrieve brand voice and tone guidelines."""
        docs = self.processor.search("brand voice", kb_type="primary")
        if not docs:
            docs = self.processor.get_by_category("brand")
        return self._merge_docs(docs, label="BRAND GUIDELINES")

    def get_product_context(self, product_name: str = "") -> str:
        """Retrieve product specs, optionally filtered by product name."""
        docs = self.processor.search(product_name or "product", kb_type="primary")
        return self._merge_docs(docs, label="PRODUCT CONTEXT")

    def get_past_performance(self) -> str:
        """Retrieve data on what content has worked historically."""
        docs = self.processor.get_by_category("past_content")
        if not docs:
            docs = self.processor.search("performance", kb_type="primary")
        return self._merge_docs(docs, label="PAST CONTENT PERFORMANCE")

    def get_all_primary_context(self, max_chars: int = 4000) -> str:
        """Return a consolidated primary KB context block."""
        return self.processor.build_context_block(kb_type="primary", max_chars_per_doc=max_chars)

    # ──────────────────────────────────────────────
    # SECONDARY KNOWLEDGE BASE — Industry Research
    # ──────────────────────────────────────────────

    def get_market_trends(self) -> str:
        """Retrieve current market trend data."""
        docs = self.processor.search("trends", kb_type="secondary")
        return self._merge_docs(docs, label="MARKET TRENDS")

    def get_competitor_insights(self, competitor: str = "") -> str:
        """Retrieve competitor analysis, optionally filtered by competitor name."""
        if competitor:
            docs = self.processor.search(competitor, kb_type="secondary")
        else:
            docs = self.processor.get_by_category("competitor")
        return self._merge_docs(docs, label="COMPETITOR INSIGHTS")

    def get_industry_stats(self) -> str:
        """Extract statistical data points for credibility injection."""
        docs = self.processor.search("statistics", kb_type="secondary")
        if not docs:
            docs = self.processor.get_by_type("secondary")
        # Extract lines with numbers/percentages
        stat_lines = []
        for doc in docs:
            for line in doc.content.split("\n"):
                if any(char.isdigit() for char in line) and len(line) > 20:
                    stat_lines.append(line.strip())
        return "\n".join(stat_lines[:30]) if stat_lines else "[No stats found]"

    def get_content_gaps(self) -> str:
        """Retrieve identified content gaps from competitor analysis."""
        docs = self.processor.search("content gap", kb_type="secondary")
        return self._merge_docs(docs, label="CONTENT GAPS & OPPORTUNITIES")

    def get_all_secondary_context(self, max_chars: int = 3000) -> str:
        """Return a consolidated secondary KB context block."""
        return self.processor.build_context_block(kb_type="secondary", max_chars_per_doc=max_chars)

    # ──────────────────────────────────────────────
    # COMBINED CONTEXT FOR PROMPTS
    # ──────────────────────────────────────────────

    def build_full_context(
        self,
        topic: str = "",
        include_primary: bool = True,
        include_secondary: bool = True,
        max_chars_each: int = 2500,
    ) -> str:
        """
        Build a rich context block combining both knowledge bases.
        If a topic is provided, documents are filtered by relevance to that topic.
        """
        sections = []

        if include_primary:
            if topic:
                primary_docs = self.processor.search(topic, kb_type="primary")
                if not primary_docs:
                    primary_docs = self.processor.get_by_type("primary")
                primary_context = self._merge_docs(
                    primary_docs, label="PRIMARY KB (Company-Specific)", max_chars=max_chars_each
                )
            else:
                primary_context = self.get_all_primary_context(max_chars=max_chars_each)
            sections.append(primary_context)

        if include_secondary:
            if topic:
                secondary_docs = self.processor.search(topic, kb_type="secondary")
                if not secondary_docs:
                    secondary_docs = self.processor.get_by_type("secondary")
                secondary_context = self._merge_docs(
                    secondary_docs, label="SECONDARY KB (Industry Research)", max_chars=max_chars_each
                )
            else:
                secondary_context = self.get_all_secondary_context(max_chars=max_chars_each)
            sections.append(secondary_context)

        return "\n\n".join(sections)

    def monitor_knowledge_state(self) -> dict:
        """
        Monitor step: Audit the knowledge base and return a health report.
        Useful for the 'Monitor' stage of the pipeline.
        """
        all_docs = self.processor.list_documents()
        primary_docs = [d for d in all_docs if d["kb_type"] == "primary"]
        secondary_docs = [d for d in all_docs if d["kb_type"] == "secondary"]

        return {
            "total_documents": len(all_docs),
            "primary_count": len(primary_docs),
            "secondary_count": len(secondary_docs),
            "primary_categories": list({d["category"] for d in primary_docs}),
            "secondary_categories": list({d["category"] for d in secondary_docs}),
            "total_words": sum(d["word_count"] for d in all_docs),
            "documents": all_docs,
        }

    # ──────────────────────────────────────────────
    # INTERNAL HELPERS
    # ──────────────────────────────────────────────

    def _merge_docs(
        self,
        docs: list,
        label: str = "CONTEXT",
        max_chars: int = 3000,
    ) -> str:
        """Merge a list of Document objects into a single labeled context block."""
        if not docs:
            return f"[{label}]\nNo relevant documents found.\n"

        parts = [f"=== {label} ==="]
        for doc in docs:
            truncated = doc.content[:max_chars]
            if len(doc.content) > max_chars:
                truncated += "\n... [content truncated for context window]"
            parts.append(f"\n[Source: {doc.filename}]\n{truncated}\n")

        return "\n".join(parts)
