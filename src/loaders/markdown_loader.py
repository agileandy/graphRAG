"""Markdown document loader for GraphRAG project."""

import os
from typing import Any

import markdown


class MarkdownLoader:
    """Loader for Markdown documents."""

    @staticmethod
    def load(file_path: str) -> tuple[str, dict[str, Any]]:
        """Load a Markdown document.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Tuple of (text, metadata)

        """
        # Read the Markdown file
        with open(file_path, encoding="utf-8") as f:
            md_content = f.read()

        # Extract metadata from frontmatter if present
        metadata = MarkdownLoader._extract_frontmatter(md_content)

        # Convert Markdown to plain text
        text = MarkdownLoader._convert_to_text(md_content)

        # Add file metadata
        metadata.update(
            {
                "title": metadata.get(
                    "title", os.path.splitext(os.path.basename(file_path))[0]
                ),
                "source": "Markdown File",
                "file_path": file_path,
            }
        )

        return text, metadata

    @staticmethod
    def _extract_frontmatter(md_content: str) -> dict[str, Any]:
        """Extract YAML frontmatter from Markdown content.

        Args:
            md_content: Markdown content

        Returns:
            Extracted metadata

        """
        metadata = {}

        # Check for YAML frontmatter (between --- delimiters)
        if md_content.startswith("---"):
            try:
                # Find the end of the frontmatter
                end_idx = md_content.find("---", 3)
                if end_idx != -1:
                    # Extract the frontmatter content
                    frontmatter = md_content[3:end_idx].strip()

                    # Parse the frontmatter as YAML
                    import yaml

                    metadata = yaml.safe_load(frontmatter)

                    # Remove the frontmatter from the content
                    md_content = md_content[end_idx + 3 :].strip()
            except Exception as e:
                print(f"Error parsing frontmatter: {e}")

        return metadata

    @staticmethod
    def _convert_to_text(md_content: str) -> str:
        """Convert Markdown to plain text.

        Args:
            md_content: Markdown content

        Returns:
            Plain text

        """
        # Convert Markdown to HTML
        html = markdown.markdown(md_content)

        # Simple HTML to text conversion
        # This is a basic implementation - for production, consider using a more robust HTML-to-text converter
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Fix spacing
        text = re.sub(r"\s+", " ", text)

        # Handle special characters
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&quot;", '"')

        return text.strip()
