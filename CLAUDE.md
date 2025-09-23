# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the **MCP Python SDK** and educational materials for learning **Model Context Protocol (MCP)** development. The focus is on understanding MCP concepts, server/client implementation, and practical MCP development patterns using the official Python SDK.

## Repository Structure

### Core Directories

- **`python-sdk/`** - **Main focus**: Official MCP Python SDK with complete implementation
- **`units/en/`** - MCP learning materials and documentation
- **`projects/`** - MCP implementation examples and practice projects
- **`quiz/`** - MCP knowledge assessments
- **`scripts/`** - Build and utility scripts

### Key Files

- **`requirements.txt`** - Documentation build dependencies (hf-doc-builder, mdx_truly_sane_lists, pyyaml)
- **`units/en/_toctree.yml`** - Course navigation structure and table of contents
- **`.github/workflows/`** - Documentation build and deployment workflows

## MCP Development Commands

### Working with MCP SDK
All MCP development uses the `uv` package manager and the python-sdk:

```bash
# Navigate to MCP SDK
cd python-sdk/

# Install MCP SDK with CLI tools
uv add "mcp[cli]"

# Create a new MCP server
uv run mcp init my-server

# Run MCP server in development mode (with inspector)
uv run mcp dev server.py

# Run MCP server directly
uv run mcp run server.py

# Install MCP server in Claude Desktop
uv run mcp install server.py

# Run tests
uv run pytest
```

### Basic MCP Server Development
```bash
# Create FastMCP server
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("my-server")

# Add tools
@mcp.tool()
def my_tool(arg: str) -> str:
    return f"Result: {arg}"

# Run server
mcp.run()
```

## MCP Architecture Overview

### Core MCP Concepts
MCP defines three main primitives:

1. **Resources** - Data exposed to LLMs (read-only, like GET endpoints)
2. **Tools** - Functions LLMs can call (executable, like POST endpoints)
3. **Prompts** - Reusable templates for LLM interactions

### MCP Server Implementation Patterns
Based on the SDK code, MCP servers follow these patterns:

```python
from mcp.server.fastmcp import FastMCP

# High-level FastMCP server
mcp = FastMCP("server-name")

# Define tools
@mcp.tool()
def my_tool(param: str) -> str:
    """Tool description for LLM"""
    return f"Response: {param}"

# Define resources
@mcp.resource("resource://path/{id}")
def get_resource(id: str) -> str:
    """Resource description"""
    return f"Resource data for {id}"

# Define prompts
@mcp.prompt()
def my_prompt(name: str) -> str:
    """Prompt template"""
    return f"Hello {name}, please..."

# Run server
mcp.run()
```

### Transport Layers
MCP supports multiple transport mechanisms:
- **stdio** - Standard input/output (most common)
- **SSE** - Server-Sent Events over HTTP
- **streamable-http** - HTTP streaming (newer)

## MCP Development Best Practices

### Package Management
- **Always use `uv`**, never `pip`
- Install MCP with: `uv add "mcp[cli]"`
- Development dependencies: `uv add --dev pytest pytest-asyncio`

### Server Development
- Use `FastMCP` for high-level development
- Use low-level `Server` for advanced control
- Tools should return structured data or JSON strings
- Include proper error handling and logging
- Use type hints for all parameters and return values

### Testing MCP Servers
```bash
# Interactive testing with MCP Inspector
uv run mcp dev server.py

# Unit testing
uv run pytest

# Manual testing with clients
uv run mcp run server.py
```

### Context and Capabilities
MCP servers can access context for advanced features:
```python
@mcp.tool()
async def advanced_tool(param: str, ctx: Context) -> str:
    # Log messages
    await ctx.info("Processing request")

    # Report progress
    await ctx.report_progress(0.5, message="Halfway done")

    # Read resources
    content = await ctx.read_resource("resource://data")

    return result
```

## Key MCP SDK Components

- **`mcp.server.fastmcp.FastMCP`** - High-level server implementation
- **`mcp.server.lowlevel.Server`** - Low-level server for advanced control
- **`mcp.client.stdio`** - Client for stdio transport
- **`mcp.types`** - MCP protocol types and messages
- **`mcp.server.session`** - Session management

## Learning Focus Areas

### Core MCP Protocol
1. **Message Protocol** - Request/response patterns between client and server
2. **Capabilities** - What features a server supports (tools, resources, prompts)
3. **Transport** - How messages are sent (stdio, HTTP, SSE)
4. **Lifecycle** - Server initialization, capabilities exchange, operation

### Server Development
1. **FastMCP** - Decorator-based server development
2. **Tool Implementation** - Creating callable functions for LLMs
3. **Resource Management** - Exposing data to LLM context
4. **Error Handling** - Proper exception management and logging

### Client Development
1. **Session Management** - Connecting to and managing server connections
2. **Protocol Handling** - Sending requests and processing responses
3. **Transport Selection** - Choosing appropriate transport mechanism