#!/usr/bin/env python3
"""
MCP Client with Local LLM
Demonstrates how to use MCP servers with a local LLM instead of Claude API
"""

import asyncio
import json
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Example using ollama for local LLM
# pip install ollama
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    print("Warning: ollama not installed. Install with: uv add ollama")


class LocalLLMWithMCP:
    """
    Client that coordinates between local LLM and MCP servers
    This is what you need to implement to use local LLM with MCP
    """

    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.mcp_session = None
        self.available_tools = []
        self.conversation_history = []
        self.server_params = None

    def setup_server_params(self, server_params: StdioServerParameters):
        """Store server parameters for connection"""
        self.server_params = server_params

    def convert_mcp_tools_to_llm_format(self) -> list[dict[str, Any]]:
        """
        Convert MCP tool definitions to the format your LLM expects
        Different LLMs have different formats for function calling
        """
        llm_tools = []

        for tool in self.available_tools:
            # Ollama/OpenAI function calling format
            llm_tool = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            llm_tools.append(llm_tool)

        return llm_tools

    async def chat(self, session: ClientSession, user_message: str) -> str:
        """
        Main chat loop that coordinates between local LLM and MCP tools
        This is the core logic you need to implement
        """
        print(f"\n{'='*60}")
        print(f"User: {user_message}")
        print(f"{'='*60}")

        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Convert MCP tools to LLM format
        tools = self.convert_mcp_tools_to_llm_format()

        # Call local LLM with tool definitions
        if not HAS_OLLAMA:
            return "Error: ollama not installed"

        print(f"[LLM] Thinking... (using {self.model_name})")

        # First LLM call - let it decide if it needs to use tools
        response = ollama.chat(
            model=self.model_name,
            messages=self.conversation_history,
            tools=tools
        )

        # Check if LLM wants to use tools
        if response.get('message', {}).get('tool_calls'):
            print("[LLM] Decided to use tools")

            tool_results = []

            # Execute each tool call
            for tool_call in response['message']['tool_calls']:
                tool_name = tool_call['function']['name']
                tool_args = tool_call['function']['arguments']

                # Call MCP server
                print(f"\n[CLIENT] Calling MCP tool: {tool_name}")
                print(f"[CLIENT] Arguments: {tool_args}")

                result = await session.call_tool(tool_name, arguments=tool_args)

                # Extract text content from result
                if result.content and len(result.content) > 0:
                    tool_result = result.content[0].text
                else:
                    tool_result = str(result)

                print(f"[MCP SERVER] Result: {tool_result[:100]}...")

                tool_results.append({
                    "role": "tool",
                    "content": tool_result
                })

            # Add assistant's tool use to history
            self.conversation_history.append(response['message'])

            # Add tool results to history
            self.conversation_history.extend(tool_results)

            # Call LLM again with tool results to generate final response
            print("[LLM] Generating final response with tool results...")
            final_response = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history
            )

            assistant_message = final_response['message']['content']
        else:
            # LLM didn't need tools
            print("[LLM] No tools needed")
            assistant_message = response['message']['content']
            self.conversation_history.append(response['message'])

        print(f"\n[ASSISTANT] {assistant_message}")
        return assistant_message


async def demo_with_local_llm():
    """
    Complete example of using local LLM with MCP servers
    """

    print("="*60)
    print("MCP Client with Local LLM Demo")
    print("="*60)

    # Setup MCP server connection parameters
    # This connects to your existing MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["resources_server.py"],
        cwd="C:/Users/wenming/source/repos/mcp-course/wenming"
    )

    # Create client
    client = LocalLLMWithMCP(model_name="llama3.1:8b")
    client.setup_server_params(server_params)

    try:
        # Connect to MCP server using proper async context managers
        print("\n[CLIENT] Connecting to MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                print("[CLIENT] Connected to MCP server")

                # Discover available tools
                tools_response = await session.list_tools()
                client.available_tools = tools_response.tools
                print(f"[CLIENT] Found {len(client.available_tools)} tools:")
                for tool in client.available_tools:
                    print(f"  - {tool.name}: {tool.description}")

                # Example conversations
                test_queries = [
                    "Search for guidelines about testing",
                    "What templates are available?",
                    "Can you search for 'code review' in the guidelines?"
                ]

                for query in test_queries:
                    response = await client.chat(session, query)
                    print("\n" + "-"*60)
                    await asyncio.sleep(1)  # Small delay between queries

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()




async def main():
    """Main entry point"""
    if not HAS_OLLAMA:
        print("\nOllama not installed!")
        print("Install with:")
        print("  1. Install ollama: https://ollama.com/download")
        print("  2. Install Python client: uv add ollama")
        print("  3. Pull a model: ollama pull llama3.1")
        return

    await demo_with_local_llm()


if __name__ == "__main__":
    asyncio.run(main())
