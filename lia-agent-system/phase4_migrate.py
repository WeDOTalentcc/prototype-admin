#!/usr/bin/env python3
"""
Phase 4 DDD migration: copy services to domain layer, rewrite originals as shims.
"""
import shutil
from pathlib import Path

WORKSPACE = Path("/home/runner/workspace/lia-agent-system")

# Domain mapping from instructions
DOMAIN_MAP = {
    "candidate_channel_selector.py": "candidates",
    "candidate_comparison_service.py": "candidates",
    "candidate_enrichment_service.py": "candidates",
    "candidate_feedback_service.py": "candidates",
    "candidate_goal_service.py": "candidates",
    "company_configuration_service.py": "company",
    "company_route_service.py": "company",
    "company_scraper_service.py": "company",
    "email_tracking_service.py": "communication",
    "job_requirements_service.py": "job_management",
    "job_stage_config.py": "job_management",
    "billing_service.py": "billing",
    "activity_service.py": "analytics",
    "triagem_session_service.py": "recruitment",
    "cv_parser_service.py": "cv_screening",
    "llm.py": "ai",
    "ai_cache_service.py": "ai",
    "multimodal_service.py": "ai",
    "voice_screening_orchestrator.py": "voice",
    "wsi_voice_transcription_service.py": "voice",
    "sourcing_pipeline_service.py": "sourcing",
    "automation_notification_service.py": "automation",
    "calendar_service.py": "interview_scheduling",
    "scheduling_service.py": "interview_scheduling",
}

# Services that already exist in their domain (from directory listing)
ALREADY_IN_DOMAIN = {
    "calendar_service.py": "app/domains/interview_scheduling/services",
    "scheduling_service.py": "app/domains/interview_scheduling/services",
}

# Collect all top-level service files
service_dir = WORKSPACE / "app/services"
all_service_files = sorted([
    f.name for f in service_dir.iterdir()
    if f.is_file() and f.suffix == ".py" and f.name != "__init__.py"
])

print(f"Found {len(all_service_files)} service files to process")

errors = []
copied = []
shimmed = []
already_existed = []

for filename in all_service_files:
    src = service_dir / filename

    # Check if it's a shim already
    content = src.read_text()
    if "Backwards-compatibility shim" in content:
        print(f"  SKIP (already shim): {filename}")
        continue

    # Determine domain
    domain = DOMAIN_MAP.get(filename, "shared")

    # Determine target directory
    if domain == "shared":
        target_dir_rel = "app/shared/services"
    else:
        target_dir_rel = f"app/domains/{domain}/services"

    target_dir = WORKSPACE / target_dir_rel

    # Ensure target dir and __init__.py exist
    target_dir.mkdir(parents=True, exist_ok=True)
    init_file = target_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()

    # Also ensure domain __init__.py exists
    domain_init = target_dir.parent / "__init__.py"
    if not domain_init.exists():
        domain_init.touch()

    target = target_dir / filename

    if target.exists():
        print(f"  EXISTS (no copy): {filename} in {target_dir_rel}")
        already_existed.append(filename)
    else:
        try:
            shutil.copy2(src, target)
            print(f"  COPIED: {filename} -> {target_dir_rel}")
            copied.append(filename)
        except Exception as e:
            print(f"  ERROR copying {filename}: {e}")
            errors.append((filename, str(e)))
            continue

    # Write shim back to app/services/
    stem = filename[:-3]
    # Convert path to module: app/domains/candidates/services -> app.domains.candidates.services
    domain_module = target_dir_rel.replace("/", ".")
    shim_content = (
        '"""Backwards-compatibility shim — canonical implementation in domain layer."""\n'
        f'from {domain_module}.{stem} import *  # noqa: F401, F403\n'
    )
    src.write_text(shim_content)
    print(f"  SHIM:   app/services/{filename}")
    shimmed.append(filename)

print()
print("=" * 60)
print(f"Total processed: {len(all_service_files)}")
print(f"Copied to domain: {len(copied)}")
print(f"Already existed (no overwrite): {len(already_existed)}")
print(f"Shimmed in app/services/: {len(shimmed)}")
print(f"Errors: {len(errors)}")
if errors:
    for f, e in errors:
        print(f"  ERROR: {f}: {e}")
