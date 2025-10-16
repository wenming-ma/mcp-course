#!/usr/bin/env python3
"""
MCP Server with Resources capability - Team Guidelines Example
This server exposes team documentation as MCP Resources
"""

import asyncio
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("team-guidelines-server")

# Define the base path for team guidelines
# Use dynamic path based on script location
REPO_ROOT = Path(__file__).parent.parent.resolve()
GUIDELINES_PATH = REPO_ROOT / "projects" / "unit3" / "team-guidelines"
TEMPLATES_PATH = REPO_ROOT / "projects" / "unit3" / "templates"

# Resource 1: PR Guidelines
@mcp.resource("guidelines://pr-guidelines")
async def get_pr_guidelines() -> str:
    """
    Get the Pull Request guidelines for the team.
    Contains rules for PR size, description, review process, and more.
    """
    file_path = GUIDELINES_PATH / "pr-guidelines.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "PR Guidelines file not found"

# Resource 2: Coding Standards
@mcp.resource("guidelines://coding-standards")
async def get_coding_standards() -> str:
    """
    Get the team's coding standards.
    Includes Python style guide, Git commit conventions, testing requirements.
    """
    file_path = GUIDELINES_PATH / "coding-standards.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Coding Standards file not found"

# Resource 3: Bug Report Template
@mcp.resource("templates://bug-report")
async def get_bug_template() -> str:
    """
    Get the bug report template.
    Standard format for reporting issues.
    """
    file_path = TEMPLATES_PATH / "bug.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Bug template file not found"

# Resource 4: Feature Request Template
@mcp.resource("templates://feature-request")
async def get_feature_template() -> str:
    """
    Get the feature request template.
    Standard format for proposing new features.
    """
    file_path = TEMPLATES_PATH / "feature.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Feature template file not found"

# Resource 5: Documentation Template
@mcp.resource("templates://documentation")
async def get_docs_template() -> str:
    """
    Get the documentation template.
    Standard format for creating documentation.
    """
    file_path = TEMPLATES_PATH / "docs.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Documentation template file not found"

# Resource 6: Performance Issue Template
@mcp.resource("templates://performance")
async def get_performance_template() -> str:
    """
    Get the performance issue template.
    Standard format for reporting performance problems.
    """
    file_path = TEMPLATES_PATH / "performance.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Performance template file not found"

# Resource 7: Security Issue Template
@mcp.resource("templates://security")
async def get_security_template() -> str:
    """
    Get the security issue template.
    Standard format for reporting security vulnerabilities.
    """
    file_path = TEMPLATES_PATH / "security.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Security template file not found"

# Resource 8: Test Template
@mcp.resource("templates://test")
async def get_test_template() -> str:
    """
    Get the test template.
    Standard format for test planning and documentation.
    """
    file_path = TEMPLATES_PATH / "test.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Test template file not found"

# Resource 9: Refactoring Template
@mcp.resource("templates://refactor")
async def get_refactor_template() -> str:
    """
    Get the refactoring template.
    Standard format for proposing code refactoring.
    """
    file_path = TEMPLATES_PATH / "refactor.md"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return "Refactor template file not found"

# Dynamic Resource: List all available guidelines
@mcp.resource("guidelines://list")
async def list_all_guidelines() -> str:
    """
    List all available team guidelines and templates.
    Provides an overview of all documentation resources.
    """
    guidelines = []

    # List guidelines
    guidelines.append("## Team Guidelines\n")
    for file in GUIDELINES_PATH.glob("*.md"):
        guidelines.append(f"- {file.stem}: guidelines://{file.stem}")

    # List templates
    guidelines.append("\n## Templates\n")
    for file in TEMPLATES_PATH.glob("*.md"):
        guidelines.append(f"- {file.stem}: templates://{file.stem}")

    return "\n".join(guidelines)

# Optional: Add a tool to search within resources
@mcp.tool()
async def search_guidelines(keyword: str) -> str:
    """
    Search for a keyword across all team guidelines and templates.

    Args:
        keyword: The keyword to search for (case-insensitive)

    Returns:
        Search results with matching lines and file sources
    """
    results = []
    keyword_lower = keyword.lower()

    # Search in guidelines
    for file in GUIDELINES_PATH.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if keyword_lower in line.lower():
                results.append(f"[{file.stem}:{i}] {line.strip()}")

    # Search in templates
    for file in TEMPLATES_PATH.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if keyword_lower in line.lower():
                results.append(f"[{file.stem}:{i}] {line.strip()}")

    if results:
        return f"Found {len(results)} matches for '{keyword}':\n\n" + "\n".join(results[:20])
    else:
        return f"No matches found for '{keyword}'"

# Optional: Add a tool to get resource metadata
@mcp.tool()
async def get_resource_info() -> str:
    """
    Get information about all available resources.

    Returns:
        A summary of all resources with their URIs and descriptions
    """
    info = [
        "## Available Resources\n",
        "### Team Guidelines",
        "- `guidelines://pr-guidelines` - Pull Request guidelines",
        "- `guidelines://coding-standards` - Coding standards and conventions",
        "- `guidelines://list` - List all available resources",
        "",
        "### Templates",
        "- `templates://bug-report` - Bug report template",
        "- `templates://feature-request` - Feature request template",
        "- `templates://documentation` - Documentation template",
        "- `templates://performance` - Performance issue template",
        "- `templates://security` - Security issue template",
        "- `templates://test` - Test template",
        "- `templates://refactor` - Refactoring template",
        "",
        "### Tools",
        "- `search_guidelines` - Search across all documentation",
        "- `get_resource_info` - Get this help information"
    ]

    return "\n".join(info)

if __name__ == "__main__":
    # Run the server
    mcp.run()