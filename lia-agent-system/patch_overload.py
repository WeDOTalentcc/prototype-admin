"""Canonical (2026-06-04): transient provider-overload resilience.

Producer fix in agentic_loop.py (retry-with-backoff on 529 + honest
failure_reason) + honest overload message in main_orchestrator.py.
"""
import sys

AL = "app/orchestrator/execution/agentic_loop.py"
MO = "app/orchestrator/execution/main_orchestrator.py"


def patch(path, old, new, label):
    src = open(path, encoding="utf-8").read()
    n = src.count(old)
    if n != 1:
        print(f"ABORT [{label}]: expected 1 match, got {n}")
        sys.exit(1)
    open(path, "w", encoding="utf-8").write(src.replace(old, new))
    print(f"OK [{label}]")


# ── Patch 1: classifier + consts after MAX_TOOL_ITERATIONS ───────────────────
patch(
    AL,
    'MAX_TOOL_ITERATIONS = int(os.getenv("LIA_MAX_TOOL_ITERATIONS", "3"))\n',
    'MAX_TOOL_ITERATIONS = int(os.getenv("LIA_MAX_TOOL_ITERATIONS", "3"))\n'
    "\n"
    "# Canonical (2026-06-04): transient provider-overload resilience.\n"
    "# A single Anthropic/Vertex `overloaded_error` (HTTP 529) is RETRYABLE —\n"
    "# burning the whole iteration budget on it (old `break`) degraded UX into a\n"
    '# misleading "reformule a pergunta". We retry the SAME LLM call with bounded\n'
    "# exponential backoff; on persistent overload we flag\n"
    '# `failure_reason="provider_overloaded"` so the orchestrator returns an\n'
    "# honest, overload-specific message (REGRA-4 honesty).\n"
    '_AGENTIC_OVERLOAD_RETRIES = int(os.getenv("LIA_AGENTIC_OVERLOAD_RETRIES", "2"))\n'
    "_AGENTIC_OVERLOAD_BACKOFF_BASE = float(\n"
    '    os.getenv("LIA_AGENTIC_OVERLOAD_BACKOFF_BASE", "0.6")\n'
    ")\n"
    "_TRANSIENT_PROVIDER_MARKERS = (\n"
    '    "overloaded_error",\n'
    '    "overloaded",\n'
    '    "rate_limit",\n'
    '    "rate limit",\n'
    '    "service unavailable",\n'
    '    "service_unavailable",\n'
    '    "internal server error",\n'
    '    "internal_server_error",\n'
    '    "temporarily unavailable",\n'
    '    "try again later",\n'
    ")\n"
    "\n"
    "\n"
    "def _is_transient_provider_error(exc: BaseException) -> bool:\n"
    '    """True when `exc` is a retryable provider hiccup (overload/429/503/5xx).\n'
    "\n"
    "    Detection is by message substring (provider-agnostic, no SDK import\n"
    "    coupling). A false positive costs only a bounded retry (benign); a false\n"
    "    negative degrades UX into the misleading generic fallback — so we err\n"
    "    toward retrying.\n"
    '    """\n'
    "    s = str(exc).lower()\n"
    "    return any(marker in s for marker in _TRANSIENT_PROVIDER_MARKERS)\n",
    "agentic: classifier + consts",
)

# ── Patch 2: retry loop replacing the try/except around the LLM call ─────────
OLD_LLM = (
    "            # --- Call LLM with tool schemas ---\n"
    "            try:\n"
    "                _t_llm_start = asyncio.get_event_loop().time()\n"
    "                llm_response = await asyncio.wait_for(\n"
    "                    self._llm_service.generate_with_tools(\n"
    "                        messages=messages,\n"
    "                        tools=tool_schemas,\n"
    "                        provider=provider,\n"
    "                        system_prompt=system_prompt or None,\n"
    "                    ),\n"
    "                    timeout=_AGENTIC_LLM_TIMEOUT_SECONDS,\n"
    "                )\n"
    "            except asyncio.TimeoutError:\n"
    "                _t_elapsed = asyncio.get_event_loop().time() - _t_llm_start\n"
    "                logger.warning(\n"
    '                    "[LIA-A04] LLM tool-call timed out (iter %d, provider=%s, "\n'
    '                    "elapsed=%.1fs, limit=%.1fs). Falling through to Phase 2 V1 — "\n'
    '                    "if frequent, bump LIA_AGENTIC_LLM_TIMEOUT_SECONDS env.",\n'
    "                    iteration, provider, _t_elapsed, _AGENTIC_LLM_TIMEOUT_SECONDS,\n"
    "                )\n"
    "                break\n"
    "            except Exception as exc:\n"
    '                logger.warning("[LIA-A04] LLM tool-call failed: %s", exc)\n'
    "                break\n"
)

NEW_LLM = (
    "            # --- Call LLM with tool schemas (retry transient overload) ---\n"
    "            llm_response = None\n"
    "            for _attempt in range(_AGENTIC_OVERLOAD_RETRIES + 1):\n"
    "                try:\n"
    "                    _t_llm_start = asyncio.get_event_loop().time()\n"
    "                    llm_response = await asyncio.wait_for(\n"
    "                        self._llm_service.generate_with_tools(\n"
    "                            messages=messages,\n"
    "                            tools=tool_schemas,\n"
    "                            provider=provider,\n"
    "                            system_prompt=system_prompt or None,\n"
    "                        ),\n"
    "                        timeout=_AGENTIC_LLM_TIMEOUT_SECONDS,\n"
    "                    )\n"
    "                    break\n"
    "                except asyncio.TimeoutError:\n"
    "                    _t_elapsed = asyncio.get_event_loop().time() - _t_llm_start\n"
    "                    logger.warning(\n"
    '                        "[LIA-A04] LLM tool-call timed out (iter %d, provider=%s, "\n'
    '                        "elapsed=%.1fs, limit=%.1fs). Falling through to Phase 2 V1 — "\n'
    '                        "if frequent, bump LIA_AGENTIC_LLM_TIMEOUT_SECONDS env.",\n'
    "                        iteration, provider, _t_elapsed, _AGENTIC_LLM_TIMEOUT_SECONDS,\n"
    "                    )\n"
    "                    return {\n"
    '                        "response": None,\n'
    '                        "tool_calls_made": tool_calls_made,\n'
    '                        "iterations": iteration + 1,\n'
    '                        "failure_reason": "llm_timeout",\n'
    "                    }\n"
    "                except Exception as exc:\n"
    "                    _transient = _is_transient_provider_error(exc)\n"
    "                    if _transient and _attempt < _AGENTIC_OVERLOAD_RETRIES:\n"
    "                        _backoff = _AGENTIC_OVERLOAD_BACKOFF_BASE * (2 ** _attempt)\n"
    "                        logger.warning(\n"
    '                            "[LIA-A04] transient provider error (iter %d, attempt "\n'
    '                            "%d/%d) — retrying in %.1fs: %s",\n'
    "                            iteration, _attempt + 1,\n"
    "                            _AGENTIC_OVERLOAD_RETRIES + 1, _backoff, exc,\n"
    "                        )\n"
    "                        await asyncio.sleep(_backoff)\n"
    "                        continue\n"
    "                    if _transient:\n"
    "                        logger.warning(\n"
    '                            "[LIA-A04] provider overloaded after %d attempts — "\n'
    '                            "returning honest overload signal: %s",\n'
    "                            _attempt + 1, exc,\n"
    "                        )\n"
    "                        return {\n"
    '                            "response": None,\n'
    '                            "tool_calls_made": tool_calls_made,\n'
    '                            "iterations": iteration + 1,\n'
    '                            "failure_reason": "provider_overloaded",\n'
    "                        }\n"
    '                    logger.warning("[LIA-A04] LLM tool-call failed: %s", exc)\n'
    "                    return {\n"
    '                        "response": None,\n'
    '                        "tool_calls_made": tool_calls_made,\n'
    '                        "iterations": iteration + 1,\n'
    '                        "failure_reason": "llm_error",\n'
    "                    }\n"
    "\n"
    "            if llm_response is None:\n"
    "                # Defensive: retries exhausted without a returnable branch.\n"
    "                return {\n"
    '                    "response": None,\n'
    '                    "tool_calls_made": tool_calls_made,\n'
    '                    "iterations": iteration + 1,\n'
    '                    "failure_reason": "provider_overloaded",\n'
    "                }\n"
)

patch(AL, OLD_LLM, NEW_LLM, "agentic: retry loop")

# ── Patch 3: orchestrator honest overload message ────────────────────────────
patch(
    MO,
    "                        _enrich_suggested_prompts(_resp, ctx)\n"
    "                        return _resp\n"
    "                except Exception as exc:\n",
    "                        _enrich_suggested_prompts(_resp, ctx)\n"
    "                        return _resp\n"
    "\n"
    "                    # Canonical (2026-06-04): transient provider overload\n"
    "                    # (HTTP 529). Don't blame the user's phrasing for a\n"
    "                    # provider outage — return an honest, overload-specific\n"
    "                    # message instead of the generic V1 fallback. (REGRA-4.)\n"
    "                    if (\n"
    "                        _agentic_result\n"
    '                        and _agentic_result.get("failure_reason")\n'
    '                        == "provider_overloaded"\n'
    "                    ):\n"
    "                        logger.warning(\n"
    '                            "[MainOrchestrator] Agentic loop provider-overloaded "\n'
    '                            "after retries — honest fail (user=%s company=%s).",\n'
    '                            getattr(ctx, "user_id", None), ctx.company_id,\n'
    "                        )\n"
    "                        return ChatResponse(\n"
    "                            success=False,\n"
    "                            content=(\n"
    '                                "Os servidores de IA estão sobrecarregados neste "\n'
    '                                "instante. Pode tentar de novo em alguns segundos? "\n'
    '                                "Sua pergunta está ok — é só uma instabilidade "\n'
    '                                "temporária do provedor."\n'
    "                            ),\n"
    '                            agent_used="agentic_loop",\n'
    "                            confidence=0.0,\n"
    '                            intent_detected="provider_overloaded",\n'
    "                            conversation_id=conv_id,\n"
    '                            error_code="PROVIDER_OVERLOADED",\n'
    '                            error_category="transient",\n'
    "                        )\n"
    "                except Exception as exc:\n",
    "orchestrator: honest overload msg",
)

print("ALL OK")
