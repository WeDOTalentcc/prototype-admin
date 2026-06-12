# Adaptive Surface Selection — Phase 1: ToolSurfaceContext Pattern

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar `ToolSurfaceContext`, `ToolActivateContext`, `SURFACE_CONFIG` e `useSurfaceForTool` — o pattern que permite que um único componente de card decida sua própria apresentação (inline compacto ou painel expandido) e que qualquer card do chat possa abrir o painel focado no seu tool call.

**Architecture:** Três peças independentes (SURFACE_CONFIG, ToolSurfaceContext, useSurfaceForTool) mais um ponto de wiring em UnifiedChat.tsx. Zero mudanças no lia-agent-system.

**Tech Stack:** React context API, TypeScript, Zustand (useLiaPanelStore — Phase 0), Vitest, SSH Replit (replit-wedo-0405), branch feat/benefits-prv-canonical

---

## Task 1 — SURFACE_CONFIG + harness sensor

## Task 2 — ToolSurfaceContext + ToolActivateContext

## Task 3 — useSurfaceForTool hook

## Task 4 — Wire ToolActivateContext em UnifiedChat.tsx
