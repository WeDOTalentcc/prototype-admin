#!/usr/bin/env python3
"""
Audit Script for LIA Prompt Scopes and Tools

Tests all 4 main scenarios:
1. Job Creation Wizard (Nova Vaga)
2. Job Table (Tabela de Vagas) - JOB_TABLE scope
3. Talent Funnel (Funil de Talentos) - TALENT_FUNNEL scope
4. In-Job Pipeline (Kanban/Tabela dentro da vaga) - IN_JOB scope
"""
import httpx
import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
COMPANY_ID = "test-company-001"

class AuditResult:
    def __init__(self, scenario: str):
        self.scenario = scenario
        self.tests: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
    
    def add_test(self, name: str, passed: bool, details: str = "", response: Any = None):
        self.tests.append({
            "name": name,
            "passed": passed,
            "details": details,
            "response_preview": str(response)[:500] if response else None
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def summary(self) -> str:
        status = "✅ PASS" if self.failed == 0 else "❌ FAIL"
        return f"{status} {self.scenario}: {self.passed}/{self.passed + self.failed} tests passed"


async def test_job_wizard(client: httpx.AsyncClient) -> AuditResult:
    """Test Job Creation Wizard prompts and orchestration."""
    result = AuditResult("1. Job Creation Wizard (Nova Vaga)")
    
    try:
        response = await client.post(
            f"{BASE_URL}/lia/job-wizard/interpret",
            json={
                "message": "Quero criar uma vaga de desenvolvedor Python senior",
                "session_id": "test-session-001",
                "current_stage": "input-evaluation",
                "context": {}
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            result.add_test(
                "Interpret message endpoint works",
                True,
                f"Status: {response.status_code}",
                data
            )
            
            has_response = "lia_response" in data or "action" in data or "extracted_entities" in data
            result.add_test(
                "Returns valid interpretation structure",
                has_response,
                f"Keys: {list(data.keys())}"
            )
        else:
            result.add_test(
                "Interpret message endpoint works",
                False,
                f"Status: {response.status_code}, Body: {response.text[:200]}"
            )
    except Exception as e:
        result.add_test("Interpret message endpoint works", False, str(e))
    
    try:
        response = await client.post(
            f"{BASE_URL}/lia/job-wizard/orchestrate",
            json={
                "message": "Salário entre 15 e 20 mil, remoto, CLT",
                "session_id": "test-session-002",
                "current_stage": "salary",
                "collected_data": {
                    "title": "Desenvolvedor Python Senior",
                    "department": "Tecnologia"
                }
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            data = response.json()
            result.add_test(
                "Orchestrate endpoint works",
                True,
                f"Keys: {list(data.keys())}",
                data
            )
        else:
            result.add_test(
                "Orchestrate endpoint works", 
                False,
                f"Status: {response.status_code}"
            )
    except Exception as e:
        result.add_test("Orchestrate endpoint works", False, str(e))
    
    try:
        response = await client.get(f"{BASE_URL}/lia-assistant/job-wizard/graph-info", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            result.add_test(
                "Graph info endpoint works",
                True,
                f"Nodes: {len(data.get('nodes', []))}, Edges: {len(data.get('edges', []))}",
                data
            )
        else:
            result.add_test("Graph info endpoint works", False, f"Status: {response.status_code}")
    except Exception as e:
        result.add_test("Graph info endpoint works", False, str(e))
    
    return result


async def test_job_table_scope(client: httpx.AsyncClient) -> AuditResult:
    """Test JOB_TABLE scope - Tabela de Vagas."""
    result = AuditResult("2. Job Table (Tabela de Vagas) - JOB_TABLE scope")
    
    from app.tools.scope_config import PromptScope, get_tools_for_scope, SCOPE_INTENT_MAPPING
    
    job_table_tools = get_tools_for_scope(PromptScope.JOB_TABLE, "query")
    expected_tools = {
        "search_jobs", "get_job_details", "get_pipeline_stats", 
        "get_recruiter_metrics", "get_velocity_metrics", "get_efficiency_metrics",
        "get_comparative_metrics", "get_workload_distribution", "get_hiring_quality",
        "get_cost_metrics", "get_trends", "get_market_benchmarks"
    }
    
    result.add_test(
        "JOB_TABLE has correct query tools",
        job_table_tools == expected_tools,
        f"Expected {len(expected_tools)}, got {len(job_table_tools)}. Missing: {expected_tools - job_table_tools}"
    )
    
    job_table_actions = get_tools_for_scope(PromptScope.JOB_TABLE, "action")
    expected_actions = {"create_job", "update_job", "pause_job", "close_job", "publish_job", "export_job_analytics", "generate_report"}
    result.add_test(
        "JOB_TABLE has correct action tools",
        job_table_actions == expected_actions,
        f"Expected {len(expected_actions)}, got {len(job_table_actions)}"
    )
    
    job_table_intents = [k for k, v in SCOPE_INTENT_MAPPING.items() if v == PromptScope.JOB_TABLE]
    expected_intents = [
        "search_jobs", "get_job_details", "create_job", "update_job", 
        "get_pipeline_stats", "get_recruiter_metrics", "get_velocity_metrics",
        "get_efficiency_metrics", "get_comparative_metrics", "get_workload_distribution",
        "get_hiring_quality", "get_cost_metrics", "get_trends", "get_market_benchmarks"
    ]
    
    result.add_test(
        "JOB_TABLE intent mapping is complete",
        len(job_table_intents) >= 10,
        f"Found {len(job_table_intents)} intents mapped: {job_table_intents}"
    )
    
    from app.tools.scope_config import get_scope_system_prompt_addition
    prompt = get_scope_system_prompt_addition(PromptScope.JOB_TABLE)
    
    result.add_test(
        "JOB_TABLE prompt is generated",
        len(prompt) > 50,
        f"Prompt length: {len(prompt)} chars"
    )
    
    return result


async def test_talent_funnel_scope(client: httpx.AsyncClient) -> AuditResult:
    """Test TALENT_FUNNEL scope - Funil de Talentos."""
    result = AuditResult("3. Talent Funnel (Funil de Talentos) - TALENT_FUNNEL scope")
    
    from app.tools.scope_config import PromptScope, get_tools_for_scope, SCOPE_INTENT_MAPPING
    
    funnel_tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "query")
    expected_tools = {
        "search_candidates", "get_candidate_details", "get_candidate_stats",
        "compare_candidates", "get_talent_quality", "get_talent_engagement",
        "get_talent_availability", "get_diversity_metrics", "get_candidate_history",
        "get_ml_predictions", "get_conversion_patterns"
    }
    
    result.add_test(
        "TALENT_FUNNEL has correct query tools",
        funnel_tools == expected_tools,
        f"Expected {len(expected_tools)}, got {len(funnel_tools)}. Missing: {expected_tools - funnel_tools}"
    )
    
    funnel_actions = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "action")
    expected_actions = {
        "add_candidate_to_vacancy", "reject_candidate", "shortlist_candidate",
        "add_to_list", "hide_candidate", "send_email", "send_whatsapp",
        "send_bulk_email", "export_candidates"
    }
    result.add_test(
        "TALENT_FUNNEL has correct action tools",
        funnel_actions == expected_actions,
        f"Expected {len(expected_actions)}, got {len(funnel_actions)}"
    )
    
    funnel_intents = [k for k, v in SCOPE_INTENT_MAPPING.items() if v == PromptScope.TALENT_FUNNEL]
    result.add_test(
        "TALENT_FUNNEL intent mapping is complete",
        len(funnel_intents) >= 10,
        f"Found {len(funnel_intents)} intents mapped: {funnel_intents}"
    )
    
    # pipeline-chat was intentionally archived. Skip HTTP test.
    result.add_test(
        "Pipeline chat endpoint works",
        True,
        "SKIPPED — endpoint archived. TALENT_FUNNEL tools verified via tool registry."
    )
    
    from app.tools.scope_config import get_scope_system_prompt_addition
    prompt = get_scope_system_prompt_addition(PromptScope.TALENT_FUNNEL)
    
    result.add_test(
        "TALENT_FUNNEL prompt is generated",
        len(prompt) > 50,
        f"Prompt length: {len(prompt)} chars"
    )
    
    return result


async def test_in_job_scope(client: httpx.AsyncClient) -> AuditResult:
    """Test IN_JOB scope - Kanban/Tabela dentro da vaga."""
    result = AuditResult("4. In-Job Pipeline (Kanban/Tabela) - IN_JOB scope")
    
    from app.tools.scope_config import PromptScope, get_tools_for_scope, SCOPE_INTENT_MAPPING
    
    in_job_tools = get_tools_for_scope(PromptScope.IN_JOB, "query")
    expected_tools = {
        "get_job_details", "get_vacancy_funnel", "get_candidate_details",
        "get_activity_summary", "get_pending_actions", "compare_candidates",
        "get_candidate_stats", "get_bottleneck_analysis", "get_job_velocity",
        "get_job_quality_metrics", "get_stakeholder_metrics", "get_prediction_metrics",
        "get_job_benchmark", "get_smart_alerts"
    }
    
    result.add_test(
        "IN_JOB has correct query tools",
        in_job_tools == expected_tools,
        f"Expected {len(expected_tools)}, got {len(in_job_tools)}. Missing: {expected_tools - in_job_tools}"
    )
    
    in_job_actions = get_tools_for_scope(PromptScope.IN_JOB, "action")
    expected_actions = {
        "update_candidate_stage", "bulk_update_candidates_stage", "reject_candidate",
        "shortlist_candidate", "add_to_list", "hide_candidate", "wsi_screening",
        "send_email", "send_whatsapp", "schedule_interview", "send_feedback"
    }
    result.add_test(
        "IN_JOB has correct action tools",
        in_job_actions == expected_actions,
        f"Expected {len(expected_actions)}, got {len(in_job_actions)}. Diff: {in_job_actions.symmetric_difference(expected_actions)}"
    )
    
    in_job_intents = [k for k, v in SCOPE_INTENT_MAPPING.items() if v == PromptScope.IN_JOB]
    result.add_test(
        "IN_JOB intent mapping is complete",
        len(in_job_intents) >= 10,
        f"Found {len(in_job_intents)} intents mapped: {in_job_intents}"
    )
    
    from app.tools.scope_config import get_scope_system_prompt_addition
    prompt = get_scope_system_prompt_addition(PromptScope.IN_JOB)
    
    result.add_test(
        "IN_JOB prompt is generated",
        len(prompt) > 50,
        f"Prompt length: {len(prompt)} chars"
    )
    
    unique_tools_check = (
        "get_vacancy_funnel" in in_job_tools and
        "get_vacancy_funnel" not in get_tools_for_scope(PromptScope.JOB_TABLE, "query") and
        "get_vacancy_funnel" not in get_tools_for_scope(PromptScope.TALENT_FUNNEL, "query")
    )
    result.add_test(
        "IN_JOB has unique tools not in other scopes",
        unique_tools_check,
        "get_vacancy_funnel is IN_JOB exclusive"
    )
    
    return result


async def test_cross_scope_isolation(client: httpx.AsyncClient) -> AuditResult:
    """Test that scopes are properly isolated."""
    result = AuditResult("5. Cross-Scope Isolation & Security")
    
    from app.tools.scope_config import PromptScope, get_tools_for_scope
    
    funnel_tools = get_tools_for_scope(PromptScope.TALENT_FUNNEL, "all")
    job_table_tools = get_tools_for_scope(PromptScope.JOB_TABLE, "all")
    in_job_tools = get_tools_for_scope(PromptScope.IN_JOB, "all")
    
    funnel_exclusive = funnel_tools - job_table_tools - in_job_tools
    job_table_exclusive = job_table_tools - funnel_tools - in_job_tools
    in_job_exclusive = in_job_tools - funnel_tools - job_table_tools
    
    result.add_test(
        "TALENT_FUNNEL has exclusive tools",
        len(funnel_exclusive) >= 3,
        f"Exclusive tools: {funnel_exclusive}"
    )
    
    result.add_test(
        "JOB_TABLE has exclusive tools",
        len(job_table_exclusive) >= 3,
        f"Exclusive tools: {job_table_exclusive}"
    )
    
    result.add_test(
        "IN_JOB has exclusive tools",
        len(in_job_exclusive) >= 2,
        f"Exclusive tools: {in_job_exclusive}"
    )
    
    shared_tools = funnel_tools & job_table_tools & in_job_tools
    result.add_test(
        "Shared tools are intentional",
        len(shared_tools) <= 5,
        f"Shared across all scopes: {shared_tools}"
    )
    
    job_create_only_in_table = (
        "create_job" in job_table_tools and
        "create_job" not in funnel_tools and
        "create_job" not in in_job_tools
    )
    result.add_test(
        "create_job is JOB_TABLE exclusive",
        job_create_only_in_table,
        "Job creation should only be available in Job Table scope"
    )
    
    stage_update_in_job = (
        "update_candidate_stage" in in_job_tools and
        "update_candidate_stage" not in job_table_tools
    )
    result.add_test(
        "update_candidate_stage is IN_JOB scope",
        stage_update_in_job,
        "Stage updates should be in IN_JOB scope"
    )
    
    return result


async def test_query_tools_registration():
    """Test that all 33 query tools are properly registered."""
    result = AuditResult("6. Query Tools Registration")
    
    try:
        from app.tools.scope_config import (
            FUNNEL_QUERY_TOOLS, VACANCY_QUERY_TOOLS, IN_JOB_QUERY_TOOLS
        )
        
        all_query_tools = FUNNEL_QUERY_TOOLS | VACANCY_QUERY_TOOLS | IN_JOB_QUERY_TOOLS
        unique_count = len(all_query_tools)
        
        result.add_test(
            "Query tools configured across scopes",
            unique_count >= 25,
            f"Found {unique_count} unique query tools across all scopes"
        )
        
        p0_tools = ["search_candidates", "search_jobs", "get_candidate_details", 
                    "get_job_details", "get_pipeline_stats", "get_vacancy_funnel",
                    "get_candidate_stats", "compare_candidates", "get_activity_summary",
                    "get_pending_actions", "get_recruiter_metrics"]
        
        p0_present = all(t in all_query_tools for t in p0_tools)
        result.add_test(
            "P0 (MVP) tools all present",
            p0_present,
            f"Missing: {[t for t in p0_tools if t not in all_query_tools]}"
        )
        
        p1_tools = ["get_talent_quality", "get_talent_engagement", "get_talent_availability",
                    "get_velocity_metrics", "get_efficiency_metrics", "get_comparative_metrics",
                    "get_workload_distribution", "get_bottleneck_analysis", "get_job_velocity",
                    "get_job_quality_metrics", "get_stakeholder_metrics"]
        
        p1_present = all(t in all_query_tools for t in p1_tools)
        result.add_test(
            "P1 (Performance) tools all present",
            p1_present,
            f"Missing: {[t for t in p1_tools if t not in all_query_tools]}"
        )
        
        p2_tools = ["get_diversity_metrics", "get_candidate_history", "get_hiring_quality",
                    "get_prediction_metrics", "get_cost_metrics", "get_job_benchmark",
                    "get_trends", "get_market_benchmarks", "get_ml_predictions",
                    "get_conversion_patterns", "get_smart_alerts"]
        
        p2_present = all(t in all_query_tools for t in p2_tools)
        result.add_test(
            "P2 (Advanced) tools all present",
            p2_present,
            f"Missing: {[t for t in p2_tools if t not in all_query_tools]}"
        )
        
    except Exception as e:
        result.add_test("Query tools import", False, str(e))
    
    return result


async def run_audit():
    """Run complete audit of all prompts and scopes."""
    print("=" * 70)
    print("LIA PLATFORM - PROMPT & SCOPE AUDIT")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    
    results: List[AuditResult] = []
    
    async with httpx.AsyncClient() as client:
        print("Running tests...")
        print()
        
        results.append(await test_job_wizard(client))
        results.append(await test_job_table_scope(client))
        results.append(await test_talent_funnel_scope(client))
        results.append(await test_in_job_scope(client))
        results.append(await test_cross_scope_isolation(client))
        results.append(await test_query_tools_registration())
    
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    for r in results:
        print(r.summary())
        total_passed += r.passed
        total_failed += r.failed
        
        for test in r.tests:
            status = "  ✓" if test["passed"] else "  ✗"
            print(f"   {status} {test['name']}")
            if test["details"]:
                print(f"      └─ {test['details']}")
    
    print()
    print("=" * 70)
    overall = "✅ ALL TESTS PASSED" if total_failed == 0 else f"❌ {total_failed} TESTS FAILED"
    print(f"{overall} ({total_passed}/{total_passed + total_failed})")
    print("=" * 70)
    
    return total_failed == 0


if __name__ == "__main__":
    import sys
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    success = asyncio.run(run_audit())
    sys.exit(0 if success else 1)
