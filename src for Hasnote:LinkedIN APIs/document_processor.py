"""
document_processor.py
Markdown document ingestion and processing for the AI Content Creator pipeline.
Handles loading, parsing, and structuring documents from both knowledge bases.
"""

import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Document:
    """Represents a processed markdown document."""
    path: str
    filename: str
    content: str
    kb_type: str  # "primary" or "secondary"
    category: str  # e.g., "brand_guidelines", "market_trends"
    word_count: int = 0
    sections: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.word_count = len(self.content.split())
        self.sections = self._extract_sections()

    def _extract_sections(self) -> dict:
        """Extract H2 sections from markdown for targeted retrieval."""
        sections = {}
        current_section = "intro"
        current_lines = []

        for line in self.content.split("\n"):
            if line.startswith("## "):
                if current_lines:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = line[3:].strip().lower().replace(" ", "_")
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections[current_section] = "\n".join(current_lines).strip()

        return sections

    def get_summary(self, max_chars: int = 500) -> str:
        """Return a truncated summary of the document."""
        clean = re.sub(r"#+ ", "", self.content)
        clean = re.sub(r"\*+", "", clean)
        clean = re.sub(r"\n{2,}", "\n", clean).strip()
        return clean[:max_chars] + "..." if len(clean) > max_chars else clean


class DocumentProcessor:
    """
    Loads and processes markdown documents from the knowledge base directories.
    Supports filtering by KB type, category, and keyword search.
    """

    SUPPORTED_EXTENSIONS = {".md", ".markdown"}

    def __init__(self, base_path: str = "knowledge_base"):
        self.base_path = Path(base_path)
        self.documents: list[Document] = []
        self._load_all()

    def _load_all(self):
        """Walk both knowledge base directories and load all markdown files."""
        for kb_type in ["primary", "secondary"]:
            kb_path = self.base_path / kb_type
            if not kb_path.exists():
                print(f"[WARNING] Knowledge base path not found: {kb_path}")
                continue

            for file_path in kb_path.rglob("*"):
                if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    doc = self._load_document(file_path, kb_type)
                    if doc:
                        self.documents.append(doc)

        print(f"[DocumentProcessor] Loaded {len(self.documents)} documents.")

    def _load_document(self, file_path: Path, kb_type: str) -> Optional[Document]:
        """Load and parse a single markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            # Derive category from parent folder name or filename
            category = file_path.parent.name if file_path.parent.name != kb_type else file_path.stem
            category = category.replace("-", "_").replace(" ", "_")

            return Document(
                path=str(file_path),
                filename=file_path.name,
                content=content,
                kb_type=kb_type,
                category=category,
                metadata={
                    "size_bytes": file_path.stat().st_size,
                    "last_modified": file_path.stat().st_mtime,
                }
            )
        except Exception as e:
            print(f"[ERROR] Failed to load {file_path}: {e}")
            return None

    def get_by_type(self, kb_type: str) -> list[Document]:
        """Return all documents from 'primary' or 'secondary' knowledge base."""
        return [d for d in self.documents if d.kb_type == kb_type]

    def get_by_category(self, category: str) -> list[Document]:
        """Return documents matching a specific category substring."""
        return [d for d in self.documents if category.lower() in d.category.lower()]

    def search(self, keyword: str, kb_type: Optional[str] = None) -> list[Document]:
        """Search documents by keyword in content (case-insensitive)."""
        results = []
        keyword_lower = keyword.lower()
        pool = self.get_by_type(kb_type) if kb_type else self.documents
        for doc in pool:
            if keyword_lower in doc.content.lower():
                results.append(doc)
        return results

    def build_context_block(
        self,
        kb_type: Optional[str] = None,
        categories: Optional[list[str]] = None,
        max_chars_per_doc: int = 2000,
    ) -> str:
        """
        Build a formatted context string to inject into LLM prompts.
        Optionally filter by KB type and/or category list.
        """
        pool = self.get_by_type(kb_type) if kb_type else self.documents

        if categories:
            pool = [d for d in pool if any(c.lower() in d.category.lower() for c in categories)]

        if not pool:
            return "[No relevant documents found in knowledge base]"

        blocks = []
        for doc in pool:
            truncated = doc.content[:max_chars_per_doc]
            if len(doc.content) > max_chars_per_doc:
                truncated += "\n... [truncated]"
            blocks.append(
                f"--- DOCUMENT: {doc.filename} ({doc.kb_type.upper()} KB) ---\n{truncated}\n"
            )

        return "\n".join(blocks)

    def list_documents(self) -> list[dict]:
        """Return a summary list of all loaded documents."""
        return [
            {
                "filename": d.filename,
                "kb_type": d.kb_type,
                "category": d.category,
                "word_count": d.word_count,
                "sections": list(d.sections.keys()),
            }
            for d in self.documents
        ]
