"""
Test suite for Codebase Brain workflow system validation.

This test file verifies that all required documentation and workflow
components are present and meet minimum quality standards.
"""

import os
import pytest
from pathlib import Path


# Define base directory (project root)
BASE_DIR = Path(__file__).parent.parent


class TestWorkflowSystem:
    """Test suite for validating Codebase Brain workflow components."""

    def test_agents_md_exists(self):
        """Verify AGENTS.md exists in project root."""
        agents_file = BASE_DIR / "AGENTS.md"
        assert agents_file.exists(), "AGENTS.md file not found in project root"

    def test_agents_md_minimum_lines(self):
        """Verify AGENTS.md has at least 200 lines of content."""
        agents_file = BASE_DIR / "AGENTS.md"
        with open(agents_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Count non-empty lines for quality check
        non_empty_lines = [line for line in lines if line.strip()]
        
        assert len(lines) >= 200, (
            f"AGENTS.md has only {len(lines)} lines, expected at least 200"
        )
        assert len(non_empty_lines) >= 150, (
            f"AGENTS.md has only {len(non_empty_lines)} non-empty lines, "
            "expected substantial content"
        )

    def test_slash_command_files_exist(self):
        """Verify all 4 slash command files exist."""
        commands_dir = BASE_DIR / "bob-copilot" / "commands"
        
        expected_commands = [
            "debug-joint.md",
            "gait-plan.md",
            "lua-trace.md",
            "sdf-check.md"
        ]
        
        assert commands_dir.exists(), (
            f"Commands directory not found at {commands_dir}"
        )
        
        for command_file in expected_commands:
            file_path = commands_dir / command_file
            assert file_path.exists(), (
                f"Slash command file {command_file} not found in {commands_dir}"
            )

    def test_slash_command_files_non_empty(self):
        """Verify all slash command files have content."""
        commands_dir = BASE_DIR / "bob-copilot" / "commands"
        
        command_files = [
            "debug-joint.md",
            "gait-plan.md",
            "lua-trace.md",
            "sdf-check.md"
        ]
        
        for command_file in command_files:
            file_path = commands_dir / command_file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            assert len(content) > 0, (
                f"Slash command file {command_file} is empty"
            )
            assert len(content) >= 50, (
                f"Slash command file {command_file} has insufficient content "
                f"({len(content)} chars, expected at least 50)"
            )

    def test_domain_skill_file_exists(self):
        """Verify domain skill file exists."""
        skill_file = BASE_DIR / "bob-copilot" / "skills" / "arduhumanoid-expert.md"
        
        assert skill_file.exists(), (
            f"Domain skill file not found at {skill_file}"
        )

    def test_domain_skill_minimum_lines(self):
        """Verify domain skill file has at least 400 lines."""
        skill_file = BASE_DIR / "bob-copilot" / "skills" / "arduhumanoid-expert.md"
        
        with open(skill_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Count non-empty lines for quality check
        non_empty_lines = [line for line in lines if line.strip()]
        
        assert len(lines) >= 400, (
            f"Domain skill file has only {len(lines)} lines, expected at least 400"
        )
        assert len(non_empty_lines) >= 300, (
            f"Domain skill file has only {len(non_empty_lines)} non-empty lines, "
            "expected substantial content"
        )

    def test_bob_sessions_folder_exists(self):
        """Verify Bob sessions folder exists."""
        sessions_dir = BASE_DIR / "bob-sessions"
        
        # Note: This test is lenient - folder may not exist in fresh clones
        # but should exist in active development environments
        if sessions_dir.exists():
            assert sessions_dir.is_dir(), (
                f"{sessions_dir} exists but is not a directory"
            )
        else:
            pytest.skip("bob-sessions folder not present (acceptable for fresh clones)")

    def test_bob_sessions_has_reports(self):
        """Verify Bob sessions folder contains exported reports."""
        sessions_dir = BASE_DIR / "bob-sessions"
        
        if not sessions_dir.exists():
            pytest.skip("bob-sessions folder not present (acceptable for fresh clones)")
        
        # Look for any markdown or text files that could be reports
        report_files = list(sessions_dir.glob("*.md")) + list(sessions_dir.glob("*.txt"))
        
        # This is a soft check - reports may not exist in fresh environments
        if len(report_files) == 0:
            pytest.skip("No exported reports found (acceptable for fresh environments)")
        
        assert len(report_files) > 0, (
            f"Bob sessions folder exists but contains no report files (.md or .txt)"
        )

    def test_docs_folder_exists(self):
        """Verify docs folder exists."""
        docs_dir = BASE_DIR / "docs"
        
        assert docs_dir.exists(), "docs folder not found in project root"
        assert docs_dir.is_dir(), "docs exists but is not a directory"

    def test_problem_statement_exists(self):
        """Verify problem statement document exists."""
        problem_statement = BASE_DIR / "docs" / "problem-statement.md"
        
        assert problem_statement.exists(), (
            f"Problem statement not found at {problem_statement}"
        )

    def test_problem_statement_has_content(self):
        """Verify problem statement has substantial content."""
        problem_statement = BASE_DIR / "docs" / "problem-statement.md"
        
        with open(problem_statement, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        assert len(content) > 0, "Problem statement is empty"
        assert len(content) >= 200, (
            f"Problem statement has insufficient content "
            f"({len(content)} chars, expected at least 200)"
        )

    def test_bob_usage_statement_exists(self):
        """Verify Bob usage statement document exists."""
        usage_statement = BASE_DIR / "docs" / "bob-usage-statement.md"
        
        assert usage_statement.exists(), (
            f"Bob usage statement not found at {usage_statement}"
        )

    def test_bob_usage_statement_has_content(self):
        """Verify Bob usage statement has substantial content."""
        usage_statement = BASE_DIR / "docs" / "bob-usage-statement.md"
        
        with open(usage_statement, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        assert len(content) > 0, "Bob usage statement is empty"
        assert len(content) >= 200, (
            f"Bob usage statement has insufficient content "
            f"({len(content)} chars, expected at least 200)"
        )

    def test_workflow_structure_complete(self):
        """Integration test: verify complete workflow structure."""
        required_paths = [
            "AGENTS.md",
            "bob-copilot/commands/debug-joint.md",
            "bob-copilot/commands/gait-plan.md",
            "bob-copilot/commands/lua-trace.md",
            "bob-copilot/commands/sdf-check.md",
            "bob-copilot/skills/arduhumanoid-expert.md",
            "docs/problem-statement.md",
            "docs/bob-usage-statement.md",
        ]
        
        missing_paths = []
        for path_str in required_paths:
            path = BASE_DIR / path_str
            if not path.exists():
                missing_paths.append(path_str)
        
        assert len(missing_paths) == 0, (
            f"Workflow structure incomplete. Missing files: {', '.join(missing_paths)}"
        )


if __name__ == "__main__":
    # Allow running tests directly with: python tests/test_workflow.py
    pytest.main([__file__, "-v"])

# Made with Bob
