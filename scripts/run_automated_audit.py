#!/usr/bin/env python3
"""Run an automated code audit using aider.

This script leverages aider to analyze the codebase and generate a comprehensive report.
"""

import datetime
import subprocess
import sys
import tempfile
from pathlib import Path


class AiderAuditor:
    """Automated code auditor that uses aider to analyze a codebase."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.audit_sections = [
            (
                "project_structure",
                "Analyze the project structure, directory organization, and "
                "overall architecture",
            ),
            (
                "code_quality",
                "Analyze Python code quality, PEP 8 compliance, type hints, "
                "docstrings, and modularity",
            ),
            (
                "documentation",
                "Review documentation completeness including README, API docs, "
                "and usage examples",
            ),
            (
                "git_compliance",
                "Check git practices including commit messages, branching strategy, "
                ".gitignore settings, and git hooks",
            ),
            ("workflow", "Check workflow compliance with development standards"),
            (
                "security",
                "Audit security considerations including authentication, API security, "
                "and database protection",
            ),
            ("testing", "Evaluate test coverage, quality, and organization"),
            ("configuration", "Review configuration management and deployment setup"),
        ]

    def create_aider_prompt(self, section: str, description: str) -> str:
        """Create a focused prompt for aider's codebase analysis."""
        base_prompt = f"""
Please analyze the codebase focusing on {section}. {description}
Provide findings in this format:
1. Status: (✅ Good, ⚠️ Needs Improvement, or ❌ Critical Issues)
2. Key Findings: (list bullet points)
3. Recommendations: (list specific actionable items)
Use factual observations and avoid subjective statements.
Analyze only the code and files present in the repository.
"""

        # Add specific guidance for git compliance checks
        if section == "git_compliance":
            base_prompt += """
For git compliance, specifically check:
- Presence and quality of .gitignore file
- Git hook configurations in .git/hooks
- Commit message patterns and consistency
- Branch naming conventions and strategy
- Git workflow documentation
- Git attributes configuration
- Large file handling (Git LFS usage if needed)
- Sensitive data exposure in git history
"""

        return base_prompt

    def run_aider_analysis(self, prompt: str) -> str:
        """Run aider with the given prompt and return its output."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt") as prompt_file:
            prompt_file.write(prompt)
            prompt_file.flush()

            try:
                # Run aider with safety flags to prevent git operations
                result = subprocess.run(
                    [
                        "aider",
                        "--no-auto-commit",  # Prevent automatic commits
                        "--no-git",  # Prevent git operations
                        "--model",
                        "gemini/gemini-2.0-flash",  # Use Gemini model
                        "--input-file",
                        prompt_file.name,
                    ],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )
                return result.stdout
            except subprocess.TimeoutExpired:
                return "Analysis timed out"
            except subprocess.CalledProcessError as e:
                return f"Error running analysis: {str(e)}"

    def parse_aider_output(self, output: str) -> dict:
        """Parse aider's output into structured findings."""
        # Extract the status emoji if present
        status = "⚠️"  # default status
        if "✅" in output:
            status = "✅"
        elif "❌" in output:
            status = "❌"

        # Extract findings and recommendations
        findings = []
        recommendations = []

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                if "recommend" in line.lower():
                    recommendations.append(line[2:])
                else:
                    findings.append(line[2:])

        return {
            "status": status,
            "findings": findings,
            "recommendations": recommendations,
        }

    def generate_report(self) -> str:
        """Generate the full audit report by running aider analysis for each section."""
        now = datetime.datetime.now()

        report = [
            "# GraphRAG Project Audit Report",
            f"**Date:** {now.strftime('%d/%m/%Y')}",
            "**Auditor:** Aider Software Audit Mode\n",
        ]

        all_recommendations = []
        overall_score = 0
        sections_analyzed = 0

        for section_num, (section, description) in enumerate(self.audit_sections, 1):
            print(f"Analyzing {section}...")

            prompt = self.create_aider_prompt(section, description)
            output = self.run_aider_analysis(prompt)
            results = self.parse_aider_output(output)

            # Add section to report
            report.extend(
                [
                    f"## {section_num}. {section.replace('_', ' ').title()}",
                    f"{results['status']} **Analysis Results**",
                ]
            )

            findings = results["findings"]
            if findings:
                report.append("")
                report.extend([f"- {finding}" for finding in findings])

            recommendations = results["recommendations"]
            if recommendations:
                report.extend(["", "**Recommendations:**"])
                report.extend([f"- {rec}" for rec in recommendations])
                all_recommendations.extend(recommendations)

            report.append("")  # Add blank line between sections

            # Calculate section score
            if results["status"] == "✅":
                score = 10
            elif results["status"] == "⚠️":
                score = 5
            else:
                score = 0

            overall_score += score
            sections_analyzed += 1

        # Add full recommendations section
        if all_recommendations:
            report.extend(["## Full Recommendations", ""])
            for i, rec in enumerate(all_recommendations, 1):
                report.append(f"{i}. {rec}")

        # Calculate and add overall rating
        if sections_analyzed > 0:
            final_score = overall_score / sections_analyzed
            rating = self._get_rating(final_score)
            report.extend(["", f"**Overall Rating:** {final_score:.1f}/10 - {rating}"])

        return "\n".join(report)

    def _get_rating(self, score: float) -> str:
        """Convert a numerical score to a rating description."""
        if score >= 9:
            return "Excellent"
        if score >= 7:
            return "Good"
        if score >= 5:
            return "Fair"
        return "Needs Improvement"


def main() -> None:
    """Execute the automated audit using aider."""
    try:
        # Get project root
        project_root = Path(__file__).parent.parent

        # Check if aider is installed
        try:
            subprocess.run(["aider", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: aider is not installed or not found in PATH")
            print("Please install aider with: pip install aider")
            sys.exit(1)

        # Initialize auditor
        print("Initializing aider-based audit...")
        auditor = AiderAuditor(project_root)

        # Generate and save report
        print("Generating report...")
        report = auditor.generate_report()

        output_path = project_root / "project" / "audit" / "audit-report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Audit report generated at: {output_path}")

    except Exception as e:
        print(f"Error during audit: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
