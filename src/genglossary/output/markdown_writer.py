"""Markdown writer for glossary output."""

from datetime import datetime
from pathlib import Path

from genglossary.models.glossary import Glossary
from genglossary.models.term import Term, TermOccurrence


class MarkdownWriter:
    """Writes glossary to Markdown format.

    Generates a well-formatted Markdown document with:
    - Metadata header (generation date, document count, model)
    - Term entries with definitions
    - Occurrence references with file paths and line numbers
    - Related term links
    """

    def write(self, glossary: Glossary, output_path: str) -> None:
        """Write glossary to a Markdown file.

        Args:
            glossary: The Glossary object to write.
            output_path: Path to the output Markdown file.
        """
        output_file = Path(output_path)

        # Create parent directories if they don't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Generate markdown content
        content = self._generate_markdown(glossary)

        # Write to file
        output_file.write_text(content, encoding="utf-8")

    def _generate_markdown(self, glossary: Glossary) -> str:
        """Generate complete Markdown content.

        Args:
            glossary: The Glossary object to format.

        Returns:
            Complete Markdown content as string.
        """
        sections = []

        # Header
        sections.append(self._format_header(glossary))

        # Terms
        sections.append("## 用語一覧\n")

        # Sort terms alphabetically for consistent output
        sorted_terms = sorted(glossary.terms.values(), key=lambda t: t.name)

        for term in sorted_terms:
            sections.append(self._format_term(term))
            sections.append("---\n")

        return "\n".join(sections)

    def _format_header(self, glossary: Glossary) -> str:
        """Format the glossary header with metadata.

        Args:
            glossary: The Glossary object.

        Returns:
            Formatted header string.
        """
        lines = ["# 用語集\n"]

        # Generated date
        if "generated_at" in glossary.metadata:
            generated_at = glossary.metadata["generated_at"]
            # Parse ISO format and format for display
            try:
                dt = datetime.fromisoformat(generated_at)
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"生成日時: {formatted_date}")
            except (ValueError, TypeError):
                lines.append(f"生成日時: {generated_at}")
        else:
            # Use current time if not specified
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"生成日時: {now}")

        # Document count
        if "document_count" in glossary.metadata:
            lines.append(f"ドキュメント数: {glossary.metadata['document_count']}")

        # Model
        if "model" in glossary.metadata:
            lines.append(f"モデル: {glossary.metadata['model']}")

        return "\n".join(lines) + "\n"

    def _format_term(self, term: Term) -> str:
        """Format a single term entry.

        Args:
            term: The Term object to format.

        Returns:
            Formatted term entry as string.
        """
        lines = []

        # Term heading
        lines.append(f"### {term.name}\n")

        # Definition
        if term.definition:
            lines.append(f"**定義**: {term.definition}\n")

        # Occurrences
        occurrences_text = self._format_occurrences(term.occurrences)
        if occurrences_text:
            lines.append(occurrences_text)

        # Related terms
        related_terms_text = self._format_related_terms(term.related_terms)
        if related_terms_text:
            lines.append(related_terms_text)

        return "\n".join(lines)

    def _format_occurrences(self, occurrences: list[TermOccurrence]) -> str:
        """Format occurrences list.

        Args:
            occurrences: List of TermOccurrence objects.

        Returns:
            Formatted occurrences section, or empty string if no occurrences.
        """
        if not occurrences:
            return ""

        lines = ["**出現箇所**:"]
        for occ in occurrences:
            lines.append(f"- `{occ.document_path}:{occ.line_number}` - \"{occ.context}\"")

        return "\n".join(lines) + "\n"

    def _format_related_terms(self, related_terms: list[str]) -> str:
        """Format related terms as Markdown links.

        Args:
            related_terms: List of related term names.

        Returns:
            Formatted related terms section, or empty string if no related terms.
        """
        if not related_terms:
            return ""

        # Create Markdown links for each related term
        links = [f"[{term}](#{term})" for term in related_terms]

        return "**関連用語**: " + ", ".join(links) + "\n"
