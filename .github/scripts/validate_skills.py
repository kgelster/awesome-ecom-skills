#!/usr/bin/env python3
"""Validate SKILL.md files against the Agent Skills spec (agentskills.io/specification).

Mechanical checks only. Parses frontmatter with a real YAML parser, never a regex:
a hand-rolled parser accepts `description: foo: bar`, which every real YAML
loader rejects, so it validates its own bugs instead of the spec.

Usage:  python3 .github/scripts/validate_skills.py [path ...]
Exit:   0 = clean, 1 = violations found, 2 = could not run
"""

import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("error: PyYAML required. Run: uv run --with pyyaml python3 " + __file__)

SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
SKIP_DIRS = {".git", "node_modules", ".venv"}


def check(path: Path):
    """Return (errors, warnings) for one SKILL.md."""
    errors, warnings = [], []
    raw = path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("UTF-8 BOM before frontmatter (file must begin with '---')")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return [f"not valid UTF-8: {exc}"], warnings

    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append("no YAML frontmatter delimited by '---' at the top of the file")
        return errors, warnings

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        detail = str(exc).splitlines()[0]
        hint = ""
        if "mapping values are not allowed" in str(exc):
            hint = " (an unquoted ': ' in a value: wrap the whole value in quotes)"
        return errors + [f"frontmatter is not valid YAML: {detail}{hint}"], warnings

    if not isinstance(meta, dict):
        return errors + ["frontmatter is not a YAML mapping"], warnings

    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("missing required field 'name'")
    else:
        if not NAME_RE.match(name):
            errors.append(
                f"'name' is {name!r}: must be lowercase a-z, 0-9 and single hyphens, "
                "no leading/trailing/consecutive hyphens"
            )
        if len(name) > 64:
            errors.append(f"'name' is {len(name)} chars, max 64")
        parent = path.parent.name
        if parent != "template" and NAME_RE.match(name or "") and name != parent:
            errors.append(f"'name' is {name!r} but parent directory is {parent!r}: they must match")

    desc = meta.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("missing required field 'description'")
    elif len(desc) > 1024:
        errors.append(f"'description' is {len(desc)} chars, max 1024")

    compat = meta.get("compatibility")
    if isinstance(compat, str) and len(compat) > 500:
        errors.append(f"'compatibility' is {len(compat)} chars, max 500")

    unknown = sorted(set(map(str, meta.keys())) - SPEC_KEYS)
    if unknown:
        errors.append(f"non-spec frontmatter keys: {unknown} (allowed: {sorted(SPEC_KEYS)})")

    body_lines = text[match.end():].count("\n") + 1
    if body_lines > 500:
        warnings.append(f"body is {body_lines} lines; spec recommends keeping SKILL.md under 500")

    return errors, warnings


def main(argv):
    repo = Path(__file__).resolve().parent.parent.parent  # repo root when installed at .github/scripts/
    roots = [Path(a).resolve() for a in argv[1:]] or [repo]

    files = []
    for root in roots:
        if root.is_file():
            files.append(root)
            continue
        for path in sorted(root.rglob("SKILL.md")):
            if not SKIP_DIRS.intersection(path.parts):
                files.append(path)

    if not files:
        print("error: no SKILL.md files found", file=sys.stderr)
        return 2

    failed = 0
    for path in files:
        rel = os.path.relpath(path, Path.cwd())
        errors, warnings = check(path)
        for warning in warnings:
            print(f"WARN  {rel}: {warning}")
        if errors:
            failed += 1
            for error in errors:
                print(f"FAIL  {rel}: {error}")

    print(f"\n{len(files) - failed}/{len(files)} SKILL.md files pass the Agent Skills spec.")
    if failed:
        print(f"{failed} file(s) with errors. See https://agentskills.io/specification")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
