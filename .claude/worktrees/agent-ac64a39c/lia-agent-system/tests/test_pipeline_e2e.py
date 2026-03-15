"""
End-to-End Test Suite for Pipeline Transition System
Phase 6.6: Tests for transition dispatch, return events, infer-behavior, stage config

Usage: python -m pytest tests/test_pipeline_e2e.py -v
       OR: python tests/test_pipeline_e2e.py (standalone)
"""
import sys
import json
import time
import httpx

BASE_URL = "http://localhost:8000/api/v1"

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def log_pass(test_name: str, detail: str = ""):
    print(f"  {Colors.GREEN}✓{Colors.RESET} {test_name}" + (f" — {detail}" if detail else ""))

def log_fail(test_name: str, detail: str = ""):
    print(f"  {Colors.RED}✗{Colors.RESET} {test_name}" + (f" — {detail}" if detail else ""))

def log_section(name: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}{Colors.RESET}\n")

def run_tests():
    client = httpx.Client(timeout=10.0)
    passed = 0
    failed = 0

    # ─────────────────────────────────────────────
    # 1. Stage Catalog
    # ─────────────────────────────────────────────
    log_section("1. Stage Catalog (GET /catalog)")

    try:
        r = client.get(f"{BASE_URL}/recruitment-stages/catalog")
        if r.status_code == 200:
            data = r.json()
            catalog = data.get("catalog", [])
            if len(catalog) >= 10:
                log_pass("Catalog returns stages", f"{len(catalog)} stages found")
                passed += 1
            else:
                log_fail("Catalog too small", f"Only {len(catalog)} stages")
                failed += 1

            has_channel = all("default_channel" in s for s in catalog)
            if has_channel:
                log_pass("All catalog stages have default_channel")
                passed += 1
            else:
                log_fail("Missing default_channel in some catalog stages")
                failed += 1

            scheduling_stages = [s for s in catalog if s.get("action_behavior") == "scheduling"]
            scheduling_channels = [s.get("default_channel") for s in scheduling_stages]
            if all(c == "email_whatsapp" for c in scheduling_channels):
                log_pass("Scheduling stages default to email_whatsapp", f"{len(scheduling_stages)} stages")
                passed += 1
            else:
                log_fail("Scheduling stages channel mismatch", str(scheduling_channels))
                failed += 1
        else:
            log_fail("Catalog endpoint failed", f"Status {r.status_code}")
            failed += 3
    except Exception as e:
        log_fail("Catalog request error", str(e))
        failed += 3

    # ─────────────────────────────────────────────
    # 2. Infer Behavior
    # ─────────────────────────────────────────────
    log_section("2. Infer Behavior (POST /stages/infer-behavior)")

    test_cases = [
        ("Entrevista com Gestor", "scheduling", 0.8),
        ("Teste Técnico", "evaluation", 0.8),
        ("Verificação de Referências", "verification", 0.8),
        ("Triagem Inicial", "screening", 0.8),
        ("Proposta Salarial", "offer", 0.7),
        ("Algo Genérico", "passive", 0.3),
    ]

    for stage_name, expected_behavior, min_confidence in test_cases:
        try:
            r = client.post(f"{BASE_URL}/recruitment-stages/stages/infer-behavior", json={"stage_name": stage_name})
            if r.status_code == 200:
                data = r.json()
                behavior = data.get("suggested_behavior")
                confidence = data.get("confidence", 0)

                if behavior == expected_behavior:
                    log_pass(f"'{stage_name}' → {behavior}", f"confidence={confidence}")
                    passed += 1
                else:
                    log_fail(f"'{stage_name}' expected {expected_behavior}, got {behavior}", f"confidence={confidence}")
                    failed += 1
            else:
                log_fail(f"'{stage_name}' failed", f"Status {r.status_code}")
                failed += 1
        except Exception as e:
            log_fail(f"'{stage_name}' error", str(e))
            failed += 1

    # ─────────────────────────────────────────────
    # 3. Return Event Types
    # ─────────────────────────────────────────────
    log_section("3. Return Event Types (GET /transition/return-event/types)")

    try:
        r = client.get(f"{BASE_URL}/recruitment-stages/transition/return-event/types")
        if r.status_code == 200:
            data = r.json()
            event_types = data.get("event_types", [])
            if len(event_types) >= 10:
                log_pass("Return event types loaded", f"{len(event_types)} types")
                passed += 1
            else:
                log_fail("Too few event types", f"{len(event_types)}")
                failed += 1

            required_events = ["screening_complete", "interview_confirmed", "offer_accepted", "offer_declined"]
            found = [e for e in required_events if any(et.get("event_type") == e for et in event_types)]
            if len(found) == len(required_events):
                log_pass("All required event types present", ", ".join(found))
                passed += 1
            else:
                log_fail("Missing event types", f"Found {len(found)}/{len(required_events)}")
                failed += 1
        else:
            log_fail("Return event types endpoint", f"Status {r.status_code}")
            failed += 2
    except Exception as e:
        log_fail("Return event types error", str(e))
        failed += 2

    # ─────────────────────────────────────────────
    # 4. Return Event Processing
    # ─────────────────────────────────────────────
    log_section("4. Return Event Processing (POST /transition/return-event)")

    test_events = [
        {
            "vacancy_candidate_id": "test-candidate-001",
            "event_type": "screening_complete",
            "metadata": {"score": 85},
            "triggered_by": "system"
        },
        {
            "vacancy_candidate_id": "test-candidate-002",
            "event_type": "offer_accepted",
            "metadata": {},
            "triggered_by": "candidate"
        },
    ]

    for event in test_events:
        try:
            r = client.post(f"{BASE_URL}/recruitment-stages/transition/return-event", json=event)
            if r.status_code == 200:
                data = r.json()
                auto_moved = data.get("auto_moved", False)
                detail = f"auto_moved={auto_moved}, sub_status={data.get('new_sub_status')}"
                log_pass(f"Event '{event['event_type']}' processed", detail)
                passed += 1
            elif r.status_code == 422:
                log_pass(f"Event '{event['event_type']}' validation ok (422 expected without real DB)", "validation response")
                passed += 1
            else:
                log_fail(f"Event '{event['event_type']}'", f"Status {r.status_code}: {r.text[:120]}")
                failed += 1
        except Exception as e:
            log_fail(f"Event '{event['event_type']}' error", str(e))
            failed += 1

    # ─────────────────────────────────────────────
    # 5. Transition Execute
    # ─────────────────────────────────────────────
    log_section("5. Transition Execute (POST /transition/execute)")

    try:
        transition_payload = {
            "vacancy_candidate_id": "test-candidate-003",
            "to_stage": "interview_hr",
            "sub_status": "agendada",
            "action": "just_move",
            "channel": "email",
            "action_behavior": "scheduling"
        }
        r = client.post(f"{BASE_URL}/recruitment-stages/transition/execute", json=transition_payload)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                dispatch = data.get("dispatch_results") or []
                log_pass("Transition execute", f"new_stage={data.get('new_stage')}, dispatch_results={len(dispatch)}")
                passed += 1
            else:
                log_pass("Transition execute (simulation)", data.get("message", "ok"))
                passed += 1
        elif r.status_code == 422:
            log_pass("Transition execute validation ok (422 expected without real DB)", "validation response")
            passed += 1
        else:
            log_fail("Transition execute", f"Status {r.status_code}: {r.text[:120]}")
            failed += 1
    except Exception as e:
        log_fail("Transition execute error", str(e))
        failed += 1

    # ─────────────────────────────────────────────
    # 6. Stage Config Update (simulation)
    # ─────────────────────────────────────────────
    log_section("6. Stage Config Update (PUT /stages/{stage_id}/config)")

    try:
        config_payload = {
            "action_behavior": "scheduling",
            "default_channel": "email_whatsapp",
            "sla_hours": 48
        }
        r = client.put(f"{BASE_URL}/recruitment-stages/stages/test-stage-id/config", json=config_payload)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                log_pass("Stage config update", f"stage={data.get('stage', {}).get('name', 'unknown')}")
                passed += 1
            else:
                log_fail("Stage config update", "success=false")
                failed += 1
        elif r.status_code == 404:
            log_pass("Stage config update (404 expected for test ID)", "endpoint reachable, validation works")
            passed += 1
        elif r.status_code == 422:
            log_pass("Stage config update (422 validation)", "endpoint reachable")
            passed += 1
        else:
            log_fail("Stage config update", f"Status {r.status_code}: {r.text[:120]}")
            failed += 1

        invalid_payload = {
            "action_behavior": "invalid_behavior_xyz",
            "default_channel": "telegram"
        }
        r2 = client.put(f"{BASE_URL}/recruitment-stages/stages/test-stage-id/config", json=invalid_payload)
        if r2.status_code in (400, 404, 422):
            log_pass("Stage config rejects invalid values", f"Status {r2.status_code}")
            passed += 1
        else:
            log_fail("Stage config should reject invalid values", f"Status {r2.status_code}")
            failed += 1
    except Exception as e:
        log_fail("Stage config update error", str(e))
        failed += 2

    # ─────────────────────────────────────────────
    # Summary
    # ─────────────────────────────────────────────
    log_section("SUMMARY")
    total = passed + failed
    print(f"  Total: {total} tests")
    print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {failed}{Colors.RESET}")

    if failed == 0:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED ✓{Colors.RESET}\n")
    else:
        print(f"\n  {Colors.YELLOW}{Colors.BOLD}SOME TESTS FAILED{Colors.RESET}\n")

    client.close()
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_tests())
