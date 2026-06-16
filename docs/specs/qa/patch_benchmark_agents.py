#!/usr/bin/env python3
"""
patch_benchmark_agents.py — Fix WSI endpoint and payload schema in benchmark_agents.py
"""
import re

filepath = "/home/runner/workspace/docs/specs/qa/benchmark_agents.py"

with open(filepath, "r") as f:
    content = f.read()

# -------------------------------------------------------------------------
# 1. Fix call_endpoint to support absolute URLs in endpoint field
# -------------------------------------------------------------------------
old_url_line = '    url = base_url.rstrip("/") + endpoint'
new_url_line = '''    # Support absolute endpoint URLs (e.g., for direct backend access)
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        url = endpoint
    else:
        url = base_url.rstrip("/") + endpoint'''

if old_url_line in content:
    content = content.replace(old_url_line, new_url_line)
    print("✅ Fixed call_endpoint to support absolute URLs")
else:
    print("❌ call_endpoint url line not found")

# Also fix fallback URL construction
old_fallback1 = '            fallback_url = base_url.rstrip("/") + fallback_endpoint\n            fb_payload = fallback_payload or payload\n            try:\n                if HAS_HTTPX:\n                    status, data, elapsed = await post_async('
new_fallback1 = '''            fallback_url = fallback_endpoint if fallback_endpoint.startswith("http") else base_url.rstrip("/") + fallback_endpoint
            fb_payload = fallback_payload or payload
            try:
                if HAS_HTTPX:
                    status, data, elapsed = await post_async('''
if old_fallback1 in content:
    content = content.replace(old_fallback1, new_fallback1)
    print("✅ Fixed fallback URL construction (1)")

old_fallback2 = '        fallback_url = base_url.rstrip("/") + fallback_endpoint\n        fb_payload = fallback_payload or payload\n        try:\n            if HAS_HTTPX:\n                status2, data2, elapsed2 = await post_async('
new_fallback2 = '''        fallback_url = fallback_endpoint if fallback_endpoint.startswith("http") else base_url.rstrip("/") + fallback_endpoint
        fb_payload = fallback_payload or payload
        try:
            if HAS_HTTPX:
                status2, data2, elapsed2 = await post_async('''
if old_fallback2 in content:
    content = content.replace(old_fallback2, new_fallback2)
    print("✅ Fixed fallback URL construction (2)")

# -------------------------------------------------------------------------
# 2. Fix WSI endpoints — change to direct backend URL
# -------------------------------------------------------------------------
content = content.replace(
    '"endpoint": "/api/lia/api/wsi/analyze-response/",',
    '"endpoint": "http://localhost:8000/api/v1/wsi/analyze-response",'
)
count_wsi = content.count('"endpoint": "http://localhost:8000/api/v1/wsi/analyze-response"')
print(f"✅ Fixed WSI endpoints ({count_wsi} occurrences)")

# -------------------------------------------------------------------------
# 3. Fix WSI payload schemas
#    Old: {job_id, question, candidate_answer, evaluation_criteria}
#    New: {session_id, question_id, candidate_id, job_vacancy_id, question_text, response_text, competency, framework}
# -------------------------------------------------------------------------

# We need to replace the 4 WSI body blocks. Let's do it with regex.
# Pattern: "body": { "job_id": BENCHMARK_JOB_ID, "question": "...", "candidate_answer": (...), "evaluation_criteria": "..." }

def fix_wsi_body(match):
    """Replace old WSI payload with new schema."""
    original = match.group(0)

    # Extract the candidate_answer text
    answer_match = re.search(r'"candidate_answer":\s*\((.*?)\),\s*"evaluation_criteria"', original, re.DOTALL)
    if not answer_match:
        answer_match = re.search(r'"candidate_answer":\s*\((.*?)\),', original, re.DOTALL)

    if answer_match:
        answer_text = answer_match.group(1).strip()
    else:
        answer_text = '"Resposta de teste"'

    # Extract wsi_id from the surrounding context (not available here, use counter)
    new_body = f'''"body": {{
            "session_id": f"benchmark-wsi-{{BENCHMARK_JOB_ID}}",
            "question_id": "q-benchmark-001",
            "candidate_id": "candidate-benchmark-001",
            "job_vacancy_id": BENCHMARK_JOB_ID,
            "question_text": "Descreva uma situação em que você liderou um projeto complexo de dados",
            "response_text": ({answer_text}),
            "competency": "lideranca_tecnica",
            "framework": "STAR",
        }}'''
    return new_body

# Find and replace all 4 WSI body blocks
pattern = r'"body":\s*\{\s*"job_id":\s*BENCHMARK_JOB_ID,.*?"evaluation_criteria":[^}]*\}'
matches = re.findall(pattern, content, re.DOTALL)
print(f"  Found {len(matches)} WSI body blocks to fix")

content = re.sub(pattern, fix_wsi_body, content, flags=re.DOTALL)

# -------------------------------------------------------------------------
# 4. Also fix any f-string issues — BENCHMARK_JOB_ID is a variable, not a string
# -------------------------------------------------------------------------
# The f-string uses BENCHMARK_JOB_ID as a variable — but in the body dict,
# it was already a variable reference. Let's check what was generated.

# Fix: session_id should be a string concat, not f-string (BENCHMARK_JOB_ID is already a var)
# Actually f-string is fine since it references the variable directly

# -------------------------------------------------------------------------
# 5. Verify no old schema remains
# -------------------------------------------------------------------------
remaining = re.findall(r'"job_id":\s*BENCHMARK_JOB_ID', content)
print(f"  Remaining old 'job_id: BENCHMARK_JOB_ID': {len(remaining)}")

remaining_ca = re.findall(r'"candidate_answer":', content)
print(f"  Remaining 'candidate_answer': {len(remaining_ca)}")

with open(filepath, "w") as f:
    f.write(content)

print("\n=== Verification ===")
with open(filepath, "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "localhost:8000/api/v1/wsi",
        "session_id", "question_id", "job_vacancy_id",
        "question_text", "response_text",
        "job_id.*BENCHMARK",
        "candidate_answer",
        "/api/lia/api/wsi"
    ]):
        if any(kw in line for kw in ["localhost:8000", "session_id", "question_id", "job_vacancy_id", "question_text", "response_text", "candidate_answer", "/api/lia/api/wsi"]):
            print(f"  {i:4d}: {line.rstrip()}")

print("\nDone!")
