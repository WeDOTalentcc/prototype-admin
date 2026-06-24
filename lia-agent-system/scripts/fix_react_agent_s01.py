from pathlib import Path

fpath = Path("/home/runner/workspace/lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py")
content = fpath.read_text()

# Find the line number with "FairnessGuard check skipped"
lines = content.splitlines()
for i, line in enumerate(lines):
    if "FairnessGuard check skipped" in line and "SourcingReActAgent" in line:
        print(f"Found at line {i+1}: {repr(line)}")
        # Show context
        print(f"Line {i}: {repr(lines[i-1])}")
        print(f"Line {i+1}: {repr(lines[i])}")
        if i+1 < len(lines):
            print(f"Line {i+2}: {repr(lines[i+1])}")
        
        # Replace logger.debug with logger.error + exc_info
        old_line = lines[i]
        # Change logger.debug to logger.error and add exc_info
        new_lines = list(lines)
        new_lines[i] = old_line.replace(
            'logger.debug("[SourcingReActAgent] FairnessGuard check skipped: %s", _fg_exc)',
            'logger.error(\n                "[SourcingReActAgent] FairnessGuard check FAILED (result served without fairness verification): %s",\n                _fg_exc, exc_info=True,\n            )'
        )
        new_content = "\n".join(new_lines) + "\n"
        fpath.write_text(new_content)
        print("WRITTEN")
        break

