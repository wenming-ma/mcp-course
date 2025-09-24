#!/usr/bin/env python3
"""
Module 1: Basic MCP Server - Starter Code
TODO: Implement tools for analyzing git changes and suggesting PR templates
"""

import json
import os
from pathlib import Path

import git
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("pr-agent")

# PR template directory (shared across all modules)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


# TODO: Implement tool functions here
# Example structure for a tool:
# @mcp.tool()
# async def analyze_file_changes(base_branch: str = "main", include_diff: bool = True) -> str:
#     """Get the full diff and list of changed files in the current git repository.
#
#     Args:
#         base_branch: Base branch to compare against (default: main)
#         include_diff: Include the full diff content (default: true)
#     """
#     # Your implementation here
#     pass

# Minimal stub implementations so the server runs
# TODO: Replace these with your actual implementations


def _get_changed_files(base_branch: str, repo_path: str = None) -> list:
    """Get list of changed files."""
    try:
        if repo_path is None:
            repo_path = os.getcwd()
            while repo_path != os.path.dirname(repo_path):
                if os.path.exists(os.path.join(repo_path, '.git')):
                    break
                repo_path = os.path.dirname(repo_path)

        repo = git.Repo(repo_path)
        diff = repo.git.diff("--name-only", f"{base_branch}...HEAD")
        return diff.strip().split("\n") if diff.strip() else []
    except Exception:
        return []


@mcp.tool()
async def analyze_file_changes(
    base_branch: str = "main", include_diff: bool = True, max_diff_lines: int = 500
) -> str:
    """Analyze file changes with smart output limiting.

    Args:
        base_branch: Branch to compare against
        include_diff: Whether to include the actual diff
        max_diff_lines: Maximum diff lines to include (default 500)
    """
    try:
        # Find git repo root
        repo_path = os.getcwd()
        while repo_path != os.path.dirname(repo_path):
            if os.path.exists(os.path.join(repo_path, '.git')):
                break
            repo_path = os.path.dirname(repo_path)

        # Use GitPython
        repo = git.Repo(repo_path)

        # Get changed files
        files_changed = _get_changed_files(base_branch, repo_path)

        # Get stats
        stats = repo.git.diff("--stat", f"{base_branch}...HEAD")

        if include_diff:
            # Get diff
            diff_output = repo.git.diff(f"{base_branch}...HEAD")
            diff_lines = diff_output.split("\n")

            # Smart truncation
            if len(diff_lines) > max_diff_lines:
                truncated_diff = "\n".join(diff_lines[:max_diff_lines])
                truncated_diff += f"\n\n... Output truncated. Showing {max_diff_lines} of {len(diff_lines)} lines ..."
                diff_output = truncated_diff
        else:
            diff_output = "Use include_diff=true to see diff"
            diff_lines = []

        return json.dumps({
            "stats": stats,
            "total_lines": len(diff_lines) if include_diff else 0,
            "diff": diff_output,
            "files_changed": files_changed,
        })

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_pr_templates() -> str:
    """List available PR templates with their content."""
    # TODO: Implement this tool
    return json.dumps(
        {"error": "Not implemented yet", "hint": "Read templates from TEMPLATES_DIR"}
    )


@mcp.tool()
async def suggest_template(changes_summary: str, change_type: str) -> str:
    """Let Claude analyze the changes and suggest the most appropriate PR template.

    Args:
        changes_summary: Your analysis of what the changes do
        change_type: The type of change you've identified (bug, feature, docs, refactor, test, etc.)
    """
    # TODO: Implement this tool
    return json.dumps(
        {"error": "Not implemented yet", "hint": "Map change_type to templates"}
    )


if __name__ == "__main__":
    mcp.run()
