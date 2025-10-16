#!/usr/bin/env python3

"""
KiCad MCP Server - Demonstrates three representative MCP tools for KiCad manipulation
From simple to complex, showcasing the KiCad Python API capabilities
"""

from typing import Dict, List, Optional

from kipy import KiCad
from kipy.board_types import (
    BoardLayer,
    FootprintInstance,
    Net,
    Track,
    Via,
    ViaType,
    Zone,
)
from kipy.geometry import Angle, Vector2
from kipy.util.units import from_mm, to_mm
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("kicad-agent")


@mcp.tool()
def get_board_info() -> str:
    """
    Tool 1 (Simple): Get basic information about the currently open KiCad board.

    Returns information including:
    - Board filename
    - Number of footprints
    - Number of nets
    - Number of tracks and vias
    - Copper layer count

    This demonstrates basic read operations on the KiCad board.
    """
    try:
        kicad = KiCad()
        board = kicad.get_board()

        footprints = board.get_footprints()
        nets = board.get_nets()
        tracks = board.get_tracks()
        vias = board.get_vias()
        copper_layers = board.get_copper_layer_count()

        info = {
            "filename": board.name,
            "footprint_count": len(footprints),
            "net_count": len(nets),
            "track_count": len(tracks),
            "via_count": len(vias),
            "copper_layer_count": copper_layers,
        }

        result = f"Board Information:\n"
        result += f"  Filename: {info['filename']}\n"
        result += f"  Footprints: {info['footprint_count']}\n"
        result += f"  Nets: {info['net_count']}\n"
        result += f"  Tracks: {info['track_count']}\n"
        result += f"  Vias: {info['via_count']}\n"
        result += f"  Copper Layers: {info['copper_layer_count']}\n"

        return result

    except Exception as e:
        return f"Error: {str(e)}\nMake sure KiCad is running with API server enabled and a board is open."


@mcp.tool()
def create_via_grid(
    start_x_mm: float,
    start_y_mm: float,
    grid_rows: int,
    grid_cols: int,
    spacing_mm: float = 2.54,
    via_diameter_mm: float = 0.8,
    via_drill_mm: float = 0.4,
    net_name: str = "",
) -> str:
    """
    Tool 2 (Moderate): Create a grid of vias on the PCB board.

    Args:
        start_x_mm: Starting X position in millimeters
        start_y_mm: Starting Y position in millimeters
        grid_rows: Number of rows in the grid
        grid_cols: Number of columns in the grid
        spacing_mm: Spacing between vias in millimeters (default: 2.54mm = 100mil)
        via_diameter_mm: Via diameter in millimeters (default: 0.8mm)
        via_drill_mm: Via drill diameter in millimeters (default: 0.4mm)
        net_name: Optional net name to assign to vias (default: no net)

    This demonstrates:
    - Creating multiple board items programmatically
    - Working with coordinates and units conversion
    - Net assignment
    - Batch operations using create_items
    """
    try:
        kicad = KiCad()
        board = kicad.get_board()

        vias = []

        target_net = None
        if net_name:
            nets = board.get_nets()
            for net in nets:
                if net.name == net_name:
                    target_net = net
                    break
            if target_net is None:
                return f"Error: Net '{net_name}' not found on board"

        for row in range(grid_rows):
            for col in range(grid_cols):
                via = Via()

                x_mm = start_x_mm + col * spacing_mm
                y_mm = start_y_mm + row * spacing_mm
                via.position = Vector2.from_xy_mm(x_mm, y_mm)

                via.type = ViaType.VT_THROUGH
                via.diameter = from_mm(via_diameter_mm)
                via.drill_diameter = from_mm(via_drill_mm)

                if target_net:
                    via.net = target_net

                via.locked = False
                vias.append(via)

        board.create_items(vias)

        result = f"Successfully created {len(vias)} vias!\n"
        result += f"  Grid: {grid_rows} x {grid_cols}\n"
        result += f"  Starting position: ({start_x_mm}mm, {start_y_mm}mm)\n"
        result += f"  Spacing: {spacing_mm}mm\n"
        result += f"  Via specs: diameter={via_diameter_mm}mm, drill={via_drill_mm}mm\n"
        if net_name:
            result += f"  Net: {net_name}\n"

        return result

    except Exception as e:
        return f"Error creating via grid: {str(e)}"


@mcp.tool()
def organize_footprints_in_grid(
    component_prefix: str,
    start_x_mm: float,
    start_y_mm: float,
    columns: int,
    spacing_x_mm: float = 10.0,
    spacing_y_mm: float = 10.0,
    rotation_degrees: float = 0.0,
) -> str:
    """
    Tool 3 (Complex): Organize footprints matching a prefix into a neat grid layout.

    Args:
        component_prefix: Prefix to filter components (e.g., "R" for resistors, "C" for capacitors)
        start_x_mm: Starting X position in millimeters
        start_y_mm: Starting Y position in millimeters
        columns: Number of columns in the grid
        spacing_x_mm: Horizontal spacing between components in millimeters
        spacing_y_mm: Vertical spacing between components in millimeters
        rotation_degrees: Rotation angle for all components in degrees

    This demonstrates:
    - Reading and filtering existing board items
    - Modifying item properties (position and orientation)
    - Using update_items to apply changes
    - Complex layout algorithms
    - Working with commits for undo/redo

    Example: organize_footprints_in_grid("R", 50, 50, 5, 10, 10, 0)
             will arrange all resistors in a 5-column grid starting at (50mm, 50mm)
    """
    try:
        kicad = KiCad()
        board = kicad.get_board()

        all_footprints = board.get_footprints()

        filtered_footprints = [
            fp
            for fp in all_footprints
            if fp.reference_field.text.value.startswith(component_prefix)
        ]

        if not filtered_footprints:
            return f"No footprints found with prefix '{component_prefix}'"

        filtered_footprints.sort(key=lambda fp: fp.reference_field.text.value)

        commit = board.begin_commit()

        try:
            for idx, footprint in enumerate(filtered_footprints):
                row = idx // columns
                col = idx % columns

                new_x = start_x_mm + col * spacing_x_mm
                new_y = start_y_mm + row * spacing_y_mm

                footprint.position = Vector2.from_xy_mm(new_x, new_y)

                footprint.orientation = Angle.from_degrees(rotation_degrees)

            board.update_items(filtered_footprints)

            board.push_commit(
                commit, f"Organize {component_prefix}* footprints in grid"
            )

            rows_used = (len(filtered_footprints) - 1) // columns + 1

            result = f"Successfully organized {len(filtered_footprints)} footprints!\n"
            result += f"  Component prefix: {component_prefix}\n"
            result += f"  Grid layout: {rows_used} rows x {columns} columns\n"
            result += f"  Starting position: ({start_x_mm}mm, {start_y_mm}mm)\n"
            result += f"  Spacing: {spacing_x_mm}mm x {spacing_y_mm}mm\n"
            result += f"  Rotation: {rotation_degrees} degrees\n"
            result += f"\n  Organized components:\n"

            for fp in filtered_footprints[:10]:
                x_pos = to_mm(fp.position.x)
                y_pos = to_mm(fp.position.y)
                result += f"    - {fp.reference_field.text.value}: ({x_pos:.2f}mm, {y_pos:.2f}mm)\n"

            if len(filtered_footprints) > 10:
                result += f"    ... and {len(filtered_footprints) - 10} more\n"

            return result

        except Exception as e:
            board.drop_commit(commit)
            raise e

    except Exception as e:
        return f"Error organizing footprints: {str(e)}"


@mcp.tool()
def adjust_pad_clearance(
    net_pattern: str,
    clearance_mm: Optional[float] = None,
    clearance_multiplier: Optional[float] = None,
) -> str:
    """
    Tool 4 (Moderate): Adjust pad-to-copper clearance for pads on nets matching a pattern.

    Args:
        net_pattern: Net name prefix to match (e.g., "GND" matches "GND", "GND1", "GND2"; "GN" matches "GND", "GND1", "GN_SIGNAL")
        clearance_mm: Absolute clearance value in millimeters (mutually exclusive with multiplier)
        clearance_multiplier: Multiply existing clearance by this factor (e.g., 2.0 for double)

    This tool adjusts the clearance between pads in footprints connected to matching nets
    and copper zones/pours from other nets. Supports fuzzy matching by net name prefix
    and both absolute and relative (multiplier) adjustment.

    This demonstrates:
    - Fuzzy net name matching with prefix
    - Reading and modifying pad properties
    - Relative vs absolute value adjustment
    - Using commits for proper undo/redo
    - Working with local clearance overrides

    Examples:
        - adjust_pad_clearance("GND", clearance_mm=0.5) - Set 0.5mm clearance for all GND* pads
        - adjust_pad_clearance("GN", clearance_multiplier=2.0) - Double clearance for all GN* net pads
    """
    try:
        if clearance_mm is None and clearance_multiplier is None:
            return "Error: Must specify either clearance_mm or clearance_multiplier"

        if clearance_mm is not None and clearance_multiplier is not None:
            return "Error: Cannot specify both clearance_mm and clearance_multiplier"

        kicad = KiCad()
        board = kicad.get_board()

        all_nets = board.get_nets()
        matching_nets = [
            net for net in all_nets if net.name.startswith(net_pattern)
        ]

        if not matching_nets:
            return f"No nets found matching pattern '{net_pattern}*'"

        all_footprints = board.get_footprints()

        modified_pads = []
        old_clearances = []
        pad_info = []

        for footprint in all_footprints:
            pads = footprint.definition.pads
            for pad in pads:
                if pad.net is None:
                    continue

                if any(pad.net.name == net.name for net in matching_nets):
                    old_clearance_nm = pad._proto.copper_clearance_override.value_nm if pad._proto.HasField("copper_clearance_override") else 0
                    old_clearance = to_mm(old_clearance_nm) if old_clearance_nm else 0.0

                    if clearance_mm is not None:
                        new_clearance_mm = clearance_mm
                    else:
                        if old_clearance == 0.0:
                            old_clearance = 0.2
                        new_clearance_mm = old_clearance * clearance_multiplier

                    pad._proto.copper_clearance_override.value_nm = from_mm(new_clearance_mm)

                    modified_pads.append(pad)
                    old_clearances.append(old_clearance)
                    pad_info.append({
                        "footprint": footprint.reference_field.text.value,
                        "pad": pad.number,
                        "net": pad.net.name,
                        "old": old_clearance,
                        "new": new_clearance_mm,
                    })

        if not modified_pads:
            return f"No pads found on nets matching pattern '{net_pattern}*'"

        commit = board.begin_commit()

        try:
            footprints_to_update = list(set(
                fp for fp in all_footprints if any(pad in fp.definition.pads for pad in modified_pads)
            ))

            board.update_items(footprints_to_update)

            if clearance_mm is not None:
                commit_msg = f"Adjust pad clearance for {net_pattern}* nets to {clearance_mm}mm"
            else:
                commit_msg = f"Adjust pad clearance for {net_pattern}* nets by {clearance_multiplier}x"

            board.push_commit(commit, commit_msg)

            result = f"Successfully adjusted clearance for {len(modified_pads)} pad(s) on {len(matching_nets)} matching net(s)!\n"
            result += f"  Net pattern: '{net_pattern}*'\n"
            result += f"  Matching nets: {', '.join([net.name for net in matching_nets[:5]])}\n"

            if len(matching_nets) > 5:
                result += f"    ... and {len(matching_nets) - 5} more net(s)\n"

            if clearance_mm is not None:
                result += f"  New clearance: {clearance_mm}mm (absolute)\n"
            else:
                result += f"  Clearance multiplier: {clearance_multiplier}x\n"

            result += f"\n  Sample of modified pads:\n"

            for info in pad_info[:10]:
                result += f"    {info['footprint']}.{info['pad']} ({info['net']}): {info['old']:.3f}mm -> {info['new']:.3f}mm\n"

            if len(pad_info) > 10:
                result += f"    ... and {len(pad_info) - 10} more pad(s)\n"

            return result

        except Exception as e:
            board.drop_commit(commit)
            raise e

    except Exception as e:
        return f"Error adjusting pad clearance: {str(e)}"


def main():
    """Main entry point for the KiCad MCP server"""
    print("Starting KiCad MCP Server...")
    print("Available tools:")
    print("  1. get_board_info() - Get basic board statistics")
    print("  2. create_via_grid() - Create a grid of vias")
    print("  3. organize_footprints_in_grid() - Organize components in a grid layout")
    print("  4. adjust_pad_clearance() - Adjust pad-to-copper clearance with fuzzy net matching")
    print("\nMake sure KiCad is running with API server enabled!")
    mcp.run()


if __name__ == "__main__":
    main()
