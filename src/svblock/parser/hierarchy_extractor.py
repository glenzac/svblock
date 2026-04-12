"""Extract block diagram IR (instances and connectivity) from SystemVerilog files."""

from __future__ import annotations

import json
from pathlib import Path

import pyslang

from svblock.model import (
    BlockDiagramIR,
    ConnectionDef,
    InstanceDef,
    PortDirection,
)
from svblock.parser.sv_extractor import ParseError

_DIRECTION_MAP = {
    pyslang.ArgumentDirection.In: PortDirection.INPUT,
    pyslang.ArgumentDirection.Out: PortDirection.OUTPUT,
    pyslang.ArgumentDirection.InOut: PortDirection.INOUT,
    pyslang.ArgumentDirection.Ref: PortDirection.REF,
}


def _get_net_name(expr: object) -> str | None:
    """Extract the connected net name from a port connection expression.

    Input ports have NamedValue expressions; output ports have Assignment
    expressions where the target net is on the left side.
    """
    if expr is None:
        return None
    kind = getattr(expr, "kind", None)
    if kind == pyslang.ExpressionKind.NamedValue:
        sym = getattr(expr, "symbol", None)
        return sym.name if sym else None
    if kind == pyslang.ExpressionKind.Assignment:
        return _get_net_name(getattr(expr, "left", None))
    if kind == pyslang.ExpressionKind.Conversion:
        return _get_net_name(getattr(expr, "operand", None))
    return None


def _extract_instances_from_syntax(body: object) -> list[tuple[str, str]]:
    """Extract (instance_name, module_type) pairs from the syntax JSON."""
    syntax = body.syntax  # type: ignore[attr-defined]
    if syntax is None:
        return []

    data = json.loads(syntax.to_json())
    result: list[tuple[str, str]] = []

    for member in data.get("members", []):
        if not isinstance(member, dict):
            continue
        if member.get("kind") != "HierarchyInstantiation":
            continue

        type_node = member.get("type", {})
        module_type = type_node.get("text", "") if isinstance(type_node, dict) else ""

        for hi in member.get("instances", []):
            if not isinstance(hi, dict):
                continue
            decl = hi.get("decl", {})
            name_node = decl.get("name", {}) if isinstance(decl, dict) else {}
            instance_name = (
                name_node.get("text", "")
                if isinstance(name_node, dict) else ""
            )
            if instance_name and module_type:
                result.append((instance_name, module_type))

    return result


def _build_connectivity(
    body: object,
    instance_names: list[tuple[str, str]],
    parent_port_names: set[str],
) -> tuple[list[ConnectionDef], dict[str, list[str]], dict[str, PortDirection]]:
    """Analyse port connections to determine inter-instance connectivity.

    Returns:
        (connections, parent_port_instances, parent_port_directions)
    """
    # net -> [(instance_name, is_output)]
    net_endpoints: dict[str, list[tuple[str, bool]]] = {}
    # parent_port -> [(instance_name, is_output)]
    parent_port_endpoints: dict[str, list[tuple[str, bool]]] = {}

    parent_port_dir_map: dict[str, PortDirection] = {}

    for iname, _mtype in instance_names:
        child = body.find(iname)  # type: ignore[attr-defined]
        if child is None or not hasattr(child, "portConnections"):
            continue

        for pc in child.portConnections:
            port = pc.port
            port_dir = port.direction
            is_output = port_dir == pyslang.ArgumentDirection.Out
            net = _get_net_name(pc.expression)
            if not net:
                continue

            if net in parent_port_names:
                if net not in parent_port_endpoints:
                    parent_port_endpoints[net] = []
                parent_port_endpoints[net].append((iname, is_output))
            else:
                if net not in net_endpoints:
                    net_endpoints[net] = []
                net_endpoints[net].append((iname, is_output))

    # Derive inter-instance connections
    pair_directions: dict[frozenset[str], set[tuple[str, str]]] = {}

    for _net, endpoints in net_endpoints.items():
        producers = [iname for iname, is_out in endpoints if is_out]
        consumers = [iname for iname, is_out in endpoints if not is_out]
        for src in producers:
            for dst in consumers:
                if src == dst:
                    continue
                key = frozenset([src, dst])
                if key not in pair_directions:
                    pair_directions[key] = set()
                pair_directions[key].add((src, dst))

    connections: list[ConnectionDef] = []
    for key, dirs in sorted(pair_directions.items(), key=lambda x: sorted(x[0])):
        a, b = sorted(key)
        fwd = any(s == a for s, _d in dirs)
        rev = any(s == b for s, _d in dirs)
        if fwd and rev:
            connections.append(ConnectionDef(a, b, is_bidirectional=True))
        elif fwd:
            connections.append(ConnectionDef(a, b, is_bidirectional=False))
        else:
            connections.append(ConnectionDef(b, a, is_bidirectional=False))

    # Derive parent port connections
    parent_port_instances: dict[str, list[str]] = {}

    for port in body.portList:  # type: ignore[attr-defined]
        pname = port.name
        pdir = _DIRECTION_MAP.get(port.direction, PortDirection.INPUT)
        parent_port_dir_map[pname] = pdir

        endpoints = parent_port_endpoints.get(pname, [])
        if endpoints:
            parent_port_instances[pname] = [iname for iname, _is_out in endpoints]

    return connections, parent_port_instances, parent_port_dir_map


def extract_block_diagram(
    file_path: str | Path,
    module_name: str | None = None,
    include_paths: list[str] | None = None,
) -> BlockDiagramIR:
    """Extract a block diagram IR showing module instances and their connectivity.

    Args:
        file_path: Path to the .sv or .v file.
        module_name: Module to analyse. If None, uses the first top-level module.
        include_paths: Optional directories to search for include files.

    Returns:
        BlockDiagramIR with instances and connections.

    Raises:
        ParseError: If the file cannot be parsed or the module is not found.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise ParseError(f"File not found: {file_path}")

    try:
        tree = pyslang.SyntaxTree.fromFile(str(file_path))
    except Exception as e:
        raise ParseError(f"Failed to parse {file_path}: {e}") from e

    comp = pyslang.Compilation()

    if include_paths:
        sm = comp.sourceManager
        if hasattr(sm, "addUserDirectories"):
            sm.addUserDirectories(include_paths)

    comp.addSyntaxTree(tree)

    diags = comp.getAllDiagnostics()
    if diags:
        for d in diags:
            severity = str(d.severity) if hasattr(d, "severity") else ""
            if "error" in severity.lower():
                raise ParseError(f"Parse error in {file_path}: {d}")

    # Find the target module
    target_inst = None
    for inst in comp.getRoot().topInstances:
        if not inst.isModule:
            continue
        if module_name is None or inst.name == module_name:
            target_inst = inst
            break

    if target_inst is None:
        available = [
            i.name for i in comp.getRoot().topInstances if i.isModule
        ]
        if module_name:
            raise ParseError(
                f"Module '{module_name}' not found in {file_path}. "
                f"Available modules: {available}"
            )
        raise ParseError(f"No modules found in {file_path}")

    body = target_inst.body

    # Parent port names
    parent_port_names = {p.name for p in body.portList}

    # Extract child instances
    instance_pairs = _extract_instances_from_syntax(body)
    if not instance_pairs:
        return BlockDiagramIR(
            parent_name=target_inst.name,
            file_path=str(file_path),
        )

    instances = [
        InstanceDef(instance_name=iname, module_name=mtype)
        for iname, mtype in instance_pairs
    ]

    # Build connectivity
    connections, parent_port_instances, parent_port_dirs = _build_connectivity(
        body, instance_pairs, parent_port_names,
    )

    return BlockDiagramIR(
        parent_name=target_inst.name,
        file_path=str(file_path),
        instances=instances,
        connections=connections,
        parent_port_instances=parent_port_instances,
        parent_port_directions=parent_port_dirs,
    )
