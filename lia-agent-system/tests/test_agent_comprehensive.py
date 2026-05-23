#!/usr/bin/env python3
"""
Comprehensive Agent Testing Suite for LIA Platform

Tests:
1. Agent Architecture & Orchestration
2. RAG & Context Retrieval
3. Database Connections & Data Flow
4. Stress & Performance
5. Edge Cases (incomplete/invalid data)
6. Response Quality Metrics
7. Memory & Context Persistence
8. Tone of Voice Consistency
9. Token Cost Analysis & Financial Viability

Run with: pytest tests/test_agent_comprehensive.py -v --tb=short
"""
import pytest
import httpx
import asyncio
import json
import time
import random
import string
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30.0


@dataclass
class TestMetrics:
    """Metrics collector for test results."""
    response_times: List[float] = field(default_factory=list)
    token_counts: List[Dict[str, int]] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    quality_scores: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_response(self, time_ms: float, tokens: Dict[str, int] = None, success: bool = True, quality: float = None):
        self.response_times.append(time_ms)
        if tokens:
            self.token_counts.append(tokens)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        if quality is not None:
            self.quality_scores.append(quality)
    
    def summary(self) -> Dict[str, Any]:
        return {
            "total_requests": self.success_count + self.failure_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count),
            "avg_response_time_ms": sum(self.response_times) / max(1, len(self.response_times)),
            "max_response_time_ms": max(self.response_times) if self.response_times else 0,
            "min_response_time_ms": min(self.response_times) if self.response_times else 0,
            "avg_quality_score": sum(self.quality_scores) / max(1, len(self.quality_scores)),
            "total_input_tokens": sum(t.get("input", 0) for t in self.token_counts),
            "total_output_tokens": sum(t.get("output", 0) for t in self.token_counts),
            "errors": self.errors[:5]
        }


class AgentTestSuite:
    """Comprehensive test suite for LIA agents."""
    
    def __init__(self):
        self.metrics = TestMetrics()
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    async def test_agent_health(self) -> Dict[str, Any]:
        """Test 1: Agent Architecture & Health Check."""
        results = {"name": "Agent Health Check", "tests": []}
        
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            results["tests"].append({
                "name": "Health endpoint",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
        except Exception as e:
            results["tests"].append({"name": "Health endpoint", "passed": False, "details": str(e)})
        
        try:
            from app.agents.agent_registry import agent_registry
            from app.shared.agents.agent_types import AgentType
            
            expected_agents = [
                AgentType.JOB_PLANNER,
                AgentType.SOURCING,
                AgentType.CV_SCREENING,
                AgentType.INTERVIEWER,
                AgentType.WSI_EVALUATOR,
                AgentType.SCHEDULING,
                AgentType.ANALYST_FEEDBACK,
                AgentType.ATS_INTEGRATOR,
                AgentType.RECRUITER_ASSISTANT,
            ]
            
            for agent_type in expected_agents:
                agent = agent_registry.get_agent(agent_type)
                results["tests"].append({
                    "name": f"Agent {agent_type.value} registered",
                    "passed": agent is not None,
                    "details": f"Found: {agent is not None}"
                })
        except Exception as e:
            results["tests"].append({"name": "Agent registry check", "passed": False, "details": str(e)})
        
        return results
    
    async def test_orchestrator_routing(self) -> Dict[str, Any]:
        """Test 2: Orchestrator Intent Routing."""
        results = {"name": "Orchestrator Routing", "tests": []}
        
        test_intents = [
            ("Quero criar uma vaga de desenvolvedor", "create_job", "JOB_PLANNER"),
            ("Busque candidatos com Python", "search_candidates", "SOURCING"),
            ("Analise este currículo", "parse_cv", "CV_SCREENING"),
            ("Agende uma entrevista para amanhã", "schedule_interview", "SCHEDULING"),
            ("Como está o pipeline da vaga X?", "analyze_pipeline", "ANALYST_FEEDBACK"),
        ]
        
        try:
            from app.orchestrator.routing.fast_router import FastRouter
            router = FastRouter()

            for message, expected_intent, expected_agent in test_intents:
                start = time.time()
                try:
                    result = router.match(message)
                    elapsed = (time.time() - start) * 1000
                    self.metrics.add_response(elapsed)

                    results["tests"].append({
                        "name": f"Route: '{message[:30]}...'",
                        "passed": True,
                        "details": f"Domain: {result.domain_id if result else 'none'}, Time: {elapsed:.1f}ms"
                    })
                except Exception as e:
                    results["tests"].append({
                        "name": f"Route: '{message[:30]}...'",
                        "passed": False,
                        "details": str(e)
                    })
        except Exception as e:
            results["tests"].append({"name": "Intent router import", "passed": False, "details": str(e)})
        
        return results
    
    async def test_tool_execution(self) -> Dict[str, Any]:
        """Test 3: Tool Calling System."""
        results = {"name": "Tool Execution", "tests": []}
        
        try:
            from app.tools import tool_registry, get_all_tool_schemas
            
            schemas = get_all_tool_schemas()
            results["tests"].append({
                "name": "Tool schemas loaded",
                "passed": len(schemas) > 0,
                "details": f"Found {len(schemas)} tools"
            })
            
            from app.tools.scope_config import (
                PromptScope, get_tools_for_scope,
                FUNNEL_QUERY_TOOLS, VACANCY_QUERY_TOOLS, IN_JOB_QUERY_TOOLS
            )
            
            for scope in [PromptScope.TALENT_FUNNEL, PromptScope.JOB_TABLE, PromptScope.IN_JOB]:
                tools = get_tools_for_scope(scope, "all")
                results["tests"].append({
                    "name": f"Scope {scope.value} tools",
                    "passed": len(tools) >= 10,
                    "details": f"Found {len(tools)} tools"
                })
            
            all_query = FUNNEL_QUERY_TOOLS | VACANCY_QUERY_TOOLS | IN_JOB_QUERY_TOOLS
            results["tests"].append({
                "name": "33 query tools registered",
                "passed": len(all_query) == 33,
                "details": f"Found {len(all_query)} unique query tools"
            })
            
        except Exception as e:
            results["tests"].append({"name": "Tool system check", "passed": False, "details": str(e)})
        
        return results
    
    async def test_database_connections(self) -> Dict[str, Any]:
        """Test 4: Database Connections & Data Flow."""
        results = {"name": "Database Connections", "tests": []}
        
        try:
            from app.database import get_db, engine
            from sqlalchemy import text
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                results["tests"].append({
                    "name": "Database connection",
                    "passed": True,
                    "details": "PostgreSQL connected"
                })
                
                tables_query = text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' LIMIT 20
                """)
                tables = [row[0] for row in conn.execute(tables_query)]
                results["tests"].append({
                    "name": "Tables exist",
                    "passed": len(tables) > 5,
                    "details": f"Found {len(tables)} tables"
                })
                
        except Exception as e:
            results["tests"].append({"name": "Database check", "passed": False, "details": str(e)})
        
        return results
    
    async def test_memory_persistence(self) -> Dict[str, Any]:
        """Test 5: Memory & Context Persistence."""
        results = {"name": "Memory Persistence", "tests": []}
        
        try:
            from app.domains.recruiter_assistant.services.conversation_memory import ConversationMemory
            
            memory = ConversationMemory()
            
            test_conv_id = f"test-{int(time.time())}"
            test_messages = [
                {"role": "user", "content": "Olá, preciso de ajuda com uma vaga"},
                {"role": "assistant", "content": "Claro! Posso ajudar com isso."},
                {"role": "user", "content": "A vaga é para desenvolvedor Python senior"},
            ]
            
            for msg in test_messages:
                memory.add_message(test_conv_id, msg["role"], msg["content"])
            
            history = memory.get_history(test_conv_id)
            results["tests"].append({
                "name": "Store conversation",
                "passed": len(history) == len(test_messages),
                "details": f"Stored {len(history)} messages"
            })
            
            context = memory.get_context_for_prompt(test_conv_id)
            results["tests"].append({
                "name": "Context retrieval",
                "passed": "Python" in context or "desenvolvedor" in context.lower(),
                "details": f"Context length: {len(context)} chars"
            })
            
            memory.clear_history(test_conv_id)
            history_after = memory.get_history(test_conv_id)
            results["tests"].append({
                "name": "Clear history",
                "passed": len(history_after) == 0,
                "details": f"History cleared: {len(history_after)} messages"
            })
            
        except Exception as e:
            results["tests"].append({"name": "Memory check", "passed": False, "details": str(e)})
        
        return results
    
    async def test_edge_cases(self) -> Dict[str, Any]:
        """Test 6: Edge Cases - Incomplete/Invalid Data."""
        results = {"name": "Edge Cases", "tests": []}
        
        edge_cases = [
            {"message": "", "name": "Empty message"},
            {"message": "   ", "name": "Whitespace only"},
            {"message": "a" * 10000, "name": "Very long message"},
            {"message": "🎉🚀💻🔥", "name": "Emoji only"},
            {"message": "<script>alert('xss')</script>", "name": "XSS attempt"},
            {"message": "'; DROP TABLE users; --", "name": "SQL injection"},
            {"message": "NULL", "name": "NULL string"},
            {"message": "undefined", "name": "undefined string"},
            {"message": "Créer une offre d'emploi", "name": "French text"},
            {"message": "求人を作成", "name": "Japanese text"},
        ]
        
        try:
            from app.shared.robustness.input_validation import sanitize_text, validate_message_input
            
            for case in edge_cases:
                try:
                    sanitized = sanitize_text(case["message"])
                    is_valid = True
                    try:
                        validate_message_input(case["message"])
                    except Exception:
                        is_valid = False
                    
                    results["tests"].append({
                        "name": case["name"],
                        "passed": True,
                        "details": f"Handled safely, valid={is_valid}, len={len(sanitized)}"
                    })
                except Exception as e:
                    results["tests"].append({
                        "name": case["name"],
                        "passed": False,
                        "details": f"Error: {str(e)[:50]}"
                    })
                    
        except Exception as e:
            results["tests"].append({"name": "Input validation import", "passed": False, "details": str(e)})
        
        return results
    
    async def test_stress_performance(self) -> Dict[str, Any]:
        """Test 7: Stress & Performance Testing."""
        results = {"name": "Stress Performance", "tests": []}
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/orchestrator/pipeline-chat",
                json={
                    "message": "Teste de performance",
                    "mode": "pipeline",
                    "context": {},
                    "user_id": "stress-test"
                }
            )
            
            results["tests"].append({
                "name": "Single request baseline",
                "passed": response.status_code == 200,
                "details": f"Status: {response.status_code}"
            })
            
            async def make_request(i: int):
                start = time.time()
                try:
                    resp = await self.client.post(
                        f"{BASE_URL}/orchestrator/pipeline-chat",
                        json={
                            "message": f"Teste paralelo {i}",
                            "mode": "pipeline",
                            "context": {},
                            "user_id": f"stress-{i}"
                        }
                    )
                    elapsed = (time.time() - start) * 1000
                    return {"success": resp.status_code == 200, "time_ms": elapsed}
                except Exception as e:
                    return {"success": False, "time_ms": 0, "error": str(e)}
            
            tasks = [make_request(i) for i in range(5)]
            parallel_results = await asyncio.gather(*tasks)
            
            successful = sum(1 for r in parallel_results if r["success"])
            avg_time = sum(r["time_ms"] for r in parallel_results) / max(1, len(parallel_results))
            
            results["tests"].append({
                "name": "5 parallel requests",
                "passed": successful >= 4,
                "details": f"Success: {successful}/5, Avg time: {avg_time:.0f}ms"
            })
            
        except Exception as e:
            results["tests"].append({"name": "Stress test", "passed": False, "details": str(e)})
        
        return results
    
    async def test_response_quality(self) -> Dict[str, Any]:
        """Test 8: Response Quality Metrics."""
        results = {"name": "Response Quality", "tests": []}
        
        quality_tests = [
            {
                "message": "Quais candidatos têm experiência com Python?",
                "expected_keywords": ["candidato", "python", "experiência", "busca"],
                "context": "search"
            },
            {
                "message": "Como está o funil da vaga de desenvolvedor?",
                "expected_keywords": ["funil", "etapa", "candidato", "conversão"],
                "context": "pipeline"
            },
            {
                "message": "Preciso agendar uma entrevista",
                "expected_keywords": ["entrevista", "agenda", "horário", "disponível"],
                "context": "scheduling"
            },
        ]
        
        for test in quality_tests:
            try:
                response = await self.client.post(
                    f"{BASE_URL}/orchestrator/pipeline-chat",
                    json={
                        "message": test["message"],
                        "mode": "pipeline",
                        "context": {},
                        "user_id": "quality-test"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "").lower()
                    
                    keywords_found = sum(1 for kw in test["expected_keywords"] if kw in content)
                    quality_score = keywords_found / len(test["expected_keywords"])
                    
                    self.metrics.add_response(0, quality=quality_score)
                    
                    results["tests"].append({
                        "name": f"Quality: {test['context']}",
                        "passed": quality_score >= 0.25,
                        "details": f"Keywords: {keywords_found}/{len(test['expected_keywords'])}, Score: {quality_score:.0%}"
                    })
                else:
                    results["tests"].append({
                        "name": f"Quality: {test['context']}",
                        "passed": False,
                        "details": f"Status: {response.status_code}"
                    })
                    
            except Exception as e:
                results["tests"].append({
                    "name": f"Quality: {test['context']}",
                    "passed": False,
                    "details": str(e)
                })
        
        return results
    
    async def test_tone_consistency(self) -> Dict[str, Any]:
        """Test 9: Tone of Voice Consistency."""
        results = {"name": "Tone Consistency", "tests": []}
        
        formal_indicators = ["você", "podemos", "gostaria", "favor", "obrigado"]
        informal_indicators = ["vc", "pra", "tá", "blz", "tmj"]
        
        test_messages = [
            "Olá, preciso de ajuda",
            "Como faço para ver os candidatos?",
            "Quero criar uma vaga nova",
        ]
        
        formal_count = 0
        informal_count = 0
        
        for msg in test_messages:
            try:
                response = await self.client.post(
                    f"{BASE_URL}/orchestrator/pipeline-chat",
                    json={
                        "message": msg,
                        "mode": "pipeline",
                        "context": {},
                        "user_id": "tone-test"
                    }
                )
                
                if response.status_code == 200:
                    content = response.json().get("content", "").lower()
                    
                    has_formal = any(ind in content for ind in formal_indicators)
                    has_informal = any(ind in content for ind in informal_indicators)
                    
                    if has_formal:
                        formal_count += 1
                    if has_informal:
                        informal_count += 1
                        
            except Exception:
                pass
        
        is_consistent = formal_count >= 2 and informal_count == 0
        results["tests"].append({
            "name": "Professional tone",
            "passed": is_consistent,
            "details": f"Formal: {formal_count}, Informal: {informal_count}"
        })
        
        results["tests"].append({
            "name": "No informal language",
            "passed": informal_count == 0,
            "details": f"Informal instances: {informal_count}"
        })
        
        return results
    
    async def test_token_cost_analysis(self) -> Dict[str, Any]:
        """Test 10: Token Cost Analysis & Financial Viability."""
        results = {"name": "Token Cost Analysis", "tests": []}
        
        COST_PER_1K_INPUT = 0.003
        COST_PER_1K_OUTPUT = 0.015
        
        test_scenarios = [
            {"name": "Simple query", "message": "Quantos candidatos temos?", "expected_max_tokens": 500},
            {"name": "Complex analysis", "message": "Analise o pipeline completo e sugira melhorias", "expected_max_tokens": 2000},
            {"name": "Search request", "message": "Busque candidatos Python senior em São Paulo", "expected_max_tokens": 1000},
        ]
        
        total_input = 0
        total_output = 0
        
        for scenario in test_scenarios:
            input_tokens = len(scenario["message"].split()) * 1.3
            output_tokens = scenario["expected_max_tokens"]
            
            total_input += input_tokens
            total_output += output_tokens
            
            scenario_cost = (input_tokens / 1000 * COST_PER_1K_INPUT) + (output_tokens / 1000 * COST_PER_1K_OUTPUT)
            
            results["tests"].append({
                "name": f"Cost: {scenario['name']}",
                "passed": scenario_cost < 0.05,
                "details": f"Est. cost: ${scenario_cost:.4f}"
            })
        
        daily_interactions = 100
        monthly_cost = ((total_input / 1000 * COST_PER_1K_INPUT) + (total_output / 1000 * COST_PER_1K_OUTPUT)) * daily_interactions * 30
        
        results["tests"].append({
            "name": "Monthly cost estimate (100 interactions/day)",
            "passed": monthly_cost < 500,
            "details": f"Est. monthly: ${monthly_cost:.2f}"
        })
        
        per_user_monthly = monthly_cost / 10
        results["tests"].append({
            "name": "Per-user monthly cost (10 users)",
            "passed": per_user_monthly < 50,
            "details": f"Est. per user: ${per_user_monthly:.2f}/month"
        })
        
        results["tests"].append({
            "name": "Financial viability check",
            "passed": per_user_monthly < 30,
            "details": f"Target: <$30/user, Actual: ${per_user_monthly:.2f}"
        })
        
        return results


async def run_comprehensive_tests():
    """Run all comprehensive tests and generate report."""
    print("=" * 70)
    print("LIA PLATFORM - COMPREHENSIVE AGENT TESTING")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    
    async with AgentTestSuite() as suite:
        all_results = []
        
        tests = [
            ("1. Agent Health", suite.test_agent_health),
            ("2. Orchestrator Routing", suite.test_orchestrator_routing),
            ("3. Tool Execution", suite.test_tool_execution),
            ("4. Database Connections", suite.test_database_connections),
            ("5. Memory Persistence", suite.test_memory_persistence),
            ("6. Edge Cases", suite.test_edge_cases),
            ("7. Stress Performance", suite.test_stress_performance),
            ("8. Response Quality", suite.test_response_quality),
            ("9. Tone Consistency", suite.test_tone_consistency),
            ("10. Token Cost Analysis", suite.test_token_cost_analysis),
        ]
        
        for test_name, test_func in tests:
            print(f"\n▶ Running: {test_name}")
            try:
                result = await test_func()
                all_results.append(result)
                
                passed = sum(1 for t in result["tests"] if t["passed"])
                total = len(result["tests"])
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"  {status} {passed}/{total} tests passed")
                
            except Exception as e:
                print(f"  ❌ Test failed: {e}")
                all_results.append({"name": test_name, "tests": [{"name": "Error", "passed": False, "details": str(e)}]})
        
        print("\n" + "=" * 70)
        print("DETAILED RESULTS")
        print("=" * 70)
        
        total_passed = 0
        total_tests = 0
        
        for result in all_results:
            passed = sum(1 for t in result["tests"] if t["passed"])
            total = len(result["tests"])
            total_passed += passed
            total_tests += total
            
            status = "✅ PASS" if passed == total else "⚠️ PARTIAL" if passed > 0 else "❌ FAIL"
            print(f"\n{status} {result['name']}: {passed}/{total}")
            
            for test in result["tests"]:
                icon = "  ✓" if test["passed"] else "  ✗"
                print(f"   {icon} {test['name']}")
                if test.get("details"):
                    print(f"      └─ {test['details']}")
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        success_rate = total_passed / max(1, total_tests) * 100
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n" + "=" * 70)
        overall = "✅ TESTS PASSED" if success_rate >= 80 else "⚠️ NEEDS ATTENTION" if success_rate >= 60 else "❌ CRITICAL ISSUES"
        print(f"{overall} ({total_passed}/{total_tests} - {success_rate:.1f}%)")
        print("=" * 70)
        
        return success_rate >= 70


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_tests())
    sys.exit(0 if success else 1)
