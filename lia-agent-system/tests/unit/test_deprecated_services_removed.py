"""UC-P1-22: Zero-caller deprecated services must be removed; remaining must have DeprecationWarning."""
import os
import glob


# Base path for services (relative to project root — tests run from lia-agent-system/)
SERVICES_DIR = "app/shared/services"


def test_human_review_sampling_removed():
    """human_review_sampling_service had 0 callers — must be deleted."""
    path = os.path.join(SERVICES_DIR, "human_review_sampling_service.py")
    assert not os.path.exists(path), (
        f"{path} still exists — should have been deleted (UC-P1-22: 0 callers confirmed)."
    )


def test_no_rails_deprecated_services_without_warnings():
    """All remaining RAILS-DEPRECATED services must have warnings.warn(DeprecationWarning)."""
    missing_warnings = []
    for fpath in sorted(glob.glob(f"{SERVICES_DIR}/*.py")):
        with open(fpath) as fh:
            content = fh.read()
        if "RAILS-DEPRECATED" in content:
            if "warnings.warn" not in content:
                missing_warnings.append(os.path.basename(fpath))
    assert not missing_warnings, (
        f"RAILS-DEPRECATED services without warnings.warn: {missing_warnings}. "
        "Add a module-level warnings.warn(DeprecationWarning) to each."
    )


def test_deprecated_warning_includes_migration_guidance():
    """Each DeprecationWarning must reference rails_adapter and UC-P1-22."""
    incomplete = []
    for fpath in sorted(glob.glob(f"{SERVICES_DIR}/*.py")):
        with open(fpath) as fh:
            content = fh.read()
        if "RAILS-DEPRECATED" in content and "warnings.warn" in content:
            # Must mention rails_adapter or Rails and reference UC-P1-22
            if "UC-P1-22" not in content:
                incomplete.append(os.path.basename(fpath))
    assert not incomplete, (
        f"Deprecation warnings missing UC-P1-22 reference: {incomplete}"
    )
