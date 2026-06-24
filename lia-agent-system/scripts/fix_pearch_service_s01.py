from pathlib import Path

fpath = Path("/home/runner/workspace/lia-agent-system/app/domains/sourcing/services/pearch_service.py")
content = fpath.read_text()

lines = content.splitlines()
for i, line in enumerate(lines):
    if "FairnessGuard check skipped" in line and "PearchService" in line:
        print(f"Found at line {i+1}: {repr(line)}")
        new_lines = list(lines)
        new_lines[i] = line.replace(
            'logger.debug("[PearchService] FairnessGuard check skipped: %s", _fg_exc)',
            'logger.error(\n                "[PearchService] FairnessGuard check FAILED (pearch query proceeding without fairness verification): %s",\n                _fg_exc, exc_info=True,\n            )'
        )
        fpath.write_text("\n".join(new_lines) + "\n")
        print("WRITTEN")
        break
