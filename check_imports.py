#!/usr/bin/env python3
"""Check all imports used across the project files."""
import re
import importlib

files = ["ai_image_analyzer.py", "app.py", "api.py"]
stdlib = {
    "os", "sys", "io", "json", "struct", "re", "tempfile",
    "pathlib", "typing", "datetime", "collections",
    "functools", "math", "statistics", "itertools",
    "dataclasses", "warnings",
}

all_imports = {}
for fname in files:
    with open(fname, encoding="utf-8") as fh:
        content = fh.read()
    for m in re.finditer(r"^(?:from|import)\s+([\w\.]+)", content, re.MULTILINE):
        mod = m.group(1).split(".")[0]
        all_imports[mod] = None

print("Checking imports:")
for mod in sorted(all_imports):
    if mod in stdlib:
        print(f"  {mod:25s} [stdlib]")
        continue
    if mod == "ai_image_analyzer":
        print(f"  {mod:25s} [local module]")
        continue
    try:
        importlib.import_module(mod)
        print(f"  {mod:25s} [installed]")
        all_imports[mod] = True
    except ImportError:
        print(f"  {mod:25s} [NOT INSTALLED]")
        all_imports[mod] = False
