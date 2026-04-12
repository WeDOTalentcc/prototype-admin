#!/usr/bin/env python3
"""
Etapa 2: Security & Compliance no Agent Studio

Patches custom_agent_runtime.py:
  2.1 SecurityPatterns in execute() — block SQL injection, XSS, etc.
  2.2 PromptInjectionGuard in execute() — block jailbreak attempts
  2.3 FairnessGuard on tool output — warn on biased tool results
  2.4 AuditCallback + PIIStripCallback by default in _run_graph()
  2.5 PII sanitize via callback (auto-injected)
  2.6 RESTRICTED tools list updated (+4 dangerous tools)
"""
import os
import sys

BASE = "/home/runner/workspace/lia-agent-system"
FILE = os.path.join(BASE, "app/domains/agent_studio/custom_agent_runtime.py")
results = []


def read_file(path):
    with open(path) as f:
        return f.read()


def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)


def patch(old, new, label=""):
    global content
    if old not in content:
        print(f"  ERROR: pattern not found — {label}")
        results.append(False)
        return False
    content = content.replace(old, new, 1)
    print(f"  OK: {label}")
    results.append(True)
    return True


content = read_file(FILE)

# ============================================================
# 2.6: RESTRICTED_TOOLS — add 4 dangerous tools
# ============================================================
print("\n=== 2.6: RESTRICTED_TOOLS update ===")
patch(
    """    _RESTRICTED_TOOLS = frozenset({
        "delete_candidate", "delete_job", "delete_company",
        "bulk_delete", "reset_pipeline", "drop_tenant",
        "modify_permissions", "change_plan", "admin_override",
    })""",
    """    _RESTRICTED_TOOLS = frozenset({
        "delete_candidate", "delete_job", "delete_company",
        "bulk_delete", "reset_pipeline", "drop_tenant",
        "modify_permissions", "change_plan", "admin_override",
        # Etapa 2: batch/destructive operations blocked from Studio
        "bulk_sync_candidates", "finalize_hiring",
        "batch_move", "batch_move_candidates",
    })""",
    "RESTRICTED_TOOLS +4",
)

# ============================================================
# 2.1 + 2.2: SecurityPatterns + PromptInjectionGuard in execute()
# ============================================================
print("\n=== 2.1 + 2.2: Security + Injection guards in execute() ===")
patch(
    """        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(message)
            if _fg_result.is_blocked:
                return AgentOutput(
                    message=_fg_result.educational_message or "Solicitação bloqueada por critérios de equidade.",
                    confidence=1.0,
                    metadata={"blocked": True, "reason": "fairness_guard"},
                )
        except Exception:
            pass""",
    """        # === 2.1: SecurityPatterns — block SQL injection, XSS, path traversal ===
        try:
            from app.shared.robustness.security_patterns import check_input_security
            _sec = check_input_security(message)
            if _sec.is_blocked:
                logger.warning(
                    "[Studio:%s] SecurityPatterns blocked input: threats=%s",
                    self._agent_name, _sec.threat_categories,
                )
                return AgentOutput(
                    message="Solicitação bloqueada: padrão de segurança detectado.",
                    confidence=1.0,
                    metadata={
                        "blocked": True,
                        "reason": "security_patterns",
                        "threats": _sec.threat_categories,
                    },
                )
        except Exception:
            pass

        # === 2.2: PromptInjectionGuard — block jailbreak attempts ===
        try:
            from app.shared.prompt_injection import PromptInjectionGuard
            _pig = PromptInjectionGuard()
            _pig_result = _pig.check(message)
            if _pig_result.is_blocked:
                logger.warning(
                    "[Studio:%s] PromptInjection blocked: patterns=%s",
                    self._agent_name, _pig_result.matched_patterns,
                )
                return AgentOutput(
                    message="Solicitação bloqueada: possível tentativa de injeção detectada.",
                    confidence=1.0,
                    metadata={
                        "blocked": True,
                        "reason": "prompt_injection",
                        "patterns": _pig_result.matched_patterns,
                    },
                )
        except Exception:
            pass

        # === Existing FairnessGuard ===
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(message)
            if _fg_result.is_blocked:
                return AgentOutput(
                    message=_fg_result.educational_message or "Solicitação bloqueada por critérios de equidade.",
                    confidence=1.0,
                    metadata={"blocked": True, "reason": "fairness_guard"},
                )
        except Exception:
            pass""",
    "SecurityPatterns + PromptInjection in execute()",
)

# ============================================================
# 2.3: FairnessGuard on tool output in _tenant_safe_wrapper
# ============================================================
print("\n=== 2.3: FairnessGuard on tool output ===")
patch(
    """                    return await _fn(*args, **kwargs)""",
    """                    _tool_result = await _fn(*args, **kwargs)

                    # === 2.3: FairnessGuard on tool output (bias detection) ===
                    try:
                        from app.shared.compliance.fairness_guard import FairnessGuard
                        _fg_out = FairnessGuard()
                        _out_text = str(_tool_result) if not isinstance(_tool_result, str) else _tool_result
                        if len(_out_text) > 20:
                            _fg_check = _fg_out.check(_out_text)
                            if _fg_check.is_blocked:
                                logger.warning(
                                    "[Studio] FairnessGuard flagged tool output: tool=%s",
                                    _fn.__name__,
                                )
                    except Exception:
                        pass

                    return _tool_result""",
    "FairnessGuard on tool output",
)

# ============================================================
# 2.4 + 2.5: AuditCallback + PIIStripCallback in _run_graph()
# ============================================================
print("\n=== 2.4 + 2.5: Auto-inject AuditCallback + PIIStripCallback ===")
patch(
    """        callbacks = [cb for cb in [audit_callback, streaming_callback] if cb is not None]
        if callbacks:
            config["callbacks"] = callbacks""",
    """        # === 2.4 + 2.5: Auto-inject PII strip + Audit callbacks ===
        try:
            from app.shared.llm.callbacks import AuditLogCallback, PIIStripCallback
            auto_callbacks = [
                PIIStripCallback(),
                AuditLogCallback(
                    tenant_id=self._company_id,
                    caller=f"studio:{self._agent_name}",
                ),
            ]
        except Exception:
            auto_callbacks = []
        callbacks = auto_callbacks + [
            cb for cb in [audit_callback, streaming_callback] if cb is not None
        ]
        if callbacks:
            config["callbacks"] = callbacks""",
    "AuditCallback + PIIStripCallback in _run_graph",
)

# Write result
write_file(FILE, content)

# ============================================================
# Verify
# ============================================================
print("\n=== Verify AST parse ===")
import ast
try:
    ast.parse(content)
    print("  OK: syntax valid")
    results.append(True)
except SyntaxError as e:
    print(f"  ERROR: {e}")
    results.append(False)

total = len(results)
ok = sum(1 for r in results if r)
print(f"\n{'=' * 60}")
print(f"Results: {ok}/{total} patches applied successfully")
if ok < total:
    print("FAILED patches need manual review")
    sys.exit(1)
else:
    print("All Etapa 2 patches applied!")
    sys.exit(0)
