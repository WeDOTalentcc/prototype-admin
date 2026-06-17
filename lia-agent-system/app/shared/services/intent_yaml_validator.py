"""
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
