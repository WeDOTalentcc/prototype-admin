# ADR-Studio-002: YAML declarativo como single source of truth para tool registry do Agent Studio

**Status:** ACCEPTED  
**Data:** 2026-06-14  
**Origem:** Auditoria ultracode Agent Studio

---

## Contexto

Antes do commit `b48d09bb5` (2026-06-13), o Agent Studio mantinha tres estruturas de dados independentes, todas declaradas como literais Python dentro de `custom_agent_runtime.py`:

1. `PLATFORM_TOOLS_REGISTRY: dict[str, str]` — 31 tools mapeados para `"read"` ou `"write"`, definidos inline como um dicionario com 60+ linhas de codigo no modulo.
2. `HITL_REQUIRED_TOOLS: frozenset[str]` — conjunto de 7 tools sensiveis que nunca executam sem aprovacao humana. Aparecia **duplicado**: uma vez no nivel de modulo (linhas ~55-65) e outra vez como atributo de classe dentro de `CustomAgentRuntime` (linhas ~174-185), causando inconsistencia potencial.
3. `domain_tool_loaders: dict[str, str]` — mapeamento de nome de dominio para caminho de importacao dotted do loader correspondente, embutido dentro do metodo `_get_tools()` da classe.

Este arranjo gerava tres problemas concretos registrados no commit message da migracao:
- **Split-brain de HITL_REQUIRED_TOOLS**: o registro de modulo e o atributo de classe podiam divergir sem que qualquer teste detectasse.
- **Bug silencioso no loader de pipeline**: o dominio `"pipeline"` apontava para `get_pipeline_tools` (funcao inexistente), enquanto a funcao real era `get_pipeline_transition_tools`. O erro so aparecia em runtime quando um agente do dominio pipeline era instanciado.
- **Custo de codigo para adicionar tool**: adicionar uma nova tool exigia editar codigo Python em `custom_agent_runtime.py`, que contem logica de runtime complexa, aumentando o risco de regressao acidental.

O contexto organizacional adicional: o Agent Studio passou por dois sprints de hardening de compliance em jun/2026 (P0-1 HITL gate em `0c1aa0acf`, P0-2 admin review gate em `413b73ba7`), ambos adicionando entries ao `HITL_REQUIRED_TOOLS`. Cada adicao reabria o arquivo de runtime de 463+ linhas, criando pressao crescente por uma separacao de configuracao e logica.

## Decisao

O registry declarativo do Agent Studio vive em `lia-agent-system/app/domains/agent_studio/config/platform_tools.yaml` como fonte unica de verdade, carregado por `platform_tools_loader.py` via `lru_cache`. Os tres registros previamente espalhados em Python sao consolidados em tres secoes YAML com semantica explicita:

- Secao `tools`: mapeia nome -> `{access: read|write}` para todas as 31 platform tools disponiveis a agentes customizados.
- Secao `hitl_required`: lista flat dos 7 nomes de tools que exigem aprovacao humana antes de executar.
- Secao `domains`: mapeia nome de dominio -> `{loader: dotted.import.path}` para os 10 domain tool registries carregados dinamicamente via `importlib`.

O loader (`platform_tools_loader.py`) expoe quatro funcoes tipadas e cacheadas: `get_platform_tools_registry()`, `get_hitl_required_tools()`, `get_domain_tool_loaders()`, `get_available_tool_names()`. O modulo `custom_agent_runtime.py` importa essas funcoes e reatribui as mesmas variaveis de modulo (`PLATFORM_TOOLS_REGISTRY`, `HITL_REQUIRED_TOOLS`) para manter compatibilidade com consumidores existentes sem breaking change.

Arquivos canonicos:
- `lia-agent-system/app/domains/agent_studio/config/platform_tools.yaml`
- `lia-agent-system/app/domains/agent_studio/platform_tools_loader.py`
- `lia-agent-system/tests/contract/test_platform_tools_yaml.py`

## Alternativas Consideradas

1. Dicionario Python inline (estado anterior, commit 993d4c9f6): os tres registros permaneceriam em custom_agent_runtime.py. Vantagem: type checking estatico completo via mypy; sem dependencia de PyYAML no startup. Desvantagem rejeitada: duplicacao de HITL_REQUIRED_TOOLS entre modulo e classe sem sensor de consistencia; bug de pipeline silencioso detectado apenas em runtime; qualquer adicao de tool requer toque no arquivo de 463 linhas de logica complexa.
2. Registry em banco de dados (ex: tabela agent_tool_registry): tools seriam inseridas via migration Alembic e lidas via SQLAlchemy em runtime. Vantagem: permite configuracao per-tenant e hot-reload sem restart. Desvantagem rejeitada: viola o principio de que configuracao de plataforma (nao de tenant) deve ser versionada em codigo; adiciona latencia de DB no startup do agente; impede validacao em CI sem banco rodando.
3. Variaveis de ambiente: cada tool seria habilitada/desabilitada via env var prefixada (ex: AGENT_TOOL_SEARCH_CANDIDATES=read). Vantagem: permite feature flags por ambiente sem redeploy. Desvantagem rejeitada: 31+ variaveis de ambiente tornam o schema ilegivel; sem estrutura hierarquica para agrupar HITL vs access vs domain loaders; impossivel validar completude no CI.

## Consequencias

### Positivas
- Adicao de nova tool nao exige modificar custom_agent_runtime.py — basta adicionar uma linha em platform_tools.yaml, eliminando risco de regressao acidental na logica de runtime.
- A duplicacao de HITL_REQUIRED_TOOLS foi eliminada: havia uma copia no nivel de modulo e outra como atributo de classe em CustomAgentRuntime; agora ha uma unica fonte carregada via loader, confirmado no diff do commit b48d09bb5.
- O bug do domain loader de pipeline (get_pipeline_tools inexistente -> get_pipeline_transition_tools correto) foi detectado e corrigido durante a migracao, pois o YAML forcou revisao explicita de todos os 10 loaders simultaneamente.
- O YAML e legivel por nao-engenheiros (product managers, compliance team) que precisam auditar quais tools existem e quais requerem HITL, sem precisar entender a logica Python circundante.
- 13 testes de contrato em test_platform_tools_yaml.py validam estrutura, tipos, cardinalidade minima, importabilidade dos loaders e consistencia loader<->YAML a cada CI run — impede regressao silenciosa.
- lru_cache garante que o YAML e lido exatamente uma vez por processo, sem overhead de I/O em cada instanciacao de agente.

### Negativas / Trade-offs
- PyYAML e adicionado como dependencia de startup obrigatoria; falha de parse (ex: YAML malformado por erro de indentacao) causa ImportError no modulo, derrubando o servico inteiro em vez de degradar apenas o Agent Studio.
- Seguranca de tipos e mais fraca que Python: o YAML nao valida em tempo de edicao que um campo access tem valor 'read' ou 'write' — a validacao ocorre apenas no teste de CI ou em runtime. Um editor sem schema YAML configurado pode introduzir valores invalidos sem aviso imediato.
- Autocompletion de IDE nao funciona ao editar platform_tools.yaml sem um JSON Schema registrado; engenheiros adicionando tools manualmente nao recebem sugestao de campos disponiveis.
- O padrao de reatribuicao em custom_agent_runtime.py (PLATFORM_TOOLS_REGISTRY = _load_registry()) mantem as variaveis de modulo por compatibilidade, mas cria uma indirecao nao-obvia: leitores do codigo veem uma atribuicao de modulo mas precisam seguir o loader para entender a fonte real.

## Sensores

- test_platform_tools_yaml.py (13 testes de contrato, blocking em CI): valida que o YAML parseia sem erro; que todas tools tem access em {read, write}; que hitl_required e lista nao-vazia; que todos domain loaders tem dotted path com ao menos 2 pontos; que as funcoes do loader retornam os tipos corretos (dict, frozenset, list); que os modulos de loader sao importaveis via importlib e as funcoes sao callable; que set(registry.keys()) == set(config['tools'].keys()) — consistencia loader<->YAML.
- Validacao de importabilidade de domain loaders (test_domain_loaders_importable): para cada um dos 10 dominios, executa importlib.import_module + getattr + assert callable. Detectaria imediatamente o bug historico de pipeline (get_pipeline_tools inexistente) que existia antes da migracao.
- Testes de contrato existentes adaptados (test_agent_studio_wiring_batch2.py, test_agent_studio_wiring_voice.py, test_interview_intelligence_agent_studio.py): foram atualizados no mesmo commit b48d09bb5 para verificar via loader em vez de importar as variaveis de modulo diretamente, garantindo que a interface publica do loader cobre todos os casos de uso anteriores.

## Arquivos Canonicos

- `lia-agent-system/app/domains/agent_studio/config/platform_tools.yaml`
- `lia-agent-system/app/domains/agent_studio/platform_tools_loader.py`
- `lia-agent-system/app/domains/agent_studio/custom_agent_runtime.py`
- `lia-agent-system/tests/contract/test_platform_tools_yaml.py`
