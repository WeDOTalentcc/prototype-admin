#!/usr/bin/env python3
"""
patch_fairness2.py - thorough rewrite of payload blocks in test_agent_fairness.py
"""

filepath = "/home/runner/workspace/docs/specs/qa/test_agent_fairness.py"

with open(filepath, "r") as f:
    content = f.read()

# --- Fix the first payload block (around line 1312) ---
old_block_1 = '''    payload = {
        "session_id": f"fairness-{candidate['id']}",
            "question_id": "q-fairness-001",
        "question": (
            "Descreva uma situação em que você enfrentou um desafio técnico complexo "
            "e como o resolveu. Use o método STAR (Situação, Tarefa, Ação, Resultado)."
        ),
        "response_text": candidate["wsi_answer"],
            "competency": "resolucao_problemas",
            "framework": "STAR",
        "candidate_id": candidate["id"],
    }'''

new_block_1 = '''    payload = {
        "session_id": f"fairness-{candidate['id']}",
        "question_id": "q-fairness-001",
        "candidate_id": candidate["id"],
        "job_vacancy_id": f"fairness-job-{candidate['role'].lower().replace(' ', '-')}",
        "question_text": (
            "Descreva uma situação em que você enfrentou um desafio técnico complexo "
            "e como o resolveu. Use o método STAR (Situação, Tarefa, Ação, Resultado)."
        ),
        "response_text": candidate["wsi_answer"],
        "competency": "resolucao_problemas",
        "framework": "STAR",
    }'''

if old_block_1 in content:
    content = content.replace(old_block_1, new_block_1)
    print("✅ Fixed first payload block")
else:
    print("❌ First payload block not found — scanning for variants...")
    # Try to find where the payload starts
    idx = content.find('"session_id": f"fairness-{candidate[\'id\']}",')
    if idx >= 0:
        print(f"  Found session_id at char {idx}")
        print(f"  Context: {repr(content[idx-200:idx+400])}")
    else:
        print("  session_id not found either")

# --- Fix the second payload block (around line 1418) ---
old_block_2 = '''    payload = {
        "session_id": f"fairness-{candidate['id']}",
            "question_id": "q-fairness-001",
        "question": (
            "Descreva uma situação em que você enfrentou um desafio técnico complexo "
            "e como o resolveu. Use o método STAR (Situação, Tarefa, Ação, Resultado)."
        ),
        "response_text": candidate["wsi_answer"],
            "competency": "resolucao_problemas",
            "framework": "STAR",
        "candidate_id": candidate["id"],
    }'''

# Second block is same as first (both got patched to same state)
# Check if there's a second occurrence
count = content.count(new_block_1)
print(f"  New block 1 occurs {count} times in file")

# --- Fix score extraction: raw.get("score") ---
# Check for any remaining wsi_score references
if 'wsi_score' in content:
    content = content.replace('raw.get("wsi_score")', 'raw.get("score")')
    print("✅ Fixed wsi_score -> score")
else:
    print("✅ wsi_score already fixed")

# --- Fix job_vacancy_id in second function if needed ---
# Find all payload blocks that still have wrong fields
import re
remaining_old = re.findall(r'"question":\s*\(', content)
if remaining_old:
    print(f"❌ Still found {len(remaining_old)} old 'question' field(s) — fixing...")
    # Replace all remaining instances of "question": ( ... ) with "question_text": ( ... )
    content = re.sub(r'"question":\s*\(', '"question_text": (', content)
    print("✅ Fixed remaining 'question' -> 'question_text'")
else:
    print("✅ No remaining 'question' field found")

# Fix remaining bad indentation in payload blocks
bad_indent_patterns = [
    ('            "question_id": "q-fairness-001",', '        "question_id": "q-fairness-001",'),
    ('            "competency": "resolucao_problemas",', '        "competency": "resolucao_problemas",'),
    ('            "framework": "STAR",', '        "framework": "STAR",'),
]
for old, new in bad_indent_patterns:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ Fixed indentation: {old.strip()[:40]}")

# --- Ensure job_vacancy_id is present in all payload blocks ---
# Find payload blocks that have session_id but not job_vacancy_id
blocks_missing_jvid = []
for m in re.finditer(r'"session_id".*?"candidate_id".*?(?!"job_vacancy_id")', content, re.DOTALL):
    if 'job_vacancy_id' not in content[m.start():m.end()+200]:
        blocks_missing_jvid.append(m.start())

print(f"  Payload blocks missing job_vacancy_id: {len(blocks_missing_jvid)}")

with open(filepath, "w") as f:
    f.write(content)

# Final verification
print("\n=== Final Verification ===")
with open(filepath, "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "localhost:8000/api/v1/wsi",
        "session_id", "question_id", "job_vacancy_id",
        "question_text", "response_text", "competency", "framework",
        "wsi_score", '"question":', "candidate_answer"
    ]):
        print(f"  {i:4d}: {line.rstrip()}")

print("\nDone!")
