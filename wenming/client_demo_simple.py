#!/usr/bin/env python3
"""
简化的 MCP 客户端演示 - 展示客户端是什么
"""

import asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from pydantic import AnyUrl

async def simple_client_demo():
    """
    这是一个 MCP 客户端程序
    客户端 = 使用 MCP 服务器提供的功能的应用程序
    """

    print("="*60)
    print("I am an MCP client application")
    print("My role: Connect to MCP server and use its resources")
    print("="*60)

    # 1. 配置要连接的服务器
    server_params = StdioServerParameters(
        command="python",
        args=["resources_server.py"],  # 连接到 resources_server.py 服务器
        cwd="C:/Users/wenming/source/repos/mcp-course/wenming"
    )

    # 2. 建立连接
    print("\nStep 1: Connecting to MCP server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 3. 初始化会话
            await session.initialize()
            print("[OK] Connected to server")

            # 4. 发现服务器提供了什么资源
            print("\nStep 2: Checking available resources...")
            resources = await session.list_resources()
            print(f"Found {len(resources.resources)} resources:")
            for r in resources.resources[:3]:  # 显示前3个
                print(f"  - {r.uri}")

            # 5. 使用资源 - 读取 PR 指南
            print("\nStep 3: Reading a resource (PR Guidelines)...")
            pr_guide = await session.read_resource(
                AnyUrl("guidelines://pr-guidelines")
            )
            if pr_guide.contents:
                content = pr_guide.contents[0].text
                print(f"Resource content preview: {content[:100]}...")

            # 6. 查看可用的工具
            print("\nStep 4: Checking available tools...")
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools:")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")

            # 7. 调用一个工具
            print("\nStep 5: Calling search tool...")
            result = await session.call_tool(
                "search_guidelines",
                arguments={"keyword": "test"}
            )
            if result.content:
                print(f"Search results: {result.content[0].text[:200]}...")

    print("\n" + "="*60)
    print("Summary:")
    print("- Client is an application (like IDE, editor, AI assistant)")
    print("- It connects to MCP servers to use their features")
    print("- Client decides when and how to use resources and tools")
    print("="*60)

async def explain_architecture():
    """Explain MCP architecture"""
    print("\n" + "="*60)
    print("MCP Architecture Explanation:")
    print("="*60)
    print("""
    User <-> Client App <-> MCP Server
             (this file)    (resources_server.py)

    1. MCP Server (resources_server.py):
       - Provides Resources: team docs, templates, etc.
       - Provides Tools: search, processing features
       - Waits for client connections and requests

    2. MCP Client (client_example.py):
       - Is an application (can be IDE, editor, Claude Desktop, etc.)
       - Connects to one or more MCP servers
       - Decides which resources to use based on user actions or app logic
       - Provides resource content to AI models as context

    3. Communication Method:
       - Uses stdio (standard input/output) for communication
       - Client starts server process and communicates via stdin/stdout
       - Uses JSON-RPC protocol to exchange messages

    Example Flow:
    1. User opens PR in editor
    2. Editor (client) decides it needs PR guidelines
    3. Client requests "guidelines://pr-guidelines" from server
    4. Server returns PR guidelines content
    5. Client adds content to AI assistant's context
    """)
    print("="*60)

if __name__ == "__main__":
    print("\nChoose demo:")
    print("1. Run simple client demo")
    print("2. View architecture explanation")

    choice = input("\nPlease choose (1 or 2): ").strip()

    if choice == "1":
        try:
            asyncio.run(simple_client_demo())
        except Exception as e:
            print(f"\nError: {e}")
            print("Hint: Make sure resources_server.py is in the same directory")
    else:
        asyncio.run(explain_architecture())