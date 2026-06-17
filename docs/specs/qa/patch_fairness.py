#!/usr/bin/env python3
"""Patch test_agent_fairness.py with correct WSI endpoint and schema."""

import re

filepath = "/home/runner/workspace/docs/specs/qa/test_agent_fairness.py"

with open(filepath, "r") as f:
    content = f.read()

# 1. Fix endpoint in _score_candidate_wsi (line ~1311)
content = content.replace(
    'endpoint = f"{base_url.rstrip(\'/\')}/api/lia/api/wsi/analyze-response"',
    'endpoint = "http://localhost:8000/api/v1/wsi/analyze-response"'
)

# 2. Fix payload schema — replace the payload dict block (both occurrences)
old_payload = '''"job_id": f"fairness-test-{candidate['role'].lower().replace(' ', '-')}",'''
new_payload_start = '''"session_id": f"fairness-{candidate['id']}",
            "question_id": "q-fairness-001",'''

content = content.replace(
    '"job_id": f"fairness-test-{candidate[\'role\'].lower().replace(\' \', \'-\')}",',
    '"session_id": f"fairness-{candidate[\'id\']}",\n            "question_id": "q-fairness-001",'
)

# 3. Replace question field
content = content.replace(
    '"question": "Descreva uma situação em que você enfrentou um desafio técnico complexo. Como você abordou o problema e qual foi o resultado?",',
    '"job_vacancy_id": f"fairness-job-{candidate[\'role\'].lower().replace(\' \', \'-\')}",\n            "question_text": "Descreva uma situação em que você enfrentou um desafio técnico complexo. Como você abordou o problema e qual foi o resultado?",'
)

# 4. Replace candidate_answer field
content = content.replace(
    '"candidate_answer": candidate["wsi_answer"],',
    '"response_text": candidate["wsi_answer"],\n            "competency": "resolucao_problemas",\n            "framework": "STAR",'
)

# 5. Fix wsi_score -> score extraction
content = content.replace(
    'or raw.get("wsi_score")',
    'or raw.get("score")'
)

# 6. Fix the summary print line
content = content.replace(
    'print(f"\\nPOST {base}/api/lia/api/wsi/analyze-response")',
    'print(f"\\nPOST http://localhost:8000/api/v1/wsi/analyze-response")'
)

with open(filepath, "w") as f:
    f.write(content)

print("Patch applied. Verifying...")

# Verify
with open(filepath, "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if any(kw in line for kw in ["wsi/analyze-response", "session_id", "question_id", "response_text", "competency", "framework", "wsi_score"]):
        print(f"  Line {i}: {line.rstrip()}")

print("\nDone!")
