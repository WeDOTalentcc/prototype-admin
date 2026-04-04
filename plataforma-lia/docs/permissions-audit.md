# Audit: Client-Side Permission Checks

## Summary
Mapped all client-side permission checks across the frontend codebase.
Categorized each as: (a) has server-side enforcement, (b) needs server enforcement, (c) UX-only hiding.

## Permission System

The centralized permission system lives in:
- `src/utils/permissions.ts` — `PermissionManager` class with role-based access control
- `src/lib/permissions.ts` — Typed helpers and enforcement catalog

## Permission Check Categories

### (a) Server-Side Enforcement Exists
These checks have corresponding backend middleware/guards:

| Permission | Location | Server Enforcement |
|---|---|---|
| `read:candidates` | Candidates page, Kanban, Search | API auth middleware on `/api/candidates` |
| `write:candidates` | Add/edit candidate modals | API auth middleware on POST/PUT `/api/candidates` |
| `delete:candidates` | Candidate deletion actions | API auth middleware on DELETE `/api/candidates` |
| `read:jobs` | Jobs listing, Kanban | API auth middleware on `/api/jobs` |
| `write:jobs` | Job creation/editing | API auth middleware on POST/PUT `/api/jobs` |
| `write:evaluations` | WSI/assessment forms | API auth middleware on evaluation endpoints |
| `execute:lia_actions` | LIA chat actions | Backend LIA action authorization |
| `read:interviews` | Interview scheduling | API auth middleware on `/api/interviews` |
| `write:interviews` | Schedule interviews | API auth middleware on interview endpoints |
| `read:assessments` | Assessment viewing | API auth middleware on assessment endpoints |
| `write:assessments` | Assessment creation | API auth middleware on assessment endpoints |
| `write:settings` | Settings pages | API auth middleware on `/api/settings` |

### (b) Needs Server-Side Enforcement
These checks exist only client-side and should be added to backend:

| Permission | Location | Risk |
|---|---|---|
| `read:reports` | Reports/indicators pages | LOW — read-only data, but should verify role |
| `write:reports` | Report generation/export | LOW — generates from existing data |
| `read:analytics` | Analytics dashboards | LOW — read-only aggregate data |
| `read:team_performance` | Team performance tab | MEDIUM — contains individual performance metrics |
| `read:lia_insights` | LIA insight panels | LOW — AI-generated recommendations |
| `read:references` | Reference check viewing | MEDIUM — contains PII |
| `write:references` | Reference request actions | MEDIUM — triggers external communications |

### (c) UX-Only Hiding (Acceptable)
These are pure UI convenience checks, not security boundaries:

| Check | Location | Purpose |
|---|---|---|
| `canEditName` (stage) | `JobProcessSection.tsx`, `StageCard.tsx` | Hide rename UI for system stages |
| `canEdit` (JD) | `JDEvaluationPanel.tsx`, `JDEvaluationHeader.tsx` | Toggle edit mode for job descriptions |
| `canEditSLA` | `ColumnContextMenu.tsx` | Hide SLA editing for system columns |
| `canRename/canDeactivate/canRemove` | `ColumnContextMenu.tsx` | Column-type-based UI options |
| `msg.role === 'user'` checks | Chat components (15+ locations) | Message styling, not authorization |
| Role display labels | `user-management.tsx` | Display role names in UI |
| `isManager` | `user-management.tsx` | Show admin features in user list |

## Recommendations

1. **Priority: Add server guards for `read:references` and `write:references`** — these involve PII
2. **Priority: Add server guards for `read:team_performance`** — contains performance metrics
3. **Low priority: Add guards for `read:reports` and `read:analytics`** — read-only aggregate data
4. **No action needed** for UX-only hiding checks — these are appropriate client-side patterns
5. **Existing `PermissionManager`** in `src/utils/permissions.ts` is well-structured with role hierarchy and condition support
6. **New typed helpers** in `src/lib/permissions.ts` provide compile-time safety for permission checks
