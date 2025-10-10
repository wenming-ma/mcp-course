#!/usr/bin/env python3
"""
MCP Client Example - Demonstrates how application logic decides when to use Resources
This shows how the client (Host application) programmatically decides when to load resources
"""

import asyncio
from enum import Enum
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from pydantic import AnyUrl

class UserAction(Enum):
    """User actions that trigger resource loading"""
    OPEN_PR_EDITOR = "open_pr_editor"
    START_CODING = "start_coding"
    REPORT_BUG = "report_bug"
    REQUEST_FEATURE = "request_feature"
    VIEW_GUIDELINES = "view_guidelines"
    START_REFACTORING = "start_refactoring"

class ApplicationContext:
    """Simulates application state and context"""
    def __init__(self):
        self.current_file = None
        self.current_task = None
        self.loaded_resources = []

class SmartCodeEditor:
    """
    Example Host application that decides when to load Resources
    based on application state and user actions
    """

    def __init__(self, session: ClientSession):
        self.session = session
        self.context = ApplicationContext()
        self.ai_context = []  # Context provided to LLM

    async def handle_user_action(self, action: UserAction, **kwargs):
        """
        Application logic that decides which resources to load
        based on user actions - NO LLM INVOLVED IN THIS DECISION
        """
        print(f"\n=== User Action: {action.value} ===")

        if action == UserAction.OPEN_PR_EDITOR:
            # Application logic: When user opens PR editor, load PR guidelines
            print("Application Decision: User is creating a PR, loading PR guidelines...")
            pr_guidelines = await self.session.read_resource(
                AnyUrl("guidelines://pr-guidelines")
            )
            self.ai_context.append({
                "type": "resource",
                "content": pr_guidelines.contents[0].text if pr_guidelines.contents else "",
                "reason": "User opened PR editor"
            })
            print("[OK] PR guidelines loaded into AI context")

        elif action == UserAction.START_CODING:
            # Application logic: When user starts coding, load coding standards
            file_type = kwargs.get('file_type', 'python')
            print(f"Application Decision: User is coding in {file_type}, loading coding standards...")
            coding_standards = await self.session.read_resource(
                AnyUrl("guidelines://coding-standards")
            )
            self.ai_context.append({
                "type": "resource",
                "content": coding_standards.contents[0].text if coding_standards.contents else "",
                "reason": f"User started coding in {file_type}"
            })
            print("[OK] Coding standards loaded into AI context")

        elif action == UserAction.REPORT_BUG:
            # Application logic: When user wants to report bug, load bug template
            print("Application Decision: User reporting bug, loading bug template...")
            bug_template = await self.session.read_resource(
                AnyUrl("templates://bug-report")
            )
            self.ai_context.append({
                "type": "resource",
                "content": bug_template.contents[0].text if bug_template.contents else "",
                "reason": "User initiated bug report"
            })
            print("[OK] Bug template loaded and ready to use")

        elif action == UserAction.REQUEST_FEATURE:
            # Application logic: When user requests feature, load feature template
            print("Application Decision: User requesting feature, loading feature template...")
            feature_template = await self.session.read_resource(
                AnyUrl("templates://feature-request")
            )
            self.ai_context.append({
                "type": "resource",
                "content": feature_template.contents[0].text if feature_template.contents else "",
                "reason": "User initiated feature request"
            })
            print("[OK] Feature template loaded")

        elif action == UserAction.START_REFACTORING:
            # Application logic: Multiple resources needed for refactoring
            print("Application Decision: User starting refactoring, loading relevant resources...")

            # Load refactoring template
            refactor_template = await self.session.read_resource(
                AnyUrl("templates://refactor")
            )

            # Also load coding standards for reference
            coding_standards = await self.session.read_resource(
                AnyUrl("guidelines://coding-standards")
            )

            self.ai_context.extend([
                {
                    "type": "resource",
                    "content": refactor_template.contents[0].text if refactor_template.contents else "",
                    "reason": "User initiated refactoring"
                },
                {
                    "type": "resource",
                    "content": coding_standards.contents[0].text if coding_standards.contents else "",
                    "reason": "Coding standards for refactoring reference"
                }
            ])
            print("[OK] Refactoring template and coding standards loaded")

        elif action == UserAction.VIEW_GUIDELINES:
            # Application logic: Show all available guidelines
            print("Application Decision: User wants to view all guidelines...")
            guidelines_list = await self.session.read_resource(
                AnyUrl("guidelines://list")
            )
            print("[OK] Guidelines list loaded")
            print(guidelines_list.contents[0].text if guidelines_list.contents else "")

    async def on_file_open(self, file_path: str):
        """
        Application logic triggered when a file is opened
        Decides which resources to preload based on file type
        """
        print(f"\n=== File Opened: {file_path} ===")
        self.context.current_file = file_path

        # Application decides: Python files need coding standards
        if file_path.endswith('.py'):
            print("Application Decision: Python file opened, loading coding standards...")
            await self.handle_user_action(UserAction.START_CODING, file_type='python')

        # Application decides: PR-related files need PR guidelines
        elif 'pull_request' in file_path or 'PR' in file_path:
            print("Application Decision: PR-related file, loading PR guidelines...")
            await self.handle_user_action(UserAction.OPEN_PR_EDITOR)

        # Application decides: Test files need test template
        elif 'test_' in file_path or '_test.py' in file_path:
            print("Application Decision: Test file opened, loading test template...")
            test_template = await self.session.read_resource(
                AnyUrl("templates://test")
            )
            self.ai_context.append({
                "type": "resource",
                "content": test_template.contents[0].text if test_template.contents else "",
                "reason": "Test file opened"
            })
            print("[OK] Test template loaded")

    def show_ai_context(self):
        """Display what resources have been loaded into AI context"""
        print("\n=== Current AI Context ===")
        if not self.ai_context:
            print("No resources loaded yet")
        else:
            for i, ctx in enumerate(self.ai_context, 1):
                print(f"{i}. {ctx['reason']}")
                print(f"   Type: {ctx['type']}")
                print(f"   Content preview: {ctx['content'][:100]}...")

async def simulate_user_session():
    """
    Simulates a user session to demonstrate how the application
    decides when to load resources without LLM involvement
    """

    # Setup server connection
    server_params = StdioServerParameters(
        command="python",
        args=["resources_server.py"],
        cwd="C:/Users/wenming/source/repos/mcp-course/wenming"
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Create our smart editor application
            editor = SmartCodeEditor(session)

            print("="*60)
            print("MCP Client Example - Application-Controlled Resource Loading")
            print("="*60)

            # Simulate various user actions
            # The APPLICATION decides what resources to load, not the LLM

            # Scenario 1: User opens a Python file
            await editor.on_file_open("src/main.py")

            # Scenario 2: User clicks "Create Pull Request" button
            await editor.handle_user_action(UserAction.OPEN_PR_EDITOR)

            # Scenario 3: User selects "Report Bug" from menu
            await editor.handle_user_action(UserAction.REPORT_BUG)

            # Scenario 4: User opens a test file
            await editor.on_file_open("tests/test_main.py")

            # Scenario 5: User initiates refactoring
            await editor.handle_user_action(UserAction.START_REFACTORING)

            # Show what's been loaded into AI context
            editor.show_ai_context()

            print("\n" + "="*60)
            print("Key Points:")
            print("1. The APPLICATION decided when to load each resource")
            print("2. Decisions were based on user actions and file types")
            print("3. No LLM was involved in deciding which resources to load")
            print("4. Resources were loaded proactively as context for the AI")
            print("="*60)

async def main():
    """Run the demonstration"""
    try:
        await simulate_user_session()
    except Exception as e:
        print(f"Error: {e}")
        # Run a simpler test without the server
        print("\nRunning simplified demonstration without server...")
        await demonstrate_decision_logic()

async def demonstrate_decision_logic():
    """
    Demonstrates the decision logic without actually connecting to a server
    """
    print("\n" + "="*60)
    print("Resource Loading Decision Logic (Pseudocode)")
    print("="*60)

    decision_map = {
        "User Action": "Resource(s) Loaded",
        "-"*40: "-"*40,
        "Open PR Editor": "guidelines://pr-guidelines",
        "Start Coding Python": "guidelines://coding-standards",
        "Click 'Report Bug'": "templates://bug-report",
        "Click 'New Feature'": "templates://feature-request",
        "Open test_*.py file": "templates://test",
        "Start Refactoring": "templates://refactor + guidelines://coding-standards",
        "Open *.md file": "templates://documentation",
        "Performance Issue": "templates://performance",
        "Security Concern": "templates://security",
    }

    for action, resource in decision_map.items():
        print(f"{action:<40} -> {resource}")

    print("\n" + "="*60)
    print("Summary: The client APPLICATION contains hardcoded logic")
    print("that maps user actions/context to specific resources.")
    print("This is APPLICATION-CONTROLLED, not MODEL-CONTROLLED.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())