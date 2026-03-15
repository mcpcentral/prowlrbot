# -*- coding: utf-8 -*-
"""AutoResearch engine — orchestrates research workflows."""

from __future__ import annotations

import hashlib
import re
import time
from typing import List, Optional

from .models import (
    ResearchFinding,
    ResearchProject,
    ResearchStatus,
    Source,
    SourceType,
)
from .store import ResearchStore


class ResearchEngine:
    """Orchestrates automated research workflows."""

    def __init__(self, store: ResearchStore):
        self.store = store

    def create_project(
        self,
        topic: str,
        objective: str = "",
        max_sources: int = 20,
    ) -> ResearchProject:
        """Create a new research project."""
        queries = self._generate_search_queries(topic)
        project = ResearchProject(
            topic=topic,
            objective=objective or f"Research and analyze: {topic}",
            search_queries=queries,
            max_sources=max_sources,
            status=ResearchStatus.PLANNING,
        )
        return self.store.save_project(project)

    def add_source(
        self,
        project_id: str,
        title: str,
        content: str,
        url: str = "",
        source_type: SourceType = SourceType.WEB,
    ) -> Optional[ResearchProject]:
        """Add a source to an existing project."""
        project = self.store.get_project(project_id)
        if not project:
            return None

        source = Source(
            source_type=source_type,
            url=url,
            title=title,
            content=content,
            summary=self._extract_summary(content),
            relevance_score=self._score_relevance(content, project.topic),
            gathered_at=time.time(),
        )
        project.sources.append(source)
        project.status = ResearchStatus.GATHERING
        return self.store.save_project(project)

    def analyze(self, project_id: str) -> Optional[ResearchProject]:
        """Analyze gathered sources and extract findings."""
        project = self.store.get_project(project_id)
        if not project:
            return None

        project.status = ResearchStatus.ANALYZING
        project.findings = self._extract_findings(project)
        return self.store.save_project(project)

    def synthesize(self, project_id: str) -> Optional[ResearchProject]:
        """Synthesize findings into a research report."""
        project = self.store.get_project(project_id)
        if not project:
            return None

        project.status = ResearchStatus.SYNTHESIZING
        project.synthesis = self._build_synthesis(project)
        project.status = ResearchStatus.COMPLETED
        return self.store.save_project(project)

    def get_context_for_llm(self, project_id: str) -> str:
        """Format project data as context for an LLM prompt."""
        project = self.store.get_project(project_id)
        if not project:
            return ""

        parts = [f"# Research: {project.topic}\n"]
        if project.objective:
            parts.append(f"**Objective:** {project.objective}\n")

        if project.sources:
            parts.append("\n## Sources\n")
            for i, src in enumerate(project.sources, 1):
                parts.append(f"### [{i}] {src.title}")
                if src.url:
                    parts.append(f"URL: {src.url}")
                parts.append(f"Relevance: {src.relevance_score:.2f}")
                parts.append(src.summary or src.content[:500])
                parts.append("")

        if project.findings:
            parts.append("\n## Key Findings\n")
            for f in project.findings:
                conf = f"({f.confidence:.0%} confidence)"
                parts.append(f"- **{f.claim}** {conf}")

        if project.synthesis:
            parts.append(f"\n## Synthesis\n{project.synthesis}")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_search_queries(topic: str) -> List[str]:
        """Generate search queries from a topic."""
        queries = [topic]
        words = topic.lower().split()
        if len(words) > 2:
            queries.append(f"what is {topic}")
            queries.append(f"{topic} overview")
            queries.append(f"{topic} comparison")
        return queries

    @staticmethod
    def _extract_summary(content: str, max_length: int = 300) -> str:
        """Extract a brief summary from content."""
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        summary = ""
        for s in sentences:
            if len(summary) + len(s) > max_length:
                break
            summary += s + " "
        return summary.strip()

    @staticmethod
    def _score_relevance(content: str, topic: str) -> float:
        """Score how relevant content is to the topic (0-1)."""
        topic_words = set(topic.lower().split())
        content_lower = content.lower()
        if not topic_words:
            return 0.0
        matches = sum(1 for w in topic_words if w in content_lower)
        return matches / len(topic_words)

    @staticmethod
    def _extract_findings(project: ResearchProject) -> List[ResearchFinding]:
        """Extract key findings from sources."""
        findings: List[ResearchFinding] = []
        topic_words = set(project.topic.lower().split())

        for source in project.sources:
            sentences = re.split(r"(?<=[.!?])\s+", source.content)
            for sentence in sentences:
                s_lower = sentence.lower()
                overlap = sum(1 for w in topic_words if w in s_lower)
                if overlap >= max(1, len(topic_words) // 2) and len(sentence) > 30:
                    findings.append(
                        ResearchFinding(
                            claim=sentence.strip(),
                            evidence=[source.id],
                            confidence=overlap / len(topic_words) if topic_words else 0,
                            category="extracted",
                        ),
                    )

        # Deduplicate similar findings
        seen = set()
        unique: List[ResearchFinding] = []
        for f in findings:
            key = hashlib.md5(f.claim[:50].lower().encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                unique.append(f)

        return sorted(unique, key=lambda x: x.confidence, reverse=True)[:20]

    @staticmethod
    def _build_synthesis(project: ResearchProject) -> str:
        """Build a synthesized report from findings."""
        parts = [f"# Research Report: {project.topic}\n"]

        if project.objective:
            parts.append(f"## Objective\n{project.objective}\n")

        parts.append(
            f"## Summary\nAnalyzed {len(project.sources)} sources, "
            f"extracted {len(project.findings)} key findings.\n",
        )

        if project.findings:
            parts.append("## Key Findings\n")
            for i, f in enumerate(project.findings[:10], 1):
                parts.append(
                    f"{i}. {f.claim} (confidence: {f.confidence:.0%})",
                )

        if project.sources:
            parts.append("\n## Sources\n")
            for i, s in enumerate(project.sources, 1):
                ref = f"[{i}] {s.title}"
                if s.url:
                    ref += f" — {s.url}"
                parts.append(ref)

        return "\n".join(parts)
