"""
Few-shot examples for the Sourcing Agent.

Exemplos de busca de candidatos, geração de boolean strings, sugestões,
outreach personalizado e tratamento de buscas vazias.
"""


SEARCH_PYTHON_CANDIDATES = {
    "user": "Busque candidatos Python sênior com experiência em FastAPI e AWS para a vaga de Desenvolvedor Backend.",
    "assistant": """🔍 **Resultado da Busca**

**Vaga**: Desenvolvedor Backend Python
**Critérios**: Python Sênior + FastAPI + AWS

---

**Resumo da Busca**
| Fonte | Candidatos Encontrados | Match > 80% |
|-------|------------------------|-------------|
| Banco Interno | 18 | 7 |
| Pearch AI | 45 | 12 |
| **Total (sem duplicatas)** | **56** | **19** |

---

**Shortlist - Top 10 Candidatos**

| # | Nome | Senioridade | Match | Skills Principais | Status | Contato |
|---|------|-------------|-------|-------------------|--------|---------|
| 1 | Ricardo Almeida | Sênior (7 anos) | 94% | Python, FastAPI, AWS, Terraform | Banco interno | ✅ Disponível |
| 2 | Camila Santos | Sênior (6 anos) | 91% | Python, FastAPI, AWS, Docker | Novo (Pearch) | ✅ Disponível |
| 3 | Fernando Costa | Sênior (8 anos) | 89% | Python, Django, FastAPI, AWS | Banco interno | ✅ Disponível |
| 4 | Amanda Oliveira | Sênior (5 anos) | 87% | Python, FastAPI, GCP, Kubernetes | Novo (Pearch) | ✅ Disponível |
| 5 | Lucas Mendes | Sênior (6 anos) | 85% | Python, Flask, FastAPI, AWS | Banco interno | ⚠️ Em processo |
| 6 | Juliana Ferreira | Pleno+ (4.5 anos) | 84% | Python, FastAPI, AWS, PostgreSQL | Novo (Pearch) | ✅ Disponível |
| 7 | Rafael Lima | Sênior (7 anos) | 82% | Python, FastAPI, Azure, Docker | Novo (Pearch) | ✅ Disponível |
| 8 | Mariana Ribeiro | Sênior (5 anos) | 81% | Python, FastAPI, AWS, Redis | Banco interno | ✅ Disponível |
| 9 | Bruno Carvalho | Sênior (6 anos) | 80% | Python, Django, AWS, Celery | Novo (Pearch) | ✅ Disponível |
| 10 | Patrícia Souza | Pleno+ (4 anos) | 79% | Python, FastAPI, AWS, MongoDB | Novo (Pearch) | ✅ Disponível |

---

**Análise do Pipeline**

*Distribuição por Senioridade*
| Nível | Quantidade | % |
|-------|------------|---|
| Sênior (5+ anos) | 42 | 75% |
| Pleno+ (4-5 anos) | 10 | 18% |
| Pleno (3-4 anos) | 4 | 7% |

*Skills mais frequentes*
| Skill | Ocorrência | Aderência à Vaga |
|-------|------------|------------------|
| Python | 100% | ✅ Obrigatório |
| AWS | 78% | ✅ Obrigatório |
| FastAPI | 62% | ✅ Obrigatório |
| Docker | 71% | ✅ Desejável |
| PostgreSQL | 54% | ✅ Desejável |

*Disponibilidade para CLT*
| Modalidade | Quantidade | % |
|------------|------------|---|
| Apenas CLT | 28 | 50% |
| CLT ou PJ | 21 | 38% |
| Apenas PJ | 7 | 12% |

---

💾 **Persistência**
- 38 novos candidatos adicionados ao WedoTalent (origem: Pearch AI)
- 18 perfis existentes atualizados
- Todos vinculados à vaga com status "Sourced"
- Sincronizado com ATS: ✅

➡️ **Próximos Passos Sugeridos**
1. Aprovar shortlist para outreach
2. Revisar Lucas Mendes (já está em outro processo nosso)
3. Iniciar contato com top 5 candidatos

Deseja que eu inicie o outreach para os candidatos selecionados?""",
    "intent": "search_candidates",
    "context": {
        "vaga": "Desenvolvedor Backend Python",
        "vaga_id": "DEV-PY-2024-001",
        "etapa": "sourcing",
        "skills_buscadas": ["Python", "FastAPI", "AWS"]
    }
}

GENERATE_BOOLEAN_STRING = {
    "user": "Gere uma boolean string para buscar Product Managers com experiência em B2B SaaS e marketplace.",
    "assistant": """🔤 **Boolean String - Product Manager B2B SaaS/Marketplace**

---

**String Principal (LinkedIn/Pearch AI)**

```
("Product Manager" OR "PM" OR "Gerente de Produto" OR "Product Owner") 
AND 
("B2B" OR "SaaS" OR "Software as a Service" OR "Enterprise") 
AND 
("marketplace" OR "two-sided" OR "plataforma" OR "platform") 
AND 
(Brazil OR Brasil OR "São Paulo" OR "Rio de Janeiro" OR Remote OR Remoto)
```

---

**Variações Otimizadas**

*Versão Expandida (maior recall)*
```
("Product Manager" OR "Sr Product Manager" OR "Senior PM" OR "Lead PM" 
OR "Gerente de Produto" OR "Product Owner" OR "PO" OR "Head of Product" 
OR "Director of Product" OR "VP Product") 
AND 
("B2B SaaS" OR "B2B" OR "Enterprise Software" OR "SaaS" OR "Software as a Service" 
OR "Corporativo" OR "Enterprise Sales") 
AND 
("marketplace" OR "two-sided marketplace" OR "peer-to-peer" OR "P2P" 
OR "platform" OR "plataforma digital" OR "e-commerce B2B")
```

*Versão Precisão (menor recall, maior qualidade)*
```
"Product Manager" 
AND ("B2B SaaS" OR "Enterprise SaaS") 
AND "marketplace" 
AND ("metrics" OR "OKRs" OR "roadmap") 
NOT ("Junior" OR "Associate" OR "Intern" OR "Estágio")
```

---

**Termos por Categoria**

| Categoria | Termos Incluídos | Termos Excluídos |
|-----------|------------------|------------------|
| Cargo | Product Manager, PM, Gerente de Produto, Product Owner, Head of Product | Junior PM, Associate PM, APM |
| Segmento | B2B, SaaS, Enterprise, Corporativo | B2C, Consumer, Varejo |
| Modelo | Marketplace, Platform, Two-sided, P2P | E-commerce D2C |
| Localização | Brasil, Brazil, São Paulo, Remote | (ajustar conforme necessidade) |

---

**Dicas de Uso**

1. **LinkedIn Recruiter**: Use a string principal, adicione filtros de localização e senioridade
2. **Pearch AI**: String completa funciona bem, pode adicionar filtros de empresa
3. **GitHub/Stack Overflow**: Não recomendado para PM (perfil não-técnico)

**Estimativa de Resultados**
| Plataforma | Resultados Estimados |
|------------|---------------------|
| LinkedIn Brasil | 800-1.200 |
| Pearch AI | 400-600 |
| Combinado (sem duplicatas) | 1.000-1.500 |

---

**Filtros Adicionais Recomendados**

```
Senioridade: 4+ anos de experiência
Idiomas: Inglês fluente (se necessário)
Empresas anteriores: 
  - Incluir: iFood, Nubank, Loft, QuintoAndar, Mercado Livre, VTEX
  - Excluir: Consultorias puras
```

💾 **Persistência**
- Boolean string salva para a vaga: ✅
- Disponível para reutilização

➡️ **Próximos Passos**
1. Executar busca com a string principal
2. Ajustar termos baseado nos primeiros resultados
3. Salvar candidatos promissores no pipeline

Deseja que eu execute a busca com esta string?""",
    "intent": "generate_boolean",
    "context": {
        "vaga": "Product Manager B2B",
        "etapa": "definicao_busca",
        "segmentos": ["B2B", "SaaS", "marketplace"]
    }
}

SUGGEST_CANDIDATES_FOR_JOB = {
    "user": "Sugira candidatos do nosso banco para a nova vaga de Data Engineer.",
    "assistant": """💡 **Sugestões de Candidatos - Data Engineer**

Com base na vaga de Data Engineer e no nosso banco de talentos, encontrei candidatos que podem ser um bom fit:

---

**Candidatos Recomendados do Banco Interno**

| # | Nome | Match | Último Processo | Motivo da Sugestão |
|---|------|-------|-----------------|-------------------|
| 1 | **Marcos Silva** | 92% | Reprovado fase final (outro perfil escolhido) - há 3 meses | Skills perfeitas: Spark, Airflow, AWS. Foi finalista em vaga similar |
| 2 | **Carolina Nunes** | 88% | Desistiu por contraproposta - há 6 meses | Excelente perfil técnico. Vale recontatá-la |
| 3 | **Thiago Martins** | 85% | Aprovado em triagem, não chamado - há 4 meses | Pool da vaga de Analytics Eng. Perfil de Data Eng |
| 4 | **Fernanda Lima** | 82% | Sourced, nunca contatada - há 2 meses | Encontrada em busca anterior, perfil promissor |
| 5 | **Roberto Souza** | 80% | Concluiu processo, não aceitou - há 8 meses | Verificar disponibilidade atual |

---

**Detalhamento dos Top 3**

**1. Marcos Silva** ⭐ Recomendado
| Atributo | Valor |
|----------|-------|
| Senioridade | Sênior (6 anos) |
| Skills | Python, Spark, Airflow, AWS (Glue, Redshift), dbt |
| Formação | Mestrado em Ciência de Dados - USP |
| Última empresa | Magazine Luiza - Data Engineer |
| Pretensão anterior | R$ 18.000 (pode ter mudado) |
| Histórico conosco | Chegou à fase final, feedback positivo. Não selecionado por fit com outro candidato |

**Por que recontatá-lo:**
- Perfil técnico excepcional
- Já conhece nosso processo
- Feedback anterior: "Excelente candidato, guardar para próxima oportunidade"

---

**2. Carolina Nunes** ⭐ Potencial alto
| Atributo | Valor |
|----------|-------|
| Senioridade | Pleno+ (4.5 anos) |
| Skills | Python, Spark, Kafka, GCP (BigQuery, Dataflow) |
| Formação | Engenharia de Computação - Unicamp |
| Última empresa | iFood - Data Engineer |
| Pretensão anterior | R$ 16.000 |
| Histórico conosco | Desistiu após contraproposta do iFood. Pode estar aberta agora |

**Por que recontatá-la:**
- 6 meses se passaram, pode estar aberta a mudanças
- Stack moderna e diferenciada (GCP)
- Excelente background

---

**3. Thiago Martins** ⭐ Pool aproveitável
| Atributo | Valor |
|----------|-------|
| Senioridade | Pleno (3.5 anos) |
| Skills | Python, SQL, Airflow, AWS, Snowflake |
| Formação | Estatística - UFMG |
| Última empresa | Creditas - Analytics Engineer |
| Pretensão anterior | R$ 14.000 |
| Histórico conosco | Triado com score 78, não foi chamado por limite de vagas |

**Por que recontatá-lo:**
- Já aprovado em triagem técnica
- Perfil em crescimento, pode ter evoluído
- Analytics Eng → Data Eng é transição natural

---

**Análise do Banco**

| Categoria | Quantidade | Ação Recomendada |
|-----------|------------|------------------|
| Finalistas de processos anteriores | 8 | Prioridade alta para recontato |
| Desistências por contraproposta | 5 | Verificar momento atual |
| Pool não utilizado de vagas similares | 12 | Reavaliar para nova vaga |
| Sourced mas nunca contatados | 23 | Incluir no outreach inicial |

**Total aproveitável**: 48 candidatos

---

💾 **Persistência**
- Candidatos sugeridos vinculados à nova vaga: ✅
- Status atualizado para "Recontato Sugerido"

➡️ **Próximos Passos**
1. Aprovar lista de recontato
2. Personalizar mensagens (mencionar processo anterior)
3. Iniciar outreach com prioridade nos top 5

Deseja que eu prepare mensagens de recontato personalizadas para estes candidatos?""",
    "intent": "suggest_candidates",
    "context": {
        "vaga": "Data Engineer",
        "vaga_id": "DE-2024-001",
        "etapa": "sourcing",
        "fonte": "banco_interno"
    }
}

PERSONALIZED_OUTREACH = {
    "user": "Crie uma mensagem de outreach personalizada para a candidata Camila Santos para a vaga de Desenvolvedora Python.",
    "assistant": """📤 **Outreach Personalizado**

**Candidata**: Camila Santos
**Vaga**: Desenvolvedora Python Sênior
**Canal**: WhatsApp (preferencial) / LinkedIn

---

**Mensagem Principal - WhatsApp**

```
Olá Camila, tudo bem?

Sou assistente de recrutamento da WeDOTalent. Vi seu perfil e fiquei impressionada com sua trajetória - especialmente sua experiência com FastAPI e arquiteturas em AWS.

Estou trabalhando em uma posição de Desenvolvedora Python Sênior para uma empresa de tecnologia que está crescendo bastante no mercado de fintechs. O projeto envolve construir sistemas de alta disponibilidade processando milhões de transações.

Alguns pontos que achei que podem interessar você:
• Stack: Python, FastAPI, AWS (seu match é alto!)
• Modelo: Híbrido em São Paulo (3x escritório)
• Faixa: R$ 20k - R$ 25k CLT + benefícios flexíveis

Você teria disponibilidade para uma conversa rápida de 15 minutos esta semana? Posso te contar mais sobre o desafio e entender se faz sentido para seu momento.

Agradeço desde já! 😊
```

---

**Variação - LinkedIn InMail**

```
Olá Camila,

Seu perfil chamou minha atenção pela combinação de FastAPI + AWS - exatamente o que estamos buscando para uma posição de Python Sênior em uma fintech em crescimento.

O desafio: arquitetar sistemas que processam milhões de transações com alta disponibilidade.

Modelo: Híbrido SP | Faixa: R$ 20-25k CLT

Topa uma conversa rápida para saber mais?

Abraço,
LIA - WeDOTalent
```

---

**Variação - Recontato (se já teve interação anterior)**

```
Olá Camila, tudo bem?

Conversamos há alguns meses sobre uma oportunidade, lembra? Na época o momento não era ideal.

Surgiu uma nova posição de Python Sênior que achei que combinaria muito com seu perfil. É numa fintech, stack com FastAPI e AWS, modelo híbrido em SP.

Se estiver aberta a ouvir mais, me avisa! Seria ótimo reconectar.

Abraço,
LIA
```

---

**Elementos de Personalização Usados**

| Elemento | Aplicação |
|----------|-----------|
| Nome | "Olá Camila" (personalizado) |
| Skills | Menção específica a FastAPI e AWS |
| Experiência | Referência à trajetória |
| Proposta de valor | Stack, modelo, faixa salarial |
| Call to action | Conversa de 15 minutos |
| Tom | Profissional mas acessível |

---

**Timing Recomendado**

| Dia | Horário | Canal | Motivo |
|-----|---------|-------|--------|
| Terça-feira | 10:00-11:00 | WhatsApp | Maior taxa de resposta |
| Quarta-feira | 14:00-15:00 | LinkedIn | Segunda opção |

---

**Follow-up (se não responder em 3 dias)**

```
Oi Camila! 

Só passando para saber se conseguiu ver minha mensagem sobre a vaga de Python Sênior. Entendo que a rotina é corrida.

Se não for o momento ou não tiver interesse, sem problemas! Me avisa para eu não ficar te incomodando. 😊

Abraço!
```

---

💾 **Persistência**
- Mensagem registrada no histórico da candidata: ✅
- Template salvo para reutilização: ✅
- Agendamento sugerido registrado

➡️ **Próximos Passos**
1. Aprovar mensagem
2. Confirmar canal de envio (WhatsApp/LinkedIn)
3. Agendar follow-up automático em 3 dias

Deseja que eu envie a mensagem agora ou prefere revisar primeiro?""",
    "intent": "personalized_outreach",
    "context": {
        "vaga": "Desenvolvedora Python Sênior",
        "candidato": "Camila Santos",
        "etapa": "outreach"
    }
}

EMPTY_SEARCH_RESPONSE = {
    "user": "Busque candidatos com experiência em Rust + WebAssembly + Kubernetes para nossa vaga de Systems Engineer.",
    "assistant": """🔍 **Resultado da Busca**

**Vaga**: Systems Engineer
**Critérios**: Rust + WebAssembly + Kubernetes

---

**Resumo da Busca**
| Fonte | Candidatos Encontrados | Match > 80% |
|-------|------------------------|-------------|
| Banco Interno | 0 | 0 |
| Pearch AI | 3 | 0 |
| **Total** | **3** | **0** |

---

⚠️ **Busca com Poucos Resultados**

A combinação de skills solicitada é muito específica e rara no mercado brasileiro. Encontrei apenas 3 candidatos, nenhum com match alto.

**Candidatos Encontrados (match parcial)**

| # | Nome | Match | Skills Presentes | Skills Faltantes |
|---|------|-------|------------------|------------------|
| 1 | André Machado | 45% | Rust, Kubernetes | WebAssembly |
| 2 | Beatriz Costa | 42% | Rust, WebAssembly | Kubernetes |
| 3 | Carlos Ramos | 38% | Kubernetes | Rust, WebAssembly |

---

**Análise do Mercado**

| Skill | Profissionais no Brasil (estimativa) | Dificuldade |
|-------|-------------------------------------|-------------|
| Rust | ~2.000 | Alta |
| WebAssembly | ~800 | Muito Alta |
| Kubernetes | ~15.000 | Média |
| Rust + WebAssembly | ~200 | Crítica |
| Rust + Wasm + K8s | ~50 | Extrema |

---

**💡 Recomendações**

**Opção 1: Flexibilizar Requisitos**
Considere aceitar candidatos com:
- Rust + Kubernetes (sem Wasm) - Pool de ~500 candidatos
- Rust + WebAssembly (K8s como desejável) - Pool de ~200 candidatos
- Golang/C++ + Kubernetes (Rust como diferencial) - Pool de ~3.000 candidatos

**Opção 2: Buscar Skills Transferíveis**
Profissionais com background em:
- C/C++ → Transição natural para Rust
- Golang + sistemas distribuídos → Podem aprender Rust
- Frontend + Performance → WebAssembly

**Opção 3: Expandir Geograficamente**
- Buscar candidatos remotos internacionais
- Focar em Portugal e países de língua espanhola
- Considerar contratação PJ internacional

**Opção 4: Desenvolver Internamente**
- Contratar dev Rust forte e treinar em Wasm
- Contratar dev K8s expert e treinar em Rust
- Programa de capacitação de 3-6 meses

---

**Nova Estratégia de Busca Sugerida**

```
Critérios relaxados:
- Obrigatório: Rust OU (C/C++ + interesse em Rust)
- Obrigatório: Kubernetes OR Docker + sistemas distribuídos
- Desejável: WebAssembly (pode treinar)
- Desejável: Background em sistemas de alta performance
```

**Estimativa com critérios relaxados**: 150-300 candidatos

---

💾 **Persistência**
- Busca registrada (resultados limitados): ✅
- 3 candidatos de match parcial adicionados

➡️ **Próximos Passos**
1. Decidir qual estratégia seguir
2. Se flexibilizar, posso executar nova busca
3. Se manter critérios, posso expandir busca internacional

Como você gostaria de prosseguir? Posso ajudar a revisar os requisitos da vaga com o gestor se necessário.""",
    "intent": "search_candidates",
    "context": {
        "vaga": "Systems Engineer",
        "vaga_id": "SE-2024-001",
        "etapa": "sourcing",
        "skills_buscadas": ["Rust", "WebAssembly", "Kubernetes"],
        "resultado": "busca_vazia"
    }
}

SOURCING_EXAMPLES = [
    SEARCH_PYTHON_CANDIDATES,
    GENERATE_BOOLEAN_STRING,
    SUGGEST_CANDIDATES_FOR_JOB,
    PERSONALIZED_OUTREACH,
    EMPTY_SEARCH_RESPONSE,
]
