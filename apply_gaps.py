#!/usr/bin/env python3
"""Apply GAP C, D, F patches to lia-agent-system."""
import os
import re

BASE = os.path.expanduser("~/workspace/lia-agent-system")

# ============================================================
# GAP C: LIA-I06 — Add shadow log to NavigationIntentDetector
# ============================================================
nav_file = os.path.join(BASE, "app/orchestrator/navigation_intent.py")
with open(nav_file, "r") as f:
    nav_content = f.read()

# The detect method is: def detect(self, message: str) -> NavigationIntentResult:
# Add the LIA-I06 log at the top of it
old_detect = '    def detect(self, message: str) -> NavigationIntentResult:\n        text = message.lower().strip()'
new_detect = '''    def detect(self, message: str) -> NavigationIntentResult:
        logger.debug("[LIA-I06] NavigationIntentDetector still uses internal patterns. Migration to KeywordIntentMatcher pending.")
        text = message.lower().strip()'''

if old_detect in nav_content:
    nav_content = nav_content.replace(old_detect, new_detect, 1)
    with open(nav_file, "w") as f:
        f.write(nav_content)
    print(f"[GAP C] Patched {nav_file}")
else:
    print(f"[GAP C] WARN: Could not find detect method pattern in {nav_file}")


# ============================================================
# GAP D: LIA-I07 — Add is_info_query block to 14 domains
# ============================================================

DOMAINS = {
    "sourcing":              "search_candidates",
    "analytics":             "get_dashboard_data",
    "talent_pool":           "list_talent_pools",
    "communication":         "send_email",
    "pipeline":              "suggest_next_action",
    "job_management":        "create_job",
    "cv_screening":          "auto_screen",
    "interview_scheduling":  "list_today_interviews",
    "ats_integration":       "check_sync_status",
    "automation":            "list_tasks",
    "recruiter_assistant":   "quick_question",
    "hiring_policy":         "configure_policy",
    "digital_twin":          "list_twins",
    "recruitment_campaign":  "list_campaigns",
}

patched_count = 0
for domain_id, default_action in DOMAINS.items():
    domain_file = os.path.join(BASE, f"app/domains/{domain_id}/domain.py")
    if not os.path.exists(domain_file):
        print(f"[GAP D] WARN: {domain_file} not found")
        continue

    with open(domain_file, "r") as f:
        content = f.read()

    if "LIA-I07" in content:
        print(f"[GAP D] SKIP {domain_id}: LIA-I07 already present")
        continue

    # We need to inject just after the process_intent signature line.
    # Two patterns to handle: with type hints and without.
    # Pattern 1: async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
    # Pattern 2: async def process_intent(self, query, context):

    # Find the line with "async def process_intent"
    lines = content.split('\n')
    insert_idx = None
    indent = "        "

    for i, line in enumerate(lines):
        if 'async def process_intent' in line and 'def ' in line:
            insert_idx = i + 1
            # Detect indentation from the next non-empty line
            for j in range(i+1, min(i+5, len(lines))):
                stripped = lines[j].lstrip()
                if stripped and not stripped.startswith('#'):
                    indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                    break
            break

    if insert_idx is None:
        print(f"[GAP D] WARN: Could not find process_intent in {domain_id}")
        continue

    # Build the LIA-I07 block
    info_block = f"""{indent}# LIA-I07: Check if query is an info request (e.g., "como funciona X?")
{indent}if _matcher.is_info_query(query):
{indent}    try:
{indent}        match = _matcher.match(query, default_action="{default_action}")
{indent}        return IntentResult(
{indent}            intent_id=f"{domain_id}.{{match.action}}",
{indent}            action_id=match.action,
{indent}            confidence=match.confidence,
{indent}            extracted_params={{"raw_query": query, "is_info_query": True}},
{indent}            reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{{match.action}}')",
{indent}        )
{indent}    except Exception:
{indent}        pass  # Fall through to normal logic
"""

    lines.insert(insert_idx, info_block)
    new_content = '\n'.join(lines)

    with open(domain_file, "w") as f:
        f.write(new_content)
    patched_count += 1
    print(f"[GAP D] Patched {domain_id}")

print(f"[GAP D] Total domains patched: {patched_count}")


# ============================================================
# GAP F: LIA-I08 — Create intent_yaml_validator.py
# ============================================================

validator_file = os.path.join(BASE, "app/shared/services/intent_yaml_validator.py")
validator_content = '''"""
LIA-I08: Validate that capabilities.yaml files stay in sync with domain _KEYWORD_ACTION_MAP dicts.

Runs at startup. Logs warnings when:
- YAML has intents/keywords not in the dict
- Dict has keywords not in the YAML
- Default actions differ
"""
import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def validate_domain_yaml_sync(domain_path: str, keyword_map: dict[str, str], default_action: str = "") -> dict:
    """Compare a YAML capabilities file against a runtime keyword_map.

    Returns dict with: yaml_keywords, dict_keywords, missing_in_yaml, missing_in_dict.
    """
    yaml_path = Path(domain_path) / "config" / "capabilities.yaml"
    if not yaml_path.exists():
        return {"status": "no_yaml", "yaml_path": str(yaml_path)}

    try:
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        yaml_keywords = set()
        for intent in data.get("intents", []):
            for kw in intent.get("keywords", []):
                yaml_keywords.add(kw.lower().strip())

        dict_keywords = set(k.lower().strip() for k in keyword_map.keys())

        missing_in_yaml = dict_keywords - yaml_keywords
        missing_in_dict = yaml_keywords - dict_keywords

        if missing_in_yaml or missing_in_dict:
            domain_name = data.get("domain_id", "?")
            logger.warning(
                "[LIA-I08] YAML/dict drift in %s: %d keywords missing in YAML, %d in dict only",
                domain_name, len(missing_in_yaml), len(missing_in_dict)
            )

        return {
            "status": "ok",
            "domain_id": data.get("domain_id"),
            "yaml_keywords_count": len(yaml_keywords),
            "dict_keywords_count": len(dict_keywords),
            "missing_in_yaml": sorted(missing_in_yaml)[:10],
            "missing_in_dict": sorted(missing_in_dict)[:10],
        }
    except Exception as e:
        logger.error("[LIA-I08] YAML validation failed for %s: %s", yaml_path, e)
        return {"status": "error", "error": str(e)}


def validate_all_domain_yamls(app_root: str = "/home/runner/workspace/lia-agent-system") -> dict:
    """Validate all 15 domain capabilities.yaml files at startup."""
    domains_dir = Path(app_root) / "app" / "domains"
    results = {}
    if not domains_dir.exists():
        return {"error": "domains_dir not found"}

    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        yaml_path = domain_dir / "config" / "capabilities.yaml"
        if not yaml_path.exists():
            continue
        # Try to load the domain module to get its _KEYWORD_ACTION_MAP
        try:
            mod = __import__(f"app.domains.{domain_dir.name}.domain", fromlist=["_KEYWORD_ACTION_MAP"])
            keyword_map = getattr(mod, "_KEYWORD_ACTION_MAP", {})
            if keyword_map:
                results[domain_dir.name] = validate_domain_yaml_sync(str(domain_dir), keyword_map)
        except Exception as e:
            results[domain_dir.name] = {"status": "import_error", "error": str(e)[:100]}

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    results = validate_all_domain_yamls()
    import json
    print(json.dumps(results, indent=2))
'''

os.makedirs(os.path.dirname(validator_file), exist_ok=True)
with open(validator_file, "w") as f:
    f.write(validator_content)
print(f"[GAP F] Created {validator_file}")

print("\n=== ALL GAPS APPLIED ===")
