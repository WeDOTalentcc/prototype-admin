# Metodologia de Feedback WSI — WeDOTalent

> **Versão:** 1.0 | **Data:** 2026-04-04 | **Classificação:** Interno · Técnico

---

## 1. Contexto e Objetivo

O **WSI (Weighted Structured Interview)** é o motor de triagem conversacional da LIA. Ao final de cada triagem, o candidato recebe um e-mail genérico de confirmação. Este documento especifica a substituição desse e-mail por um **Relatório de Feedback Construtivo** entregue em 3 canais:

| Canal | Conteúdo | Quando |
|---|---|---|
| **Chat Web** | Resumo em markdown como última mensagem da LIA | Imediatamente ao concluir |
| **WhatsApp** | Resumo condensado (~600 chars) | Imediatamente ao concluir |
| **E-mail** | Relatório completo HTML com 5 dimensões | Imediatamente ao concluir |

O feedback é **construtivo e developmental** — não revela score, classificação (aprovado/reprovado) ou red flags.

---

## 2. Os 3 Momentos do Fluxo WSI (não confundir)

| Momento | Quando | O que acontece | Este doc cobre? |
|---|---|---|---|
| **M1 — Durante WSI** | Bloco a bloco | LIA só faz perguntas, zero feedback | ❌ |
| **M2 — Fim da triagem** | `complete_session()` | ← **Feedback estruturado** | ✅ |
| **M3 — Decisão final do recrutador** | Vaga fechada | Templates `screening_passed/failed` (orphans) | ❌ (futuro) |

---

## 3. Arquitetura do Scorer WSI

### 3.1 Blocos WSI

```
Block 0 — Técnico         (technical_skills)
Block 1 — Comportamental  (interpersonal_skills)
Block 2 — Situacional     (problem_solving)
Block 3 — Autodeclaração  (self_assessment)
Block 4 — Motivação       (motivation)
Block 5 — Encerramento    (cultural_fit)
```

### 3.2 Output de `_score_response_deterministic()` por resposta

```python
{
    "score": float,          # 0-5 escala raw
    "block_type": str,       # "technical" | "behavioral" | "situational"
    "bloom_level": int,      # 1-6 (Taxonomia de Bloom)
    "dreyfus_level": int,    # 1-5 (Modelo Dreyfus)
    "evidences": List[str],  # Evidências observáveis positivas
    "red_flags": List[str],  # Interno apenas — nunca exposto ao candidato
    "justification": str,    # Justificativa interna
    "competency": str,       # Adicionado pelo caller: block.competency
    "block_index": int,      # Adicionado pelo caller: block.index
}
```

### 3.3 Fórmula de Score Final

```
wsi_final_score = (avg_technical × technical_weight) + (avg_behavioral × behavioral_weight)
                  × 2.0  # escala 0-10
```

Pesos por seniority (`SENIORITY_WEIGHTS`):

| Nível | Technical | Behavioral |
|---|---|---|
| Estagiário | 68.75% | 31.25% |
| Júnior | 62.5% | 37.5% |
| Pleno | 68.75% | 31.25% |
| Sênior | 56.25% | 43.75% |
| Lead | 43.75% | 56.25% |
| Diretor | 31.25% | 68.75% |
| VP/C-Level | 25% | 75% |

---

## 4. As 5 Dimensões de Feedback

### Mapeamento Bloco → Dimensão

| Dimensão | Blocos Fonte | Competency |
|---|---|---|
| 💬 Clareza da Comunicação | Todos (meta) | — |
| 💡 Conhecimento Técnico | Block 0 | technical_skills |
| 🔍 Raciocínio e Solução de Problemas | Block 2 | problem_solving |
| 🤝 Competências Comportamentais | Blocks 1 + 3 | interpersonal_skills + self_assessment |
| 🎯 Alinhamento com a Posição | Blocks 4 + 5 | motivation + cultural_fit |

### Estrutura de cada dimensão no relatório

```
Ponto Forte     ← baseado em bloom_level + evidências observáveis
Desenvolvimento ← gap entre bloom atual e bloom esperado para o nível
Sugestão Prática ← ação concreta (curso, prática, exercício) calibrada por competency + bloom
```

---

## 5. Taxonomia de Bloom (Cognitiva) no Feedback

| Nível | Nome | Linguagem de Força (candidato vê) |
|---|---|---|
| 1 | Recordar | "demonstrou familiaridade com conceitos fundamentais" |
| 2 | Compreender | "explicou com clareza os princípios envolvidos" |
| 3 | Aplicar | "aplicou o conhecimento de forma concreta em situações reais" |
| 4 | Analisar | "analisou cenários com visão crítica e perspectiva comparativa" |
| 5 | Avaliar | "avaliou trade-offs e defendeu suas escolhas com solidez" |
| 6 | Criar | "propôs abordagens originais e demonstrou pensamento sistêmico" |

**Regra:** Bloom NUNCA aparece como número no feedback ao candidato. Sempre traduzido.

### Gap de Desenvolvimento (bloom atual → bloom esperado)

```python
if bloom >= expected_bloom:
    # Candidato acima do esperado → aponta próxima fronteira
    return f"Para continuar evoluindo, explore como {BLOOM_DEVELOPMENT_PHRASES[bloom+1]}"
else:
    # Gap existe → bridge construtivo
    return f"Uma área de crescimento é {BLOOM_DEVELOPMENT_PHRASES[bloom+1]}. Em paralelo, {DREYFUS_DEVELOPMENT_PHRASES[dreyfus]}"
```

---

## 6. Modelo Dreyfus (Expertise) no Feedback

| Nível | Nome | Framing no feedback |
|---|---|---|
| 1 | Iniciante | "construir base prática com projetos guiados (6–12 meses)" |
| 2 | Básico | "ampliar repertório com projetos reais de complexidade crescente" |
| 3 | Intermediário | "assumir responsabilidades com maior autonomia" |
| 4 | Avançado | "explorar contextos de alta ambiguidade e liderar decisões" |
| 5 | Especialista | "atuar como referência técnica e mentor na área" |

**Regra:** Dreyfus NUNCA aparece como nível/rótulo. Aparece como timeline e recomendação de exposição.

---

## 7. Calibração por Nível de Seniority

| Nível | Tom | Bloom Esperado | Dreyfus Esperado | Intro |
|---|---|---|---|---|
| Estagiário | Encorajador | 2 | 1 | "Ficamos muito felizes com sua participação!" |
| Júnior | Orientador | 3 | 2 | "Obrigado pela sua participação na triagem!" |
| Pleno | Equilibrado | 3 | 3 | "Agradecemos sua participação!" |
| Sênior | Peer-level | 4 | 4 | "Agradecemos seu tempo e sua participação." |
| Lead | Consultivo | 5 | 4 | "Foi um prazer conhecer sua experiência." |
| Diretor | Executivo | 5 | 5 | "Agradecemos sua participação." |
| VP/C-Level | Executivo | 6 | 5 | "Agradecemos sua participação." |

---

## 8. Regras de Fairness (EU AI Act · LGPD · EEOC)

### 8.1 O que NUNCA aparece no feedback ao candidato

| Item | Motivo |
|---|---|
| `wsi_final_score` (ex: 7.5, 8.3) | Candidato não deve saber o score numérico |
| Classificação (aprovado/aguardando/reprovado) | Poder de decisão é do recrutador |
| Red flags | Informação interna — exposição gera viés e risco legal |
| Bloom/Dreyfus como número ou rótulo | "Nível 3 de 6" é descontextualizado e pode ser discriminatório |
| Comparação com outros candidatos | Viola privacidade e gera viés competitivo |
| Big Five (OCEAN) | Risco legal: neuroticism → ADA; disparate impact sem validação por cargo |
| Inferências de personalidade | Foco exclusivo em comportamentos observáveis |
| Percentis ou rankings | Viola privacidade dos outros candidatos |

### 8.2 O que SEMPRE aparece

| Item | Onde |
|---|---|
| Aviso de geração por IA | Rodapé e-mail, chat, WhatsApp |
| Direito de revisão humana | Rodapé e-mail (LGPD Art. 20) |
| Link para solicitar revisão | E-mail footer (reply-to) |

### 8.3 Bases legais

- **EU AI Act Art. 14** — Sistemas de IA de alto risco em emprego exigem transparência e mecanismo de revisão humana
- **LGPD Art. 20** — Direito à revisão de decisões automatizadas que afetam interesses do titular
- **EEOC (EUA)** — Disparate impact testing para ferramentas de seleção automatizada
- **Brasil — Decreto 11.491/2023** — Regulamentação de uso de IA em processos de RH

---

## 9. Entrega por Canal

### 9.1 Chat Web
- **Quando:** Imediatamente após `complete_session()` — TriagemMessage com `message_type="feedback"`
- **Formato:** Markdown com headers, bold, separadores
- **Tamanho:** 5 dimensões completas (~600-900 palavras)
- **Nota:** O candidato está ativo no chat — este é o canal de maior impacto imediato

### 9.2 WhatsApp
- **Quando:** Se `session.invite_channel == "whatsapp"` ou candidato tem phone registrado
- **Formato:** Texto simples com *bold* WhatsApp, emojis
- **Tamanho:** Máximo ~600 chars — resume top 3 dimensões, referencia e-mail para detalhes
- **Template:** Mensagem de sessão (dentro de 24h de conversação ativa) — sem template aprovado necessário

### 9.3 E-mail HTML
- **Quando:** Sempre que `session.candidate_email` disponível
- **Formato:** HTML responsivo com cards por dimensão
- **Tamanho:** Relatório completo (5 dimensões) com sugestões práticas
- **Template:** `triagem_feedback_email.html` (Jinja2-like via str.format)

---

## 10. Lookup de Seniority

```python
# Em _trigger_post_completion() — lookup do JobVacancy
from app.models.job_vacancy import JobVacancy
job_result = await db.execute(
    select(JobVacancy).where(JobVacancy.id == session.job_id)
)
job = job_result.scalar_one_or_none()
seniority_level = (job.seniority_level if job else None) or "junior"
```

---

## 11. Fluxo de Implementação

```
complete_session()
    │
    ├── score responses → response_scores[] (enriquecido com competency + block_index)
    ├── calculate final_score
    ├── add TriagemMessage(completion)
    │
    └── _trigger_post_completion(db, session, response_scores)
            │
            ├── WSIFeedbackGenerator.generate(response_scores, job_title, seniority, name)
            │       └── Returns: {dimensions, intro, closing, plain_text, whatsapp_text, chat_text}
            │
            ├── session.feedback_draft = json.dumps(report)
            │
            ├── TriagemMessage(sender="lia", message_type="feedback", content=chat_text)
            │   └── Canal: Chat Web
            │
            ├── send_email(body_html=render_feedback_email(report))
            │   └── Canal: E-mail
            │
            └── send_whatsapp(to_phone=candidate_phone, message=whatsapp_text)
                └── Canal: WhatsApp (se phone disponível)
```

---

## 12. Arquivos do Sistema

| Arquivo | Ação | Descrição |
|---|---|---|
| `app/domains/cv_screening/services/wsi_feedback_generator.py` | **CRIAR** | Generator principal |
| `app/templates/triagem_feedback_email.html` | **CRIAR** | Template HTML responsivo |
| `app/services/triagem_session_service.py` | **MODIFICAR** | `_trigger_post_completion()` + `complete_session()` |
| `app/domains/cv_screening/services/wsi_deterministic_scorer.py` | **LEITURA** | Reutiliza BLOOM_LEVELS, DREYFUS_LEVELS, SENIORITY_WEIGHTS |
| `app/domains/communication/services/communication_dispatcher.py` | **LEITURA** | Reutiliza `send_email()`, `send_whatsapp()` |
| `libs/models/lia_models/triagem.py` | **LEITURA** | `feedback_draft` (já existe), `invite_channel` |

---

## 13. Testes de Validação

| Caso | Verificação |
|---|---|
| Completar triagem → chat mostra feedback | `TriagemMessage.message_type == "feedback"` visível no chat |
| E-mail recebido → score NÃO aparece | Revisar HTML: buscar `wsi_final_score`, `aprovado`, `reprovado` |
| E-mail com `seniority=estagiario` | Tom encorajador, bloom_expectation=2 |
| E-mail com `seniority=diretor` | Tom executivo, bloom_expectation=5 |
| WhatsApp enviado se phone disponível | Log: `"whatsapp"` em `channels_sent` |
| `feedback_draft` populado no DB | `SELECT feedback_draft FROM triagem_sessions WHERE token=?` |
| Score numérico ausente em TODOS os textos | `assert wsi_final_score not in plain_text` |
| Red flags ausentes | `assert not any(rf in plain_text for rf in red_flags)` |

---

*Documento gerado pela LIA · WeDOTalent · 2026*
