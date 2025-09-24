#!/usr/bin/env python3
"""
Module 2: GitHub Actions Integration - STARTER CODE
Extend your PR Agent with webhook handling and MCP Prompts for CI/CD workflows.
"""

import json
import os
import subprocess
from typing import Optional
from pathlib import Path
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("pr-agent-actions")

# PR template directory (shared between starter and solution)
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# Default PR templates
DEFAULT_TEMPLATES = {
    "bug.md": "Bug Fix",
    "feature.md": "Feature",
    "docs.md": "Documentation",
    "refactor.md": "Refactor",
    "test.md": "Test",
    "performance.md": "Performance",
    "security.md": "Security"
}

# TODO: Add path to events file where webhook_server.py stores events
EVENTS_FILE = Path(__file__).parent / "github_events.json"

# Type mapping for PR templates
TYPE_MAPPING = {
    "bug": "bug.md",
    "fix": "bug.md",
    "feature": "feature.md",
    "enhancement": "feature.md",
    "docs": "docs.md",
    "documentation": "docs.md",
    "refactor": "refactor.md",
    "cleanup": "refactor.md",
    "test": "test.md",
    "testing": "test.md",
    "performance": "performance.md",
    "optimization": "performance.md",
    "security": "security.md"
}


# ===== Module 1 Tools (Already includes output limiting fix from Module 1) =====

@mcp.tool()
async def analyze_file_changes(
    base_branch: str = "main",
    include_diff: bool = True,
    max_diff_lines: int = 500
) -> str:
    """Get the full diff and list of changed files in the current git repository.
    
    Args:
        base_branch: Base branch to compare against (default: main)
        include_diff: Include the full diff content (default: true)
        max_diff_lines: Maximum number of diff lines to include (default: 500)
    """
    try:
        # Get list of changed files
        files_result = subprocess.run(
            ["git", "diff", "--name-status", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get diff statistics
        stat_result = subprocess.run(
            ["git", "diff", "--stat", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True
        )
        
        # Get the actual diff if requested
        diff_content = ""
        truncated = False
        if include_diff:
            diff_result = subprocess.run(
                ["git", "diff", f"{base_branch}...HEAD"],
                capture_output=True,
                text=True
            )
            diff_lines = diff_result.stdout.split('\n')
            
            # Check if we need to truncate (learned from Module 1)
            if len(diff_lines) > max_diff_lines:
                diff_content = '\n'.join(diff_lines[:max_diff_lines])
                diff_content += f"\n\n... Output truncated. Showing {max_diff_lines} of {len(diff_lines)} lines ..."
                diff_content += "\n... Use max_diff_lines parameter to see more ..."
                truncated = True
            else:
                diff_content = diff_result.stdout
        
        # Get commit messages for context
        commits_result = subprocess.run(
            ["git", "log", "--oneline", f"{base_branch}..HEAD"],
            capture_output=True,
            text=True
        )
        
        analysis = {
            "base_branch": base_branch,
            "files_changed": files_result.stdout,
            "statistics": stat_result.stdout,
            "commits": commits_result.stdout,
            "diff": diff_content if include_diff else "Diff not included (set include_diff=true to see full diff)",
            "truncated": truncated,
            "total_diff_lines": len(diff_lines) if include_diff else 0
        }
        
        return json.dumps(analysis, indent=2)
        
    except subprocess.CalledProcessError as e:
        return json.dumps({"error": f"Git error: {e.stderr}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def get_pr_templates() -> str:
    """List available PR templates with their content."""
    templates = [
        {
            "filename": filename,
            "type": template_type,
            "content": (TEMPLATES_DIR / filename).read_text()
        }
        for filename, template_type in DEFAULT_TEMPLATES.items()
    ]
    
    return json.dumps(templates, indent=2)


@mcp.tool()
async def suggest_template(changes_summary: str, change_type: str) -> str:
    """Let Claude analyze the changes and suggest the most appropriate PR template.
    
    Args:
        changes_summary: Your analysis of what the changes do
        change_type: The type of change you've identified (bug, feature, docs, refactor, test, etc.)
    """
    
    # Get available templates
    templates_response = await get_pr_templates()
    templates = json.loads(templates_response)
    
    # Find matching template
    template_file = TYPE_MAPPING.get(change_type.lower(), "feature.md")
    selected_template = next(
        (t for t in templates if t["filename"] == template_file),
        templates[0]  # Default to first template if no match
    )
    
    suggestion = {
        "recommended_template": selected_template,
        "reasoning": f"Based on your analysis: '{changes_summary}', this appears to be a {change_type} change.",
        "template_content": selected_template["content"],
        "usage_hint": "Claude can help you fill out this template based on the specific changes in your PR."
    }
    
    return json.dumps(suggestion, indent=2)


# ===== Module 2: New GitHub Actions Tools =====

@mcp.tool()
async def get_recent_actions_events(limit: int = 10) -> str:
    """Get recent GitHub Actions events received via webhook.

    Args:
        limit: Maximum number of events to return (default: 10)
    """
    try:
        # Check if EVENTS_FILE exists
        if not EVENTS_FILE.exists():
            return json.dumps({
                "events": [],
                "message": "No events file found. Webhook server may not be running."
            })

        # Read the JSON file
        with open(EVENTS_FILE, 'r') as f:
            all_events = json.load(f)

        # Return the most recent events (up to limit)
        recent_events = all_events[-limit:] if isinstance(all_events, list) else []

        # Sort by timestamp if available (most recent first)
        if recent_events and all(isinstance(e, dict) and 'timestamp' in e for e in recent_events):
            recent_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        return json.dumps({
            "total_events": len(all_events) if isinstance(all_events, list) else 0,
            "returned_events": len(recent_events),
            "events": recent_events
        }, indent=2)

    except json.JSONDecodeError as e:
        return json.dumps({
            "error": f"Failed to parse events file: {str(e)}",
            "events": []
        })
    except Exception as e:
        return json.dumps({
            "error": f"Failed to read events: {str(e)}",
            "events": []
        })


@mcp.tool()
async def get_workflow_status(workflow_name: Optional[str] = None) -> str:
    """Get the current status of GitHub Actions workflows.

    Args:
        workflow_name: Optional specific workflow name to filter by
    """
    try:
        # Read events from EVENTS_FILE
        if not EVENTS_FILE.exists():
            return json.dumps({
                "workflows": {},
                "message": "No events file found. Webhook server may not be running."
            })

        with open(EVENTS_FILE, 'r') as f:
            all_events = json.load(f)

        # Filter events for workflow_run events
        workflow_events = []
        for event in (all_events if isinstance(all_events, list) else []):
            if isinstance(event, dict):
                # Check for workflow_run event type
                if event.get('event_type') == 'workflow_run' or 'workflow_run' in event:
                    workflow_events.append(event)
                # Also check if it has workflow-related fields
                elif any(key in event for key in ['workflow_name', 'workflow_id', 'status', 'conclusion']):
                    workflow_events.append(event)

        # If workflow_name provided, filter by that name
        if workflow_name:
            workflow_events = [
                e for e in workflow_events
                if e.get('workflow_name', '').lower() == workflow_name.lower() or
                   e.get('workflow_run', {}).get('name', '').lower() == workflow_name.lower()
            ]

        # Group by workflow and show latest status
        workflows = {}
        for event in workflow_events:
            # Extract workflow info from event structure
            wf_name = (
                event.get('workflow_name') or
                event.get('workflow_run', {}).get('name') or
                event.get('name') or
                'Unknown Workflow'
            )

            # Extract status and conclusion
            status = (
                event.get('status') or
                event.get('workflow_run', {}).get('status') or
                'unknown'
            )
            conclusion = (
                event.get('conclusion') or
                event.get('workflow_run', {}).get('conclusion') or
                'pending'
            )

            # Extract timestamp
            timestamp = (
                event.get('timestamp') or
                event.get('workflow_run', {}).get('created_at') or
                event.get('created_at') or
                ''
            )

            # Update workflow info if this is newer or first occurrence
            if wf_name not in workflows or timestamp > workflows[wf_name].get('last_update', ''):
                workflows[wf_name] = {
                    'name': wf_name,
                    'status': status,
                    'conclusion': conclusion,
                    'last_update': timestamp,
                    'run_id': event.get('workflow_run', {}).get('id') or event.get('run_id'),
                    'run_number': event.get('workflow_run', {}).get('run_number') or event.get('run_number'),
                    'event_name': event.get('workflow_run', {}).get('event') or event.get('event_name'),
                    'head_branch': event.get('workflow_run', {}).get('head_branch') or event.get('head_branch')
                }

        # Format response
        result = {
            'total_workflows': len(workflows),
            'workflows': workflows
        }

        if workflow_name and not workflows:
            result['message'] = f"No workflow found with name: {workflow_name}"
        elif not workflows:
            result['message'] = "No workflow events found in the events file"

        return json.dumps(result, indent=2)

    except json.JSONDecodeError as e:
        return json.dumps({
            "error": f"Failed to parse events file: {str(e)}",
            "workflows": {}
        })
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get workflow status: {str(e)}",
            "workflows": {}
        })


# ===== Module 2: MCP Prompts =====

@mcp.prompt()
async def analyze_ci_results():
    """Analyze recent CI/CD results and provide insights."""
    return """Analyze the recent CI/CD pipeline results and provide actionable insights.

Please follow these steps:

1. First, retrieve recent GitHub Actions events by calling get_recent_actions_events(limit=20) to get the last 20 events.

2. Then, get the current workflow status by calling get_workflow_status() to see the overall state of all workflows.

3. Based on the data, analyze and provide insights on:
   - Overall CI/CD health (success rate, failure patterns)
   - Most frequently failing workflows or jobs
   - Recent trends (improving, degrading, stable)
   - Common failure reasons if apparent from the data
   - Time patterns (are failures happening at specific times?)
   - Any workflows that are consistently successful vs problematic

4. Identify potential issues:
   - Flaky tests (intermittent failures)
   - Infrastructure problems (timeouts, resource issues)
   - Configuration issues (missing dependencies, wrong versions)
   - Code quality issues causing consistent failures

5. Provide actionable recommendations:
   - Which workflows need immediate attention
   - Quick wins to improve CI/CD reliability
   - Suggested next steps for investigation
   - Best practices that could help

Format your response as a structured report with clear sections and bullet points for easy reading.
Focus on actionable insights rather than just describing the data."""


@mcp.prompt()
async def create_deployment_summary():
    """Generate a deployment summary for team communication."""
    return """Generate a comprehensive deployment summary suitable for team communication and stakeholder updates.

Please follow these steps:

1. Gather deployment information:
   - Call get_recent_actions_events(limit=50) to retrieve recent deployment-related events
   - Call get_workflow_status() to check the status of deployment workflows
   - Call analyze_file_changes() to understand what code changes are being deployed

2. Identify deployment activities:
   - Look for deployment-related workflows (deploy, release, production, staging)
   - Find successful deployments vs failed attempts
   - Identify which environments were targeted (production, staging, dev)
   - Note deployment timestamps and durations

3. Create a deployment summary that includes:

   **Deployment Overview:**
   - Deployment window/timeframe
   - Number of deployments attempted/successful
   - Environments affected
   - Overall deployment success rate

   **What Was Deployed:**
   - Key features or fixes included
   - Number of commits/PRs included
   - Major code changes summary
   - Configuration or infrastructure changes

   **Deployment Status:**
   - Current production version/tag
   - Rollback status if applicable
   - Any ongoing deployments
   - Health check results

   **Issues & Resolutions:**
   - Any deployment failures and their causes
   - Rollbacks performed (if any)
   - Hotfixes applied
   - Incident reports

   **Impact Assessment:**
   - Services affected
   - Expected performance improvements
   - Known issues or limitations
   - User-facing changes

   **Next Steps:**
   - Pending deployments
   - Follow-up tasks
   - Monitoring requirements
   - Team action items

4. Format for different audiences:
   - Executive Summary (2-3 sentences for leadership)
   - Technical Details (for engineering team)
   - User Impact Summary (for support/customer success)

Use clear headings, bullet points, and concise language. Include relevant metrics and timestamps.
Highlight any critical issues or successes that need immediate attention."""


@mcp.prompt()
async def generate_pr_status_report():
    """Generate a comprehensive PR status report including CI/CD results."""
    return """Generate a comprehensive Pull Request status report that combines code changes analysis with CI/CD pipeline results.

Please follow these steps to create a complete PR status report:

1. Analyze the code changes:
   - Call analyze_file_changes(include_diff=true) to get the full diff and changed files
   - Identify the type of changes (feature, bugfix, refactor, etc.)
   - Note the scope and impact of changes

2. Check CI/CD pipeline status:
   - Call get_recent_actions_events(limit=10) to get recent CI/CD events for this PR
   - Call get_workflow_status() to check all workflow statuses
   - Identify any failed checks or tests

3. Suggest appropriate PR template:
   - Based on the changes, call suggest_template() with your analysis
   - Use the suggested template as a guide for the report structure

4. Generate a comprehensive PR status report with these sections:

   **PR Overview:**
   - PR title and number (if available)
   - Branch information (source -> target)
   - Author and reviewers
   - Current status (Draft/Ready/Approved/Merged)
   - Created/Updated timestamps

   **Changes Summary:**
   - Total files changed, lines added/removed
   - Type of change (feature/fix/docs/refactor)
   - Main components affected
   - Breaking changes (if any)

   **Code Analysis:**
   - Key modifications by file/component
   - Potential impact areas
   - Dependencies updated
   - Database migrations (if any)
   - Configuration changes

   **CI/CD Pipeline Status:**
   - Build status: [Pass/Fail/Running]
   - Test results: X passed, Y failed, Z skipped
   - Code coverage: Current vs Previous
   - Linting/Formatting checks
   - Security scans results
   - Performance benchmarks (if applicable)

   **Quality Checks:**
   - Code review status
   - Required approvals met
   - Merge conflicts status
   - Documentation updates included
   - Tests added/modified

   **Risk Assessment:**
   - Risk level: [Low/Medium/High]
   - Potential issues identified
   - Rollback strategy
   - Testing recommendations

   **Action Items:**
   - Failed checks that need fixing
   - Required reviews pending
   - Merge blockers
   - Follow-up tasks post-merge

   **Ready for Merge Checklist:**
   - [ ] All CI checks passing
   - [ ] Code review approved
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No merge conflicts
   - [ ] Performance impact assessed

5. Provide recommendations:
   - Whether the PR is ready to merge
   - Any concerns that should be addressed
   - Suggested next steps

Format the report with clear sections, use checkmarks and status indicators, and highlight any critical issues in bold.
Make the report scannable with good use of formatting and emojis for status (✅ ❌ ⚠️ 🔄)."""


@mcp.prompt()
async def troubleshoot_workflow_failure():
    """Help troubleshoot a failing GitHub Actions workflow."""
    return """Help diagnose and troubleshoot a failing GitHub Actions workflow using systematic debugging approach.

Please follow this troubleshooting process:

1. **Gather Initial Information:**
   - Call get_workflow_status() to identify which workflows are failing
   - Call get_recent_actions_events(limit=30) to get detailed event history
   - Note the workflow name, failure time, and frequency of failures

2. **Identify Failure Pattern:**
   - Determine failure type:
     * Consistent failure (fails every time)
     * Intermittent/flaky failure (sometimes passes, sometimes fails)
     * Recent regression (was working, now broken)
     * Environment-specific (only fails in certain conditions)

   - Check failure timing:
     * Started failing after specific commit
     * Fails at specific time of day
     * Fails after dependency update
     * Random failures

3. **Analyze Error Details:**
   Look for specific error indicators:

   **Common Build Failures:**
   - Missing dependencies or packages
   - Version conflicts
   - Compilation errors
   - Docker image issues
   - Out of memory/disk space

   **Test Failures:**
   - Failing unit/integration tests
   - Timeout issues
   - Database connection problems
   - API rate limiting
   - Environment variable issues

   **Deployment Failures:**
   - Authentication/permission errors
   - Network connectivity issues
   - Invalid configuration
   - Resource constraints
   - Service unavailability

   **Infrastructure Issues:**
   - GitHub Actions runner problems
   - Third-party service outages
   - Rate limiting (GitHub API, npm, etc.)
   - Caching issues

4. **Systematic Debugging Steps:**

   **Step 1: Review Error Logs**
   - Identify the exact error message
   - Check which step in the workflow failed
   - Look for stack traces or error codes
   - Note any warnings before the failure

   **Step 2: Check Recent Changes**
   - Call analyze_file_changes() to review recent code changes
   - Check if workflow file itself was modified
   - Review dependency updates
   - Look for configuration changes

   **Step 3: Validate Configuration**
   - Workflow syntax correctness
   - Environment variables properly set
   - Secrets and credentials valid
   - Permissions and access rights
   - Resource limits adequate

   **Step 4: Test Isolation**
   - Can the failing step run locally?
   - Does it fail in all branches or just specific ones?
   - Does re-running the workflow help?
   - Can you reproduce in a minimal example?

5. **Common Solutions by Error Type:**

   **For Dependency Issues:**
   - Clear cache and rebuild
   - Pin specific versions
   - Update lock files
   - Check compatibility matrix

   **For Test Failures:**
   - Increase timeouts
   - Add retry logic
   - Fix test data/fixtures
   - Update test expectations
   - Check for race conditions

   **For Permission Errors:**
   - Verify GitHub tokens/secrets
   - Check repository permissions
   - Update workflow permissions
   - Validate service accounts

   **For Resource Issues:**
   - Optimize memory usage
   - Clean up disk space
   - Use larger runners
   - Implement artifact cleanup

6. **Provide Actionable Recommendations:**

   **Immediate Actions:**
   - Quick fixes that can be tried right away
   - Workarounds to unblock the pipeline
   - How to re-run with additional debugging

   **Investigation Steps:**
   - Specific logs to examine
   - Tests to run locally
   - Configuration to verify
   - External services to check

   **Long-term Improvements:**
   - Add better error handling
   - Implement retry mechanisms
   - Improve logging and monitoring
   - Add workflow status badges
   - Set up notifications

7. **Generate Troubleshooting Report:**

   Format as:
   ```
   🔍 WORKFLOW FAILURE DIAGNOSIS

   Workflow: [name]
   Status: [current status]
   Failure Rate: [X% over last Y runs]

   ❌ ROOT CAUSE ANALYSIS:
   [Identified issue]

   🔧 RECOMMENDED FIX:
   [Step-by-step solution]

   ⚡ QUICK WORKAROUND:
   [Temporary solution if available]

   📋 VERIFICATION STEPS:
   [How to confirm the fix works]
   ```

Focus on providing specific, actionable solutions rather than generic advice.
Prioritize fixes by likelihood and ease of implementation."""


if __name__ == "__main__":
    print("Starting PR Agent MCP server...")
    print("NOTE: Run webhook_server.py in a separate terminal to receive GitHub events")
    mcp.run()