#!/usr/bin/env python3
"""
Validate all service stubs in app/services/.

This script:
1. Finds all .py files in app/services/ that are less than 100 bytes
2. Reads the file content and extracts the import target
3. Checks that the target file exists on disk
4. Reports any that don't resolve
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Get the project root (parent of scripts directory)
PROJECT_ROOT = Path(__file__).parent.parent


def find_stub_files() -> List[Path]:
    """Find all .py files in app/services/ that are less than 100 bytes."""
    services_dir = PROJECT_ROOT / "app" / "services"
    stubs = []
    
    if not services_dir.exists():
        print(f"ERROR: {services_dir} does not exist")
        return stubs
    
    for py_file in services_dir.rglob("*.py"):
        # Skip __pycache__ and __init__.py files
        if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
            continue
        
        file_size = py_file.stat().st_size
        if file_size < 100:
            stubs.append(py_file)
    
    return sorted(stubs)


def extract_import_target(file_path: Path) -> str | None:
    """Extract the import target from a stub file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        print(f"ERROR reading {file_path}: {e}")
        return None
    
    # Match pattern: from app.domains.X.services.Y import *
    pattern = r"from\s+(app\.domains\.[^\s]+)\s+import\s+\*"
    match = re.match(pattern, content)
    
    if match:
        return match.group(1)
    return None


def module_path_to_file_path(module_path: str) -> Path:
    """Convert a module import path to a file system path."""
    # app.domains.X.services.Y -> app/domains/X/services/Y/__init__.py or Y.py
    parts = module_path.split(".")
    
    # Try both as a package (__init__.py) and as a module (Y.py)
    base_path = PROJECT_ROOT / Path(*parts)
    
    paths_to_check = [
        base_path / "__init__.py",  # Package
        Path(str(base_path) + ".py"),  # Module
    ]
    
    return paths_to_check


def validate_stubs() -> Tuple[int, int, List[Tuple[Path, str]]]:
    """Validate all stub files.
    
    Returns:
        Tuple of (total_stubs, valid_stubs, broken_stubs)
        broken_stubs is a list of (stub_path, import_target) tuples
    """
    stubs = find_stub_files()
    valid = 0
    broken = []
    
    print(f"Found {len(stubs)} stub files in app/services/\n")
    print("Validating stubs...")
    print("-" * 80)
    
    for stub_path in stubs:
        import_target = extract_import_target(stub_path)
        
        if not import_target:
            print(f"⚠️  {stub_path.relative_to(PROJECT_ROOT)}: Could not parse import statement")
            broken.append((stub_path, "PARSE_ERROR"))
            continue
        
        # Check if target exists
        paths_to_check = module_path_to_file_path(import_target)
        found = False
        
        for target_path in paths_to_check:
            if target_path.exists():
                found = True
                break
        
        if found:
            valid += 1
            print(f"✓ {stub_path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"✗ {stub_path.relative_to(PROJECT_ROOT)}")
            print(f"  Import: {import_target}")
            print(f"  Expected paths:")
            for target_path in paths_to_check:
                print(f"    - {target_path.relative_to(PROJECT_ROOT)}")
            broken.append((stub_path, import_target))
    
    print("-" * 80)
    return len(stubs), valid, broken


def main():
    """Main entry point."""
    total, valid, broken = validate_stubs()
    
    print(f"\n{'='*80}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total stubs: {total}")
    print(f"Valid stubs: {valid}")
    print(f"Broken stubs: {len(broken)}")
    
    if broken:
        print(f"\n{'='*80}")
        print(f"BROKEN STUBS")
        print(f"{'='*80}")
        for stub_path, import_target in broken:
            print(f"\n{stub_path.relative_to(PROJECT_ROOT)}")
            print(f"  Import: {import_target}")
            
            if import_target != "PARSE_ERROR":
                paths_to_check = module_path_to_file_path(import_target)
                print(f"  Expected paths:")
                for target_path in paths_to_check:
                    print(f"    - {target_path.relative_to(PROJECT_ROOT)}")
    else:
        print("\n✓ All stubs are valid!")
    
    print(f"\n{'='*80}")
    return 0 if not broken else 1


if __name__ == "__main__":
    exit(main())
