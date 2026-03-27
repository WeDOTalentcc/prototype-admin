---
name: lia-design-catalog
description: Design System LIA v4.1 catalogs - complete icon catalog (Lucide + Material Design Icons by category), colors by context (job status, candidate status, WeDo contexts), modal catalog (58+ modals by size with checklist). Use when choosing icons, applying status colors, or creating/reviewing modals.
---

# LIA Design System v4.1 - Catalogs

> **Source:** Design System LIA v4.1 (Fev 2026) - PARTE 5
> For complete catalogs, read `~/.agents/skills/lia-design-catalog/reference/`

## 5.1 Icons

### Specs
- **Library:** Lucide Icons (React/Vue) | Material Design Icons (Vuetify)
- **Sizes:** 16px (small/status), 20px (default/actions), 24px (large/nav), 32px (xlarge)
- **Stroke:** 2px default, 1.5px subtle
- **Color:** Inherit from parent OR gray-600

### By Category

**Navigation (24px):**
Home, BarChart, Users, Briefcase, Settings, Bell

**Actions (20px):**
Edit, Trash, Copy, Save, X, Check, Download, Upload, Search, Plus

**Status (16px) - with semantic colors:**
- CheckCircle (green-600) - Success
- AlertTriangle (amber-600) - Warning  
- XCircle (red-600) - Error
- Info (blue-600) - Information
- Clock (orange-600) - Time/Deadline

**Special WeDo:**
| Icon | Lucide | Color | When |
|------|--------|-------|------|
| Brain | `Brain` | **cyan #60BED1** | LIA, AI, automation |
| User | `User` | green #5DA47A | Profile, candidate |
| Lightbulb | `Lightbulb` | purple #9860D1 | Insights |
| Target | `Target` | magenta #D160AB | Goals |

**Brain icon ALWAYS cyan #60BED1. NEVER black/gray.**

## 5.2 Colors by Context

### Job Status
| Status | BG | Text | Border |
|--------|-----|------|--------|
| Aberta | `bg-green-50` | `text-green-700` | `border-green-200` |
| Pausada | `bg-amber-50` | `text-amber-700` | `border-amber-200` |
| Fechada | `bg-gray-100` | `text-gray-700` | `border-gray-200` |
| Rascunho | `bg-blue-50` | `text-blue-700` | `border-blue-200` |

### Candidate Status
| Status | BG | Text | Border |
|--------|-----|------|--------|
| Novo | `bg-blue-50` | `text-blue-700` | `border-blue-200` |
| Em Triagem | `bg-amber-50` | `text-amber-700` | `border-amber-200` |
| Aprovado | `bg-green-50` | `text-green-700` | `border-green-200` |
| Rejeitado | `bg-red-50` | `text-red-700` | `border-red-200` |
| Contratado | `bg-green-100` | `text-green-800` | `border-green-300` |

### WeDo Contexts (10% accent)
| Context | Color | BG (10%) | When |
|---------|-------|----------|------|
| LIA/Automação | #60BED1 | rgba(96,190,209,0.1) | AI features |
| Candidatos | #5DA47A | rgba(93,164,122,0.1) | Profiles |
| Tempo/Prazo | #D19960 | rgba(209,153,96,0.1) | Deadlines |
| Insights/IA | #9860D1 | rgba(152,96,209,0.1) | Analytics |
| Crítico | #D160AB | rgba(209,96,171,0.1) | High priority |

## 5.3 Modal Catalog (58+)

### By Size
| Size | Max Width | Count | Examples |
|------|-----------|-------|----------|
| **XS** | 384px (max-w-sm) | 5 | confirm-delete, session-expired, logout |
| **S** | 448px (max-w-md) | 12 | add-to-list, quick-note, tag-management, share-job |
| **M** | 512px (max-w-lg) | 18 | close-vacancy, interview-schedule, feedback, email-template |
| **L** | 672px (max-w-2xl) | 15 | edit-job, candidate-profile, interview-notes, import-candidates |
| **XL** | 896px (max-w-4xl) | 8 | job-insights, candidate-compare, analytics-detail, audit-log |

### Modal Checklist
When creating/reviewing a modal:
- [ ] Using one of 5 standard sizes (XS/S/M/L/XL)
- [ ] Title: 14px semibold gray-900 (Open Sans)
- [ ] Description: 12px gray-600 (Inter)
- [ ] Labels: 11px semibold gray-800 (Inter)
- [ ] Primary button: bg-gray-900 (NEVER cyan)
- [ ] Icon in header: w-5 h-5
- [ ] Footer buttons aligned right
- [ ] Focus ring implemented
- [ ] ARIA labels correct

## Reference Files
- `reference/icons.md` - Complete icon catalog by category with Lucide + Material names
- `reference/colors-by-context.md` - Job status, candidate status, WeDo context colors
- `reference/modals-catalog.md` - All 58+ modals by size with checklist
