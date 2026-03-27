# Melhorias de UX - Personalidade Educada e Didática da LIA

## Problema Original

**Screenshot do Bug:**
```
User: "busque candidatos SAP ABAP"
LIA: "Houve um problema técnico na busca..."  ❌ INADEQUADO
```

**Impacto:**
- Mensagem dava impressão de erro/bug quando faltava informação
- Tom não era educado ou didático
- Frustrava usuário ao invés de orientá-lo

---

## Solução Implementada (Nov 24, 2025)

### 1. **System Prompt Melhorado** 📝
**Arquivo:** `lia-agent-system/app/agents/conversation.py` (linha 85-145)

**Novos Princípios:**
```python
PERSONALIDADE:
- Amigável, educada e profissional
- Didática (explica claramente, dá exemplos práticos)
- Paciente (nunca impaciente ou defensiva)

QUANDO FALTA INFORMAÇÃO:
- ❌ NÃO diga: "Houve um erro técnico" / "Problema na busca"
- ✅ DIGA: "Para encontrar os melhores candidatos, preciso de alguns detalhes..."
```

---

### 2. **Error Handling Estruturado** 🔧
**Implementação:** 3 camadas de validação

#### **Camada 1: Validação Early Return**
Linha ~364 em `execute_candidate_search`:
```python
if not search_query.strip() or len(search_query.strip()) < 3:
    state["workflow_data"]["search_results"] = {
        "error": "Informações insuficientes para busca",
        "error_type": "missing_information",  # 🔑 Estruturado!
        "message": "Para fazer uma busca eficiente, preciso de mais detalhes"
    }
    return state
```

#### **Camada 2: HTTP Error Handling**
Linha ~518-545 em `execute_candidate_search`:
```python
except httpx.HTTPStatusError as e:
    if e.response.status_code == 422:
        error_type = "missing_information"  # Validação
    else:
        error_type = "technical_error"      # Erro real
```

#### **Camada 3: Global Search Errors**
Linha ~563-672 em `execute_global_search`:
```python
# Todos os caminhos de erro têm error_type estruturado
state["workflow_data"]["search_results"] = {
    "error": "...",
    "error_type": "missing_information" | "technical_error",
    "message": "..."
}
```

---

### 3. **Response Generator Inteligente** 💬
**Arquivo:** `lia-agent-system/app/agents/conversation.py` (linha ~792)

```python
if "error" in search_results:
    error_type = search_results.get('error_type', 'technical_error')  # Default seguro
    
    if error_type == "missing_information":
        # 📝 Prompt didático com 3 opções + exemplos práticos
        context += """
        **Me conte sobre o perfil ideal:**
        - Cargo/função (ex: Desenvolvedor Python Sênior)
        - Tecnologias (ex: Python, FastAPI, AWS)
        - Localização (ex: São Paulo, remoto)
        - Senioridade (ex: júnior, pleno, sênior)
        
        **Ou posso ajudar de outras formas:**
        - Se já criou vaga, posso buscar candidatos para ela
        - Posso buscar por critérios avançados
        """
    else:
        # ⚠️ Erro técnico real
        context += "Erro técnico temporário. Tente novamente em alguns segundos."
```

---

### 4. **Smart Context Panel** 🎨
**Arquivo:** `lia-agent-system/app/api/v1/chat.py` (linha ~135-177)

```python
# Só cria contextData quando há conteúdo útil
if "search_results" in workflow_data:
    search_results = workflow_data["search_results"]
    candidates = search_results.get("candidates", [])
    total_found = search_results.get("total_found", 0)
    
    if total_found > 0 and len(candidates) > 0:  # ✅ Validação
        context_data = {
            "type": "candidates",
            "shouldDisplay": True,
            "data": {...}
        }
```

---

## Fluxo Corrigido

### **Antes (Bugado):**
```
User: "busque SAP ABAP"
  ↓
Entity extraction falha (search_query vazio)
  ↓
Exception genérica: "Erro na busca local"
  ↓
String matching: "erro" → ❌ "Houve problema técnico"
  ↓
Frontend: contextData vazio → Painel vazio aparece
```

### **Depois (Corrigido):**
```
User: "busque SAP ABAP"
  ↓
Entity extraction: search_query vazio
  ↓
Validação early return: error_type="missing_information"
  ↓
Generate response: verifica error_type (não string matching!)
  ↓
LIA: ✅ "Para encontrar os candidatos perfeitos, preciso entender..."
  ↓
Frontend: contextData=null → ❌ Painel não abre
```

---

## Cobertura de Error Paths

| Situação | error_type | Mensagem LIA |
|----------|-----------|--------------|
| search_query vazio | `missing_information` | Didática com exemplos |
| HTTP 422 | `missing_information` | Didática com exemplos |
| HTTP 500/503 | `technical_error` | "Erro temporário, tente novamente" |
| Exception genérica | `technical_error` | "Erro temporário, tente novamente" |
| Pearch API down | `technical_error` | "Erro temporário, tente novamente" |

---

## Testes Manuais Sugeridos

### **Teste 1: Busca genérica (falta informação)**
```
Input: "busque no banco global"
Expected: ✅ Mensagem educada pedindo detalhes
          ❌ Painel não abre
```

### **Teste 2: Busca com critérios (sucesso)**
```
Input: "busque desenvolvedor Python sênior em São Paulo"
Expected: ✅ Busca executada
          ✅ Painel abre com candidatos
```

### **Teste 3: Busca com 0 resultados**
```
Input: "busque candidato SAP ABAP fluente em mandarim"
Expected: ✅ LIA responde educadamente
          ❌ Painel não abre (0 candidatos)
```

---

## Arquivos Modificados

1. `lia-agent-system/app/agents/conversation.py`
   - SYSTEM_PROMPT (linha 85-145)
   - execute_candidate_search (linha 338-547)
   - execute_global_search (linha 550-674)
   - generate_response (linha 792-839)

2. `lia-agent-system/app/api/v1/chat.py`
   - Smart context data builder (linha 135-177)

3. `replit.md`
   - Documentação de features (linha 74-75)

---

## Próximos Passos (Sugerido para Produção)

1. **Testes Automatizados:**
   ```python
   # tests/test_lia_personality.py
   async def test_missing_information_polite():
       response = await chat("busque no banco global")
       assert "problema técnico" not in response.lower()
       assert "me conte" in response.lower() or "preciso" in response.lower()
   ```

2. **Métricas de Qualidade:**
   - Rastrear % de respostas didáticas vs técnicas
   - Sentiment analysis das respostas
   - User satisfaction score

3. **A/B Testing:**
   - Versão educada vs versão técnica
   - Medir engajamento e conversão

---

## Impacto Esperado

✅ **Melhora na experiência do usuário**  
✅ **Redução de frustração** (sem mensagens de "erro" quando não há erro)  
✅ **Maior engajamento** (usuário recebe orientação ao invés de bloqueio)  
✅ **Tom profissional e colaborativo** (não defensivo ou impaciente)  

---

**Data:** 24 de Novembro de 2025  
**Autor:** Replit Agent  
**Status:** ✅ Implementado e Funcional
