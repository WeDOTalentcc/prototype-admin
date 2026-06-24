from pathlib import Path
import re

REGISTRY_DIR = Path("/home/runner/workspace/lia-agent-system/app/domains/sourcing/agents/")
REGISTRIES = [
    "github_tool_registry",
    "stackoverflow_tool_registry",
    "diversity_tool_registry",
    "passive_pipeline_tool_registry",
    "referral_tool_registry",
    "nurture_sequence_tool_registry",
]

IMPORT_SNIPPET = "from app.domains.sourcing.fairness import run_sourcing_fairness_check"

for reg_name in REGISTRIES:
    fpath = REGISTRY_DIR / f"{reg_name}.py"
    content = fpath.read_text()
    lines = content.splitlines()
    
    # Find the except Exception as _fg_exc line
    fg_exc_lineno = None
    for i, line in enumerate(lines):
        if "_fg_exc" in line and "except" in line:
            fg_exc_lineno = i
            break
    
    if fg_exc_lineno is None:
        print(f"SKIP (no _fg_exc): {reg_name}")
        continue
    
    # Find the try: line above it
    try_lineno = None
    for i in range(fg_exc_lineno - 1, max(0, fg_exc_lineno - 20), -1):
        if lines[i].strip() == "try:":
            try_lineno = i
            break
    
    if try_lineno is None:
        print(f"SKIP (no try:): {reg_name}")
        continue
    
    # Get indentation
    try_indent = lines[try_lineno][:len(lines[try_lineno]) - len(lines[try_lineno].lstrip())]
    inner_indent = try_indent + "    "
    
    # Extract check argument
    check_arg = "query_str"
    for i in range(try_lineno + 1, fg_exc_lineno):
        stripped = lines[i].strip()
        if ".check(" in stripped:
            m = re.search(r"\.check\(([^)]+)\)", stripped)
            if m:
                check_arg = m.group(1).strip()
            break
    
    # Find end of except block
    except_indent = len(lines[fg_exc_lineno]) - len(lines[fg_exc_lineno].lstrip())
    except_body_end = fg_exc_lineno + 1
    while except_body_end < len(lines):
        line = lines[except_body_end]
        if not line.strip():
            except_body_end += 1
            continue
        cur_indent = len(line) - len(line.lstrip())
        if cur_indent <= except_indent:
            break
        except_body_end += 1
    
    # Find is_blocked return block inside the old try
    blocked_return_lines = []
    in_blocked = False
    blocked_indent = None
    for i in range(try_lineno + 1, fg_exc_lineno):
        stripped = lines[i].strip()
        if "is_blocked" in stripped and "if" in stripped:
            in_blocked = True
            blocked_indent = len(lines[i]) - len(lines[i].lstrip())
            blocked_return_lines.append(lines[i])
            continue
        if in_blocked:
            if not lines[i].strip():
                break
            cur_indent = len(lines[i]) - len(lines[i].lstrip())
            if cur_indent > blocked_indent:
                blocked_return_lines.append(lines[i])
            else:
                break
    
    # Replace _fg_result.educational_message with _fg_block_msg in return block
    blocked_return_new = "\n".join(blocked_return_lines).replace(
        "_fg_result.educational_message",
        "_fg_block_msg"
    )
    
    # Check if FairnessGuard import is local (inside the try block)
    fg_import_local = any(
        "from app.shared.compliance.fairness_guard import FairnessGuard" in lines[i]
        for i in range(try_lineno + 1, fg_exc_lineno)
    )
    
    # Build new block
    new_block_parts = []
    if fg_import_local:
        new_block_parts.append(f"{try_indent}from app.shared.compliance.fairness_guard import FairnessGuard")
    new_block_parts.append(f"{try_indent}_fg_blocked, _fg_block_msg = run_sourcing_fairness_check(")
    new_block_parts.append(f"{inner_indent}FairnessGuard().check, {check_arg}, registry_name=\"{reg_name}\",")
    new_block_parts.append(f"{try_indent})")
    new_block_parts.append(f"{try_indent}if _fg_blocked:")
    if blocked_return_new.strip():
        for bl in blocked_return_new.splitlines():
            new_block_parts.append(bl)
    else:
        fallback_return = (
            f'{inner_indent}return {{"success": False, "data": {{}}, '
            f'"message": _fg_block_msg or "Busca bloqueada por criterio discriminatorio.", '
            f'"fairness_blocked": True}}'
        )
        new_block_parts.append(fallback_return)
    
    new_block = "\n".join(new_block_parts)
    
    # Get the old block to replace
    old_block = "\n".join(lines[try_lineno:except_body_end])
    
    print(f"\n=== {reg_name} ===")
    print(f"try_line={try_lineno+1}, fg_exc_line={fg_exc_lineno+1}, except_end={except_body_end}")
    print(f"check_arg={check_arg!r}, fg_import_local={fg_import_local}")
    print(f"OLD ({except_body_end - try_lineno} lines):\n{old_block[:400]}")
    print(f"NEW ({len(new_block_parts)} lines):\n{new_block[:400]}")
    
    new_content = content.replace(old_block, new_block, 1)
    if new_content == content:
        print(f"  WARNING: no replacement made for {reg_name}")
        continue
    
    # Add import at top if not present
    if IMPORT_SNIPPET not in new_content:
        new_lines = new_content.splitlines()
        last_import_idx = 0
        for i, line in enumerate(new_lines):
            if line.startswith("import ") or line.startswith("from "):
                last_import_idx = i
        new_lines.insert(last_import_idx + 1, IMPORT_SNIPPET)
        new_content = "\n".join(new_lines) + "\n"
    
    fpath.write_text(new_content)
    print(f"  WRITTEN OK")

print("\nDONE")
