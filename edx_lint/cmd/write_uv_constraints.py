"""The edx_lint write_uv_constraints command."""

import argparse
import importlib.resources
import re

import tomlkit


def _package_name(spec):
    """Return the normalized package name from a constraint specifier like 'Django<6.0'."""
    name = re.split(r"[<>=!~\[;@]", spec, maxsplit=1)[0].strip()
    return name.lower().replace("-", "_").replace(".", "_")


def _parse_constraints(text):
    """Parse constraints file text, stripping comments and blank lines.

    Returns a tuple of (constraints, directives) where:
      constraints: valid package-specifier lines
      directives:  pip directive lines (-c, -r, etc.) that are not valid here
    """
    constraints = []
    directives = []
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if line.startswith("-"):
            directives.append(line)
        else:
            constraints.append(line)
    return constraints, directives


def write_uv_constraints_main(argv):
    """
    write_uv_constraints [pyproject.toml]
        Write [tool.uv].constraint-dependencies in pyproject.toml by merging
        edx-lint's global constraints with optional repo-specific constraints
        from [tool.edx_lint].uv_constraints in the same file.
    """
    parser = argparse.ArgumentParser(prog="edx_lint write_uv_constraints", add_help=False)
    parser.add_argument("pyproject", nargs="?", default="pyproject.toml")
    args, unknown = parser.parse_known_args(argv)

    if unknown:
        print(f"Unknown arguments: {' '.join(unknown)}")
        return 1

    global_text = (
        importlib.resources.files("edx_lint")
        .joinpath("files/common_constraints.txt")
        .read_text(encoding="utf-8")
    )
    global_constraints, _ = _parse_constraints(global_text)

    try:
        with open(args.pyproject, encoding="utf-8") as f:
            data = tomlkit.load(f)
    except FileNotFoundError:
        print(f"File not found: {args.pyproject}")
        return 2

    # Read optional repo-specific constraints from [tool.edx_lint].uv_constraints.
    # These live in the same pyproject.toml so everything is in one place.
    try:
        local_constraints = list(data["tool"]["edx_lint"]["uv_constraints"])
    except KeyError:
        local_constraints = []

    # Merge global and local constraints, keyed by normalized package name so
    # that a local entry for the same package overrides the global one.  This
    # lets repos tighten or pin a constraint during testing without the global
    # version clobbering their pin.
    merged = {_package_name(c): c for c in global_constraints}
    for c in local_constraints:
        merged[_package_name(c)] = c  # local takes precedence
    constraints = list(merged.values())

    if "tool" not in data:
        data.add("tool", tomlkit.table())
    if "uv" not in data["tool"]:
        data["tool"].add("uv", tomlkit.table())

    uv_table = data["tool"]["uv"]
    constraint_array = tomlkit.array()
    constraint_array.multiline(True)
    constraint_array.extend(constraints)

    if "constraint-dependencies" in uv_table:
        # Replace in-place so any existing comment above the key is preserved.
        uv_table["constraint-dependencies"] = constraint_array
    else:
        # First write: add a prominent comment so humans know not to edit this.
        uv_table.add(tomlkit.comment(" DO NOT EDIT constraint-dependencies DIRECTLY."))
        uv_table.add(tomlkit.comment(" This list is managed by `edx_lint write_uv_constraints`"))
        uv_table.add(tomlkit.comment(" and will be overwritten the next time `make upgrade` is run."))
        uv_table.add(tomlkit.comment(" - GLOBAL constraints: edit edx_lint/files/common_constraints.txt"))
        uv_table.add(tomlkit.comment(" - REPO-SPECIFIC constraints: edit [tool.edx_lint].uv_constraints in this file"))
        uv_table.add("constraint-dependencies", constraint_array)

    with open(args.pyproject, "w", encoding="utf-8") as f:
        tomlkit.dump(data, f)

    print(f"Wrote {len(constraints)} constraints to {args.pyproject}")
    return 0
