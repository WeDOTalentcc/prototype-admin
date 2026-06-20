#!/usr/bin/env python3
"""
FASE 5 — H1+H3+H4+H2-warning patches.

Site A: wizard_service_tools.py — _publish_job_fastapi vacancy constructor
        Adds recruiter/manager/stakeholders/created_by fields.
Site B: wizard_service_tools.py — qs_repo.insert_set created_by=None
        Replaces hardcoded None with _uid filter.
Site C: wizard_session_service.py — after parsed_manager_email assignment
        Adds domain-mismatch warning.
"""
import sys

# ── Site A + B (wizard_service_tools.py) ─────────────────────────────────────
FILE_AB = "app/domains/job_creation/orchestrator/wizard_service_tools.py"

with open(FILE_AB, encoding="utf-8") as f:
    src_ab = f.read()

# Site A — vacancy constructor (replace JUST the constructor block, prepend _uid)
OLD_A = (
    "        repo = JobVacancyCRUDRepository(db)\n"
    "        vacancy = _JobVacancyModel(\n"
    "            company_id=company_id,\n"
    "            title=title,\n"
    "            description=description,\n"
    "            responsibilities=responsibilities if isinstance(responsibilities, list) else [],\n"
    "            technical_requirements=skills_obrigatorias if isinstance(skills_obrigatorias, list) else [],\n"
    "            department=department,\n"
    "            location=location,\n"
    "            seniority_level=seniority,\n"
    "            work_model=work_model,\n"
    "            salary_range=salary_range,\n"
    "            status=\"Ativa\",\n"
    "        )\n"
)

NEW_A = (
    "        repo = JobVacancyCRUDRepository(db)\n"
    "        # H1+H3+H4: identidade + stakeholders + audit created_by\n"
    "        # Fonte: state (unica disponivel dentro de _publish_job_fastapi).\n"
    "        # \"anonymous\" e string vazia sao filtrados — created_by=None significa\n"
    "        # \"sem autor identificado\", que e semanticamente correto.\n"
    "        _uid = state.get(\"user_id\") or \"\"\n"
    "        vacancy = _JobVacancyModel(\n"
    "            company_id=company_id,\n"
    "            title=title,\n"
    "            description=description,\n"
    "            responsibilities=responsibilities if isinstance(responsibilities, list) else [],\n"
    "            technical_requirements=skills_obrigatorias if isinstance(skills_obrigatorias, list) else [],\n"
    "            department=department,\n"
    "            location=location,\n"
    "            seniority_level=seniority,\n"
    "            work_model=work_model,\n"
    "            salary_range=salary_range,\n"
    "            status=\"Ativa\",\n"
    "            # H1: identidade do recrutador/gestor (nodes/publish.py ja popula no graph path)\n"
    "            recruiter=state.get(\"parsed_recruiter_name\") or \"\",\n"
    "            recruiter_email=state.get(\"parsed_recruiter_email\") or \"\",\n"
    "            manager=state.get(\"parsed_manager_name\") or \"\",\n"
    "            manager_email=state.get(\"parsed_manager_email\") or \"\",\n"
    "            # H3: stakeholders definidos via set_stakeholders (descartados antes deste fix)\n"
    "            stakeholders=state.get(\"parsed_stakeholders\") or [],\n"
    "            # H1: criador da vaga — filtra \"anonymous\" (truthy mas invalido)\n"
    "            created_by=_uid if _uid not in (\"\", \"anonymous\") else None,\n"
    "        )\n"
)

if OLD_A not in src_ab:
    print("ERROR: Site A — OLD block not found.")
    sys.exit(1)
if src_ab.count(OLD_A) != 1:
    print(f"ERROR: Site A — {src_ab.count(OLD_A)} occurrences, expected 1.")
    sys.exit(1)

src_ab = src_ab.replace(OLD_A, NEW_A, 1)
print("OK: Site A patched (vacancy constructor + _uid)")

# Site B — created_by=None in insert_set
# The old text is specific enough: "source" + "wizard_approved" + "created_by=None" sequence
OLD_B = (
    "                    source=\"wizard_approved\",\n"
    "                    created_by=None,\n"
)

NEW_B = (
    "                    source=\"wizard_approved\",\n"
    "                    # H4: _uid definido em Site A — mesmo bloco async with, em scope\n"
    "                    created_by=_uid if _uid not in (\"\", \"anonymous\") else None,\n"
)

if OLD_B not in src_ab:
    print("ERROR: Site B — OLD block not found.")
    sys.exit(1)
if src_ab.count(OLD_B) != 1:
    print(f"ERROR: Site B — {src_ab.count(OLD_B)} occurrences, expected 1.")
    sys.exit(1)

src_ab = src_ab.replace(OLD_B, NEW_B, 1)
print("OK: Site B patched (created_by=None → _uid filter in insert_set)")

with open(FILE_AB, "w", encoding="utf-8") as f:
    f.write(src_ab)
print(f"OK: {FILE_AB} written")

# ── Site C (wizard_session_service.py) ───────────────────────────────────────
FILE_C = "app/domains/job_creation/services/wizard_session_service.py"

with open(FILE_C, encoding="utf-8") as f:
    src_c = f.read()

OLD_C = (
    "            if _email.lower() != _recruiter_email:\n"
    "                state[\"parsed_manager_email\"] = _email\n"
    "                logger.info(\n"
    "                    \"[WizardOrchestrator] manager_email capturado deterministicamente \"\n"
    "                    \"(len=%d) thread=%s\", len(_email), thread_id,\n"
    "                )\n"
)

NEW_C = (
    "            if _email.lower() != _recruiter_email:\n"
    "                state[\"parsed_manager_email\"] = _email\n"
    "                logger.info(\n"
    "                    \"[WizardOrchestrator] manager_email capturado deterministicamente \"\n"
    "                    \"(len=%d) thread=%s\", len(_email), thread_id,\n"
    "                )\n"
    "                # H2-warning: dominio diferente do recrutador pode indicar email\n"
    "                # de outra empresa (sem validacao de tenant para manager).\n"
    "                _mgr_domain = _email.split(\"@\")[-1].lower()\n"
    "                if _recruiter_email and _mgr_domain != _recruiter_email.split(\"@\")[-1].lower():\n"
    "                    logger.warning(\n"
    "                        \"[WizardOrchestrator] manager_email dominio difere do recrutador \"\n"
    "                        \"(%s vs %s) — sem validacao de tenant, thread=%s\",\n"
    "                        _mgr_domain,\n"
    "                        _recruiter_email.split(\"@\")[-1].lower(),\n"
    "                        thread_id,\n"
    "                    )\n"
)

if OLD_C not in src_c:
    print("ERROR: Site C — OLD block not found.")
    sys.exit(1)
if src_c.count(OLD_C) != 1:
    print(f"ERROR: Site C — {src_c.count(OLD_C)} occurrences, expected 1.")
    sys.exit(1)

src_c = src_c.replace(OLD_C, NEW_C, 1)
print("OK: Site C patched (H2-warning domain mismatch)")

with open(FILE_C, "w", encoding="utf-8") as f:
    f.write(src_c)
print(f"OK: {FILE_C} written")

# ── Syntax check ─────────────────────────────────────────────────────────────
import py_compile, tempfile, os

for fpath in [FILE_AB, FILE_C]:
    tmp = tempfile.mktemp(suffix=".py")
    with open(fpath) as f:
        code = f.read()
    with open(tmp, "w") as f:
        f.write(code)
    try:
        py_compile.compile(tmp, doraise=True)
        print(f"OK: syntax OK — {fpath}")
    except py_compile.PyCompileError as e:
        print(f"SYNTAX ERROR in {fpath}: {e}")
        sys.exit(1)
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass

print("\nAll sites patched and syntax verified.")
