#!/usr/bin/env python3

"""
KiCad Code Executor MCP Server

This MCP server provides:
1. Resources: KiCad Python API documentation and examples
2. Tool: Execute dynamically generated KiCad Python code

Instead of pre-defining specific tools, this allows the LLM to:
- Read the API documentation from resources
- Generate custom code based on user requirements
- Execute the generated code through the execute_kicad_code tool
"""

import sys
import traceback
from io import StringIO
from pathlib import Path
from typing import Optional

from kipy import KiCad
from kipy.board_types import (
    BoardLayer,
    FootprintInstance,
    Net,
    Pad,
    Track,
    Via,
    ViaType,
    Zone,
)
from kipy.geometry import Angle, Vector2
from kipy.util.units import from_mm, to_mm
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kicad-code-executor")


@mcp.resource("kicad-api://board.py")
def get_board_api() -> str:
    """
    Returns the complete Board class API source code.

    This is the main API for manipulating PCB boards, including:
    - Getting/creating/updating/deleting board items
    - Working with nets, layers, design rules
    - Commit transactions for undo/redo
    """
    kicad_python_path = Path(__file__).parent.parent / "kicad-python"
    board_py = kicad_python_path / "kipy" / "board.py"

    if board_py.exists():
        return board_py.read_text(encoding="utf-8")
    return "Error: board.py not found. Make sure kicad-python is in the repository."


@mcp.resource("kicad-api://board_types.py")
def get_board_types_api() -> str:
    """
    Returns the complete board types API source code.

    Contains all PCB item types:
    - FootprintInstance, Pad, Via, Track, Zone
    - Net, Field, BoardShape, BoardText
    - PadStack, DrillProperties, etc.
    """
    kicad_python_path = Path(__file__).parent.parent / "kicad-python"
    board_types_py = kicad_python_path / "kipy" / "board_types.py"

    if board_types_py.exists():
        return board_types_py.read_text(encoding="utf-8")
    return "Error: board_types.py not found."


@mcp.resource("kicad-api://geometry.py")
def get_geometry_api() -> str:
    """
    Returns the geometry API source code.

    Contains geometric primitives:
    - Vector2, Box2, Angle
    - PolygonWithHoles
    - Geometric operations
    """
    kicad_python_path = Path(__file__).parent.parent / "kicad-python"
    geometry_py = kicad_python_path / "kipy" / "geometry.py"

    if geometry_py.exists():
        return geometry_py.read_text(encoding="utf-8")
    return "Error: geometry.py not found."


@mcp.resource("kicad-api://examples/list")
def list_examples() -> str:
    """
    Lists all available example scripts.

    These examples demonstrate common KiCad operations:
    - Creating vias, zones, tracks
    - Moving and organizing footprints
    - Selecting and highlighting items
    """
    kicad_python_path = Path(__file__).parent.parent / "kicad-python"
    examples_dir = kicad_python_path / "examples"

    if not examples_dir.exists():
        return "Error: examples directory not found."

    examples = []
    for py_file in sorted(examples_dir.glob("*.py")):
        examples.append(py_file.name)

    return "Available examples:\n" + "\n".join(f"  - {ex}" for ex in examples)


@mcp.resource("kicad-api://examples/{example_name}")
def get_example(example_name: str) -> str:
    """
    Returns the source code of a specific example.

    Use the list resource to see available examples first.
    Example: kicad-api://examples/create_via_grid.py
    """
    kicad_python_path = Path(__file__).parent.parent / "kicad-python"
    example_path = kicad_python_path / "examples" / example_name

    if not example_path.exists():
        return f"Error: Example '{example_name}' not found. Use kicad-api://examples/list to see available examples."

    return example_path.read_text(encoding="utf-8")


@mcp.resource("kicad-api://overview")
def get_api_overview() -> str:
    """
    Returns a high-level overview of the KiCad Python API.

    Quick reference for common operations.
    """
    return """# KiCad Python API Overview

## Quick Start

```python
from kipy import KiCad
kicad = KiCad()
board = kicad.get_board()
```

## Common Operations

### 1. Get Board Items
```python
footprints = board.get_footprints()
nets = board.get_nets()
tracks = board.get_tracks()
vias = board.get_vias()
pads = board.get_pads()
zones = board.get_zones()
```

### 2. Create Items
```python
via = Via()
via.position = Vector2.from_xy_mm(50, 50)
via.diameter = from_mm(0.8)
via.drill_diameter = from_mm(0.4)
via.net = target_net

board.create_items([via])
```

### 3. Update Items
```python
footprint.position = Vector2.from_xy_mm(100, 100)
board.update_items([footprint])
```

### 4. Delete Items
```python
board.remove_items([track])
```

### 5. Using Commits (for undo/redo)
```python
commit = board.begin_commit()
try:
    # Make changes
    board.create_items([item1, item2])
    board.update_items([item3])
    board.push_commit(commit, "Description of changes")
except Exception as e:
    board.drop_commit(commit)
    raise
```

## Important Concepts

1. **Units**: Most values are in nanometers internally. Use `from_mm()` and `to_mm()` for conversion.

2. **Net Matching**: Access net by name from `board.get_nets()`

3. **Footprint Structure**:
   - `FootprintInstance` has `position`, `orientation`, `layer`
   - Access pads via `footprint.definition.pads`
   - Access fields via `footprint.reference_field`, `footprint.value_field`

4. **Pad Clearance**:
   - Access via `pad._proto.copper_clearance_override.value_nm`
   - Use `from_mm()` to convert from millimeters

5. **Board Items Must Be Updated**: After modifying properties, call `board.update_items([item])`

## Resources Available

- kicad-api://board.py - Full Board API
- kicad-api://board_types.py - All PCB item types
- kicad-api://geometry.py - Geometric primitives
- kicad-api://examples/list - List all examples
- kicad-api://examples/{name} - Get specific example
"""


@mcp.tool()
def read_kicad_api_docs(doc_name: str) -> str:
    """
    Read KiCad API documentation before writing code.

    ALWAYS call this tool first to understand the API before generating code!

    Available documentation:
    - "overview" - Quick reference guide with common patterns (START HERE!)
    - "board" - Complete Board class API (get_footprints, get_nets, create_items, etc.)
    - "board_types" - All PCB item types (Pad, Via, Track, Zone, FootprintInstance, etc.)
    - "geometry" - Geometric primitives (Vector2, Angle, Box2, Polygon, etc.)
    - "examples" - List all available example scripts
    - "example:NAME" - Get specific example (e.g., "example:create_via_grid.py")

    Args:
        doc_name: Name of the documentation to read

    Returns:
        The requested API documentation

    Example workflow:
        1. read_kicad_api_docs("overview") - Get quick reference
        2. read_kicad_api_docs("board_types") - Learn about Pad, Via, etc.
        3. read_kicad_api_docs("examples") - See what examples exist
        4. read_kicad_api_docs("example:highlight_gnd_pads.py") - Study an example
        5. execute_kicad_code(generated_code) - Run your code
    """
    doc_name = doc_name.lower().strip()

    # Map friendly names to resource URIs
    doc_map = {
        "overview": "kicad-api://overview",
        "board": "kicad-api://board.py",
        "board_types": "kicad-api://board_types.py",
        "geometry": "kicad-api://geometry.py",
        "examples": "kicad-api://examples/list",
    }

    # Handle example requests
    if doc_name.startswith("example:"):
        example_name = doc_name[8:].strip()
        return get_example(example_name)

    # Get the resource URI
    if doc_name in doc_map:
        uri = doc_map[doc_name]

        # Call the appropriate resource function
        if uri == "kicad-api://overview":
            return get_api_overview()
        elif uri == "kicad-api://board.py":
            return get_board_api()
        elif uri == "kicad-api://board_types.py":
            return get_board_types_api()
        elif uri == "kicad-api://geometry.py":
            return get_geometry_api()
        elif uri == "kicad-api://examples/list":
            return list_examples()

    return f"""Error: Unknown documentation '{doc_name}'

Available documentation:
- "overview" - Quick reference guide
- "board" - Board class API
- "board_types" - PCB item types
- "geometry" - Geometric primitives
- "examples" - List examples
- "example:NAME" - Get specific example

Example: read_kicad_api_docs("overview")
"""


@mcp.tool()
def execute_kicad_code(code: str, description: Optional[str] = None) -> str:
    """
    Execute Python code that uses the KiCad API.

    IMPORTANT: Before writing code, you MUST read the API documentation from these MCP resources:

    Available Resources (read these first!):
    - kicad-api://overview - Quick reference guide (READ THIS FIRST!)
    - kicad-api://board.py - Complete Board class API documentation
    - kicad-api://board_types.py - All PCB item types (Pad, Via, Track, Zone, etc.)
    - kicad-api://geometry.py - Geometric primitives (Vector2, Angle, etc.)
    - kicad-api://examples/list - List all available example scripts
    - kicad-api://examples/{name} - Get specific example code (e.g., create_via_grid.py)

    WORKFLOW:
    1. Read kicad-api://overview to understand the API basics
    2. Read relevant API files (board.py, board_types.py) for detailed documentation
    3. Check kicad-api://examples/list for similar examples
    4. Generate code based on the documentation you read
    5. Use this tool to execute the generated code

    Args:
        code: Python code to execute. Should use kipy (kicad-python) API.
        description: Optional description of what the code does (for logging)

    Returns:
        Execution result including:
        - Status (success/error)
        - Standard output
        - Standard error
        - Exception details (if any)

    Pre-loaded imports (already available in code):
    - from kipy import KiCad
    - from kipy.board_types import BoardLayer, FootprintInstance, Net, Pad, Track, Via, ViaType, Zone
    - from kipy.geometry import Angle, Vector2
    - from kipy.util.units import from_mm, to_mm

    Common patterns (from kicad-api://overview):

    1. Get board and items:
        kicad = KiCad()
        board = kicad.get_board()
        footprints = board.get_footprints()
        pads = footprint.definition.pads

    2. Access pad clearance:
        old_val = pad._proto.copper_clearance_override.value_nm
        pad._proto.copper_clearance_override.value_nm = from_mm(0.5)

    3. Use commits for undo/redo:
        commit = board.begin_commit()
        try:
            # make changes
            board.update_items([items])
            board.push_commit(commit, "description")
        except:
            board.drop_commit(commit)

    Example:
        code = '''
        kicad = KiCad()
        board = kicad.get_board()
        footprints = board.get_footprints()
        print(f"Board has {len(footprints)} footprints")
        '''
    """
    stdout_capture = StringIO()
    stderr_capture = StringIO()

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        if description:
            print(f"Executing: {description}")
            print("-" * 60)

        exec_globals = {
            "KiCad": KiCad,
            "BoardLayer": BoardLayer,
            "FootprintInstance": FootprintInstance,
            "Net": Net,
            "Pad": Pad,
            "Track": Track,
            "Via": Via,
            "ViaType": ViaType,
            "Zone": Zone,
            "Angle": Angle,
            "Vector2": Vector2,
            "from_mm": from_mm,
            "to_mm": to_mm,
            "__name__": "__main__",
        }

        exec_locals = {}

        exec(code, exec_globals, exec_locals)

        result = {
            "status": "success",
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
        }

        return _format_result(result)

    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
        }
        return _format_result(result)

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def _format_result(result: dict) -> str:
    """Format execution result for display"""
    lines = []

    lines.append(f"{'='*60}")
    lines.append(f"Execution Status: {result['status'].upper()}")
    lines.append(f"{'='*60}")

    if result.get("stdout"):
        lines.append("\nOutput:")
        lines.append(result["stdout"].rstrip())

    if result.get("stderr"):
        lines.append("\nWarnings/Errors:")
        lines.append(result["stderr"].rstrip())

    if result["status"] == "error":
        lines.append(f"\nException Type: {result.get('error_type', 'Unknown')}")
        lines.append(f"Error Message: {result['error']}")
        lines.append("\nFull Traceback:")
        lines.append(result["traceback"].rstrip())

    lines.append(f"\n{'='*60}")

    return "\n".join(lines)


def main():
    """Main entry point for the KiCad Code Executor MCP server"""
    print("Starting KiCad Code Executor MCP Server...")
    print("\nThis server provides:")
    print("  Resources:")
    print("    - kicad-api://board.py - Board API source")
    print("    - kicad-api://board_types.py - Board types API")
    print("    - kicad-api://geometry.py - Geometry API")
    print("    - kicad-api://examples/list - List examples")
    print("    - kicad-api://examples/{name} - Get example code")
    print("    - kicad-api://overview - API overview")
    print("\n  Tool:")
    print("    - execute_kicad_code(code, description) - Execute KiCad Python code")
    print("\nMake sure KiCad is running with API server enabled!")
    print("=" * 60)
    mcp.run()


if __name__ == "__main__":
    main()
