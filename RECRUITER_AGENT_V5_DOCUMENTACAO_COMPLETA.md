# 📋 RECRUITER_AGENT_V5 — Documento Completo de Análise

  ## Repositório: talensestg/recruiter_agent_v5
  - **Linguagem Principal**: Python
  - **Repositório Privado**: Sim
  - **Branch Principal**: main
  - **Última Atualização**: 2026-03-04
  - **Total de Itens**: 403 (arquivos + diretórios)

  ---

  ## Índice

  ### Parte 1: Core — Entry Point + Agentes Principais
  - main.py — Entry point principal (FastAPI + multi-agent pipeline)
  - requirements.txt — Dependências
  - src/agents/ — 6 agentes do pipeline principal:
    - intent_analyzer.py — Análise de intenção do usuário
    - api_planner.py — Planejamento de chamadas API
    - plan_validator.py — Validação do plano
    - api_executor.py — Execução de APIs
    - data_processor.py — Processamento de dados
    - answer_formatter.py — Formatação de resposta

  ### Parte 2: Configurações + Domains Core
  - src/config/ — 11 arquivos de configuração
  - src/domains/ — Base, Registry, Orchestrator

  ### Parte 3: Evaluation Domain (LangGraph)
  - src/domains/evaluation/ — 14 arquivos
    - graph.py — LangGraph DAG
    - nodes.py — Nós do grafo
    - state.py — Estado do grafo
    - prompts.py — Prompts de avaliação
    - tasks.py + worker.py — Celery tasks

  ### Parte 4: Sourced Profile Sourcing — Actions
  - src/domains/sourced_profile_sourcing/actions/ — 8 ações
    - analysis, comparison, count, details, distribution, insights, report

  ### Parte 5: Workers, Models, Chat
  - chat.py — Interface de chat
  - celery_worker.py, evaluation_worker.py — Workers
  - src/models/ — Models de estado e dados

  ### Parte 5b: Sourcing Agents + Services + Tools + Workflow
  - src/domains/sourced_profile_sourcing/agents/ — 10 agentes de sourcing
  - src/domains/sourced_profile_sourcing/config/ — Configurações
  - src/domains/sourced_profile_sourcing/prompt_builder/ — Builder de prompts
  - src/services/ — 14 serviços (API, auth, memory, RAG, embedding, etc.)
  - src/tools/ — 6 arquivos de tools
  - src/workflow/ — Workflow graph (LangGraph)
  - src/api_controllers/ — Controllers de API

  ### Parte 6: Deploy, Scripts, Examples
  - deploy/ — Scripts de deploy GCP
  - docker-compose.workers.yml — Workers Docker
  - scripts/ — Utilidades e testes
  - examples/ — Demos

  ---

  # RECRUITER_AGENT_V5 — Documentação Completa

## Gerado em: 2026-03-08T13:24:56.413Z

---

## 📄 main.py

```python
"""
Main entry point for the Recruiter Agent V5.
Supports CLI mode and RabbitMQ worker mode.
"""

import sys
import argparse
import logging
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from src.config.settings import get_settings
from src.workflow.graph import create_workflow
from src.services.memory_service import MemoryService
from src.services.rabbitmq_service import RabbitMQService
from src.services.message_router import MessageRouter
from src.utils.logger import setup_logging
from src.utils.callbacks import send_to_rails_callback
from src.models.response import QueryResponse


logger = logging.getLogger(__name__)


class RecruiterAgentCLI:
    """Command-line interface for the recruiter agent."""

    def __init__(self):
        """Initialize CLI with workflow and settings."""
        self.settings = get_settings()
        self.workflow = create_workflow()
        self.memory = None

        # Memory is optional - system works 100% via REST APIs
        if self.settings.memory.enabled:
            try:
                self.memory = MemoryService(self.settings.postgres)
                logger.info("✓ Memory service enabled (PostgreSQL)")
            except Exception as e:
                logger.warning(f"⚠️  Memory service disabled: {e}")
                logger.info(
                    "System will work without persistence (100% via REST APIs)")
        else:
            logger.info(
                "✓ Memory service disabled (working 100% via REST APIs only)")

    def process_query(self, question: str, session_id: Optional[str] = None) -> QueryResponse:
        """
        Process a single query.

        Args:
            question: User's question.
            session_id: Optional session ID for tracking.

        Returns:
            Query response.
        """
        session_id = session_id or str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"Processing query (session: {session_id}): {question}")

        try:
            # Execute workflow
            state = self.workflow.process_query(question)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Extract metadata
            processed_data = state.get("processed_data", {})
            summary = processed_data.get("summary", {})

            # Create response
            response = QueryResponse(
                question=question,
                answer=state.get("final_answer", ""),
                intent=state.get("intent", {}),
                api_calls=summary.get("total_api_calls", 0),
                total_records=summary.get("total_records", 0),
                execution_time_ms=execution_time_ms,
                error=state.get("error"),
                metadata={
                    "session_id": session_id,
                    "processed_data": processed_data,
                    "needs_confirmation": state.get("needs_confirmation", False),
                    "confirmation_request": state.get("confirmation_request")
                }
            )

            # Save to memory if enabled
            if self.memory:
                try:
                    self.memory.save_conversation(
                        session_id=session_id,
                        question=question,
                        answer=response.answer,
                        intent=response.intent,
                        metadata=response.metadata
                    )

                    self.memory.save_metrics(
                        session_id=session_id,
                        execution_time_ms=execution_time_ms,
                        api_calls=response.api_calls,
                        total_records=response.total_records,
                        success=response.success,
                        error_message=response.error
                    )
                except Exception as e:
                    logger.warning(f"Failed to save to memory: {e}")

            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)

            execution_time_ms = (time.time() - start_time) * 1000

            return QueryResponse(
                question=question,
                answer=f"❌ Desculpe, ocorreu um erro ao processar sua pergunta.",
                error=str(e),
                execution_time_ms=execution_time_ms,
                metadata={"session_id": session_id}
            )

    def interactive_mode(self):
        """Run in interactive CLI mode."""
        print("🤖 Recruiter Agent V5 - Interactive Mode")
        print("=" * 60)
        print("Digite suas perguntas ou 'exit' para sair.\n")

        session_id = str(uuid.uuid4())

        while True:
            try:
                question = input("\n❓ Pergunta: ").strip()

                if not question:
                    continue

                if question.lower() in ['exit', 'quit', 'sair']:
                    print("\n👋 Até logo!")
                    break

                # Process query
                response = self.process_query(question, session_id)

                # Check if needs confirmation
                if hasattr(response, 'metadata') and response.metadata.get('needs_confirmation'):
                    confirmation_request = response.metadata.get(
                        'confirmation_request')

                    if confirmation_request:
                        # Display options
                        print(f"\n{confirmation_request['message']}")
                        print("\nOpções:")
                        for opt in confirmation_request['options']:
                            print(f"  {opt['index']}. {opt['name']}")
                        print("  0. Cancelar")

                        # Get user choice (intelligent interpretation)
                        while True:
                            try:
                                choice = input(
                                    "\n👉 Escolha (número, ID, email, nome ou 'cancelar'): ").strip()

                                # Check for cancel command
                                if choice.lower() in ['0', 'cancelar', 'cancel', 'sair', 'exit']:
                                    print("❌ Operação cancelada.")
                                    break

                                # Try to interpret user's choice intelligently
                                selected = self._interpret_choice(
                                    choice, confirmation_request['options'])

                                if selected:
                                    print(f"✓ Selecionado: {selected['name']}")

                                    # Continue execution with selected item
                                    response = self._continue_with_confirmation(
                                        question, session_id, confirmation_request, selected
                                    )

                                    # Display final answer
                                    print(f"\n📊 Resposta:\n{response.answer}")
                                    print(f"\n⏱️  Tempo: {response.execution_time_ms:.2f}ms | "
                                          f"APIs: {response.api_calls} | "
                                          f"Registros: {response.total_records}")
                                    break
                                else:
                                    print(
                                        f"❌ Não consegui identificar qual opção você quer. Tente: número (1-{len(confirmation_request['options'])}), ID, email ou nome.")
                            except KeyboardInterrupt:
                                print("\n❌ Operação cancelada.")
                                break
                else:
                    # Display answer normally
                    print(f"\n📊 Resposta:\n{response.answer}")
                    print(f"\n⏱️  Tempo: {response.execution_time_ms:.2f}ms | "
                          f"APIs: {response.api_calls} | "
                          f"Registros: {response.total_records}")

            except KeyboardInterrupt:
                print("\n\n👋 Até logo!")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"\n❌ Erro: {e}")

    def _interpret_choice(self, user_input: str, options: list) -> Optional[Dict[str, Any]]:
        """
        Interpreta a escolha do usuário de forma inteligente.
        Aceita: número (1-10), ID (631), email, nome, etc.

        Args:
            user_input: O que o usuário digitou
            options: Lista de opções disponíveis

        Returns:
            Opção selecionada ou None se não identificar
        """
        user_input = user_input.strip()

        # Tenta número direto (1, 2, 3...)
        try:
            choice_num = int(user_input)
            if 1 <= choice_num <= len(options):
                return options[choice_num - 1]
        except ValueError:
            pass

        # Tenta interpretar com LLM
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage
            import json

            llm = ChatGoogleGenerativeAI(
                model=self.settings.gemini.model,
                temperature=0.0,
                google_api_key=self.settings.gemini.api_key
            )

            # Prepara opções para análise
            options_info = []
            for opt in options:
                options_info.append({
                    "index": opt['index'],
                    "id": opt['id'],
                    "display": opt['name'],
                    "data": opt['item']
                })

            options_json = json.dumps(
                options_info, ensure_ascii=False, indent=2)

            prompt = f"""O usuário quer escolher uma opção e digitou: "{user_input}"

**Opções disponíveis:**
```json
{options_json}
```

**Sua tarefa:**
Identifique qual opção o usuário quer baseado no que ele digitou.

Ele pode ter mencionado:
- Um número de índice (ex: "2", "quero o 2")
- Um ID (ex: "631", "quero o ID 631")
- Um email (ex: "anderson.takemoto@gmail.com")
- Um nome (ex: "anderson takemoto")
- Qualquer outro campo identificador

**Retorne APENAS um JSON:**
{{
  "match_found": true/false,
  "index": <índice da opção escolhida>,
  "confidence": "high"/"medium"/"low",
  "reasoning": "por que você escolheu essa opção"
}}

Se não conseguir identificar com certeza, retorne match_found: false."""

            response = llm.invoke([HumanMessage(content=prompt)])
            result = json.loads(response.content.strip())

            if result.get('match_found') and result.get('confidence') in ['high', 'medium']:
                index = result['index']
                # Encontra opção pelo índice
                for opt in options:
                    if opt['index'] == index:
                        logger.info(
                            f"LLM interpreted choice: {result['reasoning']}")
                        return opt

        except Exception as e:
            logger.warning(f"Failed to interpret choice with LLM: {e}")

        # Fallback: busca simples por ID ou substring
        user_lower = user_input.lower()

        # Tenta match por ID exato
        for opt in options:
            if str(opt['id']) == user_input:
                return opt

        # Tenta match por substring no display name
        matches = []
        for opt in options:
            if user_lower in opt['name'].lower():
                matches.append(opt)

        # Retorna se achou exatamente 1 match
        if len(matches) == 1:
            return matches[0]

        return None

    def _continue_with_confirmation(
        self,
        question: str,
        session_id: str,
        confirmation_request: Dict[str, Any],
        selected_item: Dict[str, Any]
    ) -> QueryResponse:
        """
        Continue execution after user confirmation.

        Args:
            question: Original question.
            session_id: Session ID.
            confirmation_request: The confirmation request data.
            selected_item: The item selected by the user.

        Returns:
            Query response.
        """
        start_time = time.time()

        try:
            # Build state with confirmation
            initial_state = {
                "question": question,
                "messages": [],
                "intent": None,
                "api_plan": [],
                "plan_explanation": None,
                "api_results": {},
                "processed_data": {},
                "final_answer": "",
                "error": None,
                "needs_confirmation": False,
                "confirmation_request": None,
                "user_confirmation": {
                    "selected_item": selected_item['item'],
                    "selected_id": selected_item['id'],
                    "save_as": confirmation_request['save_as']
                },
                "metadata": {}
            }

            # Execute workflow with confirmation
            state = self.workflow.process_query_with_state(initial_state)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Extract metadata
            processed_data = state.get("processed_data", {})
            summary = processed_data.get("summary", {})

            # Create response
            response = QueryResponse(
                question=question,
                answer=state.get("final_answer", ""),
                intent=state.get("intent", {}),
                api_calls=summary.get("total_api_calls", 0),
                total_records=summary.get("total_records", 0),
                execution_time_ms=execution_time_ms,
                error=state.get("error"),
                metadata={
                    "session_id": session_id,
                    "processed_data": processed_data
                }
            )

            return response

        except Exception as e:
            logger.error(
                f"Error continuing with confirmation: {e}", exc_info=True)

            execution_time_ms = (time.time() - start_time) * 1000

            return QueryResponse(
                question=question,
                answer=f"❌ Desculpe, ocorreu um erro ao processar sua escolha.",
                error=str(e),
                execution_time_ms=execution_time_ms,
                metadata={"session_id": session_id}
            )


class RecruiterAgentWorker:
    """RabbitMQ worker for the recruiter agent."""

    def __init__(self):
        """Initialize worker with services."""
        self.settings = get_settings()
        self.router = MessageRouter()
        self.memory = None
        self.rabbitmq = None

        # Memory is optional - system works 100% via REST APIs
        if self.settings.memory.enabled:
            try:
                self.memory = MemoryService(self.settings.postgres)
                logger.info("✓ Memory service enabled (PostgreSQL)")
            except Exception as e:
                logger.warning(f"⚠️  Memory service disabled: {e}")
                logger.info(
                    "System will work without persistence (100% via REST APIs)")
        else:
            logger.info(
                "✓ Memory service disabled (working 100% via REST APIs only)")

    def handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming message from RabbitMQ.

        Args:
            message: Message payload with optional 'domain' and 'context_data' fields.
        """
        logger.info(f"📨 Raw message received: {message}")

        message_id = message.get("message_id") or message.get(
            "id", str(uuid.uuid4()))
        question = message.get("content", "")
        user_id = message.get("user_id") or message.get("reference_id")
        session_id = message.get("session_id", str(uuid.uuid4()))

        domain = message.get("domain")
        metadata = message.get("metadata", {})
        context = message.get("context", {})
        
        if not domain:
            domain = metadata.get("domain") or context.get("domain")

        sourcing_id = (
            message.get("domain_reference_id") or 
            message.get("sourcing_id") or
            metadata.get("sourcing_id") or
            context.get("sourcing_id") or
            context.get("domain_reference_id")
        )

        logger.info(f"Processing message {message_id}: {question}")
        logger.info(
            f"Domain: {domain or 'global'} | Sourcing ID: {sourcing_id}")
        
        if domain == "sourced_profile_sourcing" and not sourcing_id:
            logger.warning(f"⚠️ sourcing_id missing for sourced_profile_sourcing domain! Message keys: {list(message.keys())}, metadata: {metadata}, context: {context}")

        start_time = time.time()

        try:
            context_data = message.get("context_data", {})
            context_data.update({k: v for k, v in context.items() if v})
            context_data["user_id"] = user_id
            context_data["session_id"] = session_id
            if sourcing_id:
                context_data["sourcing_id"] = str(sourcing_id)

            one_time_token = message.get("one_time_token")

            response = self.router.route({
                "question": question,
                "domain": domain,
                "context_data": context_data,
                "user_id": user_id,
                "session_id": session_id,
                "one_time_token": one_time_token
            })

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Extract data
            answer = response.get("message", "")
            error = response.get("error")

            metadata_info = response.get("metadata", {})
            mode = metadata_info.get("mode", "global")

            if self.memory:
                try:
                    summary = metadata_info
                    self.memory.save_conversation(
                        session_id=session_id,
                        question=question,
                        answer=answer,
                        metadata={
                            "message_id": message_id,
                            "user_id": user_id,
                            "mode": mode,
                            "domain": metadata_info.get("domain")
                        },
                        user_id=user_id
                    )

                    self.memory.save_metrics(
                        session_id=session_id,
                        execution_time_ms=execution_time_ms,
                        api_calls=summary.get("total_api_calls", 0),
                        total_records=summary.get("total_records", 0),
                        success=error is None,
                        error_message=error
                    )
                except Exception as e:
                    logger.warning(f"Failed to save to memory: {e}")

            if mode != "domain":
                send_to_rails_callback(
                    config=self.settings.callback,
                    message_id=message_id,
                    content=answer,
                    metadata={
                        "execution_time_ms": execution_time_ms,
                        "api_calls": metadata_info.get("api_calls", 0),
                        "total_records": metadata_info.get("total_records", 0),
                        "session_id": session_id,
                        "mode": mode,
                        "domain": metadata_info.get("domain"),
                        "suggestions": response.get("suggestions", [])
                    },
                    error=error
                )

            logger.info(f"Message {message_id} processed successfully")

        except Exception as e:
            logger.error(
                f"Error processing message {message_id}: {e}", exc_info=True)

            # Send error callback
            send_to_rails_callback(
                config=self.settings.callback,
                message_id=message_id,
                content="❌ Desculpe, ocorreu um erro ao processar sua pergunta.",
                error=str(e)
            )

    def start(self):
        """Start the RabbitMQ worker."""
        logger.info("Starting RabbitMQ worker")

        try:
            self.rabbitmq = RabbitMQService(self.settings.rabbitmq)

            logger.info("Worker started, waiting for messages...")
            self.rabbitmq.consume_messages(self.handle_message)

        except KeyboardInterrupt:
            logger.info("Worker stopped by user")

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)

        finally:
            if self.rabbitmq:
                self.rabbitmq.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Recruiter Agent V5 - Multi-Agent Query System"
    )

    parser.add_argument(
        "mode",
        choices=["cli", "worker"],
        help="Run mode: cli (interactive) or worker (RabbitMQ consumer)"
    )

    parser.add_argument(
        "--question", "-q",
        help="Question to process (CLI mode only)"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )

    parser.add_argument(
        "--log-file",
        help="Log file path"
    )

    args = parser.parse_args()

    # Setup logging
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(level=args.log_level, log_file=log_file)

    logger.info(f"Starting Recruiter Agent V5 in {args.mode} mode")

    try:
        if args.mode == "cli":
            cli = RecruiterAgentCLI()

            if args.question:
                # Single query mode
                response = cli.process_query(args.question)
                print(f"\n{response.answer}\n")

                if response.error:
                    sys.exit(1)
            else:
                # Interactive mode
                cli.interactive_mode()

        elif args.mode == "worker":
            worker = RecruiterAgentWorker()
            worker.start()

    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

```

---

## 📄 requirements.txt

```txt
# Core Dependencies
langchain-core==0.3.29
langchain-google-genai==2.0.8
langgraph==0.2.58
google-generativeai==0.8.3

# HTTP Client
requests==2.32.3
urllib3==2.2.3
httpx>=0.25.0

# Database
psycopg2-binary==2.9.10
pgvector>=0.2.0

# YAML Parser for documentation
PyYAML>=6.0

# Message Queue
pika==1.3.2

# Task Queue
celery[redis]>=5.3.0
redis>=5.0.0
flower>=2.0.0

# Environment Variables
python-dotenv==1.0.1

# Web Interface
streamlit>=1.28.0
pandas>=2.0.0
# Web Framework (for Evaluation API)
flask==3.0.0
gunicorn==21.2.0

# Development Dependencies
pytest==8.3.4
pytest-cov==6.0.0
pytest-asyncio==0.24.0
black==24.10.0
mypy==1.13.0
pylint==3.3.2

```

---

## 📄 src/__init__.py

```python
"""Main package initialization."""

from .config.settings import get_settings
from .workflow.graph import create_workflow

__version__ = "5.0.0"

__all__ = ["get_settings", "create_workflow", "__version__"]

```

---

## 📄 src/agents/__init__.py

```python
"""Agents package for specialized agent implementations."""

from .intent_analyzer import IntentAnalyzerAgent
from .api_planner import APIPlannerAgent
from .api_executor import APIExecutorAgent
from .data_processor import DataProcessorAgent
from .answer_formatter import AnswerFormatterAgent
from .plan_validator import PlanValidatorAgent

__all__ = [
    "IntentAnalyzerAgent",
    "APIPlannerAgent",
    "APIExecutorAgent",
    "DataProcessorAgent",
    "AnswerFormatterAgent",
    "PlanValidatorAgent",
]

```

---

## 📄 src/agents/intent_analyzer.py

```python
"""
Intent Analyzer Agent - Analyzes user questions and identifies intent.
Follows Single Responsibility Principle.
"""

import json
import logging
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from ..models.state import QueryState
from ..config.settings import get_settings
from ..services.rag_service import RAGService


logger = logging.getLogger(__name__)


class IntentAnalyzerAgent:
    """
    Agent responsible for analyzing user questions and extracting intent.
    Uses LLM to understand natural language and structure it into actionable intent.
    """

    SYSTEM_PROMPT = """Você é o Intent Analyzer. Analise a pergunta e identifique:

1. **entities**: Quais tabelas são necessárias? (candidates, jobs, applies, selective_processes)
2. **main_action**: Qual a ação principal?
   - "list": listar registros
   - "count": contar registros
   - "filter": filtrar por critérios
   - "aggregate": calcular métricas (média, soma, etc)
   - "analyze": análise complexa (correlações, padrões)
   - "create_applies": inscrever/enviar/adicionar candidatos em vaga (AÇÃO COMPOSTA)
   - "multi_step": múltiplas ações encadeadas
   
3. **filters**: Filtros a serem aplicados
4. **aggregations**: Agregações necessárias (count, avg, sum, min, max, group_by)
5. **fields_needed**: Campos específicos necessários
6. **restricted_fields**: CRÍTICO - Se usuário diz "apenas X e Y" ou "only X", liste SOMENTE esses campos
   - "apenas nomes e emails" → ["name", "email"]
   - "somente IDs" → ["id"]
   - Se NÃO mencionar restrição, deixe null

7. **⚠️ DETECÇÃO DE AMBIGUIDADE (CRÍTICO)**:
   - **ambiguous_references**: Lista de referências que NÃO podem ser resolvidas sem busca
   - **requires_entity_resolution**: true se precisa resolver entidades ANTES de continuar
   - **unresolved_entities**: Lista de entidades mencionadas que podem ter múltiplos matches
   - **requires_confirmation**: true se a ação é destrutiva ou em massa
   - **confirmation_reason**: Por que confirmação é necessária
   - **affected_count_unknown**: true se não sabemos quantos registros serão afetados

**REGRAS DE DETECÇÃO DE AMBIGUIDADE:**

1. **Nomes de pessoas SEM identificador único** → ambiguous_references
   - "João Silva" → pode haver múltiplos
   - "candidato@email.com" → único (email é identificador)
   - "candidato ID 123" → único (ID explícito)

2. **Referências vagas a entidades** → ambiguous_references
   - "a vaga de desenvolvedor" → qual vaga exatamente?
   - "o processo seletivo" → qual processo?
   - "a primeira fase" → primeira fase de qual vaga?

3. **IMPORTANTE: "candidatos DA VAGA X"** → main_action = "list"
   - Objetivo: listar CANDIDATOS que se inscreveram na vaga
   - NÃO é buscar a vaga, é buscar candidatos inscritos
   - Sempre envolve: jobs_search → applies_search → candidates
   - entities: ["candidates", "jobs", "applies"]

4. **Operações em massa** → requires_confirmation = true
   - "inscreva TODOS os candidatos" → confirmar quantidade
   - "delete os candidatos inativos" → confirmar antes de deletar
   - "mova para próxima fase" → confirmar quantos candidatos

5. **Dependências não resolvidas** → requires_entity_resolution = true
   - "candidatos na fase X da vaga Y" → precisa: 1) buscar vaga, 2) buscar fases, 3) buscar candidatos

**Tabelas disponíveis:**
- **candidates**: candidatos (name, email, role_name, city, state, clt_expectation, pj_expectation, remote_work, etc)
- **jobs**: vagas (title, description, city, state, is_remote, seniority, salary_from, salary_to, etc)
- **applies**: candidaturas (candidate_id, job_id, selective_process_id, selective_process_status, applied_at, etc)
- **selective_processes**: processos seletivos/etapas (job_id, status_name, description, etc)

**EXEMPLOS:**

Pergunta: "Inscreva João Silva na vaga de desenvolvedor"
```json
{
  "entities": ["candidates", "jobs", "selective_processes", "applies"],
  "main_action": "create_applies",
  "filters": {
    "candidates.name": {"ilike": "%joão silva%"},
    "jobs.title": {"ilike": "%desenvolvedor%"}
  },
  "ambiguous_references": [
    {"type": "candidate", "reference": "João Silva", "reason": "Nome comum, pode haver múltiplos"},
    {"type": "job", "reference": "vaga de desenvolvedor", "reason": "Múltiplas vagas podem ter 'desenvolvedor' no título"}
  ],
  "requires_entity_resolution": true,
  "unresolved_entities": ["candidate_id", "job_id", "selective_process_id"],
  "requires_confirmation": true,
  "confirmation_reason": "Operação de criação com entidades ambíguas",
  "affected_count_unknown": false
}
```

Pergunta: "Liste apenas nomes e emails dos candidatos de TI"
```json
{
  "entities": ["candidates"],
  "main_action": "list",
  "filters": {"role_name": {"ilike": "%TI%"}},
  "fields_needed": ["id", "name", "email"],
  "restricted_fields": ["name", "email"],
  "ambiguous_references": [],
  "requires_entity_resolution": false,
  "unresolved_entities": [],
  "requires_confirmation": false,
  "note": "Usuário pediu APENAS nomes e emails - compact deve ter SOMENTE: id,name,email"
}
```

Pergunta: "Quantos candidatos de São Paulo?"
```json
{
  "entities": ["candidates"],
  "main_action": "count",
  "filters": {"city": {"ilike": "%são paulo%"}},
  "aggregations": [{"function": "count", "entity": "candidates"}],
  "fields_needed": ["id"],
  "restricted_fields": null,
  "ambiguous_references": [],
  "requires_entity_resolution": false,
  "unresolved_entities": [],
  "requires_confirmation": false
}
```

Pergunta: "Liste TODOS os candidatos da vaga de Backend Developer"
```json
{
  "entities": ["candidates", "jobs", "applies"],
  "main_action": "list",
  "filters": {
    "jobs.title": {"ilike": "%backend developer%"}
  },
  "fields_needed": ["candidates.id", "candidates.name", "candidates.email"],
  "ambiguous_references": [
    {"type": "job", "reference": "vaga de Backend Developer", "reason": "Pode haver múltiplas vagas com este título"}
  ],
  "requires_entity_resolution": true,
  "unresolved_entities": ["job_id"],
  "requires_confirmation": false,
  "note": "Buscar: 1) jobs_search(Backend Developer), 2) applies_search(job_id), 3) candidates_search(candidate_ids)"
}
```

Pergunta: "Candidatos inscritos na vaga 123"
```json
{
  "entities": ["candidates", "applies"],
  "main_action": "list",
  "filters": {
    "applies.job_id": 123
  },
  "fields_needed": ["candidates.id", "candidates.name", "candidates.email"],
  "ambiguous_references": [],
  "requires_entity_resolution": false,
  "unresolved_entities": [],
  "requires_confirmation": false,
  "note": "ID explícito, buscar: 1) applies_search(job_id=123), 2) candidates by IDs"
}
```

Pergunta: "Inscreva todos os candidatos de SP na vaga mais recente"
```json
{
  "entities": ["candidates", "jobs", "applies"],
  "main_action": "create_applies",
  "filters": {
    "candidates.city": {"ilike": "%são paulo%"}
  },
  "ambiguous_references": [],
  "requires_entity_resolution": true,
  "unresolved_entities": ["job_id"],
  "requires_confirmation": true,
  "confirmation_reason": "Operação em massa - quantidade de candidatos afetados desconhecida",
  "affected_count_unknown": true
}
```

Pergunta: "Procure candidatos com javascript e coloque na vaga fullstack do instato inscrito"
```json
{
  "entities": ["candidates", "jobs", "selective_processes", "applies"],
  "main_action": "create_applies",
  "filters": {
    "candidates.skills": {"ilike": "%javascript%"},
    "jobs.title": {"ilike": "%fullstack%"},
    "jobs.company": {"ilike": "%instato%"},
    "selective_processes.status_name": {"ilike": "%inscrito%"}
  },
  "aggregations": [],
  "fields_needed": ["candidates.id", "jobs.id", "selective_processes.id"],
  "ambiguous_references": [
    {"type": "job", "reference": "vaga fullstack do instato", "reason": "Pode haver múltiplas vagas"},
    {"type": "process", "reference": "inscrito", "reason": "Pode haver múltiplas etapas"}
  ],
  "requires_entity_resolution": true,
  "unresolved_entities": ["job_id", "selective_process_id"],
  "requires_confirmation": true,
  "confirmation_reason": "Operação de criação em massa com entidades ambíguas",
  "affected_count_unknown": true
}
```

Pergunta: "Qual a média de expectativa salarial dos candidatos que se aplicaram para vaga X?"
```json
{
  "entities": ["applies", "candidates"],
  "main_action": "aggregate",
  "filters": {"applies.job_id": "X"},
  "aggregations": [{"function": "avg", "field": "candidates.clt_expectation"}],
  "fields_needed": ["candidates.clt_expectation"],
  "ambiguous_references": [],
  "requires_entity_resolution": false,
  "unresolved_entities": [],
  "requires_confirmation": false
}
```

**DETECÇÃO DE PAGINAÇÃO:**

Pergunta: "Próxima página" ou "Página 2" ou "Mais candidatos" ou "Ver mais"
```json
{
  "entities": ["_context_"],
  "main_action": "pagination",
  "pagination_action": "next",
  "note": "Usuário quer ver próxima página do resultado anterior. Usar contexto da query anterior."
}
```

Pergunta: "Página anterior" ou "Voltar" (após paginação)
```json
{
  "entities": ["_context_"],
  "main_action": "pagination",
  "pagination_action": "previous",
  "note": "Usuário quer voltar para página anterior."
}
```

Pergunta: "Mostre a página 5"
```json
{
  "entities": ["_context_"],
  "main_action": "pagination",
  "pagination_action": "goto",
  "page_number": 5,
  "note": "Usuário quer ir para página específica."
}
```

**REFERÊNCIAS AO CONTEXTO ANTERIOR:**

Pergunta: "e do itau vc consegui encontrar?" (após buscar "candidatos da Google ou Microsoft")
```json
{
  "entities": ["candidates", "experiences"],
  "main_action": "list",
  "filters": {
    "experiences.company": {"ilike": "%itau%"}
  },
  "note": "Mantém mesma ação e entidades da query anterior (candidatos com experiências), apenas atualiza filtro para 'itau'"
}
```

Pergunta: "e da google?" (após buscar "candidatos desenvolvedores")
```json
{
  "entities": ["candidates", "experiences"],
  "main_action": "list",
  "filters": {
    "role_name": {"ilike": "%desenvolvedor%"},
    "experiences.company": {"ilike": "%google%"}
  },
  "note": "Mantém filtro anterior (desenvolvedor) e adiciona filtro de empresa (google)"
}
```

**IMPORTANTE:**
- Se `requires_entity_resolution = true`, o planner DEVE criar steps de resolução PRIMEIRO
- Se `requires_confirmation = true`, o executor DEVE pausar e pedir confirmação
- Se `affected_count_unknown = true`, SEMPRE perguntar antes de executar
- Para ações create_applies SEMPRE set requires_confirmation = true

**CONTEXTO DE CONVERSA:**
Se houver contexto da query anterior no prompt:
- Se a pergunta atual faz referência ao contexto (ex: "e do itau?", "e da google?"), MANTENHA:
  * A mesma `main_action` da query anterior
  * As mesmas `entities` da query anterior
  * Apenas atualize os `filters` com a nova informação mencionada
- Exemplo: Query anterior buscava "candidatos da Google" → entities: ["candidates", "experiences"]
  Se pergunta atual é "e do itau?", mantenha entities e atualize filtro para "itau"
- NÃO mude de entidade (ex: de candidates para jobs) a menos que explicitamente solicitado

Retorne APENAS o JSON da intenção, sem texto adicional."""

    def __init__(self):
        """Initialize the Intent Analyzer Agent with LLM and RAG."""
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini.model,
            temperature=settings.gemini.temperature,
            google_api_key=settings.gemini.api_key
        )
        try:
            self.rag_service = RAGService()
            logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.warning(
                f"RAG service initialization failed: {e}. Will work without RAG.")
            self.rag_service = None

    def analyze(self, state: QueryState) -> QueryState:
        """
        Analyze user question and extract intent.

        Args:
            state: Current query state.

        Returns:
            Updated state with intent information.
        """
        # Extract question and check for pagination context
        question = state["question"]
        messages = state.get("messages", [])

        # Check if there's context from previous query
        has_context = False
        context_info = ""
        if messages and "[CONTEXTO DA QUERY ANTERIOR]" in str(messages[0].content):
            has_context = True
            message_content = str(messages[0].content)

            # Extrair informações do contexto
            context_lines = message_content.split("[CONTEXTO DA QUERY ANTERIOR]")[
                1] if "[CONTEXTO DA QUERY ANTERIOR]" in message_content else ""

            # Detectar se é paginação ou referência contextual
            pagination_keywords = ["próxima",
                                   "anterior", "página", "mais", "ver mais"]
            is_pagination = any(kw in question.lower()
                                for kw in pagination_keywords)

            # Detectar referências contextuais (ex: "e do itau?", "e da google?")
            contextual_refs = ["e do", "e da", "e de", "e no",
                               "e na", "consegui encontrar", "encontrou"]
            has_contextual_ref = any(ref in question.lower()
                                     for ref in contextual_refs)

            if is_pagination:
                context_info = "\n\n⚠️ IMPORTANTE: Esta é uma query de PAGINAÇÃO!\nO usuário quer navegar nos resultados da query anterior.\nUse as informações do contexto para criar o plano correto.\n"
            elif has_contextual_ref:
                context_info = "\n\n⚠️ IMPORTANTE: Esta pergunta faz REFERÊNCIA à query anterior!\n"
                context_info += "Mantenha a mesma ação (main_action) e entidades (entities) da query anterior.\n"
                context_info += "Apenas atualize os filtros com a nova informação mencionada (ex: 'itau', 'google').\n"
                context_info += "Exemplo: Se anterior era 'candidatos da Google', e agora pergunta 'e do itau?',\n"
                context_info += "mantenha entities=['candidates', 'experiences'] e atualize filtros para 'itau'.\n"
            else:
                context_info = "\n\n⚠️ IMPORTANTE: Há contexto da query anterior disponível.\n"
                context_info += "Use as informações do contexto para entender melhor a intenção do usuário.\n"
                context_info += "Se a pergunta atual complementa ou modifica a anterior, mantenha o contexto relevante.\n"

        print("\n" + "="*80)
        print("🧠 INTENT ANALYZER")
        print("="*80)
        logger.info(f"Analyzing intent for question: {question}")
        print(f"📝 Question: {question}")

        if has_context:
            print(
                "🔄 Context from previous query detected - will use context to understand intent")

        # Retrieve relevant API documentation using RAG
        # Se houver contexto, usar query enriquecida com contexto
        docs_context = ""
        if self.rag_service:
            print("\n🔍 Retrieving relevant API documentation...")
            try:
                # Se houver contexto, enriquecer query para RAG
                rag_query = question
                if has_context and messages:
                    message_content = str(messages[0].content)
                    # Extrair query anterior do contexto para melhorar busca RAG
                    if "Query anterior:" in message_content:
                        lines = message_content.split("\n")
                        for line in lines:
                            if "Query anterior:" in line:
                                prev_query = line.split(
                                    "Query anterior:")[1].strip()
                                # Combinar query atual com anterior para melhor contexto
                                rag_query = f"{question} (contexto: {prev_query})"
                                break

                relevant_docs = self.rag_service.retrieve(
                    query=rag_query,
                    top_k=10,  # Mais docs para o analyzer ter contexto
                    use_hybrid=True
                )

                docs_context = self.rag_service.format_for_llm(relevant_docs)
                logger.info(
                    f"Retrieved {len(relevant_docs)} relevant API docs")
                print(f"✅ Retrieved {len(relevant_docs)} relevant APIs:")
                for i, doc in enumerate(relevant_docs[:5], 1):
                    print(
                        f"   {i}. {doc['api_id']} - {doc['summary'][:60]}...")
            except Exception as e:
                logger.warning(f"Failed to retrieve docs: {e}")
                print(f"⚠️  Failed to retrieve docs: {e}")
                docs_context = ""

        try:
            # Prepare enhanced prompt with API documentation
            enhanced_prompt = f"""{self.SYSTEM_PROMPT}

## Documentações de APIs Disponíveis

{docs_context}

{context_info}

Analise a pergunta considerando as APIs disponíveis acima.
Use as APIs documentadas para identificar quais endpoints podem ser utilizados."""

            print("\n💭 Thinking... (analyzing intent)")

            # Prepare messages for LLM - usar a mensagem com contexto se disponível
            query_content = messages[0].content if messages else question
            messages_for_llm = [
                HumanMessage(
                    content=f"{enhanced_prompt}\n\nPergunta: {query_content}")
            ]

            # Get response from LLM
            response = self.llm.invoke(messages_for_llm)

            # Parse JSON response
            content = response.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            # Parse intent
            intent = json.loads(content)

            print("\n✅ Intent identified:")
            print(f"   • Action: {intent.get('main_action', 'N/A')}")
            print(f"   • Entities: {', '.join(intent.get('entities', []))}")
            if intent.get('filters'):
                print(f"   • Filters: {intent.get('filters')}")
            if intent.get('aggregations'):
                print(f"   • Aggregations: {intent.get('aggregations')}")

            # Update state
            state["intent"] = intent
            state["messages"].append(
                AIMessage(
                    content=f"✓ Intenção identificada: {intent['main_action']} em {', '.join(intent['entities'])}")
            )

            logger.info(
                f"Intent analyzed successfully: {intent['main_action']}")

        except json.JSONDecodeError as e:
            error_msg = f"Erro ao parsear intenção: {e}"
            logger.error(error_msg)
            state["error"] = error_msg
            state["intent"] = {}

        except Exception as e:
            error_msg = f"Erro ao analisar intenção: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            state["intent"] = {}

        return state

    def __call__(self, state: QueryState) -> QueryState:
        """Make agent callable."""
        return self.analyze(state)

```

---

## 📄 src/agents/api_planner.py

```python
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from ..models.state import QueryState
from ..config.settings import get_settings
from ..services.rag_service import RAGService


logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    step: int
    api: str
    params: Dict[str, Any]
    save_as: str
    description: str
    execute_if: Optional[str] = None
    fallback_step: Optional[int] = None
    requires_confirmation: bool = False
    confirmation_type: Optional[str] = None


class PlanPromptBuilder:

    BASE_INSTRUCTIONS = """Você é o API Planner. Crie um plano de execução usando APENAS as APIs fornecidas.

**Responsabilidades:**
1. Quebrar perguntas complexas em subproblemas
2. Identificar API adequada para cada subproblema
3. Criar plano sequencial com dependências
4. Adicionar estratégias de fallback

**Estrutura do Step (TODOS OS CAMPOS SÃO OBRIGATÓRIOS):**
- step: número sequencial (OBRIGATÓRIO)
- api: nome da API (OBRIGATÓRIO)
- params: parâmetros (OBRIGATÓRIO, objeto vazio {} se não houver params)
- save_as: nome para salvar resultado (OBRIGATÓRIO - ex: "candidates_data", "job_info")
- description: explicação clara (OBRIGATÓRIO)
- execute_if (opcional): condição para executar
- fallback_step (opcional): step alternativo
- requires_confirmation (opcional): se precisa confirmação
- confirmation_type (opcional): tipo de confirmação

**Referências Entre Steps:**
- $step_name[0].id - primeiro elemento
- $step_name.ids - array de ids
- $step_name.count - quantidade

**REGRA CRÍTICA - Estrutura de Parâmetros:**
Para APIs _show (que recebem ID):
- CORRETO: "params": {"id": 123}
- ERRADO: "params": {"where": {"id": 123}}

Para APIs _search (que fazem busca):
- Use "where" para filtros: "params": {"where": {"city": "..."}}"

**REGRA CRÍTICA - Normalização de Texto:**
SEMPRE use o campo correto para cada filtro:
- Habilidades/Skills → use "role_name" (nome do cargo), NÃO "skills"
- Status de Vagas → use "status" diretamente, sem ilike (valores: active, cancelled, finished, closed)
- Exemplos:
  * "JavaScript" → {"role_name": {"ilike": "%javascript%"}}
  * "Vagas ativas" → {"status": "active"}

SEMPRE converta valores de texto para LOWERCASE com ilike:
- "SÃO PAULO" → {"city": {"ilike": "%são paulo%"}}
- "JavaScript" → {"role_name": {"ilike": "%javascript%"}}
- "Google" → {"company_name": {"ilike": "%google%"}}

**REGRA CRÍTICA - Operador OR (_or):**
Para múltiplas condições OR no mesmo campo, use "_or" no nível superior do "where":
- ❌ ERRADO: {"company": {"or": [{"like": "%google%"}, {"like": "%microsoft%"}]}}
- ✅ CORRETO: {"_or": [{"company": {"like": "%google%"}}, {"company": {"like": "%microsoft%"}}]}
- Exemplo: "Google OU Microsoft" → {"_or": [{"company": {"like": "%google%"}}, {"company": {"like": "%microsoft%"}}]}

**Diretrizes de Compact:**
SEMPRE use os campos completos padrão a menos que o usuário EXPLICITAMENTE peça campos específicos:
- candidates_search: "id,name,email,role_name,phone,city"
- jobs_search: "id,title,company_name,city,is_remote,status"
- selective_processes_search: "id,job_id,name,status"
- applies_search: "id,candidate_name,job_title,status"

Se usuário pedir APENAS campos específicos (ex: "apenas nome e email"):
- Inclua "id" + campos solicitados
- Exemplo: "apenas nome e email" → "id,name,email"
- Exemplo: "só o título" → "id,title"

**Regras:**
- Limite padrão: 50-100 registros
- Se step usa $ref, adicione execute_if para prevenir erros
- Para create_applies: busque selective_processes ANTES
- Use requires_confirmation=True APENAS quando:
  * Há ambiguidade real (múltiplas entidades possíveis que precisam escolha do usuário)
  * Operações destrutivas (delete, bulk operations)
  * Operações em massa com quantidade desconhecida
  * O intent indica requires_confirmation=true
- NÃO use requires_confirmation para listagens simples sem ambiguidade
- NÃO use APIs que não estejam na lista fornecida (ex: jobs_status_search não existe)

Retorne APENAS array JSON, sem texto adicional."""

    @staticmethod
    def build_example_plan() -> str:
        return """
Exemplo de plano válido:
```json
[
  {
    "step": 1,
    "api": "candidates_search",
    "params": {
      "where": {"role_name": {"ilike": "%developer%"}},
      "compact": "id,name,email,role_name,phone,city",
      "limit": 50
    },
    "save_as": "candidates_data",
    "description": "Buscar candidatos developers",
    "requires_confirmation": true,
    "confirmation_type": "entity_selection"
  },
  {
    "step": 2,
    "api": "experiences_search",
    "params": {
      "where": {"_or": [{"company": {"ilike": "%google%"}}, {"company": {"ilike": "%microsoft%"}}]},
      "limit": 50
    },
    "save_as": "experiences_data",
    "description": "Buscar experiências na Google OU Microsoft"
  }
]
```"""

    @staticmethod
    def build_pagination_context(last_query: str, current_page: int, total_pages: int) -> str:
        return f"""
⚠️ PAGINAÇÃO DETECTADA:
Query anterior: "{last_query}"
Página: {current_page}/{total_pages}

Crie o MESMO plano, mas atualize o parâmetro 'page'.
Mantenha todos os filtros iguais."""

    @classmethod
    def build_full_prompt(
        cls,
        docs_context: str,
        intent: Dict[str, Any],
        question: str,
        pagination_context: Optional[str] = None
    ) -> str:
        parts = [
            cls.BASE_INSTRUCTIONS,
            cls.build_example_plan(),
            "\n## APIs Disponíveis\n",
            docs_context,
            "\nUse APENAS as APIs listadas acima."
        ]

        if pagination_context:
            parts.append(pagination_context)

        parts.extend([
            f"\n\n## Intent\n{json.dumps(intent, indent=2, ensure_ascii=False)}",
            f"\n## Query\n{question}",
            "\nCrie o plano de APIs."
        ])

        return "\n".join(parts)


class PlanValidator:

    @staticmethod
    def validate_plan_structure(plan: Any) -> Tuple[bool, Optional[str]]:
        if not isinstance(plan, list):
            return False, "Plan must be a list of steps"

        if not plan:
            return False, "Plan cannot be empty"

        for i, step in enumerate(plan, 1):
            if not isinstance(step, dict):
                return False, f"Step {i} must be a dictionary"

            required_fields = ["step", "api",
                               "params", "save_as", "description"]
            missing = [f for f in required_fields if f not in step]

            if missing:
                if "save_as" in missing and "api" in step:
                    api_name = step["api"].replace("/", "_").replace("-", "_")
                    step["save_as"] = f"{api_name}_data"
                    missing.remove("save_as")
                    logger.warning(
                        f"Auto-fixed missing save_as in step {i}: {step['save_as']}")

                if "params" in missing:
                    step["params"] = {}
                    missing.remove("params")
                    logger.warning(f"Auto-fixed missing params in step {i}")

                if "description" in missing and "api" in step:
                    step["description"] = f"Executar {step['api']}"
                    missing.remove("description")
                    logger.warning(
                        f"Auto-fixed missing description in step {i}")

                if missing:
                    return False, f"Step {i} missing fields: {missing}"

        return True, None

    @staticmethod
    def validate_api_references(plan: List[Dict], available_apis: List[str]) -> Tuple[bool, Optional[str]]:
        FORBIDDEN_PATTERNS = [
            r'/admin/',
            r'\.\./',
            r'/etc/',
            r'delete_all',
            r'DROP\s+TABLE',
            r'TRUNCATE',
            r'eval\(',
            r'exec\('
        ]

        for step in plan:
            api_name = step.get("api", "")

            for pattern in FORBIDDEN_PATTERNS:
                import re
                if re.search(pattern, api_name, re.IGNORECASE):
                    return False, f"Forbidden API pattern detected: {api_name}"

            if api_name not in available_apis and not api_name.startswith("$"):
                return False, f"Unknown API: {api_name}"

        return True, None


class PlanVisualizer:

    @staticmethod
    def print_plan_header(step_count: int, explanation: str):
        print(f"\n✅ Execution plan created with {step_count} steps:")
        print(f"\n📝 Strategy: {explanation}\n")
        print("=" * 80)
        print("📋 DETAILED EXECUTION PLAN")
        print("=" * 80)

    @staticmethod
    def print_step_details(step: Dict[str, Any], index: int):
        api_name = step.get('api', 'unknown')
        description = step.get('description', 'No description')
        params = step.get('params', {})
        save_as = step.get('save_as', 'N/A')

        print(f"\n┌─ STEP {index}: {api_name}")
        print(f"│  📝 Description: {description}")
        print(f"│  💾 Save as: {save_as}")

        if params:
            PlanVisualizer._print_parameters(params)

        PlanVisualizer._print_conditions(step)

        print(f"└{'─' * 78}")

    @staticmethod
    def _print_parameters(params: Dict[str, Any]):
        print(f"│  🔧 Parameters:")
        for key, value in params.items():
            if key == 'where' and isinstance(value, dict):
                print(f"│     • where:")
                for wk, wv in value.items():
                    if isinstance(wv, dict):
                        op = list(wv.keys())[0]
                        val = wv[op]
                        print(f"│       - {wk}: {{{op}: {val}}}")
                    else:
                        print(f"│       - {wk}: {wv}")
            elif isinstance(value, dict):
                print(
                    f"│     • {key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                print(f"│     • {key}: {value}")

    @staticmethod
    def _print_conditions(step: Dict[str, Any]):
        if step.get('execute_if'):
            print(f"│  ⚠️  Execute if: {step.get('execute_if')}")

        if step.get('fallback_step'):
            print(f"│  🔄 Fallback: Step {step.get('fallback_step')}")

        if step.get('requires_confirmation'):
            conf_type = step.get('confirmation_type', 'unknown')
            print(f"│  ✋ Requires confirmation: {conf_type}")


class APIPlannerAgent:

    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini.model,
            temperature=settings.gemini.temperature,
            google_api_key=settings.gemini.api_key
        )
        self.rag_service = self._initialize_rag()
        self.prompt_builder = PlanPromptBuilder()
        self.validator = PlanValidator()
        self.visualizer = PlanVisualizer()

    def _initialize_rag(self) -> Optional[RAGService]:
        try:
            rag = RAGService()
            logger.info("RAG service initialized successfully")
            return rag
        except Exception as e:
            logger.warning(f"RAG service initialization failed: {e}")
            return None

    def plan(self, state: QueryState) -> QueryState:
        intent = state.get("intent", {})

        if not self._should_plan(state, intent):
            return state

        self._print_header()

        docs_context = self._retrieve_relevant_apis(state, intent)
        pagination_context = self._extract_pagination_context(state)

        try:
            plan = self._generate_plan(
                state, intent, docs_context, pagination_context)

            if not plan:
                return self._handle_empty_plan(state)

            explanation = self._generate_explanation(plan, intent)

            self._visualize_plan(plan, explanation)

            return self._update_state(state, plan, explanation)

        except Exception as e:
            return self._handle_error(state, e)

    def _should_plan(self, state: QueryState, intent: Dict[str, Any]) -> bool:
        if state.get("error"):
            logger.warning("Skipping planning: error in state")
            return False

        if not intent:
            logger.warning("Skipping planning: no intent")
            return False

        return True

    def _print_header(self):
        print("\n" + "=" * 80)
        print("📋 API PLANNER")
        print("=" * 80)
        logger.info("Creating API execution plan")

    def _retrieve_relevant_apis(self, state: QueryState, intent: Dict[str, Any]) -> str:
        if not self.rag_service:
            return "Documentação indisponível."

        entities = intent.get("entities", [])
        print(f"\n🔍 Searching APIs for entities: {', '.join(entities)}")

        try:
            # Enriquecer query com contexto se disponível
            query = state["question"]
            messages = state.get("messages", [])
            if messages and "[CONTEXTO DA QUERY ANTERIOR]" in str(messages[0].content):
                # Extrair query anterior para melhorar busca RAG
                message_content = str(messages[0].content)
                if "Query anterior:" in message_content:
                    lines = message_content.split("\n")
                    for line in lines:
                        if "Query anterior:" in line:
                            prev_query = line.split(
                                "Query anterior:")[1].strip()
                            query = f"{query} (contexto: {prev_query})"
                            break

            relevant_docs = self.rag_service.retrieve(
                query=query,
                entities=entities,
                top_k=10,
                use_hybrid=True
            )

            self._print_found_apis(relevant_docs)

            return self.rag_service.format_for_llm(relevant_docs)

        except Exception as e:
            logger.warning(f"Failed to retrieve docs: {e}")
            print(f"⚠️  Failed to retrieve docs: {e}")
            return "Documentação indisponível."

    def _print_found_apis(self, docs: List[Dict]):
        logger.info(f"Retrieved {len(docs)} API docs")
        print(f"✅ Found {len(docs)} relevant APIs:")
        for i, doc in enumerate(docs, 1):
            print(f"   {i}. {doc['api_id']} ({doc['method']} {doc['path']})")

    def _extract_pagination_context(self, state: QueryState) -> Optional[str]:
        messages = state.get("messages", [])

        if not messages:
            return None

        first_message = str(messages[0].content)

        if "[CONTEXTO DA QUERY ANTERIOR]" not in first_message:
            return None

        last_query = state.get("last_query", "")
        current_page = state.get("current_page", 1)
        total_pages = state.get("total_pages", 1)

        return self.prompt_builder.build_pagination_context(
            last_query, current_page, total_pages
        )

    def _generate_plan(
        self,
        state: QueryState,
        intent: Dict[str, Any],
        docs_context: str,
        pagination_context: Optional[str]
    ) -> List[Dict[str, Any]]:

        prompt = self.prompt_builder.build_full_prompt(
            docs_context, intent, state["question"], pagination_context
        )

        print("\n💭 Thinking... (decomposing query and creating execution plan)")

        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages)

        plan_json = self._extract_json_from_response(response.content)
        plan = json.loads(plan_json)

        plan = self._fix_or_operator(plan)
        plan = self._normalize_text_values(plan)

        is_valid, error_msg = self.validator.validate_plan_structure(plan)
        if not is_valid:
            raise ValueError(error_msg)

        return plan

    def _extract_json_from_response(self, content: str) -> str:
        content = content.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        return content

    def _fix_or_operator(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Corrige operador 'or' incorreto dentro de campos para '_or' no nível superior.
        Converte: {"company": {"or": [...]}} → {"_or": [{"company": {...}}, ...]}
        """
        import copy
        fixed_plan = copy.deepcopy(plan)

        for step in fixed_plan:
            params = step.get("params", {})
            where = params.get("where", {})

            if not isinstance(where, dict):
                continue

            or_conditions = []
            fields_to_remove = []

            for field, condition in where.items():
                if isinstance(condition, dict) and "or" in condition:
                    or_array = condition.get("or", [])
                    if isinstance(or_array, list):
                        for cond in or_array:
                            if isinstance(cond, dict):
                                or_conditions.append({field: cond})
                        fields_to_remove.append(field)

            for field in fields_to_remove:
                where.pop(field, None)

            if or_conditions:
                if "_or" in where:
                    existing_or = where["_or"] if isinstance(
                        where["_or"], list) else []
                    where["_or"] = existing_or + or_conditions
                else:
                    where["_or"] = or_conditions

        return fixed_plan

    def _normalize_text_values(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converte valores de texto em filtros 'where' para lowercase.
        Aplica apenas em operadores ilike para garantir case-insensitive search.
        """
        import copy
        normalized_plan = copy.deepcopy(plan)

        for step in normalized_plan:
            params = step.get("params", {})
            where = params.get("where", {})

            if not isinstance(where, dict):
                continue

            self._normalize_where_values(where)

        return normalized_plan

    def _normalize_where_values(self, where: Dict[str, Any]) -> None:
        """Normaliza valores recursivamente em estruturas 'where'."""
        for key, value in where.items():
            if key == "_or" and isinstance(value, list):
                for condition in value:
                    if isinstance(condition, dict):
                        self._normalize_where_values(condition)

            elif isinstance(value, dict):
                for operator, val in value.items():
                    if operator == "ilike" and isinstance(val, str):
                        value[operator] = val.lower()
                    elif operator == "in" and isinstance(val, list):
                        value[operator] = [v.lower() if isinstance(v, str)
                                           else v for v in val]

            elif isinstance(value, str):
                where[key] = value.lower()

    def _generate_explanation(self, plan: List[Dict], intent: Dict[str, Any]) -> str:
        main_action = intent.get("main_action", "unknown")

        explanations = {
            "create_applies": self._explain_create_applies,
            "filter": lambda p: f"Vou buscar e filtrar dados. Total de {len(p)} consultas.",
            "count": lambda p: f"Vou contar registros. Total de {len(p)} consultas.",
            "aggregate": lambda p: f"Vou buscar dados e calcular métricas. Total de {len(p)} consultas."
        }

        explanation = explanations.get(
            main_action,
            lambda p: f"Vou executar {len(p)} consultas para responder sua pergunta."
        )(plan)

        fallback_count = sum(
            1 for step in plan
            if step.get('execute_if') or step.get('fallback_step')
        )

        if fallback_count > 0:
            explanation += f" (incluindo {fallback_count} estratégias alternativas)"

        return explanation

    def _explain_create_applies(self, plan: List[Dict]) -> str:
        explanation = "Vou inscrever candidatos em uma vaga. Etapas: "
        steps_desc = []

        api_descriptions = {
            "candidates_search": "1) Buscar candidatos",
            "jobs_search": "2) Localizar vaga",
            "selective_processes": "3) Encontrar processo seletivo",
            "applies_create": "4) Criar inscrições"
        }

        for step in plan:
            api = step.get("api", "")
            for key, desc in api_descriptions.items():
                if key in api:
                    steps_desc.append(desc)
                    break

        return explanation + " → ".join(steps_desc)

    def _visualize_plan(self, plan: List[Dict], explanation: str):
        self.visualizer.print_plan_header(len(plan), explanation)

        for i, step in enumerate(plan, 1):
            self.visualizer.print_step_details(step, i)

        print(f"\n{'=' * 80}\n")

    def _update_state(
        self,
        state: QueryState,
        plan: List[Dict],
        explanation: str
    ) -> QueryState:

        state["api_plan"] = plan
        state["plan_explanation"] = explanation
        state["messages"].append(
            AIMessage(content=f"✓ Plano criado: {len(plan)} chamadas de API")
        )

        logger.info(f"API plan created with {len(plan)} steps")

        return state

    def _handle_empty_plan(self, state: QueryState) -> QueryState:
        state["error"] = "Nenhum plano foi gerado"
        state["api_plan"] = []
        return state

    def _handle_error(self, state: QueryState, error: Exception) -> QueryState:
        error_msg = f"Erro ao criar plano de API: {str(error)}"
        logger.error(error_msg)
        state["error"] = error_msg
        state["api_plan"] = []
        return state

    def __call__(self, state: QueryState) -> QueryState:
        return self.plan(state)

```

---

## 📄 src/agents/plan_validator.py

```python
"""
Plan Validator Agent - Validates execution results and decides if replanning is needed.
"""

import logging
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from ..models.state import QueryState
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class PlanValidatorAgent:
    """
    Valida se os resultados da execução são suficientes para responder a pergunta.
    Se não forem, marca estado para replanning.
    """

    def __init__(self):
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini.model,
            temperature=0.0,
            google_api_key=settings.gemini.api_key
        )

    def __call__(self, state: QueryState) -> QueryState:
        """
        Validate execution results and decide next action.

        Args:
            state: Current query state

        Returns:
            Updated state with validation decision
        """
        logger.info("🔍 Validating execution results...")

        if state.get("error"):
            return state

        attempt_number = state.get("attempt_number", 1)
        max_attempts = state.get("max_attempts", 3)

        validation_result = self._validate_results(state)

        if validation_result["is_valid"]:
            logger.info("✅ Validation passed - results are sufficient")
            state["needs_replanning"] = False
            state["critical_failure"] = False
            return state

        if attempt_number >= max_attempts:
            logger.warning(
                f"❌ Max attempts ({max_attempts}) reached - aborting")
            state["critical_failure"] = True
            state["needs_replanning"] = False
            state["error"] = self._build_failure_message(
                state, validation_result)
            return state

        logger.warning(
            f"⚠️  Validation failed - replanning (attempt {attempt_number + 1}/{max_attempts})")

        current_strategy = {
            "attempt": attempt_number,
            "plan": state.get("api_plan", []),
            "failure_reason": validation_result["reason"]
        }

        failed_strategies = state.get("failed_strategies", [])
        failed_strategies.append(current_strategy)

        execution_feedback = state.get("execution_feedback", [])
        execution_feedback.append(validation_result["feedback"])

        state["needs_replanning"] = True
        state["critical_failure"] = False
        state["failed_strategies"] = failed_strategies
        state["execution_feedback"] = execution_feedback
        state["attempt_number"] = attempt_number + 1

        return state

    def _validate_results(self, state: QueryState) -> Dict[str, Any]:
        """
        Analyze execution results and determine if they're sufficient.

        Returns:
            Dict with is_valid, reason, and feedback
        """
        api_results = state.get("api_results", {})
        api_plan = state.get("api_plan", [])
        question = state.get("question", "")

        if not api_results:
            return {
                "is_valid": False,
                "reason": "no_results",
                "feedback": "Nenhum resultado foi obtido da execução da API"
            }

        critical_steps = self._identify_critical_steps(api_plan)

        for step_name in critical_steps:
            step_result = api_results.get(step_name, {})
            data = step_result.get("data", [])

            if not data or len(data) == 0:
                return {
                    "is_valid": False,
                    "reason": f"empty_critical_step_{step_name}",
                    "feedback": f"Step crítico '{step_name}' retornou 0 resultados"
                }

        total_records = sum(
            len(result.get("data", []))
            for result in api_results.values()
        )

        if total_records == 0:
            return {
                "is_valid": False,
                "reason": "all_steps_empty",
                "feedback": "Todos os steps retornaram 0 resultados"
            }

        validation_prompt = self._build_validation_prompt(state)

        try:
            response = self.llm.invoke(validation_prompt)
            llm_decision = response.content.strip().lower()

            if "valid" in llm_decision or "suficient" in llm_decision or "ok" in llm_decision:
                return {
                    "is_valid": True,
                    "reason": "llm_approved",
                    "feedback": "Resultados validados pela LLM"
                }
            else:
                return {
                    "is_valid": False,
                    "reason": "llm_rejected",
                    "feedback": f"LLM identificou resultados insuficientes: {llm_decision}"
                }
        except Exception as e:
            logger.error(f"Erro na validação LLM: {e}")
            return {
                "is_valid": True,
                "reason": "validation_error_fallback",
                "feedback": "Erro na validação - assumindo resultados válidos"
            }

    def _identify_critical_steps(self, api_plan: list) -> list:
        critical_steps = []

        for step in api_plan:
            api_id = step.get("api_id", "")

            if "_create" in api_id or "_update" in api_id or "_delete" in api_id:
                continue

            if "_search" in api_id or "_show" in api_id:
                step_name = step.get("step_name", "")
                if step_name:
                    critical_steps.append(step_name)

        return critical_steps[:2] if critical_steps else []

    def _build_validation_prompt(self, state: QueryState) -> str:
        """Build prompt for LLM validation."""
        question = state.get("question", "")
        api_results = state.get("api_results", {})

        results_summary = []
        for step_name, result in api_results.items():
            data = result.get("data", [])
            count = len(data)
            results_summary.append(f"- {step_name}: {count} resultados")

        results_text = "\n".join(results_summary)

        return f"""Você é um validador de resultados de API.

Pergunta original: {question}

Resultados obtidos:
{results_text}

Os resultados são SUFICIENTES para responder a pergunta?
Responda apenas: VALID ou INVALID e explique brevemente."""

    def _build_failure_message(self, state: QueryState, validation_result: Dict[str, Any]) -> str:
        """Build user-friendly failure message."""
        question = state.get("question", "")
        max_attempts = state.get("max_attempts", 3)

        return (
            f"Não consegui responder sua pergunta após {max_attempts} tentativas. "
            f"Motivo: {validation_result['feedback']}"
        )

```

---

## 📄 src/agents/api_executor.py

```python
import logging
from typing import Dict, Any, Optional

from langchain_core.messages import AIMessage

from ..models.state import QueryState
from ..models.exceptions import StepDependencyError
from ..services.api_client import ATSAPIClient
from ..config.settings import get_settings
from ..utils.variable_substitutor import VariableSubstitutor
from ..utils.confirmation_builder import ConfirmationBuilder


logger = logging.getLogger(__name__)


class APIExecutorAgent:

    def __init__(self):
        settings = get_settings()
        self.api_client = ATSAPIClient(settings.ats_api)

    def execute(self, state: QueryState) -> QueryState:
        plan = state.get("api_plan", [])

        if state.get("error") or not plan:
            return state

        logger.info(f"🔧 Executing {len(plan)} API calls")

        results = state.get("api_results", {})

        user_confirmation = state.get("user_confirmation")
        if user_confirmation:
            self._inject_confirmation(user_confirmation, results)

        try:
            for i, step in enumerate(plan, 1):
                step_num = step.get("step", 0)
                api_name = step.get("api", "")
                params = step.get("params", {})
                save_as = step.get("save_as", f"step_{step_num}")
                description = step.get("description", "")

                if save_as in results:
                    logger.debug(f"Step {step_num} skipped: already confirmed")
                    continue

                if not self._should_execute(step, results):
                    logger.debug(f"Step {step_num} skipped: condition not met")
                    continue

                if step.get("requires_confirmation") and self._needs_user_input(params):
                    logger.info(
                        f"⚠️  Step requires user input before execution")
                    confirmation = self._build_input_request(
                        step, api_name, params)
                    return self._return_confirmation(state, confirmation, results)

                logger.info(f"[{i}/{len(plan)}] {api_name}")
                if description:
                    logger.info(f"   {description}")

                try:
                    params = VariableSubstitutor.substitute(params, results)
                except StepDependencyError as e:
                    logger.error(f"Dependency error: {e}")
                    return self._return_error(state, str(e), results)

                raw_result = self.api_client.call(api_name, params)
                normalized = self._normalize_response(raw_result, api_name)

                confirmation = self._check_confirmation(
                    normalized, step, api_name, params, state)
                if confirmation:
                    return self._return_confirmation(state, confirmation, results)

                results[save_as] = normalized
                self._log_result(normalized)

            logger.info(f"✅ Completed {len(results)} API calls")
            self._log_summary(results)

            state["api_results"] = results
            state["messages"].append(
                AIMessage(content=f"✓ Executadas {len(results)} chamadas")
            )

        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            state["error"] = str(e)
            state["api_results"] = results

        return state

    def _inject_confirmation(
        self,
        user_confirmation: Dict,
        results: Dict[str, Dict]
    ) -> None:
        save_as = user_confirmation.get("save_as")
        selected_item = user_confirmation.get("selected_item")

        if save_as and selected_item:
            results[save_as] = {
                "data": [selected_item],
                "count": 1,
                "entity_type": save_as.replace("_data", "")
            }
            logger.info(f"✓ Injected confirmation for {save_as}")

    def _should_execute(self, step: Dict, results: Dict) -> bool:
        execute_if = step.get("execute_if")
        if not execute_if:
            return True

        import re
        pattern = r'\$([a-zA-Z_]+)\.([a-zA-Z_]+)\s*(==|!=|>|<|>=|<=)\s*(\d+)'
        match = re.match(pattern, execute_if)

        if not match:
            return True

        var_name, field, operator, value = match.groups()
        value = int(value)

        if var_name not in results:
            return True

        field_value = results[var_name].get(field)
        if field_value is None:
            return True

        ops = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
        }

        return ops[operator](field_value, value)

    def _normalize_response(self, raw: Any, api_name: str) -> Dict[str, Any]:
        entity_type = api_name.replace("_search", "").replace("_show", "").replace(
            "_create", "").replace("_update", "").replace("_delete", "")

        if api_name.endswith("_search"):
            if "data" in raw and "meta" in raw:
                return {
                    "data": raw["data"],
                    "count": raw["meta"].get("total", len(raw["data"])),
                    "entity_type": entity_type,
                    "meta": raw["meta"]
                }

        if api_name.endswith("_show"):
            return {
                "data": [raw],
                "count": 1,
                "entity_type": entity_type
            }

        if api_name.endswith("_create") or api_name.endswith("_update"):
            return {
                "data": [raw],
                "count": 1,
                "entity_type": entity_type,
                "success": True
            }

        if api_name == "applies_create_collection":
            return {
                "data": [raw],
                "count": 1,
                "entity_type": "applies",
                "success": True
            }

        return {"data": [], "count": 0, "entity_type": entity_type}

    def _check_confirmation(
        self,
        result: Dict[str, Any],
        step: Dict,
        api_name: str,
        params: Dict,
        state: QueryState = None
    ) -> Optional[Dict[str, Any]]:

        if not step.get("requires_confirmation"):
            return None

        data = result.get("data", [])
        count = len(data)

        # Auto-continuar se há apenas 1 resultado e está configurado
        if count == 1 and step.get("on_single_result") == "auto_continue":
            return None

        # Auto-continuar para listagens simples sem ambiguidade real
        # Se o intent não indica necessidade de confirmação e é uma listagem simples
        if state:
            intent = state.get("intent", {})
            main_action = intent.get("main_action", "")
            requires_confirmation = intent.get("requires_confirmation", False)
            ambiguous_references = intent.get("ambiguous_references", [])

            # Se é uma listagem simples (list) e não há ambiguidade real, auto-continuar
            if main_action == "list" and not requires_confirmation and not ambiguous_references:
                # Apenas se não for operação destrutiva ou em massa
                if count > 0 and count <= 100:  # Limite razoável para auto-continuar
                    logger.info(
                        f"Auto-continuing: simple list with {count} results, no ambiguity")
                    return None

        if count == 0:
            if step.get("on_zero_results") == "abort":
                return {
                    "type": "abort",
                    "message": "❌ Nenhum resultado encontrado",
                    "step": step.get("step"),
                    "api_name": api_name
                }
            return None

        confirmation_type = step.get("confirmation_type", "entity_selection")
        return ConfirmationBuilder.build(confirmation_type, data, step, api_name, params)

    def _log_result(self, result: Dict[str, Any]) -> None:
        if "data" in result:
            count = len(result["data"])
            total = result.get("count", count)
            if total != count:
                logger.info(f"   ✓ Retrieved {count} records (total: {total})")
            else:
                logger.info(f"   ✓ Retrieved {count} records")

    def _log_summary(self, results: Dict[str, Dict]) -> None:
        total_records = sum(r.get("count", 0)
                            for r in results.values() if isinstance(r, dict))
        logger.info(f"📊 Total: {total_records} records")

        for save_as, result in results.items():
            if isinstance(result, dict) and "count" in result:
                count = result["count"]
                entity = result.get("entity_type", save_as)
                if count > 0:
                    logger.info(f"   • {entity}: {count}")
                else:
                    logger.info(f"   • {entity}: ⚠️  empty")

    def _return_error(
        self,
        state: QueryState,
        error: str,
        results: Dict
    ) -> QueryState:
        return {
            **state,
            "error": error,
            "needs_replanning": True,
            "api_results": results
        }

    def _return_confirmation(
        self,
        state: QueryState,
        confirmation: Dict,
        results: Dict
    ) -> QueryState:
        logger.info(f"⚠️  Confirmation needed: {confirmation.get('type')}")
        return {
            **state,
            "needs_confirmation": True,
            "confirmation_request": confirmation,
            "api_results": results
        }

    def __call__(self, state: QueryState) -> QueryState:
        return self.execute(state)

    def _needs_user_input(self, params: Dict[str, Any]) -> bool:
        return any(
            value == "" or value is None or (
                isinstance(value, str) and value.strip() == "")
            for value in params.values()
        )

    def _build_input_request(self, step: Dict, api_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        missing_fields = [
            key for key, value in params.items()
            if value == "" or value is None or (isinstance(value, str) and value.strip() == "")
        ]

        return {
            "type": "input_required",
            "message": f"📝 Para criar o registro, preciso dos seguintes dados:",
            "fields": missing_fields,
            "step": step.get("step"),
            "api_name": api_name,
            "description": step.get("description", "")
        }

    def __del__(self):
        if hasattr(self, 'api_client'):
            self.api_client.close()

```

---

## 📄 src/agents/data_processor.py

```python
"""
API Executor Agent - Executes API calls according to the plan.
Follows Single Responsibility Principle.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

from langchain_core.messages import AIMessage

from ..models.state import QueryState
from ..models.exceptions import StepDependencyError
from ..services.api_client import ATSAPIClient
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class APIExecutorAgent:
    """
    Agent responsible for executing API calls.
    Handles sequential execution and variable substitution.
    """

    def __init__(self):
        """Initialize the API Executor Agent with API client."""
        settings = get_settings()
        self.api_client = ATSAPIClient(settings.ats_api)

    def execute(self, state: QueryState) -> QueryState:
        """
        Execute API calls according to the plan.
        
        Args:
            state: Current query state with API plan.
            
        Returns:
            Updated state with API results.
        """
        plan = state.get("api_plan", [])

        # Skip if there's an error or empty plan
        if state.get("error") or not plan:
            logger.warning("Skipping API execution due to error or empty plan")
            return state

        print("\n" + "="*80)
        print("🔧 API EXECUTOR")
        print("="*80)
        print(f"\n📡 Executing {len(plan)} API calls...\n")
        logger.info(f"Executing {len(plan)} API calls")

        results = state.get("api_results", {})

        # Check if we have a user confirmation to inject
        user_confirmation = state.get("user_confirmation")
        if user_confirmation:
            save_as = user_confirmation.get("save_as")
            selected_item = user_confirmation.get("selected_item")
            if save_as and selected_item:
                print(f"   ✓ Using confirmed selection for {save_as}")
                results[save_as] = {
                    "data": [selected_item],
                    "count": 1,
                    "total": 1
                }
                logger.info(f"Injected confirmed selection into {save_as}")

        try:
            for i, step in enumerate(plan, 1):
                step_num = step.get("step", 0)
                api_name = step.get("api", "")
                params = step.get("params", {})
                save_as = step.get("save_as", f"step_{step_num}")
                description = step.get("description", "")
                execute_if = step.get("execute_if", None)

                # Skip if we already have this result from confirmation
                if save_as in results:
                    print(
                        f"   [{i}/{len(plan)}] Skipping {api_name} (already confirmed)")
                    logger.debug(f"Step {step_num} skipped: already confirmed")
                    continue

                # Check if this step should be skipped (conditional execution)
                if execute_if and not self._evaluate_condition(execute_if, results):
                    print(
                        f"   [{i}/{len(plan)}] Skipping {api_name} (condition not met: {execute_if})")
                    logger.debug(f"Step {step_num} skipped: {execute_if}")
                    continue

                print(f"   [{i}/{len(plan)}] Calling {api_name}...")
                if description:
                    print(f"      📌 {description}")
                logger.debug(f"Executing step {step_num}: {api_name}")

                try:
                    params = self._substitute_variables(params, results)
                except StepDependencyError as e:
                    logger.error(f"Dependency error in step {step_num}: {e}")
                    self._add_execution_feedback(
                        state,
                        f"Falha na etapa {step_num} ({api_name}): {str(e)}"
                    )
                    return {
                        **state,
                        "error": str(e),
                        "needs_replanning": True,
                        "api_results": results
                    }

                # Execute API call
                raw_result = self._call_api(api_name, params)

                # Normalize API response to standard format
                normalized_result = self._normalize_response(
                    raw_result, api_name)

                # Check if result needs user confirmation
                confirmation = self._check_if_needs_confirmation(
                    api_name, normalized_result, step, params)
                if confirmation:
                    self._print_confirmation_request(confirmation)
                    return {
                        **state,
                        "needs_confirmation": True,
                        "confirmation_request": confirmation,
                        "api_results": results  # Save progress so far
                    }

                # Save normalized result
                results[save_as] = normalized_result

                # Show result summary
                result_count = normalized_result.get('count', 0)
                page_size = normalized_result.get('page_size', 0)

                if isinstance(normalized_result, dict):
                    if 'data' in normalized_result and isinstance(normalized_result['data'], list):
                        # Show both page size and total if different
                        if page_size and page_size != result_count:
                            print(
                                f"      ✓ Retrieved {page_size} records (total: {result_count})")
                        else:
                            print(
                                f"      ✓ Retrieved {len(normalized_result['data'])} records")
                    elif 'data' in normalized_result:
                        print(f"      ✓ Retrieved 1 record")
                    elif 'success' in normalized_result:
                        print(f"      ✓ Success")
                    else:
                        print(f"      ✓ Success")
                else:
                    print(f"      ✓ Success")

                # Check if result is empty and if there's a fallback
                if result_count == 0 and step.get('fallback_step'):
                    fallback_step_num = step.get('fallback_step')
                    print(
                        f"      ⚠️  No results found. Will execute fallback at step {fallback_step_num}")

                logger.debug(f"Step {step_num} completed successfully")

            # Summary of execution
            total_records = sum(r.get('count', 0)
                                for r in results.values() if isinstance(r, dict))
            print(f"\n✅ Completed {len(results)} API calls")
            print(f"📊 Total records retrieved: {total_records}")

            # Show what was found
            for save_as, result in results.items():
                if isinstance(result, dict) and 'count' in result:
                    count = result['count']
                    entity = result.get('entity_type', save_as)
                    if count > 0:
                        print(f"   • {entity}: {count} found")
                    else:
                        print(f"   • {entity}: ⚠️  empty (0 found)")

            # Update state
            state["api_results"] = results
            state["messages"].append(
                AIMessage(
                    content=f"✓ Executadas {len(results)} chamadas com sucesso")
            )

            logger.info("All API calls executed successfully")

        except Exception as e:
            error_msg = f"Erro ao executar chamadas de API: {str(e)}"
            logger.error(error_msg)

            # Show helpful error message
            print(f"\n❌ ERRO NA EXECUÇÃO:")
            print(f"   {str(e)}")
            print(f"\n📊 Progresso até o erro:")
            for save_as, result in results.items():
                if isinstance(result, dict) and 'count' in result:
                    count = result['count']
                    entity = result.get('entity_type', save_as)
                    print(f"   • {entity}: {count} found")

            state["error"] = error_msg
            state["api_results"] = results  # Save partial results

        return state

    def _call_api(self, api_name: str, params: Dict[str, Any]) -> Any:
        """
        Call specific API method with automatic pagination.
        
        Args:
            api_name: Name of the API method to call.
            params: Parameters for the API call.
            
        Returns:
            API response data (aggregated from all pages if paginated).
            
        Raises:
            ValueError: If API name is not recognized.
        """
        # Map API names to client methods
        api_methods = {
            "candidates_search": self.api_client.candidates_search,
            "candidates_show": self.api_client.candidates_show,
            "jobs_search": self.api_client.jobs_search,
            "jobs_show": self.api_client.jobs_show,
            "applies_search": self.api_client.applies_search,
            "applies_show": self.api_client.applies_show,
            "applies_create_collection": self.api_client.applies_create_collection,
            "selective_processes_search": self.api_client.selective_processes_search,
            "selective_processes_show": self.api_client.selective_processes_show,
            "experiences_search": self.api_client.experiences_search,
            "experiences_show": self.api_client.experiences_show,
        }

        if api_name not in api_methods:
            raise ValueError(f"Unknown API: {api_name}")

        method = api_methods[api_name]

        # Handle create_collection methods (POST with specific structure)
        if api_name == "applies_create_collection":
            return method(**params)

        # Handle show methods (require ID as positional argument)
        if api_name.endswith("_show"):
            entity_id = params.pop("id", None)
            if entity_id is None:
                raise ValueError(f"{api_name} requires 'id' parameter")
            return method(entity_id, **params)

        # Handle search methods with automatic pagination
        if api_name.endswith("_search"):
            return self._call_api_with_pagination(method, params, api_name)

        # Fallback for other methods
        return method(**params)

    def _call_api_with_pagination(
        self,
        method: callable,
        params: Dict[str, Any],
        api_name: str,
        max_records: int = 1000
    ) -> Dict[str, Any]:
        """
        Call API method with automatic pagination to fetch up to max_records.
        
        Implementation as described in implementation.txt:
        - Default limit: 100 per page
        - Max total: 1000 records
        - Aggregates results from multiple pages
        
        Args:
            method: API client method to call
            params: Parameters for the API
            api_name: Name of the API (for logging)
            max_records: Maximum records to fetch (default 1000)
            
        Returns:
            Aggregated response with all pages combined
        """
        # Set default limit if not specified
        limit = params.get("limit", 100)
        if limit > 100:
            limit = 100  # API max per page
            params["limit"] = limit

        page = params.get("page", 1)
        params["page"] = page

        # First API call
        logger.debug(f"Fetching {api_name} page {page} (limit: {limit})")
        response = method(**params)

        # Determine entity key
        entity_key = None
        if "candidates" in response:
            entity_key = "candidates"
        elif "jobs" in response:
            entity_key = "jobs"
        elif "applies" in response:
            entity_key = "applies"

        if not entity_key:
            # No pagination needed if no recognized entity
            return response

        all_records = response[entity_key]
        total_fetched = len(all_records)

        # Check if more pages exist
        while len(response.get(entity_key, [])) == limit and total_fetched < max_records:
            page += 1
            params["page"] = page

            logger.debug(
                f"Fetching {api_name} page {page} (total so far: {total_fetched})")

            try:
                next_response = method(**params)
                next_records = next_response.get(entity_key, [])

                if not next_records:
                    break  # No more data

                all_records.extend(next_records)
                total_fetched += len(next_records)

                if total_fetched >= max_records:
                    logger.info(
                        f"Reached max_records limit ({max_records}) for {api_name}")
                    all_records = all_records[:max_records]
                    break

            except Exception as e:
                logger.warning(
                    f"Error fetching page {page} for {api_name}: {e}")
                break  # Stop on error but return what we have

        logger.info(
            f"Fetched {total_fetched} records for {api_name} ({page} pages)")

        # Return response with aggregated records
        response[entity_key] = all_records
        return response

    def _normalize_response(self, raw_response: Any, api_name: str) -> Dict[str, Any]:
        """
        Normalize API response to standard format expected by DataProcessor.
        
        Real API returns: {"candidates": [...]} or {"jobs": [...]} or {"applies": [...]}
        We normalize to: {"data": [...], "entity_type": "candidates"}
        
        Args:
            raw_response: Raw response from API
            api_name: Name of the API method called
            
        Returns:
            Normalized response with "data" key containing list of records
        """
        if not isinstance(raw_response, dict):
            logger.warning(f"Unexpected response type: {type(raw_response)}")
            return {"data": [], "entity_type": "unknown", "raw": raw_response}

        # Determine entity type from API name
        entity_type = api_name.replace("_search", "").replace("_show", "")

        # For search endpoints: extract list from response
        if api_name.endswith("_search"):
            # API returns {"data": [...], "meta": {"total": X}}
            if "data" in raw_response and "meta" in raw_response:
                data_list = raw_response["data"]
                meta = raw_response["meta"]
                # Use meta.total for accurate count (handles pagination)
                total_count = meta.get("total", len(data_list))

                return {
                    "data": data_list,
                    "entity_type": entity_type,
                    "count": total_count,  # Real total from meta
                    "meta": meta,  # Preserve meta for downstream use
                    "page_size": len(data_list)  # Actual records in this page
                }

            # Fallback if API response doesn't have expected format
            logger.warning(
                f"Unexpected response format for {api_name}: {raw_response.keys()}")
            return {
                "data": [],
                "entity_type": entity_type,
                "count": 0
            }

        # For create_collection endpoints: return success info
        elif api_name == "applies_create_collection":
            # API returns success message or created applies
            # Normalize to show what was created
            return {
                "data": [raw_response],
                "entity_type": "applies",
                "count": 1,
                "success": True
            }

        # For show endpoints: wrap single object in list
        elif api_name.endswith("_show"):
            # API returns single object or {"candidate": {...}}
            if "candidate" in raw_response:
                single_obj = raw_response["candidate"]
            elif "job" in raw_response:
                single_obj = raw_response["job"]
            elif "apply" in raw_response:
                single_obj = raw_response["apply"]
            elif "selective_process" in raw_response:
                single_obj = raw_response["selective_process"]
            else:
                # Assume entire response is the object
                single_obj = raw_response

            return {
                "data": [single_obj],
                "entity_type": entity_type,
                "count": 1
            }

        # Unknown endpoint type
        logger.warning(f"Unknown endpoint pattern: {api_name}")
        return {
            "data": [],
            "entity_type": entity_type,
            "raw": raw_response
        }

    def _substitute_variables(
        self,
        params: Dict[str, Any],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Substitute variables like $variable_name.field or $variable_name[0].field in parameters.
        
        Works with normalized data format: {"data": [...], "entity_type": "..."}
        Supports patterns:
        - $remote_jobs.ids -> extract "id" field from all records
        - $applies_data.candidate_ids -> extract "candidate_id" from all records
        - $jobs_data[0].id -> extract "id" field from first record
        - $processes_data[0].id -> extract "id" field from first record
        
        Args:
            params: Parameters dictionary that may contain variables.
            results: Previous results to substitute from (normalized format).
            
        Returns:
            Parameters with variables substituted.
        """
        # Convert to JSON string for easier pattern matching
        params_str = json.dumps(params)

        # Pattern 1: $variable_name[index].field (single element access)
        pattern_indexed = r'\"\$([a-zA-Z_]+)\[(\d+)\]\.([a-zA-Z_]+)\"'
        matches_indexed = re.findall(pattern_indexed, params_str)

        for var_name, index, field in matches_indexed:
            if var_name not in results:
                logger.warning(f"Variable ${var_name} not found in results")
                continue

            result_data = results[var_name]

            # Work with normalized format: {"data": [...], ...}
            if not isinstance(result_data, dict) or "data" not in result_data:
                logger.warning(
                    f"Result ${var_name} is not in normalized format")
                continue

            data_list = result_data["data"]
            idx = int(index)

            if idx >= len(data_list):
                error_msg = (
                    f"Cannot substitute ${var_name}[{idx}].{field}: "
                    f"result has only {len(data_list)} records. "
                    f"Previous step may have returned insufficient data."
                )
                logger.error(f"❌ {error_msg}")
                raise StepDependencyError(error_msg)

            record = data_list[idx]
            value = record.get(field)

            if value is None:
                logger.warning(
                    f"Field '{field}' not found in ${var_name}[{idx}]")
                continue

            # Replace in params string
            search_pattern = f'"${var_name}[{idx}].{field}"'
            replacement = json.dumps(value)
            params_str = params_str.replace(search_pattern, replacement)

        # Pattern 2: $variable_name.field_pattern (all elements)
        pattern = r'\"\$([a-zA-Z_]+)\.([a-zA-Z_]+)"'
        matches = re.findall(pattern, params_str)

        for var_name, field_pattern in matches:
            if var_name not in results:
                logger.warning(f"Variable ${var_name} not found in results")
                continue

            result_data = results[var_name]

            # Work with normalized format: {"data": [...], ...}
            if not isinstance(result_data, dict) or "data" not in result_data:
                logger.warning(
                    f"Result ${var_name} is not in normalized format")
                continue

            data_list = result_data["data"]

            # Handle special field patterns
            if field_pattern == "ids":
                # Extract "id" field from all records
                values = [record.get("id")
                          for record in data_list if "id" in record]
            elif field_pattern.endswith("_ids"):
                # Extract specific ID field (e.g., candidate_ids -> candidate_id)
                id_field = field_pattern[:-1]  # Remove trailing 's'
                values = [record.get(id_field)
                          for record in data_list if id_field in record]
            else:
                # Extract any other field
                values = [record.get(field_pattern)
                          for record in data_list if field_pattern in record]

            # Filter out None values
            values = [v for v in values if v is not None]

            # Replace in params string
            search_pattern = f'"${var_name}.{field_pattern}"'
            replacement = json.dumps(values)
            params_str = params_str.replace(search_pattern, replacement)

            logger.debug(
                f"Substituted ${var_name}.{field_pattern} with {len(values)} values")

        # Convert back to dict
        return json.loads(params_str)

    def _evaluate_condition(self, condition: str, results: Dict[str, Any]) -> bool:
        """
        Evaluate a condition to decide if a step should execute.
        
        Supports conditions like:
        - "$candidates_data.count == 0" - check if result is empty
        - "$jobs_data.count > 0" - check if result has data
        
        Args:
            condition: Condition string to evaluate
            results: Previous results
            
        Returns:
            True if condition is met, False otherwise
        """
        # Parse condition: $variable.field operator value
        pattern = r'\$([a-zA-Z_]+)\.([a-zA-Z_]+)\s*(==|!=|>|<|>=|<=)\s*(\d+)'
        match = re.match(pattern, condition)

        if not match:
            logger.warning(f"Invalid condition format: {condition}")
            return True  # If can't parse, execute the step

        var_name, field, operator, value = match.groups()
        value = int(value)

        if var_name not in results:
            logger.warning(
                f"Variable ${var_name} not found in results for condition")
            return True  # If variable doesn't exist, execute the step

        result_data = results[var_name]

        # Get field value
        if not isinstance(result_data, dict):
            logger.warning(f"Result ${var_name} is not a dict")
            return True

        field_value = result_data.get(field)

        if field_value is None:
            logger.warning(f"Field '{field}' not found in ${var_name}")
            return True

        # Evaluate condition
        try:
            if operator == "==":
                return field_value == value
            elif operator == "!=":
                return field_value != value
            elif operator == ">":
                return field_value > value
            elif operator == "<":
                return field_value < value
            elif operator == ">=":
                return field_value >= value
            elif operator == "<=":
                return field_value <= value
        except Exception as e:
            logger.warning(f"Error evaluating condition {condition}: {e}")
            return True

        return True

    def _check_if_needs_confirmation(
        self,
        api_name: str,
        result: Dict[str, Any],
        step: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if result contains ambiguity that requires user confirmation.
        
        PRIORIDADE:
        1. Respeitar flag explícita do planner (requires_confirmation)
        2. Auto-continue se só 1 resultado e step permite
        3. Abort se zero resultados
        4. Pedir confirmação para múltiplos resultados
        5. Detectar automaticamente (fallback)
        
        Args:
            api_name: Name of the API that was called.
            result: Normalized result from the API call.
            step: The step configuration.
            params: Parameters used in the API call.
            
        Returns:
            Confirmation request dict if needed, None otherwise.
        """
        data = result.get("data", [])
        count = len(data) if isinstance(data, list) else 0

        # 1. RESPEITAR FLAG EXPLÍCITA DO PLANNER
        if step.get("requires_confirmation"):
            confirmation_type = step.get(
                "confirmation_type", "entity_selection")

            # AUTO-CONTINUE: só 1 resultado e step permite
            if count == 1 and step.get("on_single_result") == "auto_continue":
                logger.info(
                    f"✅ Auto-continuing: single result found for {api_name}")
                return None

            # ABORT: zero resultados
            if count == 0:
                on_zero = step.get("on_zero_results", "abort")
                if on_zero == "abort":
                    return {
                        "type": "abort",
                        "message": f"❌ Nenhum resultado encontrado para sua busca.",
                        "step": step.get("step"),
                        "api_name": api_name
                    }

            # CONFIRMAÇÃO: múltiplos resultados ou bulk operation
            if count > 1 and confirmation_type == "entity_selection":
                return self._build_entity_selection_confirmation(
                    data, step, api_name, params
                )

            if confirmation_type == "bulk_operation":
                return self._build_bulk_operation_confirmation(
                    data, step, api_name, params
                )

            if confirmation_type == "destructive_action":
                return self._build_destructive_action_confirmation(
                    data, step, api_name, params
                )

        # 2. DETECÇÃO AUTOMÁTICA (fallback para planos sem flags)
        # Only check search APIs
        search_apis = ["candidates_search", "jobs_search",
                       "selective_processes_search", "applies_search"]
        if api_name not in search_apis:
            return None

        # Get data from normalized result
        if not isinstance(data, list) or len(data) <= 1:
            return None  # 0 or 1 result is fine

        # Check if the query contained specific identifiers that should match exactly one result
        search_term = params.get("search", "")
        where = params.get("where", {})

        # Detect if user specified a specific name/identifier
        has_specific_identifier = False

        if search_term:
            # If search term is short and specific (not a generic skill)
            words = search_term.lower().split()
            # Names are usually 3+ chars, not common tech terms
            specific_terms = [w for w in words if len(w) >= 3 and w not in
                              ['javascript', 'python', 'java', 'react', 'node', 'senior', 'junior',
                              'pleno', 'developer', 'engineer', 'fullstack', 'backend', 'frontend',
                               'desenvolvedor', 'engenheiro']]
            has_specific_identifier = len(specific_terms) > 0

        if where:
            # If where has name/email/title filters with specific values
            for key, value in where.items():
                if key in ["name", "email", "title"]:
                    # Check if it's a specific value (not a pattern)
                    if isinstance(value, dict) and "ilike" in value:
                        search_val = value["ilike"].replace("%", "").strip()
                        if len(search_val) >= 3 and not any(tech in search_val.lower() for tech in
                                                            ['javascript', 'python', 'java', 'fullstack', 'backend', 'frontend']):
                            has_specific_identifier = True
                    elif isinstance(value, str) and len(value) >= 3:
                        has_specific_identifier = True

        if not has_specific_identifier:
            return None  # Generic search, multiple results expected

        # Build automatic confirmation request
        return self._build_entity_selection_confirmation(data, step, api_name, params)

    def _build_entity_selection_confirmation(
        self, data: List[Dict], step: Dict, api_name: str, params: Dict
    ) -> Dict[str, Any]:
        """Build confirmation for entity selection."""
        entity_type = api_name.replace("_search", "")
        entity_label = {
            "candidates": "candidatos",
            "jobs": "vagas",
            "selective_processes": "processos seletivos",
            "applies": "inscrições"
        }.get(entity_type, entity_type)

        # Format options for user (limit to 10)
        items_to_format = data[:10]

        # Format all items intelligently in one LLM call
        formatted_displays = self._format_items_batch(
            items_to_format, entity_type)

        options = []
        for idx, (item, display_name) in enumerate(zip(items_to_format, formatted_displays), 1):
            options.append({
                "index": idx,
                "id": item.get("id", "?"),
                "name": display_name,
                "item": item
            })

        more_text = f" (mostrando {len(options)} de {len(data)})" if len(
            data) > 10 else ""

        message = step.get(
            "confirmation_message", f"Encontrei {len(data)} {entity_label}{more_text}. Qual você quer?")
        message = message.replace("{count}", str(len(data)))

        return {
            "type": "disambiguation",
            "entity_type": entity_label,
            "message": message,
            "options": options,
            "total_count": len(data),
            "step": step.get("step"),
            "save_as": step.get("save_as"),
            "api_name": api_name,
            "original_params": params
        }

    def _build_bulk_operation_confirmation(
        self, data: List[Dict], step: Dict, api_name: str, params: Dict
    ) -> Dict[str, Any]:
        """Build confirmation for bulk operation."""

        # Calcular quantos registros serão afetados
        affected_count = len(params.get("reference_ids", [])) or len(data)

        message = step.get(
            "confirmation_message", f"Esta operação afetará {affected_count} registros. Confirma?")
        message = message.replace("{count}", str(affected_count))

        # Mostrar preview se configurado
        preview_items = []
        if step.get("show_preview"):
            max_preview = step.get("max_preview_items", 5)
            entity_type = api_name.replace(
                "_search", "").replace("_create_collection", "")
            formatted = self._format_items_batch(
                data[:max_preview], entity_type)
            preview_items = formatted

        return {
            "type": "bulk_operation",
            "message": message,
            "affected_count": affected_count,
            "preview": preview_items,
            "step": step.get("step"),
            "save_as": step.get("save_as"),
            "api_name": api_name,
            "require_explicit_yes": step.get("require_explicit_yes", False)
        }

    def _build_destructive_action_confirmation(
        self, data: List[Dict], step: Dict, api_name: str, params: Dict
    ) -> Dict[str, Any]:
        """Build confirmation for destructive action."""

        affected_count = len(data)

        message = step.get("confirmation_message",
                           f"⚠️ ATENÇÃO: Isso vai DELETAR {affected_count} registros. Esta ação é IRREVERSÍVEL. Confirma?")
        message = message.replace("{count}", str(affected_count))

        return {
            "type": "destructive_action",
            "message": message,
            "affected_count": affected_count,
            "step": step.get("step"),
            "save_as": step.get("save_as"),
            "api_name": api_name,
            "require_explicit_yes": True
        }

    def _format_items_batch(self, items: List[Dict[str, Any]], entity_type: str) -> List[str]:
        """
        Formata múltiplos items de uma vez usando LLM (mais eficiente).
        
        Args:
            items: Lista de items para formatar
            entity_type: Tipo da entidade
            
        Returns:
            Lista de strings formatadas
        """
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        from ..config.settings import get_settings

        # Fallback simples
        fallback_displays = []
        for idx, item in enumerate(items, 1):
            item_id = item.get("id", "?")
            simple_name = item.get("name") or item.get(
                "title") or f"Item {idx}"
            fallback_displays.append(f"[ID: {item_id}] {simple_name}")

        try:
            settings = get_settings()
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini.model,
                temperature=0.0,
                google_api_key=settings.gemini.api_key
            )

            # Tradução de tipos
            entity_labels = {
                "candidates": "candidatos",
                "jobs": "vagas",
                "selective_processes": "processos seletivos",
                "applies": "candidaturas"
            }
            entity_label = entity_labels.get(entity_type, entity_type)

            # Prepara lista de items
            items_list = []
            for idx, item in enumerate(items, 1):
                # Remove campos vazios
                clean_item = {k: v for k, v in item.items() if v not in [
                    None, "", [], {}]}
                items_list.append({
                    "index": idx,
                    "data": clean_item
                })

            items_json = json.dumps(items_list, ensure_ascii=False, indent=2)

            prompt = f"""Formate estes {len(items)} {entity_label} para exibição em lista de opções.

**Dados:**
```json
{items_json}
```

**Regras para CADA item:**
1. SEMPRE comece com [ID: <id do item>]
2. Mostre campos mais relevantes primeiro
3. Use • para separar informações
4. Máximo 150 caracteres por linha
5. Sem aspas ou quebras de linha extras
6. Priorize: nome/título, email, telefone, localização, cargo/empresa, status

**Ordem de prioridade por tipo:**
- Candidatos: nome, cargo, email, telefone, cidade
- Vagas: título, empresa, cidade, remoto?, status
- Processos: nome, vaga relacionada, status
- Candidaturas: candidato, vaga, status

**Formato esperado:**
```
1: [ID: 123] Nome • Info1 • Info2 • Info3
2: [ID: 456] Nome • Info1 • Info2
3: [ID: 789] Nome • Info1 • Info2 • Info3
```

Retorne APENAS as linhas formatadas (uma por item), numeradas de 1 a {len(items)}."""

            response = llm.invoke([HumanMessage(content=prompt)])
            formatted_text = response.content.strip()

            # Parse response (espera formato: "1: [ID: ...]\n2: [ID: ...]\n...")
            formatted_lines = []
            for line in formatted_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Remove número inicial se existir (1:, 2:, etc)
                if ':' in line and line.split(':')[0].strip().isdigit():
                    line = ':'.join(line.split(':')[1:]).strip()
                formatted_lines.append(line)

            # Valida que temos o número certo de linhas
            if len(formatted_lines) == len(items):
                # Valida que cada linha tem ID correto
                valid = True
                for i, (item, formatted_line) in enumerate(zip(items, formatted_lines)):
                    expected_id = item.get("id")
                    if expected_id and f"[ID: {expected_id}]" not in formatted_line:
                        valid = False
                        break

                if valid:
                    return formatted_lines

            # Se parsing falhou, usa fallback
            logger.warning("LLM formatting failed validation, using fallback")
            return fallback_displays

        except Exception as e:
            logger.warning(f"Failed to format items with LLM: {e}")
            return fallback_displays

    def _add_execution_feedback(self, state: QueryState, message: str) -> None:
        """
        Add feedback message to execution_feedback list in state.
        
        Args:
            state: Current query state
            message: Feedback message to add
        """
        feedback_list = state.get("execution_feedback", [])
        feedback_list.append(message)
        state["execution_feedback"] = feedback_list

    def _print_confirmation_request(self, confirmation: Dict[str, Any]) -> None:
        """
        Print formatted confirmation request with data table.
        
        Args:
            confirmation: Confirmation request dictionary
        """
        conf_type = confirmation.get("type")

        if conf_type == "disambiguation":
            self._print_disambiguation_table(confirmation)
        elif conf_type == "bulk_operation":
            self._print_bulk_operation_confirmation(confirmation)
        elif conf_type == "destructive_action":
            self._print_destructive_action_confirmation(confirmation)
        elif conf_type == "abort":
            print(f"\n❌ {confirmation.get('message', 'Operação abortada')}\n")
        else:
            print(f"\n⚠️  CONFIRMAÇÃO NECESSÁRIA")
            print(f"   {confirmation.get('message', 'Confirmação requerida')}\n")

    def _print_disambiguation_table(self, confirmation: Dict[str, Any]) -> None:
        """Print formatted disambiguation table with all options."""
        entity_label = confirmation.get("entity_type", "resultados")
        total_count = confirmation.get("total_count", 0)
        options = confirmation.get("options", [])
        message = confirmation.get("message", "")

        shown = len(options)
        more_text = f" (mostrando {shown} de {total_count})" if total_count > shown else ""

        print("\n" + "╔" + "═"*78 + "╗")
        print("║  ⚠️  MÚLTIPLOS RESULTADOS - Qual você quer?" + " "*32 + "║")
        print("╠" + "═"*78 + "╣")
        print(f"║  🔍 Busca: {message[:60]:<60} ║")
        print(
            f"║  📊 Encontrados: {total_count} {entity_label}{more_text:<40} ║"[:79] + "║")
        print("╠" + "═"*78 + "╣")

        if not options:
            print("║  ❌ Nenhuma opção disponível" + " "*47 + "║")
        else:
            for opt in options:
                index = opt.get("index", "?")
                name = opt.get("name", "Sem nome")

                if len(name) > 68:
                    name = name[:65] + "..."

                line = f"║  {index:>2}. {name:<68} ║"
                print(line)

        print("╠" + "═"*78 + "╣")
        print("║  💡 Responda com:                                                      ║")
        print("║     • Número: \"1\", \"2\", \"3\"...                                         ║")
        if options:
            first_id = options[0].get("id", "")
            print(f"║     • ID: \"{first_id}\"" +
                  " "*(69-len(str(first_id))) + "║")
        print(
            "║     • \"cancelar\" para desistir                                         ║")
        print("╚" + "═"*78 + "╝\n")

    def _print_bulk_operation_confirmation(self, confirmation: Dict[str, Any]) -> None:
        """Print bulk operation confirmation request."""
        message = confirmation.get("message", "Operação em massa")
        affected_count = confirmation.get("affected_count", 0)
        preview = confirmation.get("preview", [])

        print("\n" + "╔" + "═"*78 + "╗")
        print("║  ⚠️  CONFIRMAÇÃO DE OPERAÇÃO EM MASSA" + " "*39 + "║")
        print("╠" + "═"*78 + "╣")
        print(f"║  {message[:74]:<74} ║")
        print(f"║  📊 Registros afetados: {affected_count:<54} ║")

        if preview:
            print("╠" + "═"*78 + "╣")
            print("║  📋 PREVIEW:" + " "*64 + "║")
            for item in preview[:5]:
                item_str = str(item)[:72]
                print(f"║    • {item_str:<70} ║")
            if len(preview) > 5:
                print(f"║    ... e mais {len(preview)-5} itens" + " "*52 + "║")

        print("╠" + "═"*78 + "╣")
        print(
            "║  ❓ Digite \"sim\" para confirmar ou \"cancelar\" para abortar              ║")
        print("╚" + "═"*78 + "╝\n")

    def _print_destructive_action_confirmation(self, confirmation: Dict[str, Any]) -> None:
        """Print destructive action confirmation request."""
        message = confirmation.get("message", "Ação destrutiva")
        affected_count = confirmation.get("affected_count", 0)

        print("\n" + "╔" + "═"*78 + "╗")
        print("║  🚨 ATENÇÃO: AÇÃO DESTRUTIVA E IRREVERSÍVEL" + " "*33 + "║")
        print("╠" + "═"*78 + "╣")
        print(f"║  {message[:74]:<74} ║")
        print(f"║  📊 Registros que serão DELETADOS: {affected_count:<42} ║")
        print("╠" + "═"*78 + "╣")
        print("║  ❗ Esta ação NÃO pode ser desfeita!" + " "*39 + "║")
        print("║  ❓ Digite \"CONFIRMO\" para prosseguir ou \"cancelar\"" + " "*25 + "║")
        print("╚" + "═"*78 + "╝\n")

    def __call__(self, state: QueryState) -> QueryState:
        """Make agent callable."""
        return self.execute(state)

    def __del__(self):
        """Cleanup API client on deletion."""
        if hasattr(self, 'api_client'):
            self.api_client.close()


"""
Data Processor Agent - Processes and aggregates API results.
Follows Single Responsibility Principle.
"""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

from langchain_core.messages import AIMessage

from ..models.state import QueryState


logger = logging.getLogger(__name__)


class DataProcessorAgent:
    """
    Agent responsible for processing API results.
    Performs aggregations, joins, and data transformations in-memory.
    """
    
    def process(self, state: QueryState) -> QueryState:
        """
        Process API results and perform aggregations.
        
        Args:
            state: Current query state with API results.
            
        Returns:
            Updated state with processed data.
        """
        results = state.get("api_results", {})
        intent = state.get("intent", {})
        plan = state.get("api_plan", [])
        
        # Skip if there's an error or no results
        if state.get("error") or not results:
            logger.warning("Skipping data processing due to error or empty results")
            return state
        
        print("\n" + "="*80)
        print("📊 DATA PROCESSOR")
        print("="*80)
        print(f"\n🔄 Processing {len(results)} result sets...")
        logger.info("Processing API results")
        
        try:
            processed = {
                "raw_results": results,
                "aggregations": {},
                "transformations": {}
            }
            
            # Process post_process instructions from plan
            post_process_count = 0
            for step in plan:
                save_as = step.get("save_as", f"step_{step.get('step')}")
                post_process = step.get("post_process")
                
                if post_process and save_as in results:
                    result = results[save_as]
                    processed_result = self._execute_post_process(result, post_process)
                    processed["transformations"][save_as] = processed_result
                    post_process_count += 1
            
            if post_process_count > 0:
                print(f"   ✓ Applied {post_process_count} transformations")
            
            # Execute aggregations from intent
            aggregations = intent.get("aggregations", [])
            if aggregations:
                print(f"   🧮 Computing {len(aggregations)} aggregations...")
                for agg in aggregations:
                    agg_result = self._execute_aggregation(results, agg)
                    agg_name = f"{agg.get('function')}_{agg.get('field', agg.get('entity', 'result'))}"
                    processed["aggregations"][agg_name] = agg_result
                print(f"   ✓ Aggregations completed")
            
            # Calculate summary statistics
            processed["summary"] = self._calculate_summary(results)
            
            state["total_pages"] = processed["summary"].get("total_pages", 1)
            state["page_size"] = processed["summary"].get("page_size", 30)
            
            print(f"\n✅ Processed {processed['summary']['total_records']} total records")
            
            # Update state
            state["processed_data"] = processed
            state["messages"].append(
                AIMessage(content=f"✓ Processados {processed['summary']['total_records']} registros")
            )
            
            logger.info("Data processing completed successfully")
            
        except Exception as e:
            error_msg = f"Erro ao processar dados: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            state["processed_data"] = {}
        
        return state
    
    def _execute_post_process(self, data: Any, instruction: str) -> Any:
        """
        Execute post-processing instruction on data.
        
        Args:
            data: Data to process.
            instruction: Processing instruction (e.g., "calculate_avg:field_name").
            
        Returns:
            Processed data.
        """
        if not instruction:
            return data
        
        parts = instruction.split(":")
        operation = parts[0]
        
        # Extract data array if wrapped in response
        data_list = self._extract_data_list(data)
        
        if operation == "calculate_avg" and len(parts) > 1:
            field = parts[1]
            return self._calculate_average(data_list, field)
        
        elif operation == "count":
            return len(data_list)
        
        elif operation == "extract_ids":
            return self._extract_field(data_list, "id")
        
        elif operation == "group_by" and len(parts) > 1:
            field = parts[1]
            return self._group_by(data_list, field)
        
        elif operation == "sum" and len(parts) > 1:
            field = parts[1]
            return self._calculate_sum(data_list, field)
        
        else:
            logger.warning(f"Unknown post-process operation: {operation}")
            return data
    
    def _execute_aggregation(self, results: Dict[str, Any], agg: Dict[str, Any]) -> Any:
        """
        Execute aggregation from intent.
        
        Args:
            results: All API results.
            agg: Aggregation specification.
            
        Returns:
            Aggregation result.
        """
        function = agg.get("function")
        field = agg.get("field")
        entity = agg.get("entity")
        
        # Find relevant data
        data_list = []
        for key, result in results.items():
            if entity and entity not in key:
                continue
            data_list.extend(self._extract_data_list(result))
        
        if function == "count":
            return len(data_list)
        
        elif function == "avg" and field:
            return self._calculate_average(data_list, field)
        
        elif function == "sum" and field:
            return self._calculate_sum(data_list, field)
        
        elif function == "min" and field:
            return self._calculate_min(data_list, field)
        
        elif function == "max" and field:
            return self._calculate_max(data_list, field)
        
        elif function == "group_by" and field:
            return self._group_by(data_list, field)
        
        else:
            logger.warning(f"Unknown aggregation function: {function}")
            return None
    
    def _extract_data_list(self, data: Any) -> List[Dict[str, Any]]:
        """
        Extract list of records from API response.
        
        Args:
            data: API response data.
            
        Returns:
            List of records.
        """
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "data" in data:
                return data["data"] if isinstance(data["data"], list) else [data["data"]]
            elif "results" in data:
                return data["results"] if isinstance(data["results"], list) else [data["results"]]
        return []
    
    def _extract_field(self, data_list: List[Dict[str, Any]], field: str) -> List[Any]:
        """Extract specific field from all records."""
        return [record.get(field) for record in data_list if field in record]
    
    def _calculate_average(self, data_list: List[Dict[str, Any]], field: str) -> Optional[float]:
        """Calculate average of a numeric field."""
        values = [
            record.get(field)
            for record in data_list
            if field in record and record.get(field) is not None
        ]
        
        if not values:
            return None
        
        # Convert to float and filter out non-numeric
        numeric_values = []
        for val in values:
            try:
                numeric_values.append(float(val))
            except (ValueError, TypeError):
                continue
        
        if not numeric_values:
            return None
        
        return sum(numeric_values) / len(numeric_values)
    
    def _calculate_sum(self, data_list: List[Dict[str, Any]], field: str) -> Optional[float]:
        """Calculate sum of a numeric field."""
        values = [
            record.get(field)
            for record in data_list
            if field in record and record.get(field) is not None
        ]
        
        if not values:
            return None
        
        numeric_values = []
        for val in values:
            try:
                numeric_values.append(float(val))
            except (ValueError, TypeError):
                continue
        
        return sum(numeric_values) if numeric_values else None
    
    def _calculate_min(self, data_list: List[Dict[str, Any]], field: str) -> Optional[float]:
        """Calculate minimum of a numeric field."""
        values = self._extract_field(data_list, field)
        numeric_values = [float(v) for v in values if v is not None]
        return min(numeric_values) if numeric_values else None
    
    def _calculate_max(self, data_list: List[Dict[str, Any]], field: str) -> Optional[float]:
        """Calculate maximum of a numeric field."""
        values = self._extract_field(data_list, field)
        numeric_values = [float(v) for v in values if v is not None]
        return max(numeric_values) if numeric_values else None
    
    def _group_by(self, data_list: List[Dict[str, Any]], field: str) -> Dict[str, int]:
        """Group records by field and count."""
        values = self._extract_field(data_list, field)
        return dict(Counter(values))
    
    def _calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate summary statistics from all results.
        
        Args:
            results: All API results.
            
        Returns:
            Summary statistics dictionary.
        """
        total_records = 0
        total_api_calls = len(results)
        total_count = 0
        page_size = 30
        
        for result in results.values():
            data_list = self._extract_data_list(result)
            total_records += len(data_list)
            
            if isinstance(result, dict):
                total_count = result.get("total", result.get("count", total_records))
                page_size = result.get("page_size", len(data_list) if data_list else 30)
        
        total_pages = max(1, (total_count + page_size - 1) // page_size) if page_size > 0 else 1
        
        return {
            "total_records": total_records,
            "total_count": total_count,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_api_calls": total_api_calls,
            "result_keys": list(results.keys())
        }
    
    def __call__(self, state: QueryState) -> QueryState:
        """Make agent callable."""
        return self.process(state)

```

---

## 📄 src/agents/answer_formatter.py

```python
"""
Answer Formatter Agent - Formats final response in natural language.
Follows Single Responsibility Principle.
"""

import json
import logging
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

from ..models.state import QueryState
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class AnswerFormatterAgent:
    """
    Agent responsible for formatting the final answer.
    Uses Response Format Taxonomy for consistent formatting across 11 types.
    """

    SYSTEM_PROMPT = """Você é o Answer Formatter do Recruiter Agent. Sua função é formatar respostas de forma clara, profissional e consistente usando a taxonomia de 11 tipos de resposta.

═══════════════════════════════════════════════════════════════════════════════
TAXONOMIA DE FORMATOS DE RESPOSTA
═══════════════════════════════════════════════════════════════════════════════

## MATRIZ DE DECISÃO - Use este fluxo para escolher o formato:

1. É AÇÃO (create/update/delete)? 
   → Sucesso? → ACTION_SUCCESS
   → Falhou? → ACTION_FAILED

2. É CONTAGEM ("quantos", "total")? → COUNT

3. É AGREGAÇÃO (média, soma, distribuição)? → AGGREGATION

4. É COMPARAÇÃO ("compare", "vs", "diferença")? → COMPARISON

5. Quantos resultados?
   → 0 resultados → NOT_FOUND
   → 1 resultado → ENTITY_DETAIL
   → 2-15 resultados → ENTITY_LIST
   → Múltiplos quando precisa de 1 → DISAMBIGUATION

6. Precisa confirmação? (bulk/destrutivo) → CONFIRMATION_REQUEST

7. Sistema não consegue fazer? → IMPOSSIBLE

═══════════════════════════════════════════════════════════════════════════════
TEMPLATES POR TIPO
═══════════════════════════════════════════════════════════════════════════════

### 1. ENTITY_LIST - Múltiplos registros

**CRITICAL**: Display ALL records from API response (up to 30 per page).
DO NOT limit to 8-10 rows. Show everything the API returned.

```
📋 **{total} {entidade}(s) encontrado(s)**
{filtros}

| ID | Nome | Atributo1 | Atributo2 |
|----|------|-----------|-----------|
| 123 | João | Dev | SP |
| 456 | Maria | Designer | RJ |

📄 Mostrando {exibidos} de {total}

💡 "Mostre detalhes do [ID]"
💡 "Próxima página" ou "Página {next_page}" (se total > exibidos e current_page < total_pages)
```

### 2. ENTITY_DETAIL - Um único registro

```
╔═══════════════════════════════════════════╗
║ 👤 {ENTIDADE}: {Nome}          [ID: {id}] ║
╠═══════════════════════════════════════════╣
║ Campo1: Valor1                            ║
║ Campo2: Valor2                            ║
╠═══════════════════════════════════════════╣
║ 📊 SEÇÃO ADICIONAL                        ║
║    • Métrica1: valor                      ║
║    • Métrica2: valor                      ║
╚═══════════════════════════════════════════╝

💡 Ações sugeridas
```

### 3. COUNT - Contagem

```
╔════════════════════════════════╗
║         📊 RESULTADO           ║
╠════════════════════════════════╣
║                                ║
║          ██ {número} ██        ║
║          {descrição}           ║
║                                ║
╠════════════════════════════════╣
║ 🔍 Filtros: {filtros}          ║
╚════════════════════════════════╝

💡 "Liste esses registros"
```

### 4. AGGREGATION - Estatísticas

```
💰 **{TÍTULO DA AGREGAÇÃO}**

╔═══════════════════════════════════════╗
║ 📊 MÉDIA: {valor_principal}           ║
╠═══════════════════════════════════════╣
║ 📈 Mediana: {valor}                   ║
║ 📉 Mínimo: {valor}                    ║
║ 📈 Máximo: {valor}                    ║
║ 👥 Base: {N} registros                ║
╠═══════════════════════════════════════╣
║ 📊 DISTRIBUIÇÃO:                      ║
║ Faixa1  ████████░░  X (Y%)            ║
║ Faixa2  ████░░░░░░  X (Y%)            ║
╚═══════════════════════════════════════╝
```

### 5. COMPARISON - Comparar entidades

```
⚖️ **COMPARAÇÃO: {A} vs {B}**

| Atributo | Entidade A | Entidade B |
|----------|------------|------------|
| ID | 123 | 456 |
| Campo1 | Valor1 | Valor2 ⚠️ |
| Campo2 | Valor3 | Valor4 ✨ |

📌 **Insights:**
- Diferença principal observada
```

### 6. ACTION_SUCCESS - Ação bem-sucedida

```
╔═══════════════════════════════════════╗
║ ✅ {AÇÃO} COM SUCESSO!                ║
╠═══════════════════════════════════════╣
║ 👤 Entidade1: {nome} [ID: {id}]       ║
║ 💼 Entidade2: {nome} [ID: {id}]       ║
║ 🆔 Resultado ID: {id}                 ║
║ 📅 Data: {timestamp}                  ║
╠═══════════════════════════════════════╣
║ 🎯 PRÓXIMOS PASSOS:                   ║
║ 1. Ação1                              ║
║ 2. Ação2                              ║
╚═══════════════════════════════════════╝
```

### 7. ACTION_FAILED - Ação falhou

```
╔═══════════════════════════════════════╗
║ ❌ NÃO FOI POSSÍVEL {AÇÃO}            ║
╠═══════════════════════════════════════╣
║ 📛 Motivo: {explicação}                ║
║                                       ║
║ Contexto: {detalhes}                  ║
╠═══════════════════════════════════════╣
║ 💡 ALTERNATIVAS:                      ║
║ 1. Sugestão1                          ║
║ 2. Sugestão2                          ║
╚═══════════════════════════════════════╝
```

### 8. DISAMBIGUATION - Escolher entre múltiplos

```
╔═══════════════════════════════════════╗
║ 🤔 ENCONTREI {N} {ENTIDADE}           ║
║    Qual você quer?                    ║
╠═══════════════════════════════════════╣
║ 1️⃣ {Nome} [ID: {id}]                  ║
║    📧 {email}                          ║
║    💼 {diferenciador}                  ║
║                                       ║
║ 2️⃣ {Nome} [ID: {id}]                  ║
║    📧 {email}                          ║
║    💼 {diferenciador}                  ║
╠═══════════════════════════════════════╣
║ 📝 Responda com número, ID ou email   ║
╚═══════════════════════════════════════╝
```

### 9. CONFIRMATION_REQUEST - Pedir confirmação

```
╔═══════════════════════════════════════╗
║ ⚠️ CONFIRMAÇÃO NECESSÁRIA             ║
╠═══════════════════════════════════════╣
║ Você vai: {descrição_ação}            ║
║ Quantidade: {N} registros             ║
║                                       ║
║ 📋 PREVIEW:                           ║
║ • Item1                               ║
║ • Item2                               ║
║ • ... e mais {N-5}                    ║
╠═══════════════════════════════════════╣
║ ❓ Digite "sim" para confirmar        ║
╚═══════════════════════════════════════╝
```

### 10. NOT_FOUND - Nenhum resultado

```
╔═══════════════════════════════════════╗
║ 🔍 NENHUM RESULTADO ENCONTRADO        ║
╠═══════════════════════════════════════╣
║ Busquei por: {critérios}              ║
║ Resultado: 0 registros                ║
╠═══════════════════════════════════════╣
║ 💡 SUGESTÕES:                         ║
║ 1. Ampliar busca: "{sugestão1}"       ║
║ 2. Termos similares: "{sugestão2}"    ║
╚═══════════════════════════════════════╝
```

### 11. IMPOSSIBLE - Fora do escopo

```
╔═══════════════════════════════════════╗
║ 🚫 AÇÃO FORA DO ESCOPO                ║
╠═══════════════════════════════════════╣
║ ❌ Solicitado: {pedido}                ║
║ 📌 Motivo: {explicação}                ║
╠═══════════════════════════════════════╣
║ ✅ O QUE POSSO FAZER:                 ║
║ 1. Alternativa1                       ║
║ 2. Alternativa2                       ║
╚═══════════════════════════════════════╝
```

═══════════════════════════════════════════════════════════════════════════════
REGRAS GLOBAIS
═══════════════════════════════════════════════════════════════════════════════

**Formatação:**
- ID: sempre `[ID: X]` ao lado do nome
- Moeda: `R$ X.XXX,XX`
- Data: `DD/MM/YYYY`
- Percentual: `XX%`

**Emojis:**
✅ Sucesso | ❌ Erro | ⚠️ Alerta | 🔍 Busca | 📊 Dados | 👤 Candidato
💼 Vaga | 💰 Dinheiro | 📍 Local | 📧 Email | 💡 Insight | 🎯 Ação

**Obrigatório:**
1. IDs visíveis para rastreabilidade
2. Contexto (filtros aplicados)
3. Formatação brasileira
4. Próximas ações sugeridas
5. NUNCA inventar dados
6. NUNCA omitir IDs

═══════════════════════════════════════════════════════════════════════════════
INSTRUÇÕES
═══════════════════════════════════════════════════════════════════════════════

1. Analise pergunta + dados retornados
2. Use MATRIZ DE DECISÃO para escolher formato
3. Aplique template escolhido
4. Siga REGRAS GLOBAIS
5. Inclua sugestões de ações
6. Use apenas dados da API

Retorne APENAS a resposta formatada, sem texto adicional."""

    def __init__(self):
        """Initialize the Answer Formatter Agent with LLM."""
        settings = get_settings()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini.model,
            temperature=0.3,  # Slightly higher for more natural language
            google_api_key=settings.gemini.api_key
        )

    def format(self, state: QueryState) -> QueryState:
        """
        Format final answer in natural language.

        Args:
            state: Current query state with processed data.

        Returns:
            Updated state with final answer.
        """
        processed = state.get("processed_data", {})
        intent = state.get("intent", {})
        question = state.get("question", "")

        print("\n" + "="*80)
        print("✨ ANSWER FORMATTER")
        print("="*80)

        retry_note = self._build_retry_note(state)

        if state.get("error"):
            error_msg = state["error"]
            print(f"\n❌ Formatting error response")
            state["final_answer"] = self._format_error(error_msg)
            logger.info("Formatted error response")
            return state

        if not processed:
            print(f"\n⚠️  No data to format")
            state["final_answer"] = "❌ Não foi possível processar os dados. Tente reformular sua pergunta."
            logger.warning("No processed data to format")
            return state

        print(f"\n📝 Formatting response for question: {question}")
        logger.info("Formatting final answer")

        try:
            # Prepare processed data for LLM
            processed_json = json.dumps(
                processed, indent=2, ensure_ascii=False, default=str)

            current_page = state.get("current_page", 1)
            total_pages = state.get("total_pages", 1)
            next_page = current_page + 1

            print(f"\n💭 Thinking... (generating natural language response)")

            # Prepare messages for LLM
            messages = [
                HumanMessage(content=f"""{self.SYSTEM_PROMPT}

**Pergunta:** {question}

**Paginação:**
- Página atual: {current_page}
- Total de páginas: {total_pages}
- Próxima página: {next_page}

**Dados processados:**
```json
{processed_json}
```

Formate uma resposta clara e objetiva para o usuário.

**IMPORTANTE para sugestões de paginação:**
- Se existem mais páginas (current_page < total_pages), SEMPRE use exatamente: 💡 "Próxima página" ou "Página {next_page}"
- Se está na última página, não mostre sugestão de próxima página
- NUNCA omita "Próxima página" ou, sempre use o formato completo com ambas as opções""")
            ]

            # Get response from LLM
            response = self.llm.invoke(messages)

            # Extract formatted answer
            answer = response.content.strip()

            if answer.startswith("```") and answer.endswith("```"):
                lines = answer.split("\n")
                answer = "\n".join(lines[1:-1])

            if retry_note:
                answer = retry_note + "\n\n" + answer

            print(f"\n✅ Response formatted successfully")

            # Update state
            state["final_answer"] = answer
            state["messages"].append(AIMessage(content="✓ Resposta formatada"))

            logger.info("Answer formatted successfully")

        except Exception as e:
            error_msg = f"Erro ao formatar resposta: {str(e)}"
            logger.error(error_msg)
            state["final_answer"] = self._format_fallback(processed, question)
            state["messages"].append(
                AIMessage(content="⚠️ Resposta formatada com fallback"))

        return state

    def _format_error(self, error: str) -> str:
        """
        Format error message in a user-friendly way.

        Args:
            error: Error message.

        Returns:
            Formatted error message.
        """
        return f"""❌ **Erro ao processar sua pergunta**

Detalhes: {error}

💡 **Sugestões:**
- Tente reformular sua pergunta de forma mais específica
- Verifique se os termos utilizados estão corretos
- Para perguntas complexas, tente dividir em partes menores
"""

    def _format_fallback(self, processed: Dict[str, Any], question: str) -> str:
        """
        Create a fallback formatted response when LLM fails.

        Args:
            processed: Processed data.
            question: Original question.

        Returns:
            Basic formatted response.
        """
        summary = processed.get("summary", {})
        aggregations = processed.get("aggregations", {})

        lines = [
            f"📊 **Resultados para:** {question}",
            "",
            "**Resumo:**"
        ]

        if summary:
            lines.append(
                f"- Total de registros: {summary.get('total_records', 0)}")
            lines.append(
                f"- Chamadas de API: {summary.get('total_api_calls', 0)}")

        if aggregations:
            lines.append("")
            lines.append("**Agregações:**")
            for key, value in aggregations.items():
                if value is not None:
                    if isinstance(value, float):
                        lines.append(f"- {key}: {value:,.2f}")
                    elif isinstance(value, dict):
                        lines.append(f"- {key}:")
                        for k, v in list(value.items())[:10]:  # Show top 10
                            lines.append(f"  - {k}: {v}")
                    else:
                        lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _build_retry_note(self, state: QueryState) -> str:
        """
        Build a note explaining retry attempts if any occurred.

        Args:
            state: Current query state

        Returns:
            Retry note or empty string
        """
        attempt_number = state.get("attempt_number", 1)

        if attempt_number <= 1:
            return ""

        feedback_list = state.get("execution_feedback", [])

        if not feedback_list:
            return "💡 **Nota:** A busca inicial não retornou resultados. Ampliei os critérios e encontrei dados."

        first_feedback = feedback_list[0]

        return f"💡 **Nota:** {first_feedback}\n   Ajustei a estratégia de busca para encontrar resultados relevantes."

    def __call__(self, state: QueryState) -> QueryState:
        """Make agent callable."""
        return self.format(state)

```

---



# RECRUITER_AGENT_V5 — Part 2: Config + Domains Core

---

## 📄 src/config/__init__.py

```python
"""Configuration package for recruiter agent."""

from .settings import Settings

__all__ = ["Settings"]

```

---

## 📄 src/config/settings.py

```python
"""
Settings module for managing environment variables and configuration.
Follows Single Responsibility Principle - only handles configuration loading.
All dataclass configs are now in separate files (1 class per file).
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from src.config.gemini_config import GeminiConfig
from src.config.langsmith_config import LangSmithConfig
from src.config.postgres_config import PostgresConfig
from src.config.ats_api_config import ATSAPIConfig
from src.config.rabbitmq_config import RabbitMQConfig
from src.config.memory_config import MemoryConfig
from src.config.multi_agent_config import MultiAgentConfig
from src.config.callback_config import CallbackConfig
from src.config.rails_api_config import RailsAPIConfig


class Settings:
    """
    Centralized settings manager for the application.
    Loads and validates all environment variables.
    """

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize settings by loading environment variables.

        Args:
            env_file: Optional path to .env file. If None, searches in default locations.
        """
        if env_file is None:
            # Search for .env in project root
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            env_file = project_root / ".env"

        if env_file.exists():
            load_dotenv(env_file)

        self._validate_required_vars()

    def _validate_required_vars(self) -> None:
        """Validate that all required environment variables are set."""
        required_vars = [
            "GEMINI_API_KEY",
            "API_BASE_URL",
            "ATS_USERNAME",
            "ATS_PASSWORD",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB",
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    @property
    def gemini(self) -> GeminiConfig:
        """Get Gemini API configuration."""
        return GeminiConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.0"))
        )

    @property
    def langsmith(self) -> LangSmithConfig:
        """Get LangSmith configuration."""
        return LangSmithConfig(
            tracing_enabled=os.getenv(
                "LANGCHAIN_TRACING_V2", "false").lower() == "true",
            api_key=os.getenv("LANGCHAIN_API_KEY", ""),
            project=os.getenv("LANGCHAIN_PROJECT", "recruiter-agent-v5"),
            endpoint=os.getenv("LANGCHAIN_ENDPOINT",
                               "https://api.smith.langchain.com")
        )

    @property
    def postgres(self) -> PostgresConfig:
        """Get PostgreSQL configuration."""
        return PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5433")),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
            database=os.getenv("POSTGRES_DB", "recruiter_agent")
        )

    @property
    def ats_api(self) -> ATSAPIConfig:
        """Get ATS API configuration."""
        return ATSAPIConfig(
            base_url=os.getenv("API_BASE_URL", "http://localhost:8080"),
            username=os.getenv("ATS_USERNAME", ""),
            password=os.getenv("ATS_PASSWORD", "")
        )

    @property
    def rabbitmq(self) -> RabbitMQConfig:
        """Get RabbitMQ configuration."""
        return RabbitMQConfig(
            url=os.getenv("RABBITMQ_URL",
                          "amqp://guest:guest@localhost:5672/"),
            exchange=os.getenv("RABBITMQ_EXCHANGE", "messages_exchange"),
            request_queue=os.getenv(
                "RABBITMQ_REQUEST_QUEUE", "recruiter_agent"),
            request_routing_key=os.getenv(
                "RABBITMQ_REQUEST_ROUTING_KEY", "messages_created"),
            # Evaluation system configuration
            evaluation_exchange=os.getenv("EVAL_EXCHANGE", "evaluations_exchange"),
            evaluation_queue_in=os.getenv("EVAL_QUEUE_IN", "evaluation_requests"),
            evaluation_queue_out=os.getenv("EVAL_QUEUE_OUT", "evaluation_responses"),
            evaluation_routing_in=os.getenv("EVAL_ROUTING_IN", "evaluation_request"),
            evaluation_routing_out=os.getenv("EVAL_ROUTING_OUT", "evaluation_response")
        )

    @property
    def memory(self) -> MemoryConfig:
        """Get memory system configuration."""
        return MemoryConfig(
            enabled=os.getenv("MEMORY_SYSTEM_ENABLED",
                              "true").lower() == "true"
        )

    @property
    def multi_agent(self) -> MultiAgentConfig:
        """Get multi-agent configuration."""
        return MultiAgentConfig(
            enabled=os.getenv("MULTI_AGENT_ENABLED", "true").lower() == "true",
            mode=os.getenv("MULTI_AGENT_MODE", "hybrid"),
            domains=os.getenv("MULTI_AGENT_DOMAINS", "recruitment")
        )

    @property
    def callback(self) -> CallbackConfig:
        """Get callback configuration."""
        return CallbackConfig(
            rails_callback_url=os.getenv(
                "RAILS_CALLBACK_URL", "http://localhost:8080/v1/users/messages"),
            authorization_token=os.getenv("AUTHORIZATION_TOKEN")
        )

    @property
    def rails_api(self) -> RailsAPIConfig:
        """Get Rails API configuration for aggregated stats."""
        return RailsAPIConfig(
            base_url=os.getenv("RAILS_API_BASE_URL", "http://localhost:3000"),
            timeout=int(os.getenv("RAILS_API_TIMEOUT", "30"))
        )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create singleton settings instance.

    Returns:
        Settings instance with all configuration loaded.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

```

---

## 📄 src/config/ats_api_config.py

```python
"""
ATS REST API configuration.
Single Responsibility: Manage ATS API connection settings only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ATSAPIConfig:
    """Configuration for ATS REST API."""
    base_url: str
    username: str
    password: str

```

---

## 📄 src/config/gemini_config.py

```python
"""
Gemini API configuration.
Single Responsibility: Manage Gemini API settings only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GeminiConfig:
    """Configuration for Google Gemini API."""
    api_key: str
    model: str = "gemini-1.5-flash-latest"
    temperature: float = 0.0

```

---

## 📄 src/config/multi_agent_config.py

```python
"""
Multi-agent system configuration.
Single Responsibility: Manage multi-agent orchestration settings only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MultiAgentConfig:
    """Configuration for multi-agent features."""
    enabled: bool
    mode: str
    domains: str

```

---

## 📄 src/config/postgres_config.py

```python
"""
PostgreSQL database configuration.
Single Responsibility: Manage PostgreSQL connection settings only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PostgresConfig:
    """Configuration for PostgreSQL database."""
    host: str
    port: int
    user: str
    password: str
    database: str
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

```

---

## 📄 src/config/memory_config.py

```python
"""
Memory system configuration.
Single Responsibility: Manage memory persistence settings only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryConfig:
    """Configuration for memory system."""
    enabled: bool

```

---

## 📄 src/config/celery_config.py

```python
from dataclasses import dataclass, field
from typing import Dict, List
import os


@dataclass(frozen=True)
class QueueConfig:
    name: str
    priority: int
    routing_key: str


@dataclass(frozen=True)
class CeleryConfig:
    broker_url: str
    result_backend: str
    task_serializer: str
    result_serializer: str
    accept_content: tuple
    timezone: str
    enable_utc: bool
    task_track_started: bool
    task_time_limit: int
    task_soft_time_limit: int
    worker_prefetch_multiplier: int
    worker_concurrency: int
    worker_send_task_events: bool
    task_send_sent_event: bool


DOMAIN_QUEUES: Dict[str, QueueConfig] = {
    "sourced_profile_sourcing": QueueConfig(
        name="sourcing_high",
        priority=10,
        routing_key="sourcing.high",
    ),
    "evaluation": QueueConfig(
        name="evaluation_normal",
        priority=5,
        routing_key="evaluation.normal",
    ),
    "default": QueueConfig(
        name="default",
        priority=1,
        routing_key="default",
    ),
}


def get_queue_for_domain(domain_id: str) -> QueueConfig:
    return DOMAIN_QUEUES.get(domain_id, DOMAIN_QUEUES["default"])


def get_celery_config() -> CeleryConfig:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    rabbitmq_url = os.getenv(
        "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    broker = os.getenv("CELERY_BROKER_URL", rabbitmq_url)
    # Use RabbitMQ as result backend if Redis is not available
    default_backend = os.getenv("REDIS_URL")
    if not default_backend:
        # Use RabbitMQ (rpc://) as fallback - simpler, no Redis dependency
        default_backend = "rpc://"
    backend = os.getenv("CELERY_RESULT_BACKEND", default_backend)

    return CeleryConfig(
        broker_url=broker,
        result_backend=backend,
        task_serializer="json",
        result_serializer="json",
        accept_content=("json",),
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "300")),
        task_soft_time_limit=int(
            os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "240")),
        worker_prefetch_multiplier=int(
            os.getenv("CELERY_PREFETCH_MULTIPLIER", "1")),
        worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "4")),
        worker_send_task_events=os.getenv(
            "CELERY_SEND_EVENTS", "false").lower() == "true",
        task_send_sent_event=os.getenv(
            "CELERY_SEND_EVENTS", "false").lower() == "true",
    )

```

---

## 📄 src/config/rabbitmq_config.py

```python
"""
RabbitMQ message broker configuration.
Single Responsibility: Manage RabbitMQ connection settings only.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RabbitMQConfig:
    """Configuration for RabbitMQ message broker."""
    url: str
    exchange: str
    request_queue: str
    request_routing_key: str
    
    # Evaluation system queues (optional, for backward compatibility)
    evaluation_exchange: Optional[str] = None
    evaluation_queue_in: Optional[str] = None
    evaluation_queue_out: Optional[str] = None
    evaluation_routing_in: Optional[str] = None
    evaluation_routing_out: Optional[str] = None
```

---

## 📄 src/config/langsmith_config.py

```python
"""
LangSmith tracing configuration.
Single Responsibility: Manage LangSmith observability settings only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LangSmithConfig:
    """Configuration for LangSmith tracing and observability."""
    tracing_enabled: bool
    api_key: str
    project: str
    endpoint: str

```

---

## 📄 src/config/callback_config.py

```python
"""
Rails callback configuration.
Single Responsibility: Manage callback URL settings only.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CallbackConfig:
    """Configuration for Rails callbacks."""
    rails_callback_url: str
    authorization_token: Optional[str]

```

---

## 📄 src/config/rails_api_config.py

```python
from dataclasses import dataclass


@dataclass
class RailsAPIConfig:
    base_url: str = "http://localhost:3000"
    timeout: int = 30

```

---

## 📄 src/domains/__init__.py

```python
from src.domains.registry import DomainRegistry, register_domain
from src.domains.base import (
    DomainPrompt,
    DomainAction,
    DomainContext,
    DomainResponse,
    ActionType
)
from src.domains.orchestrator import DomainOrchestrator

from src.domains.sourced_profile_sourcing.domain import SourcedProfileSourcingDomain
from src.domains.evaluation.domain import EvaluationDomain

__all__ = [
    "DomainRegistry",
    "register_domain",
    "DomainPrompt",
    "DomainAction",
    "DomainContext",
    "DomainResponse",
    "ActionType",
    "DomainOrchestrator",
    "SourcedProfileSourcingDomain",
    "EvaluationDomain",
]

```

---

## 📄 src/domains/base.py

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime


@dataclass
class APICallRecord:
    endpoint: str
    method: str
    params: Dict[str, Any]
    path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "path": self.path,
            "params": self.params,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "status_code": self.status_code,
            "success": self.success,
            "error": self.error
        }


class ActionType(Enum):
    QUERY = "query"
    AGGREGATE = "aggregate"
    ANALYZE = "analyze"
    ACTION = "action"


@dataclass
class DomainAction:
    id: str
    name: str
    description: str
    action_type: ActionType
    examples: Tuple[str, ...] = field(default_factory=tuple)
    requires_confirmation: bool = False
    allowed_apis: Tuple[str, ...] = field(default_factory=tuple)
    requires_params: Tuple[str, ...] = field(default_factory=tuple)


@dataclass
class DomainContext:
    domain_id: str
    current_data: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    selected_ids: List[Any] = field(default_factory=list)
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    sourcing_id: Optional[str] = None
    conversation_memory: Optional[Any] = None
    api_calls_history: List[APICallRecord] = field(default_factory=list)
    allow_sensitive_filters: bool = False
    sensitive_filter_justification: Optional[str] = None
    auth_token: Optional[str] = None

    def has_data(self) -> bool:
        return len(self.current_data) > 0

    def get_total_count(self) -> int:
        return self.metadata.get("total", len(self.current_data))

    def get_selected_count(self) -> int:
        return len(self.selected_ids)

    def get_by_id(self, item_id: Any) -> Optional[Dict[str, Any]]:
        return next((item for item in self.current_data if item.get("id") == item_id), None)

    def filter_selected(self) -> List[Dict[str, Any]]:
        return [item for item in self.current_data if item.get("id") in self.selected_ids]

    def get_memory(self):
        if self.conversation_memory is None:
            from src.domains.sourced_profile_sourcing.memory import ConversationMemory
            self.conversation_memory = ConversationMemory()
        return self.conversation_memory

    def track_api_call(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        path: str = "",
        duration_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        record = APICallRecord(
            endpoint=endpoint,
            method=method,
            path=path,
            params=params,
            duration_ms=duration_ms,
            status_code=status_code,
            success=success,
            error=error
        )
        self.api_calls_history.append(record)

    def get_api_calls(self) -> List[Dict[str, Any]]:
        return [call.to_dict() for call in self.api_calls_history]


@dataclass
class DomainResponse:
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    needs_confirmation: bool = False
    confirmation_message: Optional[str] = None
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    clarification_options: List[str] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    api_calls: List[Dict[str, Any]] = field(default_factory=list)


class DomainPrompt(ABC):

    @property
    @abstractmethod
    def domain_id(self) -> str:
        pass

    @property
    @abstractmethod
    def domain_name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def get_allowed_actions(self) -> List[DomainAction]:
        pass

    @abstractmethod
    def get_system_prompt(self, context: DomainContext) -> str:
        pass

    @abstractmethod
    def process_intent(self, user_query: str, context: DomainContext) -> Dict[str, Any]:
        pass

    @abstractmethod
    def execute_action(
        self,
        action_id: str,
        params: Dict[str, Any],
        context: DomainContext
    ) -> DomainResponse:
        pass

    def get_suggestions(self, context: DomainContext) -> List[str]:
        return []

    def validate_context(self, context: DomainContext) -> Tuple[bool, Optional[str]]:
        return True, None

```

---

## 📄 src/domains/base_dispatcher.py

```python
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any
import pika

logger = logging.getLogger(__name__)


class BaseDispatcher(ABC):
    def __init__(
        self,
        queue_name: str,
        rabbitmq_host: Optional[str] = None,
        rabbitmq_port: Optional[int] = None,
        rabbitmq_user: Optional[str] = None,
        rabbitmq_password: Optional[str] = None,
        prefetch_count: int = 5,
        max_priority: int = 10,
    ):
        self.queue_name = queue_name
        self.rabbitmq_host = rabbitmq_host or os.getenv(
            "RABBITMQ_HOST", "localhost")
        self.rabbitmq_port = rabbitmq_port or int(
            os.getenv("RABBITMQ_PORT", "5672"))
        self.rabbitmq_user = rabbitmq_user or os.getenv(
            "RABBITMQ_USER", "guest")
        self.rabbitmq_password = rabbitmq_password or os.getenv(
            "RABBITMQ_PASSWORD", "guest")
        self.prefetch_count = prefetch_count
        self.max_priority = max_priority
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.adapters.blocking_connection.BlockingChannel] = None

    def connect(self) -> None:
        credentials = pika.PlainCredentials(
            self.rabbitmq_user, self.rabbitmq_password)
        parameters = pika.ConnectionParameters(
            host=self.rabbitmq_host,
            port=self.rabbitmq_port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.queue_declare(
            queue=self.queue_name,
            durable=True,
            arguments={"x-max-priority": self.max_priority},
        )
        self.channel.basic_qos(prefetch_count=self.prefetch_count)
        logger.info(f"Connected to RabbitMQ queue: {self.queue_name}")

    def disconnect(self) -> None:
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    @abstractmethod
    def dispatch_task(self, message: dict, correlation_id: Optional[str] = None) -> None:
        pass

    def _process_message(
        self,
        channel: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.BasicProperties,
        body: bytes,
    ) -> None:
        try:
            message = json.loads(body)
            correlation_id = properties.correlation_id or message.get(
                "correlation_id")

            self.dispatch_task(message, correlation_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)

            logger.info(f"Dispatched task from queue: {self.queue_name}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self) -> None:
        if not self.channel:
            self.connect()

        logger.info(f"Starting to consume from: {self.queue_name}")
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self._process_message,
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
        finally:
            self.disconnect()

    @classmethod
    def run(cls, **kwargs) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        dispatcher = cls(**kwargs)
        dispatcher.start_consuming()


class CallbackMixin:
    def publish_callback(
        self,
        callback_queue: str,
        result: Any,
        correlation_id: Optional[str] = None,
    ) -> None:
        if not hasattr(self, "channel") or not self.channel:
            return

        self.channel.basic_publish(
            exchange="",
            routing_key=callback_queue,
            properties=pika.BasicProperties(
                correlation_id=correlation_id,
                content_type="application/json",
                delivery_mode=2,
            ),
            body=json.dumps(result),
        )

```

---

## 📄 src/domains/orchestrator.py

```python
import logging
from typing import Dict, Any, Optional
import time

from src.domains.base import DomainContext, DomainResponse
from src.domains.registry import DomainRegistry
from src.domains.workflow import DomainWorkflow
from src.utils.timing import log_step, get_timer

logger = logging.getLogger(__name__)


class DomainOrchestrator:

    def __init__(self):
        self.workflow = DomainWorkflow()
        self._sourcing_api_client = None

    @property
    def sourcing_api_client(self):
        if self._sourcing_api_client is None:
            from src.domains.sourced_profile_sourcing.api_client import SourcingAPIClient
            self._sourcing_api_client = SourcingAPIClient()
        return self._sourcing_api_client

    def process_query(
        self,
        domain_id: str,
        user_query: str,
        context_data: Dict[str, Any]
    ) -> DomainResponse:

        logger.info(
            f"Processing domain query: {domain_id} | Query: {user_query}")

        start_time = time.time()
        log_step("domain_setup")

        domain = DomainRegistry.get_instance(domain_id)
        if not domain:
            return DomainResponse(
                success=False,
                message=f"❌ Domínio '{domain_id}' não encontrado",
                error=f"Domain '{domain_id}' not registered",
                suggestions=["Tente uma pergunta geral"]
            )

        context = self._build_context(domain_id, context_data)

        is_valid, error_msg = domain.validate_context(context)
        if not is_valid:
            return DomainResponse(
                success=False,
                message=f"⚠️ {error_msg}",
                error=error_msg,
                suggestions=domain.get_suggestions(context)
            )

        aggregated_stats = None
        if domain_id == "sourced_profile_sourcing" and context.sourcing_id:
            try:
                log_step("fetch_aggregated_stats")
                aggregated_stats = domain.ensure_aggregated_stats_sync(
                    sourcing_id=int(context.sourcing_id),
                    context=context
                )
                if aggregated_stats:
                    logger.info(
                        f"Loaded aggregated stats for sourcing {context.sourcing_id}")
            except Exception as e:
                logger.warning(f"Failed to load aggregated stats: {e}")

        try:
            log_step("workflow_process")
            result = self.workflow.process(
                question=user_query,
                domain_id=domain_id,
                domain_instance=domain,
                context=context,
                aggregated_stats=aggregated_stats
            )

            execution_time_ms = (time.time() - start_time) * 1000

            response = DomainResponse(
                success=result['success'],
                message=result['final_answer'],
                data=result.get('data', {}),
                suggestions=result.get('suggestions', []),
                needs_confirmation=result.get('needs_confirmation', False),
                error=result.get('error'),
                metadata={
                    "domain": domain_id,
                    "execution_time_ms": execution_time_ms,
                    "used_aggregated_stats": aggregated_stats is not None,
                    **result.get('metadata', {})
                },
                api_calls=context.get_api_calls()
            )

            if domain_id == "sourced_profile_sourcing" and context.user_id:
                self._create_domain_message(
                    user_id=context.user_id,
                    content=response.message,
                    metadata={
                        "sourcing_id": context.sourcing_id,
                        "action_id": result.get('metadata', {}).get('action_id'),
                        "success": response.success,
                        "execution_time_ms": execution_time_ms,
                        "needs_clarification": response.needs_clarification,
                        "api_calls": context.get_api_calls()
                    }
                )

            logger.info(
                f"Domain query processed | Success: {response.success} | Time: {execution_time_ms:.2f}ms")

            return response

        except Exception as e:
            logger.error(f"Error processing domain query: {e}", exc_info=True)
            error_response = DomainResponse(
                success=False,
                message="❌ Erro ao processar sua pergunta",
                error=str(e),
                suggestions=["Tente novamente", "Reformule a pergunta"]
            )

            if domain_id == "sourced_profile_sourcing" and context.user_id:
                self._create_domain_message(
                    user_id=context.user_id,
                    content=error_response.message,
                    metadata={
                        "sourcing_id": context.sourcing_id,
                        "success": False,
                        "error": str(e)
                    }
                )

            return error_response

    def _build_context(self, domain_id: str, context_data: Dict[str, Any]) -> DomainContext:
        return DomainContext(
            domain_id=domain_id,
            current_data=context_data.get("data", []),
            metadata=context_data.get("metadata", {}),
            selected_ids=context_data.get("selected_ids", []),
            filters_applied=context_data.get("filters_applied", {}),
            user_id=context_data.get("user_id"),
            session_id=context_data.get("session_id"),
            sourcing_id=context_data.get("sourcing_id"),
            auth_token=context_data.get("auth_token")
        )

    def _create_domain_message(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        try:
            result = self.sourcing_api_client.create_message(
                user_id=user_id,
                content=content,
                metadata=metadata
            )
            if result.get("success"):
                logger.info(f"Domain message created for user {user_id}")
            else:
                logger.warning(
                    f"Failed to create domain message: {result.get('error')}")
        except Exception as e:
            logger.warning(f"Error creating domain message: {e}")

```

---

## 📄 src/domains/registry.py

```python
from typing import Dict, Type, Optional
import logging

logger = logging.getLogger(__name__)


class DomainRegistry:
    _domains: Dict[str, Type['DomainPrompt']] = {}

    @classmethod
    def register(cls, domain_class: Type['DomainPrompt']) -> Type['DomainPrompt']:
        instance = domain_class()
        domain_id = instance.domain_id

        if domain_id in cls._domains:
            logger.warning(
                f"Domain '{domain_id}' already registered, overwriting")

        cls._domains[domain_id] = domain_class
        logger.info(f"Registered domain: {domain_id} ({instance.domain_name})")

        return domain_class

    @classmethod
    def get(cls, domain_id: str) -> Optional[Type['DomainPrompt']]:
        return cls._domains.get(domain_id)

    @classmethod
    def get_instance(cls, domain_id: str) -> Optional['DomainPrompt']:
        domain_class = cls.get(domain_id)
        return domain_class() if domain_class else None

    @classmethod
    def list_domains(cls) -> Dict[str, str]:
        return {
            domain_id: domain_class().domain_name
            for domain_id, domain_class in cls._domains.items()
        }

    @classmethod
    def is_registered(cls, domain_id: str) -> bool:
        return domain_id in cls._domains


def register_domain(cls: Type['DomainPrompt']) -> Type['DomainPrompt']:
    return DomainRegistry.register(cls)

```

---



# RECRUITER_AGENT_V5 — Part 3: Evaluation Domain

---

## 📄 src/domains/evaluation/__init__.py

```python
from src.domains.evaluation.domain import EvaluationDomain
from src.domains.evaluation.processor import EvaluationProcessor, get_processor
from src.domains.evaluation.final_analysis import FinalAnalysisService, get_final_analysis_service
from src.domains.evaluation.models import (
    InputClassification,
    RubricEvaluation,
    FlowDecision,
    CandidateMessage,
    EvaluationResponse,
    AIResponse,
    FinalAnalysisRequest,
    FinalAnalysisResponse,
)
from src.domains.evaluation.tasks import (
    process_evaluation,
    process_evaluation_batch,
    process_final_analysis,
    process_and_publish,
)

__all__ = [
    "EvaluationDomain",
    "EvaluationProcessor",
    "get_processor",
    "FinalAnalysisService",
    "get_final_analysis_service",
    "InputClassification",
    "RubricEvaluation",
    "FlowDecision",
    "CandidateMessage",
    "EvaluationResponse",
    "AIResponse",
    "FinalAnalysisRequest",
    "FinalAnalysisResponse",
    "process_evaluation",
    "process_evaluation_batch",
    "process_final_analysis",
    "process_and_publish",
]

```

---

## 📄 src/domains/evaluation/domain.py

```python
import logging
from typing import Dict, Any, List, Tuple, Optional

from src.domains.base import DomainPrompt, DomainContext, DomainResponse, DomainAction, ActionType
from src.domains.registry import register_domain
from src.domains.evaluation.state import create_initial_state, InterviewState
from src.domains.evaluation.graph import get_interview_graph
from src.domains.evaluation.models import (
    EvaluationResponse,
    AIResponse,
    EvaluationDetails,
    NextQuestionHint,
)

logger = logging.getLogger(__name__)


@register_domain
class EvaluationDomain(DomainPrompt):

    @property
    def domain_id(self) -> str:
        return "evaluation"

    @property
    def domain_name(self) -> str:
        return "Avaliação de Candidatos"

    @property
    def description(self) -> str:
        return "Processa e avalia respostas de candidatos em entrevistas de emprego via chat"

    def get_allowed_actions(self) -> List[DomainAction]:
        return [
            DomainAction(
                id="evaluate_response",
                name="Avaliar Resposta",
                description="Avalia a resposta de um candidato a uma pergunta",
                action_type=ActionType.ANALYZE,
                examples=("Avaliar resposta do candidato",),
            ),
            DomainAction(
                id="classify_intent",
                name="Classificar Intenção",
                description="Classifica o tipo de mensagem do candidato",
                action_type=ActionType.ANALYZE,
                examples=("Classificar mensagem",),
            ),
        ]

    def get_system_prompt(self, context: DomainContext) -> str:
        return """Você é um sistema de avaliação de candidatos para entrevistas de emprego.
Sua função é avaliar respostas de forma justa, objetiva e sem vieses."""

    def process_intent(self, user_query: str, context: DomainContext) -> Dict[str, Any]:
        return {
            "action_id": "evaluate_response",
            "params": {},
            "confidence": 1.0,
            "source": "evaluation_domain",
        }

    def execute_action(
        self,
        action_id: str,
        params: Dict[str, Any],
        context: DomainContext,
        **kwargs,
    ) -> DomainResponse:
        if action_id == "evaluate_response":
            return self._execute_evaluation(params, context)

        return DomainResponse(
            success=False,
            message=f"Ação '{action_id}' não suportada",
            error=f"Unknown action: {action_id}",
        )

    def _execute_evaluation(
        self,
        params: Dict[str, Any],
        context: DomainContext,
    ) -> DomainResponse:
        try:
            payload = params.get("payload", params)
            initial_state = create_initial_state(payload)

            thread_id = self._build_thread_id(payload)

            graph = get_interview_graph()
            final_state = graph.invoke(initial_state, thread_id)

            response = self._build_response(payload, final_state)

            return DomainResponse(
                success=True,
                message="Avaliação concluída",
                data={"evaluation_response": response.model_dump()},
            )

        except Exception as e:
            logger.error(f"Evaluation execution error: {e}", exc_info=True)
            return DomainResponse(
                success=False,
                message="Erro ao processar avaliação",
                error=str(e),
            )

    def _build_thread_id(self, payload: dict) -> str:
        account_id = payload.get("account_id", "unknown")
        eval_cand_id = payload.get("evaluation_candidate_id", "unknown")
        message_id = payload.get("message_id", "unknown")
        return f"{account_id}-{eval_cand_id}-{message_id}"

    def _build_response(
        self,
        original_payload: dict,
        state: InterviewState,
    ) -> EvaluationResponse:
        evaluation = state.get("evaluation")
        message = state.get("final_message")
        classification = state.get("classification")

        evaluation_details = None
        if evaluation:
            evaluation_details = EvaluationDetails(
                relevance=evaluation.relevance_score,
                depth=evaluation.depth_score,
                clarity=evaluation.clarity_score,
                examples=evaluation.examples_score,
                strengths=evaluation.strengths,
                gaps=evaluation.gaps,
            )

        next_question = state.get("next_question")
        next_q_hint = None
        if next_question:
            next_q_hint = NextQuestionHint(
                id=next_question.id if hasattr(
                    next_question, 'id') else next_question.get('id'),
                text=next_question.text if hasattr(
                    next_question, 'text') else next_question.get('text'),
            )

        ai_response = AIResponse(
            score=state.get("final_score", 0.0),
            is_answer_satisfactory=state.get("is_satisfactory", False),
            feedback_for_recruiter=evaluation.feedback if evaluation else "",
            chat_ack=message.full_message if message else "",
            responded=classification.intent == "answer" if classification else False,
            changed_subject=classification.intent == "off_topic" if classification else False,
            response_to_candidate=None,
            followup_needed=state.get("followup_needed", False),
            followup_question=state.get("followup_question"),
            next_question=next_q_hint,
            end=state.get("end_interview", False),
            interested_job=state.get("interested_job", True),
            interested_job_msg=None,
            evaluation_details=evaluation_details,
        )

        return EvaluationResponse(
            original_payload=original_payload,
            ai_response=ai_response,
            chatbot_channel=state.get("chatbot_channel", "whatsapp"),
        )

    def get_suggestions(self, context: DomainContext) -> List[str]:
        return []

    def validate_context(self, context: DomainContext) -> Tuple[bool, Optional[str]]:
        return True, None

```

---

## 📄 src/domains/evaluation/graph.py

```python
import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.domains.evaluation.state import InterviewState
from src.domains.evaluation.nodes import (
    classify_input_node,
    evaluate_response_node,
    decide_flow_node,
    craft_message_node,
)

logger = logging.getLogger(__name__)


def _route_after_classification(state: InterviewState) -> Literal["evaluate", "decide_flow"]:
    classification = state.get("classification")

    if not classification:
        return "decide_flow"

    if classification.intent == "answer":
        return "evaluate"

    return "decide_flow"


def create_interview_graph(with_checkpointer: bool = True) -> StateGraph:
    workflow = StateGraph(InterviewState)

    workflow.add_node("classify_input", classify_input_node)
    workflow.add_node("evaluate", evaluate_response_node)
    workflow.add_node("decide_flow", decide_flow_node)
    workflow.add_node("craft_message", craft_message_node)

    workflow.set_entry_point("classify_input")

    workflow.add_conditional_edges(
        "classify_input",
        _route_after_classification,
        {
            "evaluate": "evaluate",
            "decide_flow": "decide_flow",
        },
    )

    workflow.add_edge("evaluate", "decide_flow")
    workflow.add_edge("decide_flow", "craft_message")
    workflow.add_edge("craft_message", END)

    if with_checkpointer:
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    return workflow.compile()


class InterviewGraph:
    _instance = None
    _graph = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._graph = create_interview_graph(with_checkpointer=True)
        return cls._instance

    @property
    def graph(self):
        return self._graph

    def invoke(self, state: InterviewState, thread_id: str) -> InterviewState:
        config = {"configurable": {"thread_id": thread_id}}
        return self._graph.invoke(state, config=config)


def get_interview_graph() -> InterviewGraph:
    return InterviewGraph()

```

---

## 📄 src/domains/evaluation/nodes.py

```python
import logging
from typing import Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from src.config.settings import get_settings
from src.config.evaluation_config import get_evaluation_config
from src.domains.evaluation.state import InterviewState
from src.domains.evaluation.models import (
    InputClassification,
    RubricEvaluation,
    FlowDecision,
    CandidateMessage,
    NextQuestionHint,
)
from src.domains.evaluation.prompts import (
    CLASSIFY_INPUT_PROMPT,
    EVALUATE_RESPONSE_PROMPT,
    CRAFT_MESSAGE_PROMPT,
)
from src.domains.evaluation.security import (
    safe_process_input,
    create_safe_context,
)

logger = logging.getLogger(__name__)


def _get_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini.model,
        temperature=0.2,
        google_api_key=settings.gemini.api_key,
    )


def classify_input_node(state: InterviewState) -> Dict[str, Any]:
    candidate_answer = state.get("candidate_answer", "")

    sanitized, is_injection, pattern = safe_process_input(candidate_answer)

    if is_injection:
        logger.warning(f"Injection detected in candidate answer: {pattern}")
        return {
            "classification": InputClassification(
                intent="off_topic",
                confidence=1.0,
                summary="Conteúdo inválido detectado na resposta",
            ),
            "errors": [f"security_block:{pattern}"],
        }

    if not sanitized or len(sanitized.strip()) < 3:
        return {
            "classification": InputClassification(
                intent="unclear",
                confidence=0.9,
                summary="Resposta vazia ou muito curta",
            ),
        }

    safe_ctx = create_safe_context(
        job_description=state.get("job_description", ""),
        question_text=state.get("question_text", ""),
        expected_response=state.get("expected_response", ""),
        candidate_answer=sanitized,
    )

    llm = _get_llm().with_structured_output(InputClassification)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CLASSIFY_INPUT_PROMPT),
        ("human", "Resposta do candidato: {answer}"),
    ])

    try:
        result = (prompt | llm).invoke({
            "question": safe_ctx["question_text"],
            "expected": safe_ctx["expected_response"],
            "answer": safe_ctx["candidate_answer"],
        })
        return {"classification": result}

    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        return {
            "classification": InputClassification(
                intent="unclear",
                confidence=0.3,
                summary="Erro ao classificar resposta",
            ),
            "errors": [f"classify_error:{str(e)}"],
        }


def evaluate_response_node(state: InterviewState) -> Dict[str, Any]:
    config = get_evaluation_config()

    safe_ctx = create_safe_context(
        job_description=state.get("job_description", ""),
        question_text=state.get("question_text", ""),
        expected_response=state.get("expected_response", ""),
        candidate_answer=state.get("candidate_answer", ""),
    )

    llm = _get_llm().with_structured_output(RubricEvaluation)

    prompt = ChatPromptTemplate.from_messages([
        ("system", EVALUATE_RESPONSE_PROMPT),
        ("human", "Resposta do candidato:\n{answer}"),
    ])

    try:
        result = (prompt | llm).invoke({
            "job_description": safe_ctx["job_description"],
            "question": safe_ctx["question_text"],
            "expected": safe_ctx["expected_response"],
            "answer": safe_ctx["candidate_answer"],
        })

        return {
            "evaluation": result,
            "final_score": result.overall_score,
            "is_satisfactory": result.overall_score >= config.thresholds.satisfactory_score,
        }

    except Exception as e:
        logger.error(f"Evaluation error: {e}", exc_info=True)
        return {
            "evaluation": None,
            "final_score": 0.0,
            "is_satisfactory": False,
            "errors": [f"evaluate_error:{str(e)}"],
        }


def decide_flow_node(state: InterviewState) -> Dict[str, Any]:
    config = get_evaluation_config()
    classification = state.get("classification")
    evaluation = state.get("evaluation")

    if not classification:
        return {
            "flow_decision": FlowDecision(
                action="followup",
                reason="Classificação não disponível",
                followup_focus="Tentar novamente",
            ),
            "followup_needed": True,
        }

    if classification.intent == "not_interested":
        return {
            "flow_decision": FlowDecision(
                action="end_interview",
                reason="Candidato indicou desinteresse",
            ),
            "interested_job": False,
            "end_interview": True,
        }

    if classification.intent == "question":
        return {
            "flow_decision": FlowDecision(
                action="handle_question",
                reason="Candidato fez uma pergunta",
            ),
        }

    if classification.intent in ("off_topic", "unclear"):
        return {
            "flow_decision": FlowDecision(
                action="followup",
                reason=f"Resposta {classification.intent}",
                followup_focus="Redirecionar para a pergunta original",
            ),
            "followup_needed": True,
        }

    if not evaluation:
        return {
            "flow_decision": FlowDecision(
                action="followup",
                reason="Avaliação não disponível",
                followup_focus="Pedir mais detalhes",
            ),
            "followup_needed": True,
        }

    if evaluation.overall_score >= config.thresholds.followup_threshold:
        next_hint = state.get("next_question_hint")
        if next_hint and next_hint.id:
            return {
                "flow_decision": FlowDecision(
                    action="next_question",
                    reason=f"Score {evaluation.overall_score:.2f} satisfatório",
                ),
                "next_question": next_hint,
                "followup_needed": False,
            }
        return {
            "flow_decision": FlowDecision(
                action="end_interview",
                reason="Última pergunta respondida satisfatoriamente",
            ),
            "end_interview": True,
        }

    if evaluation.overall_score >= config.thresholds.satisfactory_score:
        gap = evaluation.gaps[0] if evaluation.gaps else "mais detalhes"
        return {
            "flow_decision": FlowDecision(
                action="followup",
                reason=f"Score {evaluation.overall_score:.2f} - precisa aprofundar",
                followup_focus=gap,
            ),
            "followup_needed": True,
        }

    return {
        "flow_decision": FlowDecision(
            action="followup",
            reason="Resposta insuficiente",
            followup_focus="Reformular a pergunta de forma mais clara",
        ),
        "followup_needed": True,
    }


def craft_message_node(state: InterviewState) -> Dict[str, Any]:
    flow = state.get("flow_decision")
    evaluation = state.get("evaluation")
    classification = state.get("classification")
    style = state.get("style")
    channel = state.get("chatbot_channel", "whatsapp")

    if not flow or not classification:
        return {
            "final_message": CandidateMessage(
                acknowledgment="Obrigado pela resposta.",
                transition="",
                next_content="Podemos continuar?",
                full_message="Obrigado pela resposta. Podemos continuar?",
            ),
        }

    action_context_map = {
        "followup": f"Faça um follow-up focando em: {flow.followup_focus or 'mais detalhes'}",
        "next_question": f"Transicione para a próxima pergunta",
        "end_interview": "Encerre a entrevista de forma positiva e profissional",
        "handle_question": "Responda brevemente a dúvida e retome a pergunta original",
    }

    action_context = action_context_map.get(flow.action, "Continue a conversa")

    next_hint = state.get("next_question_hint")
    if flow.action == "next_question" and next_hint and next_hint.text:
        action_context = f"Transicione para: {next_hint.text}"

    evaluation_context = ""
    if evaluation and evaluation.strengths:
        points = ", ".join(evaluation.strengths[:2])
        evaluation_context = f"Pontos positivos para mencionar: {points}"

    persona = style.persona if style else "cordial e profissional"

    llm = _get_llm().with_structured_output(CandidateMessage)

    prompt = ChatPromptTemplate.from_messages([
        ("system", CRAFT_MESSAGE_PROMPT),
        ("human", "Gere a mensagem para o candidato."),
    ])

    try:
        result = (prompt | llm).invoke({
            "persona": persona,
            "summary": classification.summary,
            "action_context": action_context,
            "evaluation_context": evaluation_context,
            "channel": channel,
        })

        followup_question = None
        if state.get("followup_needed"):
            followup_question = result.next_content

        return {
            "final_message": result,
            "followup_question": followup_question,
        }

    except Exception as e:
        logger.error(f"Craft message error: {e}", exc_info=True)
        return {
            "final_message": CandidateMessage(
                acknowledgment="Obrigado pela resposta.",
                transition="",
                next_content="Podemos continuar com a próxima pergunta?",
                full_message="Obrigado pela resposta. Podemos continuar com a próxima pergunta?",
            ),
            "errors": [f"craft_error:{str(e)}"],
        }

```

---

## 📄 src/domains/evaluation/state.py

```python
from typing import TypedDict, Optional, List, Annotated, Any
import operator

from src.domains.evaluation.models import (
    InputClassification,
    RubricEvaluation,
    FlowDecision,
    CandidateMessage,
    NextQuestionHint,
    EvaluationStyle,
)


class HistoryMessage(TypedDict, total=False):
    role: str
    content: str


class InterviewState(TypedDict, total=False):
    account_id: int
    evaluation_candidate_id: int
    message_id: str
    job_description: str
    question_text: str
    expected_response: str
    candidate_answer: str
    history: List[HistoryMessage]
    next_question_hint: Optional[NextQuestionHint]
    is_introduction: bool
    chatbot_channel: str
    style: EvaluationStyle

    classification: Optional[InputClassification]
    evaluation: Optional[RubricEvaluation]
    flow_decision: Optional[FlowDecision]

    final_message: Optional[CandidateMessage]
    final_score: float
    is_satisfactory: bool
    followup_needed: bool
    followup_question: Optional[str]
    next_question: Optional[NextQuestionHint]
    end_interview: bool
    interested_job: bool

    errors: Annotated[List[str], operator.add]
    metadata: dict


def create_initial_state(payload: dict) -> InterviewState:
    style_data = payload.get("style", {})
    style = EvaluationStyle(
        persona=style_data.get("persona", "cordial e profissional"),
        pt_br=style_data.get("pt_br", True),
    )

    hint_data = payload.get("next_question_hint")
    next_hint = None
    if hint_data and isinstance(hint_data, dict):
        next_hint = NextQuestionHint(
            id=hint_data.get("id"),
            text=hint_data.get("text"),
        )

    return InterviewState(
        account_id=payload.get("account_id", 0),
        evaluation_candidate_id=payload.get("evaluation_candidate_id", 0),
        message_id=payload.get("message_id", ""),
        job_description=payload.get("job_description", ""),
        question_text=payload.get("question_text", ""),
        expected_response=payload.get("expected_response", ""),
        candidate_answer=payload.get("candidate_answer", ""),
        history=payload.get("history", []),
        next_question_hint=next_hint,
        is_introduction=payload.get("is_introduction", False),
        chatbot_channel=payload.get("chatbot_channel", "whatsapp"),
        style=style,
        classification=None,
        evaluation=None,
        flow_decision=None,
        final_message=None,
        final_score=0.0,
        is_satisfactory=False,
        followup_needed=False,
        followup_question=None,
        next_question=None,
        end_interview=False,
        interested_job=True,
        errors=[],
        metadata={},
    )

```

---

## 📄 src/domains/evaluation/prompts.py

```python
CLASSIFY_INPUT_PROMPT = """Você é um classificador de respostas de candidatos em entrevistas de emprego.

Analise a resposta do candidato e classifique em uma das categorias:
- "answer": Candidato respondeu a pergunta (mesmo que parcialmente ou de forma incompleta)
- "question": Candidato fez uma pergunta ao entrevistador
- "off_topic": Resposta completamente fora do contexto da pergunta
- "unclear": Resposta muito confusa ou curta demais para entender
- "not_interested": Candidato indica desinteresse em continuar ou na vaga

IMPORTANTE:
- Seja objetivo na classificação
- Se houver dúvida entre "answer" e "unclear", prefira "answer" se houver qualquer conteúdo relevante
- "not_interested" só deve ser usado quando o candidato explicitamente demonstra desinteresse

PERGUNTA ATUAL:
{question}

RESPOSTA ESPERADA (referência para contexto):
{expected}"""


EVALUATE_RESPONSE_PROMPT = """Você é um avaliador técnico de respostas em entrevistas de emprego.

RUBRICA DE AVALIAÇÃO:
1. **Relevância** (0-1): A resposta aborda diretamente a pergunta feita?
2. **Profundidade** (0-1): Demonstra conhecimento técnico adequado ao nível da vaga?
3. **Clareza** (0-1): A comunicação é clara, estruturada e fácil de entender?
4. **Exemplos** (0-1): Usa exemplos concretos, situações reais ou experiências práticas?

PESOS PARA SCORE FINAL:
- Relevância: 30%
- Profundidade: 30%
- Clareza: 20%
- Exemplos: 20%

CONTEXTO DA VAGA:
{job_description}

PERGUNTA:
{question}

RESPOSTA ESPERADA (referência, não critério absoluto):
{expected}

DIRETRIZES:
- Avalie objetivamente com base nos critérios
- Considere o nível da vaga ao avaliar profundidade
- Não penalize fortemente respostas curtas se forem precisas
- Identifique no máximo 3 pontos fortes e 3 lacunas
- O feedback deve ser útil para o recrutador tomar decisões"""


CRAFT_MESSAGE_PROMPT = """Você é um entrevistador {persona}.

DIRETRIZES DE COMUNICAÇÃO:
- Seja empático e encorajador
- Reconheça brevemente o que o candidato disse
- Faça transições naturais entre tópicos
- Use linguagem conversacional adequada ao canal ({channel})
- Máximo 3-4 frases curtas
- Não seja robótico ou excessivamente formal
- Evite repetir informações do candidato

RESUMO DA RESPOSTA DO CANDIDATO:
{summary}

AÇÃO A TOMAR:
{action_context}

{evaluation_context}

CANAL: {channel}
- WhatsApp: mensagens curtas, diretas, tom informal mas profissional
- Web: pode ser levemente mais elaborado"""


FINAL_ANALYSIS_PROMPT = """Você é um analista de RH especializado em avaliação de candidatos.

CANDIDATO: {candidate_name}
VAGA: {job_title}

CURRÍCULO (se disponível):
{curriculum}

RESPOSTAS DA ENTREVISTA:
{answers_summary}

TAREFA:
Gere uma análise completa do candidato considerando:

1. **Análise Detalhada** (4-6 parágrafos):
   - Avalie o desempenho geral nas respostas
   - Compare com os requisitos da vaga
   - Identifique padrões positivos e negativos
   - Considere comunicação e postura

2. **Resumo Executivo** (2-3 frases):
   - Síntese objetiva para decisão rápida

3. **Pontos Fortes** (3-5 itens):
   - Aspectos positivos demonstrados

4. **Pontos de Atenção** (3-5 itens):
   - Aspectos que precisam desenvolvimento ou validação

5. **Recomendação**:
   - APPROVED: Score médio >= 7.5/10 e >= 70% respostas satisfatórias
   - ADDITIONAL_ANALYSIS: Score entre 5.0 e 7.5
   - NOT_RECOMMENDED: Score < 5.0 ou problemas críticos

6. **Próximos Passos**:
   - Sugestões concretas baseadas na recomendação"""

```

---

## 📄 src/domains/evaluation/models.py

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class InputClassification(BaseModel):
    intent: Literal["answer", "question", "off_topic", "unclear", "not_interested"] = Field(
        description="Tipo de input do candidato"
    )
    confidence: float = Field(
        ge=0, le=1, description="Confiança na classificação")
    summary: str = Field(
        description="Resumo do que o candidato disse", max_length=500)


class RubricEvaluation(BaseModel):
    relevance_score: float = Field(
        ge=0, le=1, description="Quão relevante à pergunta")
    depth_score: float = Field(ge=0, le=1, description="Profundidade técnica")
    clarity_score: float = Field(
        ge=0, le=1, description="Clareza da comunicação")
    examples_score: float = Field(
        ge=0, le=1, description="Uso de exemplos concretos")
    overall_score: float = Field(
        ge=0, le=1, description="Score final ponderado")
    strengths: List[str] = Field(default_factory=list, max_length=5)
    gaps: List[str] = Field(default_factory=list, max_length=5)
    feedback: str = Field(
        description="Feedback para o recrutador", max_length=800)


class FlowDecision(BaseModel):
    action: Literal["followup", "next_question", "end_interview", "handle_question"] = Field(
        description="Próxima ação"
    )
    reason: str = Field(description="Justificativa da decisão", max_length=300)
    followup_focus: Optional[str] = Field(None, max_length=300)


class CandidateMessage(BaseModel):
    acknowledgment: str = Field(
        description="Reconhecimento da resposta", max_length=200)
    transition: str = Field(description="Transição natural", max_length=150)
    next_content: str = Field(
        description="Próxima pergunta ou fechamento", max_length=500)
    full_message: str = Field(
        description="Mensagem completa formatada", max_length=800)


class NextQuestionHint(BaseModel):
    id: Optional[int] = None
    text: Optional[str] = None


class EvaluationStyle(BaseModel):
    persona: str = "cordial e profissional"
    pt_br: bool = True


class EvaluationDetails(BaseModel):
    relevance: Optional[float] = None
    depth: Optional[float] = None
    clarity: Optional[float] = None
    examples: Optional[float] = None
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


class AIResponse(BaseModel):
    score: float = 0.0
    is_answer_satisfactory: bool = False
    feedback_for_recruiter: str = ""
    chat_ack: str = ""
    responded: bool = False
    changed_subject: bool = False
    response_to_candidate: Optional[str] = None
    followup_needed: bool = False
    followup_question: Optional[str] = None
    next_question: Optional[NextQuestionHint] = None
    end: bool = False
    interested_job: bool = True
    interested_job_msg: Optional[str] = None
    evaluation_details: Optional[EvaluationDetails] = None


class EvaluationResponse(BaseModel):
    original_payload: dict
    ai_response: AIResponse
    chatbot_channel: str = "whatsapp"


class FinalAnalysisRequest(BaseModel):
    candidate_name: str
    candidate_id: int
    job_title: str
    job_id: int
    evaluation_id: int
    curriculum_text: Optional[str] = None
    answers: List[dict]


class FinalAnalysisResponse(BaseModel):
    status: str
    candidate_id: int
    candidate_name: str
    evaluation_id: int
    full_analysis: str
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendation: Literal["APPROVED",
                            "ADDITIONAL_ANALYSIS", "NOT_RECOMMENDED"]
    recommendation_justification: str
    next_steps: str
    processing_time_ms: float
    request_id: str

```

---

## 📄 src/domains/evaluation/processor.py

```python
import logging
from typing import Dict, Any

from src.domains.evaluation.state import create_initial_state
from src.domains.evaluation.graph import get_interview_graph
from src.domains.evaluation.models import (
    EvaluationResponse,
    AIResponse,
    EvaluationDetails,
    NextQuestionHint,
)

logger = logging.getLogger(__name__)


class EvaluationProcessor:

    def __init__(self):
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = get_interview_graph()
        return self._graph

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        thread_id = self._build_thread_id(payload)
        initial_state = create_initial_state(payload)

        logger.info(f"Processing evaluation: {thread_id}")

        final_state = self.graph.invoke(initial_state, thread_id)

        response = self._build_response(payload, final_state)

        logger.info(
            f"Evaluation complete: {thread_id}, score={response.ai_response.score:.2f}")

        return response.model_dump()

    def _build_thread_id(self, payload: dict) -> str:
        account_id = payload.get("account_id", "unknown")
        eval_cand_id = payload.get("evaluation_candidate_id", "unknown")
        message_id = payload.get("message_id", "unknown")
        return f"{account_id}-{eval_cand_id}-{message_id}"

    def _build_response(self, original_payload: dict, state: dict) -> EvaluationResponse:
        evaluation = state.get("evaluation")
        message = state.get("final_message")
        classification = state.get("classification")

        evaluation_details = None
        if evaluation:
            evaluation_details = EvaluationDetails(
                relevance=evaluation.relevance_score,
                depth=evaluation.depth_score,
                clarity=evaluation.clarity_score,
                examples=evaluation.examples_score,
                strengths=evaluation.strengths,
                gaps=evaluation.gaps,
            )

        next_question = state.get("next_question")
        next_q_hint = None
        if next_question:
            q_id = getattr(next_question, 'id', None) or (
                next_question.get('id') if isinstance(next_question, dict) else None)
            q_text = getattr(next_question, 'text', None) or (
                next_question.get('text') if isinstance(next_question, dict) else None)
            next_q_hint = NextQuestionHint(id=q_id, text=q_text)

        responded = False
        changed_subject = False
        if classification:
            responded = classification.intent == "answer"
            changed_subject = classification.intent == "off_topic"

        ai_response = AIResponse(
            score=state.get("final_score", 0.0),
            is_answer_satisfactory=state.get("is_satisfactory", False),
            feedback_for_recruiter=evaluation.feedback if evaluation else "",
            chat_ack=message.full_message if message else "",
            responded=responded,
            changed_subject=changed_subject,
            response_to_candidate=None,
            followup_needed=state.get("followup_needed", False),
            followup_question=state.get("followup_question"),
            next_question=next_q_hint,
            end=state.get("end_interview", False),
            interested_job=state.get("interested_job", True),
            interested_job_msg=None,
            evaluation_details=evaluation_details,
        )

        return EvaluationResponse(
            original_payload=original_payload,
            ai_response=ai_response,
            chatbot_channel=state.get("chatbot_channel", "whatsapp"),
        )


_processor = None


def get_processor() -> EvaluationProcessor:
    global _processor
    if _processor is None:
        _processor = EvaluationProcessor()
    return _processor

```

---

## 📄 src/domains/evaluation/tasks.py

```python
import logging
import time
import json
from typing import Dict, Any, Optional

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from src.domains.evaluation.processor import get_processor
from src.domains.evaluation.final_analysis import get_final_analysis_service
from src.domains.evaluation.models import FinalAnalysisRequest

logger = logging.getLogger(__name__)


@shared_task
def test_simple():
    """Simple test task to verify worker is processing."""
    logger.info("🧪 TEST TASK EXECUTED!")
    return {"status": "success", "message": "Worker is alive!"}


def _correlation_id(payload: dict) -> str:
    acc = payload.get("account_id", "acc?")
    ec = payload.get("evaluation_candidate_id", "ec?")
    mid = payload.get("message_id", "msg?")
    return f"acc-{acc}|ec-{ec}|msg-{mid}"


@shared_task(
    bind=True,
    name="src.domains.evaluation.tasks.process_evaluation",
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_evaluation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    correlation = _correlation_id(payload)
    start_time = time.time()

    logger.info(
        f"[{correlation}] Starting evaluation task (attempt {self.request.retries + 1})")

    try:
        processor = get_processor()
        result = processor.process(payload)

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"[{correlation}] Completed in {elapsed:.0f}ms")

        return result

    except SoftTimeLimitExceeded:
        logger.error(f"[{correlation}] Task soft time limit exceeded")
        return _build_error_response(payload, "Tempo limite excedido")

    except Exception as e:
        logger.error(f"[{correlation}] Task error: {e}", exc_info=True)
        raise


@shared_task(
    bind=True,
    name="src.domains.evaluation.tasks.process_evaluation_batch",
    max_retries=2,
    acks_late=True,
)
def process_evaluation_batch(self, payloads: list) -> list:
    logger.info(f"Processing batch of {len(payloads)} evaluations")

    results = []
    for payload in payloads:
        try:
            result = process_evaluation.delay(payload)
            results.append({"task_id": result.id, "status": "queued"})
        except Exception as e:
            correlation = _correlation_id(payload)
            logger.error(f"[{correlation}] Failed to queue: {e}")
            results.append({"error": str(e), "status": "failed"})

    return results


@shared_task(
    bind=True,
    name="src.domains.evaluation.tasks.process_final_analysis",
    max_retries=2,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    acks_late=True,
)
def process_final_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
    candidate_id = data.get("candidate_id", "unknown")
    evaluation_id = data.get("evaluation_id", "unknown")
    start_time = time.time()

    logger.info(
        f"Starting final analysis for candidate {candidate_id}, evaluation {evaluation_id}")

    try:
        request = FinalAnalysisRequest(
            candidate_name=data.get("candidate_name", ""),
            candidate_id=data.get("candidate_id", 0),
            job_title=data.get("job_title", ""),
            job_id=data.get("job_id", 0),
            evaluation_id=data.get("evaluation_id", 0),
            curriculum_text=data.get("curriculum_text"),
            answers=data.get("answers", []),
        )

        service = get_final_analysis_service()
        response = service.analyze(request)

        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Final analysis completed in {elapsed:.0f}ms")

        return response.model_dump()

    except SoftTimeLimitExceeded:
        logger.error(
            f"Final analysis time limit exceeded for candidate {candidate_id}")
        return {"status": "error", "error": "Tempo limite excedido"}

    except Exception as e:
        logger.error(f"Final analysis error: {e}", exc_info=True)
        raise


@shared_task(
    name="src.domains.evaluation.tasks.publish_evaluation_response",
    max_retries=5,
    default_retry_delay=2,
)
def publish_evaluation_response(response: Dict[str, Any], callback_url: Optional[str] = None):
    import pika
    from src.config.settings import get_settings
    from src.config.evaluation_config import get_evaluation_config

    config = get_evaluation_config()
    settings = get_settings()

    try:
        params = pika.URLParameters(settings.rabbitmq.url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.basic_publish(
            exchange=config.rabbitmq.exchange,
            routing_key=config.rabbitmq.routing_key_out,
            body=json.dumps(response, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )

        connection.close()
        logger.info("Published evaluation response to RabbitMQ")

    except Exception as e:
        logger.error(f"Failed to publish response: {e}")
        raise


@shared_task(
    bind=True,
    name="src.domains.evaluation.tasks.process_and_publish",
    max_retries=3,
    acks_late=True,
)
def process_and_publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    correlation = _correlation_id(payload)

    try:
        processor = get_processor()
        result = processor.process(payload)

        publish_evaluation_response.delay(result)

        logger.info(f"[{correlation}] Processed and queued for publishing")
        return {"status": "success", "correlation": correlation}

    except Exception as e:
        logger.error(f"[{correlation}] Process and publish error: {e}")
        raise


@shared_task(
    bind=True,
    name="src.domains.evaluation.tasks.evaluate_candidate_with_service",
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def evaluate_candidate_with_service(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Evaluate candidate response using EvaluationService (Gemini direct).
    This task replicates the behavior of the original evaluation_worker.py.
    """
    from src.services.evaluation_service import EvaluationService
    
    # Build correlation ID for logging
    acc = payload.get("account_id", "acc?")
    ec = payload.get("evaluation_candidate_id", "ec?")
    mid = payload.get("message_id", "msg?")
    correlation_id = f"acc-{acc}|ec-{ec}|msg-{mid}"
    
    start_time = time.time()
    
    logger.info(
        f"📦 [{correlation_id}] Processing evaluation with EvaluationService "
        f"(attempt {self.request.retries + 1})"
    )
    logger.debug(f"📦 [{correlation_id}] Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        # Initialize service and evaluate
        evaluation_service = EvaluationService()
        result = evaluation_service.evaluate_candidate_response(payload)
        
        if result:
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"✅ [{correlation_id}] Evaluation completed in {elapsed:.0f}ms")
            logger.debug(f"🚀 [{correlation_id}] Result: {json.dumps(result, ensure_ascii=False)}")
            return result
        else:
            logger.error(f"❌ [{correlation_id}] Evaluation returned None")
            return None
            
    except SoftTimeLimitExceeded:
        logger.error(f"❌ [{correlation_id}] Task soft time limit exceeded")
        return _build_error_response(payload, "Tempo limite excedido")
        
    except Exception as e:
        logger.error(f"❌ [{correlation_id}] Error processing evaluation: {e}", exc_info=True)
        raise


@shared_task(
    bind=True,
    name="src.domains.evaluation.tasks.consume_and_evaluate",
    max_retries=3,
    acks_late=True,
    reject_on_worker_lost=True,
)
def consume_and_evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process evaluation request from RabbitMQ queue and publish result.
    This is the main entry point for RabbitMQ consumer integration.
    """
    import pika
    from src.config.settings import get_settings
    
    # Build correlation ID
    acc = payload.get("account_id", "acc?")
    ec = payload.get("evaluation_candidate_id", "ec?")
    mid = payload.get("message_id", "msg?")
    correlation_id = f"acc-{acc}|ec-{ec}|msg-{mid}"
    
    try:
        # Evaluate using service
        result = evaluate_candidate_with_service(payload)
        
        if not result:
            logger.error(f"❌ [{correlation_id}] No result from evaluation")
            return {"status": "error", "correlation_id": correlation_id}
        
        # Publish result to output queue
        settings = get_settings()
        eval_exchange = settings.rabbitmq.evaluation_exchange or "evaluations_exchange"
        eval_queue_out = settings.rabbitmq.evaluation_queue_out or "evaluation_responses"
        eval_routing_out = settings.rabbitmq.evaluation_routing_out or "evaluation_response"
        
        try:
            params = pika.URLParameters(settings.rabbitmq.url)
            params.heartbeat = 60
            params.blocked_connection_timeout = 300
            params.socket_timeout = 30
            
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            
            # Declare exchange and queue
            channel.exchange_declare(
                exchange=eval_exchange,
                exchange_type="direct",
                durable=True
            )
            channel.queue_declare(queue=eval_queue_out, durable=True)
            channel.queue_bind(
                exchange=eval_exchange,
                queue=eval_queue_out,
                routing_key=eval_routing_out
            )
            
            # Publish result
            channel.basic_publish(
                exchange=eval_exchange,
                routing_key=eval_routing_out,
                body=json.dumps(result, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type="application/json",
                    correlation_id=correlation_id
                )
            )
            
            connection.close()
            logger.info(f"✅ [{correlation_id}] Result published to {eval_queue_out}")
            
        except Exception as e:
            logger.error(f"❌ [{correlation_id}] Failed to publish result: {e}")
            raise
        
        return {"status": "success", "correlation_id": correlation_id}
        
    except Exception as e:
        logger.error(f"❌ [{correlation_id}] Error in consume_and_evaluate: {e}", exc_info=True)
        raise


def _build_error_response(payload: dict, error_msg: str) -> dict:
    return {
        "original_payload": payload,
        "ai_response": {
            "score": 0.0,
            "is_answer_satisfactory": False,
            "feedback_for_recruiter": f"Erro no processamento: {error_msg}",
            "chat_ack": "Desculpe, houve um problema técnico. Pode repetir sua resposta?",
            "responded": False,
            "changed_subject": False,
            "response_to_candidate": None,
            "followup_needed": True,
            "followup_question": "Pode repetir sua resposta, por favor?",
            "next_question": None,
            "end": False,
            "interested_job": True,
            "interested_job_msg": None,
            "evaluation_details": None,
        },
        "chatbot_channel": payload.get("chatbot_channel", "whatsapp"),
    }

```

---

## 📄 src/domains/evaluation/worker.py

```python
import json
import logging
import time
import signal
import sys
from typing import Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.config.settings import get_settings
from src.config.evaluation_config import get_evaluation_config
from src.domains.evaluation.processor import get_processor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


class EvaluationWorker:

    def __init__(self):
        self._settings = get_settings()
        self._config = get_evaluation_config()
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None
        self._processor = get_processor()
        self._running = False

    def _correlation_id(self, payload: dict) -> str:
        acc = payload.get("account_id", "acc?")
        ec = payload.get("evaluation_candidate_id", "ec?")
        mid = payload.get("message_id", "msg?")
        return f"acc-{acc}|ec-{ec}|msg-{mid}"

    def _connect(self) -> None:
        params = pika.URLParameters(self._settings.rabbitmq.url)
        params.heartbeat = 600
        params.blocked_connection_timeout = 300

        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()

        self._channel.exchange_declare(
            exchange=self._config.rabbitmq.exchange,
            exchange_type="direct",
            durable=True,
        )

        self._channel.queue_declare(
            queue=self._config.rabbitmq.queue_in,
            durable=True,
        )
        self._channel.queue_declare(
            queue=self._config.rabbitmq.queue_out,
            durable=True,
        )

        self._channel.queue_bind(
            exchange=self._config.rabbitmq.exchange,
            queue=self._config.rabbitmq.queue_in,
            routing_key=self._config.rabbitmq.routing_key_in,
        )
        self._channel.queue_bind(
            exchange=self._config.rabbitmq.exchange,
            queue=self._config.rabbitmq.queue_out,
            routing_key=self._config.rabbitmq.routing_key_out,
        )

        self._channel.basic_qos(
            prefetch_count=self._config.rabbitmq.prefetch_count)

        logger.info("Connected to RabbitMQ")

    def _publish_response(self, response: dict) -> None:
        if not self._channel:
            raise RuntimeError("Channel not initialized")

        self._channel.basic_publish(
            exchange=self._config.rabbitmq.exchange,
            routing_key=self._config.rabbitmq.routing_key_out,
            body=json.dumps(response, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )

    def _process_with_retry(self, payload: dict) -> dict:
        correlation = self._correlation_id(payload)
        last_error = None

        for attempt in range(1, self._config.max_retries + 1):
            try:
                return self._processor.process(payload)

            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{correlation}] Attempt {attempt}/{self._config.max_retries} failed: {e}"
                )

                if attempt < self._config.max_retries:
                    backoff = self._config.initial_backoff * \
                        (2 ** (attempt - 1))
                    time.sleep(backoff)

        logger.error(f"[{correlation}] All retries exhausted: {last_error}")
        return self._build_error_response(payload, str(last_error))

    def _build_error_response(self, payload: dict, error_msg: str) -> dict:
        return {
            "original_payload": payload,
            "ai_response": {
                "score": 0.0,
                "is_answer_satisfactory": False,
                "feedback_for_recruiter": f"Erro no processamento: {error_msg}",
                "chat_ack": "Desculpe, houve um problema técnico. Pode repetir sua resposta?",
                "responded": False,
                "changed_subject": False,
                "response_to_candidate": None,
                "followup_needed": True,
                "followup_question": "Pode repetir sua resposta, por favor?",
                "next_question": None,
                "end": False,
                "interested_job": True,
                "interested_job_msg": None,
                "evaluation_details": None,
            },
            "chatbot_channel": payload.get("chatbot_channel", "whatsapp"),
        }

    def _callback(
        self,
        ch: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        start_time = time.time()

        try:
            payload = json.loads(body.decode("utf-8"))
            correlation = self._correlation_id(payload)
            logger.info(f"[{correlation}] Processing message")

            response = self._process_with_retry(payload)
            self._publish_response(response)

            elapsed = (time.time() - start_time) * 1000
            logger.info(f"[{correlation}] Completed in {elapsed:.0f}ms")

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(
                f"Unexpected error processing message: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _shutdown(self, signum, frame) -> None:
        logger.info("Shutdown signal received")
        self._running = False

        if self._channel:
            self._channel.stop_consuming()

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        self._running = True

        while self._running:
            try:
                self._connect()

                self._channel.basic_consume(
                    queue=self._config.rabbitmq.queue_in,
                    on_message_callback=self._callback,
                    auto_ack=False,
                )

                logger.info(
                    f"Consuming from {self._config.rabbitmq.queue_in}, "
                    f"publishing to {self._config.rabbitmq.queue_out}"
                )

                self._channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"RabbitMQ connection error: {e}")
                if self._running:
                    logger.info("Reconnecting in 5 seconds...")
                    time.sleep(5)

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                if self._running:
                    time.sleep(5)

            finally:
                if self._connection and not self._connection.is_closed:
                    try:
                        self._connection.close()
                    except Exception:
                        pass

        logger.info("Worker stopped")


def main():
    if not get_evaluation_config().enabled:
        logger.info("Evaluation worker is disabled")
        sys.exit(0)

    worker = EvaluationWorker()
    worker.run()


if __name__ == "__main__":
    main()

```

---

## 📄 src/domains/evaluation/final_analysis.py

```python
import logging
import time
import uuid
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from src.config.settings import get_settings
from src.domains.evaluation.models import FinalAnalysisRequest, FinalAnalysisResponse
from src.domains.evaluation.prompts import FINAL_ANALYSIS_PROMPT
from src.domains.evaluation.security import sanitize_input, escape_for_prompt

logger = logging.getLogger(__name__)


class FinalAnalysisService:

    def __init__(self):
        self._settings = get_settings()
        self._llm = None

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=self._settings.gemini.model,
                temperature=0.3,
                google_api_key=self._settings.gemini.api_key,
            )
        return self._llm

    def analyze(self, request: FinalAnalysisRequest) -> FinalAnalysisResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())

        logger.info(
            f"Starting final analysis for candidate {request.candidate_id}, "
            f"evaluation {request.evaluation_id}"
        )

        answers_summary = self._format_answers(request.answers)
        curriculum = sanitize_input(
            request.curriculum_text or "Não disponível")

        prompt = ChatPromptTemplate.from_messages([
            ("system", FINAL_ANALYSIS_PROMPT),
            ("human", "Gere a análise completa do candidato."),
        ])

        try:
            response = (prompt | self.llm).invoke({
                "candidate_name": escape_for_prompt(request.candidate_name),
                "job_title": escape_for_prompt(request.job_title),
                "curriculum": escape_for_prompt(curriculum),
                "answers_summary": answers_summary,
            })

            parsed = self._parse_analysis(response.content)

            processing_time = (time.time() - start_time) * 1000

            return FinalAnalysisResponse(
                status="success",
                candidate_id=request.candidate_id,
                candidate_name=request.candidate_name,
                evaluation_id=request.evaluation_id,
                full_analysis=parsed["full_analysis"],
                summary=parsed["summary"],
                strengths=parsed["strengths"],
                weaknesses=parsed["weaknesses"],
                recommendation=parsed["recommendation"],
                recommendation_justification=parsed["justification"],
                next_steps=parsed["next_steps"],
                processing_time_ms=processing_time,
                request_id=request_id,
            )

        except Exception as e:
            logger.error(f"Final analysis error: {e}", exc_info=True)
            processing_time = (time.time() - start_time) * 1000

            return FinalAnalysisResponse(
                status="error",
                candidate_id=request.candidate_id,
                candidate_name=request.candidate_name,
                evaluation_id=request.evaluation_id,
                full_analysis=f"Erro ao gerar análise: {str(e)}",
                summary="Análise não disponível devido a erro técnico",
                strengths=[],
                weaknesses=[],
                recommendation="ADDITIONAL_ANALYSIS",
                recommendation_justification="Recomendação padrão devido a erro no processamento",
                next_steps="Realizar análise manual do candidato",
                processing_time_ms=processing_time,
                request_id=request_id,
            )

    def _format_answers(self, answers: List[dict]) -> str:
        formatted = []

        for idx, answer in enumerate(answers, 1):
            title = sanitize_input(answer.get("title", f"Pergunta {idx}"))
            description = sanitize_input(
                answer.get("description", "Sem resposta"))

            comments = answer.get("comments_response", "{}")
            score_info = self._extract_score_info(comments)

            formatted.append(
                f"**Pergunta {idx}: {title}**\n"
                f"Resposta: {description}\n"
                f"{score_info}\n"
            )

        return "\n".join(formatted)

    def _extract_score_info(self, comments_json: str) -> str:
        try:
            import json
            data = json.loads(comments_json) if isinstance(
                comments_json, str) else comments_json

            score = data.get("score", 0)
            satisfactory = data.get("is_answer_satisfactory", False)
            feedback = data.get("feedback_for_recruiter", "")

            return (
                f"Score: {score:.2f} | "
                f"Satisfatória: {'Sim' if satisfactory else 'Não'}\n"
                f"Feedback: {feedback}"
            )
        except Exception:
            return "Score: N/A"

    def _parse_analysis(self, content: str) -> dict:
        lines = content.strip().split("\n")

        result = {
            "full_analysis": content,
            "summary": "",
            "strengths": [],
            "weaknesses": [],
            "recommendation": "ADDITIONAL_ANALYSIS",
            "justification": "",
            "next_steps": "",
        }

        current_section = None
        section_content = []

        for line in lines:
            line_lower = line.lower().strip()

            if "resumo" in line_lower and "executivo" in line_lower:
                if current_section and section_content:
                    result[current_section] = self._finalize_section(
                        current_section, section_content)
                current_section = "summary"
                section_content = []
                continue

            if "pontos fortes" in line_lower or "strengths" in line_lower:
                if current_section and section_content:
                    result[current_section] = self._finalize_section(
                        current_section, section_content)
                current_section = "strengths"
                section_content = []
                continue

            if "pontos de atenção" in line_lower or "weaknesses" in line_lower or "pontos fracos" in line_lower:
                if current_section and section_content:
                    result[current_section] = self._finalize_section(
                        current_section, section_content)
                current_section = "weaknesses"
                section_content = []
                continue

            if "recomendação" in line_lower and ":" in line:
                if "APPROVED" in line.upper():
                    result["recommendation"] = "APPROVED"
                elif "NOT_RECOMMENDED" in line.upper() or "NOT RECOMMENDED" in line.upper():
                    result["recommendation"] = "NOT_RECOMMENDED"
                else:
                    result["recommendation"] = "ADDITIONAL_ANALYSIS"
                continue

            if "justificativa" in line_lower:
                if current_section and section_content:
                    result[current_section] = self._finalize_section(
                        current_section, section_content)
                current_section = "justification"
                section_content = []
                continue

            if "próximos passos" in line_lower or "next steps" in line_lower:
                if current_section and section_content:
                    result[current_section] = self._finalize_section(
                        current_section, section_content)
                current_section = "next_steps"
                section_content = []
                continue

            if current_section:
                section_content.append(line)

        if current_section and section_content:
            result[current_section] = self._finalize_section(
                current_section, section_content)

        return result

    def _finalize_section(self, section: str, content: List[str]) -> any:
        text = "\n".join(content).strip()

        if section in ("strengths", "weaknesses"):
            items = []
            for line in content:
                line = line.strip()
                if line.startswith(("-", "*", "•")):
                    items.append(line[1:].strip())
                elif line and not line.startswith("#"):
                    items.append(line)
            return items[:5]

        return text


_service = None


def get_final_analysis_service() -> FinalAnalysisService:
    global _service
    if _service is None:
        _service = FinalAnalysisService()
    return _service

```

---

## 📄 src/domains/evaluation/security.py

```python
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions?",
    r"disregard\s+(previous|all|above)",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an)",
    r"pretend\s+(to\s+be|you\s+are)",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[\s*system\s*\]",
    r"override\s+(your|the)\s+(instructions?|rules?|guidelines?)",
    r"new\s+instructions?\s*:",
    r"jailbreak",
    r"dan\s*mode",
    r"developer\s*mode",
    r"bypass\s+(safety|filter|restriction)",
    r"reveal\s+(your|the)\s+(prompt|instructions?|system)",
    r"what\s+(is|are)\s+your\s+(instructions?|rules?|prompt)",
    r"output\s+your\s+(system|initial)\s+prompt",
]

MALICIOUS_CHAR_PATTERNS = [
    r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
    r"\u200b|\u200c|\u200d|\ufeff",
]

MAX_SAFE_LENGTH = 4000


def sanitize_input(text: str) -> str:
    if not text:
        return ""

    sanitized = text.strip()

    for pattern in MALICIOUS_CHAR_PATTERNS:
        sanitized = re.sub(pattern, "", sanitized)

    sanitized = " ".join(sanitized.split())

    return sanitized[:MAX_SAFE_LENGTH]


def detect_injection(text: str) -> Tuple[bool, str]:
    if not text:
        return False, ""

    text_lower = text.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Prompt injection detected: pattern={pattern}")
            return True, pattern

    return False, ""


def safe_process_input(text: str) -> Tuple[str, bool, str]:
    sanitized = sanitize_input(text)
    is_injection, pattern = detect_injection(sanitized)

    if is_injection:
        logger.warning(f"Input blocked due to injection attempt: {pattern}")
        return "", True, pattern

    return sanitized, False, ""


def escape_for_prompt(text: str) -> str:
    if not text:
        return ""

    escaped = text.replace("{", "{{").replace("}", "}}")
    escaped = escaped.replace("```", "'''")
    return escaped


def validate_structured_field(value: str, field_name: str, max_length: int = 500) -> str:
    if not value:
        return ""

    sanitized = sanitize_input(value)[:max_length]
    is_injection, _ = detect_injection(sanitized)

    if is_injection:
        logger.warning(
            f"Injection in structured field {field_name}, returning empty")
        return ""

    return sanitized


def create_safe_context(
    job_description: str,
    question_text: str,
    expected_response: str,
    candidate_answer: str,
) -> dict:
    return {
        "job_description": escape_for_prompt(sanitize_input(job_description)),
        "question_text": escape_for_prompt(sanitize_input(question_text)),
        "expected_response": escape_for_prompt(sanitize_input(expected_response)),
        "candidate_answer": escape_for_prompt(sanitize_input(candidate_answer)),
    }

```

---

## 📄 src/domains/evaluation/api.py

```python
import logging
from typing import Dict, Any

from src.domains.evaluation.models import FinalAnalysisRequest, FinalAnalysisResponse
from src.domains.evaluation.final_analysis import get_final_analysis_service
from src.domains.evaluation.processor import get_processor

logger = logging.getLogger(__name__)


def process_evaluation_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    processor = get_processor()
    return processor.process(payload)


def process_final_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    request = FinalAnalysisRequest(
        candidate_name=data.get("candidate_name", ""),
        candidate_id=data.get("candidate_id", 0),
        job_title=data.get("job_title", ""),
        job_id=data.get("job_id", 0),
        evaluation_id=data.get("evaluation_id", 0),
        curriculum_text=data.get("curriculum_text"),
        answers=data.get("answers", []),
    )

    service = get_final_analysis_service()
    response = service.analyze(request)

    return response.model_dump()


def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "evaluation",
    }

```

---

## 📄 src/domains/evaluation/dispatcher.py

```python
import json
import logging
import signal
import sys
from typing import Optional

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.config.settings import get_settings
from src.config.evaluation_config import get_evaluation_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


class EvaluationDispatcher:

    def __init__(self):
        self._settings = get_settings()
        self._config = get_evaluation_config()
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[BlockingChannel] = None
        self._running = False

    def _connect(self) -> None:
        params = pika.URLParameters(self._settings.rabbitmq.url)
        params.heartbeat = 600
        params.blocked_connection_timeout = 300

        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()

        self._channel.exchange_declare(
            exchange=self._config.rabbitmq.exchange,
            exchange_type="direct",
            durable=True,
        )

        self._channel.queue_declare(
            queue=self._config.rabbitmq.queue_in,
            durable=True,
        )

        self._channel.queue_bind(
            exchange=self._config.rabbitmq.exchange,
            queue=self._config.rabbitmq.queue_in,
            routing_key=self._config.rabbitmq.routing_key_in,
        )

        self._channel.basic_qos(
            prefetch_count=self._config.rabbitmq.prefetch_count)

        logger.info("Dispatcher connected to RabbitMQ")

    def _callback(
        self,
        ch: BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        from src.domains.evaluation.tasks import process_and_publish

        try:
            payload = json.loads(body.decode("utf-8"))
            correlation = self._correlation_id(payload)

            logger.info(f"[{correlation}] Dispatching to Celery")

            process_and_publish.delay(payload)

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"[{correlation}] Dispatched successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Dispatch error: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _correlation_id(self, payload: dict) -> str:
        acc = payload.get("account_id", "acc?")
        ec = payload.get("evaluation_candidate_id", "ec?")
        mid = payload.get("message_id", "msg?")
        return f"acc-{acc}|ec-{ec}|msg-{mid}"

    def _shutdown(self, signum, frame) -> None:
        logger.info("Shutdown signal received")
        self._running = False
        if self._channel:
            self._channel.stop_consuming()

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        self._running = True

        while self._running:
            try:
                self._connect()

                self._channel.basic_consume(
                    queue=self._config.rabbitmq.queue_in,
                    on_message_callback=self._callback,
                    auto_ack=False,
                )

                logger.info(
                    f"Dispatching from {self._config.rabbitmq.queue_in} to Celery")
                self._channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"RabbitMQ connection error: {e}")
                if self._running:
                    import time
                    time.sleep(5)

            except Exception as e:
                logger.error(f"Dispatcher error: {e}", exc_info=True)
                if self._running:
                    import time
                    time.sleep(5)

            finally:
                if self._connection and not self._connection.is_closed:
                    try:
                        self._connection.close()
                    except Exception:
                        pass

        logger.info("Dispatcher stopped")


def main():
    if not get_evaluation_config().enabled:
        logger.info("Evaluation dispatcher is disabled")
        sys.exit(0)

    dispatcher = EvaluationDispatcher()
    dispatcher.run()


if __name__ == "__main__":
    main()

```

---



# RECRUITER_AGENT_V5 — Part 4: Sourced Profile Sourcing Domain

---

## 📄 src/domains/sourced_profile_sourcing/__init__.py

```python
from src.domains.sourced_profile_sourcing.domain import SourcedProfileSourcingDomain
from src.domains.sourced_profile_sourcing.tasks import (
    process_query,
    process_query_with_callback,
    batch_process_queries,
    refresh_aggregated_stats,
)
from src.domains.sourced_profile_sourcing.dispatcher import (
    SourcingDispatcher,
    run_sourcing_dispatcher,
)

__all__ = [
    "SourcedProfileSourcingDomain",
    "process_query",
    "process_query_with_callback",
    "batch_process_queries",
    "refresh_aggregated_stats",
    "SourcingDispatcher",
    "run_sourcing_dispatcher",
]

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/__init__.py

```python
import warnings
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id
from src.domains.sourced_profile_sourcing.actions.count import CountActions
from src.domains.sourced_profile_sourcing.actions.score import ScoreActions
from src.domains.sourced_profile_sourcing.actions.distribution import DistributionActions
from src.domains.sourced_profile_sourcing.actions.analysis import AnalysisActions
from src.domains.sourced_profile_sourcing.actions.search import SearchActions
from src.domains.sourced_profile_sourcing.actions.details import DetailActions
from src.domains.sourced_profile_sourcing.actions.comparison import ComparisonActions
from src.domains.sourced_profile_sourcing.actions.report import ReportActions
from src.domains.sourced_profile_sourcing.actions.search_improvement import SearchImprovementActions
from src.domains.sourced_profile_sourcing.actions.insights import InsightsActions

warnings.warn(
    "src.domains.sourced_profile_sourcing.actions is deprecated. "
    "Use src.domains.sourced_profile_sourcing.api_operations for API operations "
    "and agents/ for LLM-powered orchestration.",
    DeprecationWarning,
    stacklevel=2
)


class SourcedProfileSourcingActions(
    InsightsActions,
    SearchImprovementActions,
    ReportActions,
    ComparisonActions,
    DetailActions,
    SearchActions,
    CountActions,
    ScoreActions,
    DistributionActions,
    AnalysisActions
):
    pass

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/base.py

```python
from typing import Dict, Any, List, Optional
from functools import wraps
from collections import Counter
import logging

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.api_client import SourcingAPIClient

logger = logging.getLogger(__name__)


def require_sourcing_id(func):
    @wraps(func)
    def wrapper(self, params: Dict[str, Any], context: DomainContext, aggregated_stats: Optional[Dict[str, Any]] = None) -> DomainResponse:
        if not context.sourcing_id:
            return DomainResponse(
                success=False,
                message="❌ sourcing_id é obrigatório para esta operação",
                error="missing_sourcing_id"
            )
        return func(self, params, context, aggregated_stats)
    return wrapper


class BaseAction:

    def get_api_client(self, context: DomainContext = None) -> SourcingAPIClient:
        return SourcingAPIClient(context)

    def _apply_filter(self, data: List[Dict], filter_spec: Dict) -> List[Dict]:
        result = data

        for field, condition in filter_spec.items():
            if isinstance(condition, dict):
                if "gte" in condition:
                    result = [d for d in result if (
                        d.get(field) or 0) >= condition["gte"]]
                if "lte" in condition:
                    result = [d for d in result if (
                        d.get(field) or 0) <= condition["lte"]]
                if "eq" in condition:
                    result = [d for d in result if d.get(
                        field) == condition["eq"]]
                if "ilike" in condition:
                    pattern = condition["ilike"].replace("%", "").lower()
                    result = [d for d in result if pattern in str(
                        d.get(field, "")).lower()]
            else:
                result = [d for d in result if d.get(field) == condition]

        return result

    def _describe_filter(self, filter_spec: Dict) -> str:
        parts = []

        for field, condition in filter_spec.items():
            if isinstance(condition, dict):
                if "gte" in condition:
                    parts.append(f"com {field} ≥ {condition['gte']}")
                if "lte" in condition:
                    parts.append(f"com {field} ≤ {condition['lte']}")
                if "ilike" in condition:
                    parts.append(
                        f"contendo '{condition['ilike'].replace('%', '')}'")
            else:
                parts.append(f"com {field} = {condition}")

        return " e ".join(parts) if parts else ""

    def _extract_list_items(self, items: List, name_key: str = "name", count_key: str = "count") -> List[tuple]:
        result = []
        for item in items:
            if isinstance(item, dict):
                result.append(
                    (item.get(name_key, "N/A"), item.get(count_key, 0)))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                result.append((item[0], item[1]))
        return result

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/analysis.py

```python
from typing import Dict, Any, Optional
from collections import Counter

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id


class AnalysisActions(BaseAction):

    @require_sourcing_id
    def analyze_skills(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._skills_from_aggregated(stats=aggregated_stats)
        return self._skills_from_local(context)

    def _skills_from_aggregated(self, stats: Dict) -> DomainResponse:
        skills_dist = stats.get("skills_distribution", {})
        top_skills = skills_dist.get("top_skills", {})
        unique_count = skills_dist.get("unique_count", 0)

        if not top_skills:
            return DomainResponse(success=True, message="⚠️ Dados de skills não disponíveis", data={"skills": []})

        if isinstance(top_skills, dict):
            sorted_skills = sorted(
                top_skills.items(), key=lambda x: x[1], reverse=True)[:15]
        else:
            sorted_skills = [(item.get("name", "N/A"), item.get("count", 0))
                             for item in top_skills[:15]]

        lines = ["🛠️ **Skills mais comuns**\n"]
        if unique_count:
            lines.append(f"*{unique_count} skills únicas identificadas*\n")
        lines.extend(["| Skill | Candidatos |", "|-------|------------|"])

        for name, count in sorted_skills:
            lines.append(f"| {name.title()} | {count} |")

        return DomainResponse(success=True, message="\n".join(lines), data=skills_dist, suggestions=["Quem tem Python?", "Distribuição por cidade"])

    def _skills_from_local(self, context: DomainContext) -> DomainResponse:
        all_skills = []
        for c in context.current_data:
            for s in (c.get("skills_data") or c.get("skills") or []):
                if isinstance(s, dict):
                    all_skills.append(s.get("name", "").lower())
                elif isinstance(s, str):
                    all_skills.append(s.lower())

        if not all_skills:
            return DomainResponse(success=True, message="⚠️ Dados de skills não disponíveis", data={"skills": []})

        skill_counts = Counter(all_skills).most_common(15)
        lines = ["🛠️ **Skills mais comuns**\n",
                 "| Skill | Candidatos |", "|-------|------------|"]
        for skill, count in skill_counts:
            lines.append(f"| {skill.title()} | {count} |")

        return DomainResponse(success=True, message="\n".join(lines), data={"skills": skill_counts}, suggestions=["Quem tem Python?", "Distribuição por cidade"])

    @require_sourcing_id
    def average_experience(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._experience_from_aggregated(stats=aggregated_stats)
        return self._experience_from_local(context)

    def _experience_from_aggregated(self, stats: Dict) -> DomainResponse:
        exp_stats = stats.get("experience_stats", {})
        avg = exp_stats.get("average")

        if avg is None:
            return DomainResponse(success=True, message="⚠️ Dados de experiência não disponíveis", data={"average": None})

        lines = [f"📊 **Experiência média: {avg:.1f} anos**"]
        if median := exp_stats.get("median"):
            lines.append(f"• Mediana: {median:.1f} anos")

        if distribution := exp_stats.get("distribution", {}):
            lines.append("\n**Distribuição:**")
            for range_name, count in distribution.items():
                if count:
                    lines.append(f"• {range_name}: {count}")

        return DomainResponse(success=True, message="\n".join(lines), data=exp_stats, suggestions=["Quantos com mais de 5 anos?", "Distribuição de seniority"])

    def _experience_from_local(self, context: DomainContext) -> DomainResponse:
        experiences = [c.get("total_experience_years", 0) for c in context.current_data if c.get(
            "total_experience_years") is not None]

        if not experiences:
            return DomainResponse(success=True, message="⚠️ Dados de experiência não disponíveis", data={"average": None})

        avg = sum(experiences) / len(experiences)
        return DomainResponse(
            success=True,
            message=f"📊 **Experiência média: {avg:.1f} anos** (de {len(experiences)} candidatos)",
            data={"average": avg, "count": len(experiences), "min": min(
                experiences), "max": max(experiences)},
            suggestions=["Quantos com mais de 5 anos?",
                         "Distribuição de seniority"]
        )

    @require_sourcing_id
    def average_salary_expectation(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._salary_from_aggregated(stats=aggregated_stats)
        return self._salary_from_local(context)

    def _salary_from_aggregated(self, stats: Dict) -> DomainResponse:
        salary_stats = stats.get("salary_stats", {})
        clt = salary_stats.get("clt", {})
        pj = salary_stats.get("pj", {})

        if not clt and not pj:
            return DomainResponse(success=True, message="⚠️ Dados de pretensão salarial não disponíveis", data={"average": None})

        lines = ["💰 **Pretensão Salarial**\n"]

        if avg_clt := clt.get("average"):
            lines.append("**CLT:**")
            lines.append(f"• Média: R$ {avg_clt:,.2f}")
            if median_clt := clt.get("median"):
                lines.append(f"• Mediana: R$ {median_clt:,.2f}")
            lines.append("")

        if avg_pj := pj.get("average"):
            lines.append("**PJ:**")
            lines.append(f"• Média: R$ {avg_pj:,.2f}")

        return DomainResponse(success=True, message="\n".join(lines), data=salary_stats, suggestions=["Quantos abaixo de R$ 10.000?", "Distribuição salarial"])

    def _salary_from_local(self, context: DomainContext) -> DomainResponse:
        salaries = [c.get("salary_expectation", 0) for c in context.current_data if c.get(
            "salary_expectation") and c.get("salary_expectation") > 0]

        if not salaries:
            return DomainResponse(success=True, message="⚠️ Dados de pretensão salarial não disponíveis ou campo não existe", data={"average": None}, suggestions=["Verifique se o campo 'salary_expectation' existe no banco de dados"])

        avg = sum(salaries) / len(salaries)
        return DomainResponse(
            success=True,
            message=f"💰 **Pretensão salarial média: R$ {avg:,.2f}** (de {len(salaries)} candidatos)\n\n• Mínimo: R$ {min(salaries):,.2f}\n• Máximo: R$ {max(salaries):,.2f}",
            data={"average": avg, "count": len(salaries), "min": min(
                salaries), "max": max(salaries)},
            suggestions=["Quantos abaixo de R$ 10.000?",
                         "Distribuição salarial"]
        )

    @require_sourcing_id
    def diversity_analysis(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._diversity_from_aggregated(stats=aggregated_stats)
        return self._diversity_from_local(context)

    def _diversity_from_aggregated(self, stats: Dict) -> DomainResponse:
        diversity = stats.get("diversity_stats", {})
        by_gender = diversity.get("by_gender", {})
        by_ethnicity = diversity.get("by_ethnicity", {})
        pcds = diversity.get("pcds", 0)
        total = stats.get("counts", {}).get("total", 0)

        if not any([by_gender, by_ethnicity, pcds]):
            return DomainResponse(success=True, message="⚠️ Dados de diversidade não disponíveis", data={"diversity": {}})

        lines = ["🌈 **Análise de Diversidade e Inclusão**\n"]

        if by_gender:
            lines.append("**Gênero:**")
            for gender, count in by_gender.items():
                pct = (count / total * 100) if total else 0
                lines.append(f"• {gender.title()}: {count} ({pct:.1f}%)")
            lines.append("")

        if by_ethnicity:
            lines.append("**Raça/Etnia:**")
            for ethnicity, count in by_ethnicity.items():
                pct = (count / total * 100) if total else 0
                lines.append(f"• {ethnicity.title()}: {count} ({pct:.1f}%)")
            lines.append("")

        if pcds:
            pct = (pcds / total * 100) if total else 0
            lines.append(
                f"**Pessoas com Deficiência (PCDs):** {pcds} ({pct:.1f}%)")

        return DomainResponse(success=True, message="\n".join(lines), data=diversity, suggestions=["Distribuição por gênero", "Distribuição geográfica"])

    def _diversity_from_local(self, context: DomainContext) -> DomainResponse:
        data = context.current_data
        total = len(data)

        races = [c.get("race") or c.get("ethnicity")
                 or "Não informado" for c in data]
        race_counts = Counter(races).most_common()

        pcds = sum(1 for c in data if c.get("disability") or c.get("is_pcd"))

        genders = [c.get("gender", "Não informado") for c in data]
        gender_counts = Counter(genders).most_common()

        has_race = not all(r == "Não informado" for r, _ in race_counts)
        has_disability = any(c.get("disability") is not None or c.get(
            "is_pcd") is not None for c in data)
        has_gender = not all(g == "Não informado" for g, _ in gender_counts)

        if not (has_race or has_disability or has_gender):
            return DomainResponse(
                success=True,
                message="⚠️ Dados de diversidade não disponíveis\n\nCampos esperados:\n• `race` ou `ethnicity` - raça/etnia\n• `disability` ou `is_pcd` - pessoa com deficiência\n• `gender` - gênero",
                data={"diversity": {}},
                suggestions=[
                    "Verifique se os campos de diversidade existem no banco de dados"]
            )

        lines = ["🌈 **Análise de Diversidade e Inclusão**\n"]

        if has_gender:
            lines.append("**Gênero:**")
            for gender, count in gender_counts:
                if gender != "Não informado":
                    lines.append(
                        f"• {gender.title()}: {count} ({count/total*100:.1f}%)")
            lines.append("")

        if has_race:
            lines.append("**Raça/Etnia:**")
            for race, count in race_counts:
                if race != "Não informado":
                    lines.append(
                        f"• {race.title()}: {count} ({count/total*100:.1f}%)")
            lines.append("")

        if has_disability:
            lines.append(
                f"**Pessoas com Deficiência (PCDs):** {pcds} ({pcds/total*100:.1f}%)")

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"total": total, "gender": gender_counts if has_gender else None,
                  "race": race_counts if has_race else None, "pcds": pcds if has_disability else None},
            suggestions=["Distribuição por gênero", "Distribuição geográfica"]
        )

    @require_sourcing_id
    def summarize_search(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._summarize_from_aggregated(context, aggregated_stats)
        return self._summarize_from_local(context)

    def _summarize_from_aggregated(self, context: DomainContext, stats: Dict) -> DomainResponse:
        counts = stats.get("counts", {})
        score_stats = stats.get("score_stats", {})
        exp_stats = stats.get("experience_stats", {})
        loc_dist = stats.get("location_distribution", {})
        skills_dist = stats.get("skills_distribution", {})
        salary_stats = stats.get("salary_stats", {})
        diversity_stats = stats.get("diversity_stats", {})
        remote_stats = stats.get("remote_work_stats", {})
        languages_dist = stats.get("languages_distribution", {})
        contact_stats = stats.get("contact_stats", {})
        companies_dist = stats.get("companies_distribution", {})
        education_stats = stats.get("education_stats", {})

        lines = [f"# 📊 Relatório Completo - Sourcing #{context.sourcing_id}\n"]

        sourcing_query = getattr(
            context, 'sourcing_query', None) or context.metadata.get('query')
        if sourcing_query:
            lines.append(f"**🔍 Busca:** _{sourcing_query}_\n")

        lines.append("## 👥 Candidatos")
        lines.append(f"| Métrica | Valor |")
        lines.append(f"|---------|-------|")
        lines.append(f"| **Total** | **{counts.get('total', 0)}** |")
        if counts.get('from_local'):
            lines.append(f"| Base local | {counts.get('from_local', 0)} |")
        if counts.get('from_linkedin'):
            lines.append(f"| LinkedIn | {counts.get('from_linkedin', 0)} |")
        if counts.get('already_candidates'):
            lines.append(
                f"| Já são candidatos | {counts.get('already_candidates', 0)} |")
        if counts.get('with_curriculum'):
            lines.append(
                f"| Com currículo | {counts.get('with_curriculum', 0)} |")

        if score_stats.get("average"):
            lines.append(f"\n## 📈 Score de Match")
            lines.append(f"| Métrica | Valor |")
            lines.append(f"|---------|-------|")
            lines.append(
                f"| **Média** | **{score_stats.get('average', 0):.1f}** |")
            lines.append(f"| Mediana | {score_stats.get('median', 0):.0f} |")
            lines.append(f"| Máximo | {score_stats.get('max', 0):.0f} |")
            lines.append(f"| Mínimo | {score_stats.get('min', 0):.0f} |")
            if score_stats.get('std_deviation'):
                lines.append(
                    f"| Desvio Padrão | {score_stats.get('std_deviation', 0):.2f} |")

            lines.append(f"\n**Distribuição por faixa:**")
            dist = score_stats.get("distribution", {})
            if dist:
                for faixa, count in [("🟢 Excelente (90+)", dist.get("excellent", 0)),
                                     ("🟡 Bom (70-89)", dist.get("good", 0)),
                                     ("🟠 Regular (50-69)", dist.get("regular", 0)),
                                     ("🔴 Baixo (<50)", dist.get("low", 0))]:
                    if count:
                        lines.append(f"- {faixa}: {count}")

        if remote_stats:
            accepts_remote = remote_stats.get("accepts_remote", 0)
            has_mobility = remote_stats.get("has_mobility", 0)
            onsite_only = remote_stats.get("onsite_only", 0)
            remote_not_specified = remote_stats.get("remote_not_specified", 0)

            if accepts_remote or has_mobility or onsite_only:
                lines.append(f"\n## 🏠 Modelo de Trabalho")
                if accepts_remote:
                    lines.append(f"- ✅ Aceita remoto: {accepts_remote}")
                if has_mobility:
                    lines.append(f"- 🚗 Com mobilidade: {has_mobility}")
                if onsite_only:
                    lines.append(f"- 🏢 Apenas presencial: {onsite_only}")
                if remote_not_specified:
                    lines.append(
                        f"- ❓ Não especificado: {remote_not_specified}")

        if exp_stats.get("average"):
            lines.append(f"\n## 💼 Experiência")
            lines.append(
                f"- **Média:** {exp_stats.get('average', 0):.1f} anos")
            lines.append(f"- Mediana: {exp_stats.get('median', 0):.1f} anos")
            lines.append(f"- Máxima: {exp_stats.get('max', 0)} anos")
            lines.append(f"- Mínima: {exp_stats.get('min', 0)} anos")
            exp_dist = exp_stats.get("distribution", {})
            if exp_dist:
                levels = [(k, v) for k, v in exp_dist.items() if v > 0]
                if levels:
                    lines.append(
                        f"- Níveis: {', '.join(f'{k.capitalize()} ({v})' for k, v in levels)}")

        clt = salary_stats.get("clt", {})
        pj = salary_stats.get("pj", {})
        has_salary = clt.get("average") or pj.get("average")
        without_salary = salary_stats.get("without_salary_info", 0)
        if has_salary:
            lines.append(f"\n## 💰 Pretensão Salarial")
            if clt.get("average"):
                lines.append(
                    f"- CLT média: R$ {clt['average']:,.0f}".replace(",", "."))
            if pj.get("average"):
                lines.append(
                    f"- PJ média: R$ {pj['average']:,.0f}".replace(",", "."))
        elif without_salary:
            lines.append(f"\n## 💰 Pretensão Salarial")
            lines.append(f"- Sem informação: {without_salary} candidatos")

        if contact_stats:
            lines.append(f"\n## 📞 Contato")
            contactable = contact_stats.get("contactable", 0)
            not_contactable = contact_stats.get("not_contactable", 0)
            with_email = contact_stats.get("with_email", 0)
            with_phone = contact_stats.get("with_phone", 0)
            with_linkedin = contact_stats.get("with_linkedin", 0)
            with_github = contact_stats.get("with_github", 0)
            lines.append(f"| Canal | Quantidade |")
            lines.append(f"|-------|------------|")
            lines.append(f"| ✅ Contatáveis | **{contactable}** |")
            lines.append(f"| 📧 Com email | {with_email} |")
            lines.append(f"| 📱 Com telefone | {with_phone} |")
            if with_linkedin:
                lines.append(f"| 💼 Com LinkedIn | {with_linkedin} |")
            if with_github:
                lines.append(f"| 🐙 Com GitHub | {with_github} |")
            if not_contactable:
                lines.append(f"| ❌ Sem contato | {not_contactable} |")

        current_companies = companies_dist.get("current_companies", {})
        if current_companies and isinstance(current_companies, dict):
            total_companies = len(current_companies)
            lines.append(
                f"\n## 🏢 Empresas Atuais ({total_companies} diferentes)")
            sorted_companies = sorted(
                current_companies.items(), key=lambda x: x[1], reverse=True)
            for company, count in sorted_companies[:10]:
                lines.append(f"- {company.title()}: {count}")
            if total_companies > 10:
                lines.append(f"- _...e mais {total_companies - 10} empresas_")

        top_skills = skills_dist.get("top_skills", {})
        if top_skills and isinstance(top_skills, dict) and len(top_skills) > 0:
            lines.append(f"\n## 🛠️ Top Skills")
            sorted_skills = sorted(
                top_skills.items(), key=lambda x: x[1], reverse=True)[:10]
            for skill, count in sorted_skills:
                lines.append(f"- {skill.title()}: {count}")
            unique_count = skills_dist.get('unique_count', 0)
            total_mentions = skills_dist.get('total_mentions', 0)
            if unique_count:
                lines.append(
                    f"- _Total: {unique_count} skills únicas, {total_mentions} menções_")

        by_city = loc_dist.get("by_city", {})
        by_state = loc_dist.get("by_state", {})
        by_country = loc_dist.get("by_country", {})
        if by_city and isinstance(by_city, dict) and len(by_city) > 0:
            lines.append(f"\n## 📍 Localização")
            top_cities = sorted(
                by_city.items(), key=lambda x: x[1], reverse=True)[:8]
            for name, count in top_cities:
                lines.append(f"- {name.title()}: {count}")
        elif by_country and isinstance(by_country, dict) and len(by_country) > 0:
            lines.append(f"\n## 📍 Localização")
            for country, count in by_country.items():
                lines.append(f"- {country.title()}: {count}")
        if loc_dist.get("without_location"):
            if "## 📍 Localização" not in lines[-5:]:
                lines.append(f"\n## 📍 Localização")
            lines.append(f"- Sem localização: {loc_dist['without_location']}")

        english_dist = languages_dist.get("english_distribution", {})
        by_language = languages_dist.get("by_language", {})
        if english_dist and isinstance(english_dist, dict) and len(english_dist) > 0:
            lines.append(f"\n## 🌍 Idiomas")
            lines.append("**Inglês:**")
            for level, count in sorted(english_dist.items(), key=lambda x: x[1], reverse=True):
                level_name = level.replace(
                    "english_", "").replace("inglês_", "").upper()
                lines.append(f"- {level_name}: {count}")
        elif by_language and isinstance(by_language, dict) and len(by_language) > 0:
            lines.append(f"\n## 🌍 Idiomas")
            for lang, count in sorted(by_language.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {lang.title()}: {count}")

        profiles_without_lang = languages_dist.get(
            "profiles_without_languages", 0)
        if profiles_without_lang and profiles_without_lang > 0:
            if "## 🌍 Idiomas" not in "\n".join(lines[-10:]):
                lines.append(f"\n## 🌍 Idiomas")
            lines.append(f"- Sem informação: {profiles_without_lang}")

        by_gender = diversity_stats.get("by_gender", {})
        gender_informed = diversity_stats.get("gender_informed", 0)
        gender_not_informed = diversity_stats.get("gender_not_informed", 0)
        if by_gender and isinstance(by_gender, dict):
            lines.append(f"\n## 🌈 Diversidade")
            for gender, count in by_gender.items():
                lines.append(f"- {gender.title()}: {count}")
            if gender_not_informed:
                lines.append(f"- _Não informado: {gender_not_informed}_")

        top_institutions = education_stats.get("top_institutions", {})
        with_education = education_stats.get("with_education_data", 0)
        without_education = education_stats.get("without_education_data", 0)
        if top_institutions and isinstance(top_institutions, dict) and len(top_institutions) > 0:
            lines.append(f"\n## 🎓 Formação")
            for inst, count in sorted(top_institutions.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {inst.title()}: {count}")
        elif without_education:
            lines.append(f"\n## 🎓 Formação")
            lines.append(f"- Sem informação: {without_education}")

        suggestions = [
            "Liste os candidatos",
            "Compare o top 3",
            "Quem tem score acima de 90?",
            "Relatório executivo"
        ]

        return DomainResponse(success=True, message="\n".join(lines), data=stats, suggestions=suggestions)

    def _summarize_from_local(self, context: DomainContext) -> DomainResponse:
        data = context.current_data
        total = context.get_total_count()

        scores = [c.get("score") or c.get("sourcing_score", 0) for c in data if c.get(
            "score") is not None or c.get("sourcing_score") is not None]
        cities = Counter(c.get("city", "N/I") for c in data).most_common(3)
        avg_score = sum(scores) / len(scores) if scores else 0

        lines = [
            f"📋 **Resumo do Sourcing `{context.sourcing_id}`**\n",
            f"**Total de candidatos:** {total}",
            f"**Carregados na tela:** {len(data)}",
            f"**Score médio:** {avg_score:.1f}" if scores else "**Score médio:** N/A",
            f"**Principais cidades:** {', '.join(f'{c} ({n})' for c, n in cities)}",
            "",
            "**Distribuição por score:**",
        ]

        if scores:
            for label, condition in [("90-100 (Excelente)", lambda s: s >= 90), ("70-89 (Bom)", lambda s: 70 <= s < 90), ("50-69 (Regular)", lambda s: 50 <= s < 70), ("< 50 (Baixo)", lambda s: s < 50)]:
                if count := len([s for s in scores if condition(s)]):
                    lines.append(f"- {label}: {count}")

        return DomainResponse(success=True, message="\n".join(lines), data={"total": total, "average_score": avg_score, "top_cities": cities}, suggestions=["Top 10 candidatos", "Analisar skills"])

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/comparison.py

```python
from typing import Dict, Any, Optional, List
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class ComparisonActions(BaseAction):

    def __init__(self):
        self._llm = None

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            settings = get_settings()
            self._llm = ChatGoogleGenerativeAI(
                model=settings.gemini.model,
                temperature=0.3,
                google_api_key=settings.gemini.api_key
            )
        return self._llm

    @require_sourcing_id
    def compare_candidates(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        plan = self._create_plan(params)
        logger.info(f"📋 Plano de comparação: {plan}")

        candidates_data = self._execute_plan(plan, context)

        if not candidates_data:
            return DomainResponse(
                success=False,
                message="❌ Não foi possível encontrar candidatos para comparar",
                error="no_candidates_found"
            )

        return self._synthesize_comparison(candidates_data, plan, context)

    def _create_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        plan = {
            "type": "comparison",
            "strategy": None,
            "filters": {},
            "limit": 3
        }

        candidate_ids = params.get("candidate_ids", [])
        candidate_names = params.get("candidate_names", [])

        if candidate_ids:
            plan["strategy"] = "specific_ids"
            plan["candidate_ids"] = candidate_ids
            plan["limit"] = len(candidate_ids)
            return plan

        if candidate_names:
            plan["strategy"] = "by_names"
            plan["candidate_names"] = candidate_names
            plan["limit"] = len(candidate_names)
            return plan

        min_score = params.get("min_score")
        if min_score:
            plan["strategy"] = "by_score_filter"
            plan["filters"]["min_score"] = min_score
            plan["limit"] = params.get("limit", 10)
            return plan

        top_n = params.get("top_n") or params.get("limit", 3)
        plan["strategy"] = "top_n"
        plan["limit"] = min(top_n, 10)

        return plan

    def _execute_plan(self, plan: Dict[str, Any], context: DomainContext) -> List[Dict[str, Any]]:
        strategy = plan["strategy"]

        if strategy == "specific_ids":
            return self._fetch_by_ids(plan["candidate_ids"], context)

        if strategy == "by_names":
            return self._fetch_by_names(plan["candidate_names"], context)

        if strategy == "by_score_filter":
            return self._fetch_by_score(plan["filters"]["min_score"], plan["limit"], context)

        if strategy == "top_n":
            return self._fetch_top_n(plan["limit"], context)

        return []

    def _fetch_by_ids(self, ids: List[int], context: DomainContext) -> List[Dict[str, Any]]:
        candidates = []
        for cid in ids:
            try:
                response = self.get_api_client(context).call("sourced_profile_sourcings_search", {
                    "where": {"id": int(cid), "sourcing_id": int(context.sourcing_id)},
                    "per_page": 1,
                    "_single_page": True
                })
                data = response.get("data", [])
                if data:
                    candidates.append(data[0].get("attributes", data[0]))
            except Exception as e:
                logger.warning(f"Erro ao buscar candidato {cid}: {e}")
        return candidates

    def _fetch_by_names(self, names: List[str], context: DomainContext) -> List[Dict[str, Any]]:
        candidates = []
        for name in names:
            try:
                response = self.get_api_client(context).call("sourced_profile_sourcings_search", {
                    "where": {"sourcing_id": int(context.sourcing_id)},
                    "search": name,
                    "per_page": 5,
                    "_single_page": True
                })
                data = response.get("data", [])
                if data:
                    name_lower = name.lower()
                    best_match = None
                    for item in data:
                        attrs = item.get("attributes", item)
                        candidate_name = (attrs.get("name") or "").lower()
                        if name_lower in candidate_name or candidate_name.startswith(name_lower):
                            best_match = attrs
                            break
                    if best_match:
                        candidates.append(best_match)
                    else:
                        candidates.append(data[0].get("attributes", data[0]))
            except Exception as e:
                logger.warning(f"Erro ao buscar candidato '{name}': {e}")
        return candidates

    def _fetch_by_score(self, min_score: float, limit: int, context: DomainContext) -> List[Dict[str, Any]]:
        try:
            response = self.get_api_client(context).call("sourced_profile_sourcings_search", {
                "where": {"sourcing_id": int(context.sourcing_id)},
                "order": {"sourcing_score": "desc"},
                "per_page": 100,
                "_single_page": True
            })
            data = response.get("data", [])

            filtered = []
            for item in data:
                attrs = item.get("attributes", item)
                score = attrs.get("score") or attrs.get("sourcing_score") or 0
                if score >= min_score:
                    filtered.append(attrs)

            return filtered[:limit]
        except Exception as e:
            logger.error(f"Erro ao buscar por score: {e}")
            return []

    def _fetch_top_n(self, limit: int, context: DomainContext) -> List[Dict[str, Any]]:
        try:
            response = self.get_api_client(context).call("sourced_profile_sourcings_search", {
                "where": {"sourcing_id": int(context.sourcing_id)},
                "order": {"sourcing_score": "desc"},
                "per_page": limit,
                "_single_page": True
            })
            data = response.get("data", [])
            return [item.get("attributes", item) for item in data]
        except Exception as e:
            logger.error(f"Erro ao buscar top {limit}: {e}")
            return []

    def _synthesize_comparison(
        self,
        candidates: List[Dict[str, Any]],
        plan: Dict[str, Any],
        context: DomainContext
    ) -> DomainResponse:
        lines = [f"## 🔄 Comparação de {len(candidates)} Candidatos", ""]

        lines.extend(self._build_transposed_table(candidates))
        lines.append("")

        llm_analysis = self._generate_llm_analysis(candidates)
        if llm_analysis:
            lines.extend(llm_analysis)

        suggestions = [
            f"Detalhes do candidato {candidates[0].get('id', '')}" if candidates else "",
            "Qual candidato tem mais experiência?",
            "Compare outros candidatos"
        ]

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"candidates": candidates, "plan": plan},
            suggestions=[s for s in suggestions if s]
        )

    def _build_transposed_table(self, candidates: List[Dict[str, Any]]) -> List[str]:
        lines = ["### 📊 Comparativo Lado a Lado", ""]

        names = [c.get("name", "?").split()[0] for c in candidates]
        header = ["Critério"] + names
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|---" + "|:---:" * len(names) + "|")

        lines.append(self._table_row(
            "🆔 ID", [str(c.get("id", "-")) for c in candidates]))
        lines.append(self._table_row(
            "📊 **Score**", [f"**{c.get('score') or c.get('sourcing_score') or '-'}**" for c in candidates]))
        lines.append(self._table_row("📅 Experiência", [
                     f"{c.get('total_experience_years', '-')} anos" for c in candidates]))
        lines.append(self._table_row("🏢 Empresa", [self._sanitize(
            c.get("current_company", "-")) for c in candidates]))
        lines.append(self._table_row("💼 Cargo", [self._sanitize(
            c.get("title") or c.get("role_name", "-")) for c in candidates]))
        lines.append(self._table_row(
            "📍 Local", [self._format_location(c) for c in candidates]))

        skills_row = []
        for c in candidates:
            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            skills = analysis.get("skills_assessment", {}).get("strong", [])
            skills_row.append(", ".join(skills[:3]) if skills else "-")
        lines.append(self._table_row("🛠️ Top Skills", skills_row))

        highlights_row = []
        for c in candidates:
            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            highlights = analysis.get("highlights", [])
            if highlights:
                desc = highlights[0].get("description", "-")
                highlights_row.append(desc)
            else:
                highlights_row.append("-")
        lines.append(self._table_row("✨ Destaque", highlights_row))

        flags_row = []
        for c in candidates:
            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            flags = analysis.get("red_flags", [])
            if flags:
                severity = flags[0].get("severity", "").upper()
                emoji = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
                flags_row.append(emoji)
            else:
                flags_row.append("✅")
        lines.append(self._table_row("⚠️ Alertas", flags_row))

        return lines

    def _table_row(self, label: str, values: List[str]) -> str:
        return f"| {label} | " + " | ".join(values) + " |"

    def _generate_llm_analysis(self, candidates: List[Dict[str, Any]]) -> List[str]:
        if len(candidates) < 2:
            return []

        try:
            candidates_summary = []
            for c in candidates:
                name = c.get("name", "?")
                score = c.get("score") or c.get("sourcing_score") or 0
                exp = c.get("total_experience_years", "?")
                company = c.get("current_company", "?")

                analysis = c.get("analysis") or c.get("ai_analysis") or {}
                highlights = [h.get("description", "")
                              for h in analysis.get("highlights", [])]
                red_flags = [f.get("description", "")
                             for f in analysis.get("red_flags", [])]
                skills = analysis.get(
                    "skills_assessment", {}).get("strong", [])

                candidates_summary.append({
                    "nome": name,
                    "score": score,
                    "experiencia_anos": exp,
                    "empresa_atual": company,
                    "skills_fortes": skills[:5],
                    "destaques": highlights[:3],
                    "pontos_atencao": red_flags[:2]
                })

            prompt = f"""Você é um recrutador experiente. Analise a comparação entre estes candidatos e dê seu parecer:

CANDIDATOS:
{candidates_summary}

Responda em português, de forma direta e objetiva:
1. **Resumo da Comparação** (2-3 frases comparando os candidatos)
2. **Quem Contratar?** - Sua recomendação clara de qual candidato priorizar e por quê
3. **Pontos de Atenção na Entrevista** - O que perguntar para cada candidato para esclarecer dúvidas

Seja específico e use os dados fornecidos. Não invente informações."""

            response = self.llm.invoke([
                SystemMessage(
                    content="Você é um consultor de RH especializado em tech recruiting."),
                HumanMessage(content=prompt)
            ])

            lines = [
                "---",
                "",
                "### 🧠 Análise Comparativa (IA)",
                "",
                response.content.strip()
            ]

            return lines

        except Exception as e:
            logger.error(f"Erro ao gerar análise LLM: {e}")
            return ["", "*Análise comparativa não disponível*"]

    def _format_location(self, attrs: Dict[str, Any]) -> str:
        city = attrs.get("city", "")
        state = attrs.get("state", "")
        if city and state:
            return f"{city}, {state}"
        return city or state or "-"

    def _sanitize(self, value: Optional[str]) -> str:
        if not value:
            return "-"
        return str(value).replace("|", "/")

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/count.py

```python
from typing import Dict, Any, Optional

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id


class CountActions(BaseAction):

    @require_sourcing_id
    def count_candidates(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            counts = aggregated_stats.get("counts", {})
            total = counts.get("total", 0)
            with_score = counts.get("with_score", 0)

            message = f"📊 **{total} candidatos** no sourcing `{context.sourcing_id}`"
            if with_score:
                message += f"\n• {with_score} com score calculado"

            return DomainResponse(
                success=True,
                message=message,
                data=counts,
                suggestions=["Qual a média de score?", "Top 10 candidatos"]
            )

        total = context.get_total_count()
        local_count = len(context.current_data)

        message = f"📊 **{total} candidatos** vinculados ao sourcing `{context.sourcing_id}`"
        if local_count < total:
            message += f" ({local_count} carregados na tela)"

        return DomainResponse(
            success=True,
            message=message,
            data={"total": total, "loaded": local_count},
            suggestions=["Qual a média de score?", "Top 10 candidatos"]
        )

    @require_sourcing_id
    def count_by_filter(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        filter_spec = params.get("filter", {})
        filtered = self._apply_filter(context.current_data, filter_spec)
        filter_desc = self._describe_filter(filter_spec)

        return DomainResponse(
            success=True,
            message=f"📊 **{len(filtered)} candidatos** {filter_desc}",
            data={"count": len(filtered), "filter": filter_spec,
                  "candidates": filtered},
            suggestions=["Quem são eles?", "Qual a média de score deles?"]
        )

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/details.py

```python
from typing import Dict, Any, Optional, List
import logging

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class DetailActions(BaseAction):

    def __init__(self):
        pass

    @require_sourcing_id
    def show_candidate_details(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        candidate_id = params.get("candidate_id") or params.get(
            "id") or params.get("profile_id")
        candidate_name = params.get("name") or params.get("candidate_name")

        if not candidate_id and candidate_name:
            return self._search_and_show_by_name(candidate_name, context)

        if not candidate_id:
            return DomainResponse(
                success=False,
                message="❌ Por favor, especifique o ID do candidato (ex: 'detalhes do candidato 368')",
                error="missing_candidate_id",
                suggestions=["Liste os candidatos primeiro", "Busque por nome"]
            )

        try:
            response = self.get_api_client(context).call(
                "sourced_profile_sourcings_search",
                {
                    "where": {"id": int(candidate_id)},
                    "per_page": 1,
                    "_single_page": True
                }
            )

            data_list = response.get("data", [])
            if not data_list:
                return DomainResponse(
                    success=False,
                    message=f"❌ Candidato `{candidate_id}` não encontrado",
                    error="not_found"
                )

            attrs = data_list[0].get("attributes", data_list[0])
            return self._format_candidate_details(attrs, candidate_id)

        except Exception as e:
            logger.error(f"Error fetching candidate details: {e}")
            return DomainResponse(
                success=False,
                message=f"❌ Erro ao buscar detalhes: {str(e)}",
                error=str(e)
            )

    def _search_and_show_by_name(self, name: str, context: DomainContext) -> DomainResponse:
        try:
            response = self.get_api_client(context).call("sourced_profile_sourcings_search", {
                "where": {"sourcing_id": int(context.sourcing_id)},
                "search": name,
                "per_page": 5
            })

            data = response.get("data", [])

            if not data:
                return DomainResponse(
                    success=False,
                    message=f"❌ Nenhum candidato encontrado com nome '{name}'",
                    suggestions=["Verifique a ortografia",
                                 "Liste todos os candidatos"]
                )

            if len(data) == 1:
                candidate = data[0]
                attrs = candidate.get("attributes", candidate)
                candidate_id = attrs.get("id") or candidate.get("id")
                return self._format_candidate_details(attrs, str(candidate_id))

            lines = [
                f"🔍 Encontrei **{len(data)} candidatos** com '{name}'. Qual você quer ver?", ""]
            for c in data:
                attrs = c.get("attributes", c)
                cid = attrs.get("id") or c.get("id")
                cname = attrs.get("name", "N/A")
                lines.append(f"• `{cid}` - {cname}")

            return DomainResponse(
                success=True,
                message="\n".join(lines),
                data={"candidates": data},
                suggestions=[f"Detalhes do candidato {data[0].get('id', '')}"]
            )

        except Exception as e:
            logger.error(f"Error searching candidate by name: {e}")
            return DomainResponse(
                success=False,
                message=f"❌ Erro na busca: {str(e)}",
                error=str(e)
            )

    def _sanitize(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return str(value).replace("|", "/")

    def _format_candidate_details(self, attrs: Dict[str, Any], candidate_id: str) -> DomainResponse:
        name = attrs.get("name", "N/A")
        score = attrs.get("score") or attrs.get("sourcing_score")
        analysis = attrs.get("analysis") or attrs.get("ai_analysis") or {}

        lines = [f"## 👤 {name}", ""]

        summary = attrs.get("summary", "")
        if summary and len(summary) > 20:
            lines.append(f"> {summary}")
            lines.append("")

        lines.append("### 📋 Informações Básicas")
        lines.append("")
        lines.append("| Campo | Valor |")
        lines.append("|-------|-------|")
        lines.append(f"| 🆔 ID | `{candidate_id}` |")

        if score:
            lines.append(f"| 📊 Score | **{score}** |")

        basic_fields = [
            ("💼", "Cargo", self._sanitize(
                attrs.get("role_name") or attrs.get("title"))),
            ("🏢", "Empresa", self._sanitize(attrs.get("current_company"))),
            ("📧", "Email", attrs.get("email")),
            ("📱", "Telefone", attrs.get("phone")),
            ("📍", "Localização", self._format_location(attrs)),
            ("📅", "Experiência", f"{attrs.get('total_experience_years')} anos" if attrs.get(
                "total_experience_years") else None),
            ("🏠", "Remoto", "Aceita" if attrs.get("remote_work")
             else "Não aceita" if attrs.get("remote_work") is False else None),
            ("🔗", "LinkedIn", f"[Perfil]({attrs.get('linkedin_url')})" if attrs.get(
                "linkedin_url") else None),
        ]

        for emoji, label, value in basic_fields:
            if value:
                lines.append(f"| {emoji} {label} | {value} |")

        lines.append("")

        if analysis:
            lines.extend(self._format_ai_analysis(analysis))

        experiences = attrs.get("experiences") or []
        if experiences:
            lines.extend(self._format_experiences(experiences[:5]))

        educations = attrs.get("educations") or []
        if educations:
            lines.extend(self._format_educations(educations[:3]))

        certifications = attrs.get("certifications") or []
        if certifications:
            lines.extend(self._format_certifications(certifications[:5]))

        skills = attrs.get("skills") or attrs.get("expertise") or []
        if skills:
            lines.append("### 🛠️ Skills/Expertise")
            lines.append("")
            skills_str = ", ".join([f"`{s}`" for s in skills[:15]])
            lines.append(skills_str)
            if len(skills) > 15:
                lines.append(f"*... e mais {len(skills) - 15}*")
            lines.append("")

        suggested_questions = analysis.get("suggested_questions", [])
        suggestions = suggested_questions[:3] if suggested_questions else [
            "Qual a média de score?",
            "Liste outros candidatos"
        ]

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"candidate": attrs, "id": candidate_id},
            suggestions=suggestions
        )

    def _format_ai_analysis(self, analysis: Dict[str, Any]) -> List[str]:
        lines = []

        one_liner = analysis.get("one_liner")
        if one_liner:
            lines.append("### 🤖 Análise da IA")
            lines.append("")
            lines.append(f"> {one_liner}")
            lines.append("")

        highlights = analysis.get("highlights", [])
        if highlights:
            lines.append("### ✨ Destaques")
            lines.append("")
            for h in highlights:
                h_type = h.get("type", "").replace("_", " ").title()
                h_desc = h.get("description", "")
                lines.append(f"- **{h_type}**: {h_desc}")
            lines.append("")

        red_flags = analysis.get("red_flags", [])
        if red_flags:
            lines.append("### ⚠️ Pontos de Atenção")
            lines.append("")
            for rf in red_flags:
                severity = rf.get("severity", "").upper()
                desc = rf.get("description", "")
                emoji = "🔴" if severity == "HIGH" else "🟡" if severity == "MEDIUM" else "🟢"
                lines.append(f"- {emoji} {desc}")
            lines.append("")

        evaluation = analysis.get("evaluation", [])
        if evaluation:
            lines.extend(self._format_evaluation(evaluation))

        skills_assessment = analysis.get("skills_assessment", {})
        if skills_assessment:
            lines.extend(self._format_skills_assessment(skills_assessment))

        return lines

    def _format_evaluation(self, evaluation: List[Dict]) -> List[str]:
        lines = ["### 📋 Avaliação Detalhada da Lia", ""]

        for ev in evaluation:
            req = ev.get("requirement", "")
            points = ev.get("points", 0)
            match_level = ev.get("match_level", "")
            priority = ev.get("priority", "")
            rationale = ev.get("rationale", "")
            confidence = ev.get("confidence", "")
            evidence = ev.get("evidence", [])

            match_emoji = "✅" if match_level == "exceeds" else "☑️" if match_level == "meets" else "❌"
            priority_label = {"essential": "🔴 Essencial", "important": "🟠 Importante",
                              "nice_to_have": "🟢 Desejável"}.get(priority, priority)

            lines.append(f"#### {match_emoji} {req}")
            lines.append(
                f"**Pontuação:** {points}/100 | **Prioridade:** {priority_label} | **Confiança:** {confidence}")
            lines.append("")
            lines.append(f"**Análise:** {rationale}")
            lines.append("")

            if evidence:
                lines.append("**Evidências do perfil:**")
                for e in evidence[:3]:
                    lines.append(f"- _{e}_")
                lines.append("")

        return lines

    def _format_skills_assessment(self, skills_assessment: Dict[str, Any]) -> List[str]:
        lines = ["### 🛠️ Avaliação de Skills", ""]

        strong = skills_assessment.get("strong", [])
        if strong:
            lines.append(
                f"**💪 Fortes:** {', '.join([f'`{s}`' for s in strong])}")
            lines.append("")

        mentioned = skills_assessment.get("mentioned", [])
        if mentioned:
            lines.append(
                f"**📝 Mencionadas:** {', '.join([f'`{s}`' for s in mentioned])}")
            lines.append("")

        missing = skills_assessment.get("missing_from_search", [])
        if missing:
            lines.append(
                f"**❌ Não encontradas:** {', '.join([f'`{s}`' for s in missing])}")
            lines.append("")

        return lines

    def _format_experiences(self, experiences: List[Dict]) -> List[str]:
        lines = ["### 💼 Experiência Profissional", ""]

        for exp in experiences:
            company = exp.get("company", "N/A")
            role = exp.get("role", "N/A")
            start = exp.get("start_date", "")
            end = exp.get("end_date", "Atual") or "Atual"
            is_current = exp.get("is_current", False)

            if is_current:
                end = "**Atual**"

            lines.append(f"**{role}** @ {company}")
            lines.append(f"*{start} - {end}*")

            summary = exp.get("summary", "")
            if summary and len(summary) > 10:
                lines.append(f"> {summary[:200]}...")

            lines.append("")

        return lines

    def _format_location(self, attrs: Dict[str, Any]) -> Optional[str]:
        parts = []
        if attrs.get("city"):
            parts.append(attrs["city"])
        if attrs.get("state"):
            parts.append(attrs["state"])
        if attrs.get("country"):
            parts.append(attrs["country"])
        return ", ".join(parts) if parts else None

    def _format_educations(self, educations: List[Dict]) -> List[str]:
        lines = ["### 🎓 Educação", ""]

        for edu in educations:
            institution = edu.get("institution", "N/A")
            degree = edu.get("degree", "")
            start = edu.get("start_date", "")[
                :4] if edu.get("start_date") else ""
            end = edu.get("end_date", "")[:4] if edu.get("end_date") else ""

            period = f"{start} - {end}" if start or end else ""

            lines.append(f"**{institution}**")
            if degree:
                lines.append(f"*{degree}*")
            if period:
                lines.append(f"📅 {period}")
            lines.append("")

        return lines

    def _format_certifications(self, certifications: List[Dict]) -> List[str]:
        lines = ["### 📜 Certificações", ""]

        for cert in certifications:
            title = cert.get("title", "N/A")
            issuer = cert.get("issuer", "")

            if issuer:
                lines.append(f"- **{title}** - {issuer}")
            else:
                lines.append(f"- **{title}**")

        lines.append("")
        return lines

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/distribution.py

```python
from typing import Dict, Any, Optional
from collections import Counter

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id


class DistributionActions(BaseAction):

    @require_sourcing_id
    def location_distribution(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._location_from_aggregated(context, aggregated_stats)
        return self._location_from_local(context)

    def _location_from_aggregated(self, context: DomainContext, stats: Dict) -> DomainResponse:
        loc_dist = stats.get("location_distribution", {})
        by_city = loc_dist.get("by_city", {})

        if not by_city:
            return DomainResponse(success=True, message="⚠️ Dados de localização não disponíveis", data={"distribution": []})

        if isinstance(by_city, dict):
            sorted_cities = sorted(
                by_city.items(), key=lambda x: x[1], reverse=True)[:10]
        else:
            sorted_cities = [(item.get("name", "N/A"), item.get("count", 0))
                             for item in by_city[:10]]

        lines = ["📍 **Distribuição Geográfica**\n", "**Por Cidade:**",
                 "| Cidade | Candidatos |", "|--------|------------|"]

        for name, count in sorted_cities:
            lines.append(f"| {name.title()} | {count} |")

        return DomainResponse(success=True, message="\n".join(lines), data=loc_dist, suggestions=["Quantos de São Paulo?", "Top candidatos de SP"])

    def _location_from_local(self, context: DomainContext) -> DomainResponse:
        cities = [c.get("city", "Não informado") for c in context.current_data]
        city_counts = Counter(cities).most_common(10)

        lines = ["📍 **Distribuição por Cidade**\n",
                 "| Cidade | Candidatos |", "|--------|------------|"]
        for city, count in city_counts:
            lines.append(f"| {city} | {count} |")

        return DomainResponse(success=True, message="\n".join(lines), data={"distribution": city_counts}, suggestions=["Quantos de São Paulo?", "Top candidatos de SP"])

    @require_sourcing_id
    def gender_distribution(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._gender_from_aggregated(stats=aggregated_stats)
        return self._gender_from_local(context)

    def _gender_from_aggregated(self, stats: Dict) -> DomainResponse:
        by_gender = stats.get("diversity_stats", {}).get("by_gender", {})

        if not by_gender:
            return DomainResponse(success=True, message="⚠️ Dados de gênero não disponíveis", data={"distribution": []})

        total = sum(by_gender.values())
        lines = ["⚧️ **Distribuição por Gênero**\n",
                 "| Gênero | Candidatos | % |", "|--------|------------|---|"]

        for gender, count in by_gender.items():
            pct = (count / total * 100) if total else 0
            lines.append(f"| {gender.title()} | {count} | {pct:.1f}% |")

        return DomainResponse(success=True, message="\n".join(lines), data={"distribution": by_gender, "total": total}, suggestions=["Análise de diversidade completa", "Distribuição por localização"])

    def _gender_from_local(self, context: DomainContext) -> DomainResponse:
        genders = [c.get("gender", "Não informado")
                   for c in context.current_data]
        gender_counts = Counter(genders).most_common()

        if all(g == "Não informado" for g, _ in gender_counts):
            return DomainResponse(success=True, message="⚠️ Dados de gênero não disponíveis ou campo não existe", data={"distribution": []}, suggestions=["Verifique se o campo 'gender' existe no banco de dados"])

        total = len(context.current_data)
        lines = ["⚧️ **Distribuição por Gênero**\n",
                 "| Gênero | Candidatos | % |", "|--------|------------|---|"]

        for gender, count in gender_counts:
            pct = (count / total * 100) if total else 0
            lines.append(f"| {gender.title()} | {count} | {pct:.1f}% |")

        return DomainResponse(success=True, message="\n".join(lines), data={"distribution": gender_counts, "total": total}, suggestions=["Análise de diversidade completa", "Distribuição por localização"])

    @require_sourcing_id
    def work_model_distribution(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._work_model_from_aggregated(stats=aggregated_stats)
        return self._work_model_from_local(context)

    def _work_model_from_aggregated(self, stats: Dict) -> DomainResponse:
        remote_stats = stats.get("remote_work_stats", {})
        accepts_remote = remote_stats.get("accepts_remote", 0)
        prefers_onsite = remote_stats.get("prefers_onsite", 0)
        has_mobility = remote_stats.get("has_mobility", 0)

        if not any([accepts_remote, prefers_onsite, has_mobility]):
            return DomainResponse(success=True, message="⚠️ Dados de modelo de trabalho não disponíveis", data={"distribution": []})

        total = stats.get("counts", {}).get("total", 0)
        lines = ["🏢 **Preferência de Modelo de Trabalho**\n"]

        if accepts_remote:
            lines.append(
                f"• Aceitam remoto: {accepts_remote} ({accepts_remote/total*100:.1f}%)" if total else f"• Aceitam remoto: {accepts_remote}")
        if prefers_onsite:
            lines.append(
                f"• Preferem presencial: {prefers_onsite} ({prefers_onsite/total*100:.1f}%)" if total else f"• Preferem presencial: {prefers_onsite}")
        if has_mobility:
            lines.append(
                f"• Com mobilidade: {has_mobility} ({has_mobility/total*100:.1f}%)" if total else f"• Com mobilidade: {has_mobility}")

        return DomainResponse(success=True, message="\n".join(lines), data=remote_stats, suggestions=["Quantos aceitam apenas remoto?", "Distribuição por cidade"])

    def _work_model_from_local(self, context: DomainContext) -> DomainResponse:
        models = [
            c.get("work_model_preference") or c.get("work_model") or c.get(
                "work_preference") or "Não informado"
            for c in context.current_data
        ]
        model_counts = Counter(models).most_common()

        if all(m == "Não informado" for m, _ in model_counts):
            return DomainResponse(success=True, message="⚠️ Dados de modelo de trabalho não disponíveis ou campo não existe", data={"distribution": []}, suggestions=["Verifique se campos 'work_model_preference', 'accepts_remote', 'accepts_hybrid' existem"])

        total = len(context.current_data)
        lines = ["🏢 **Preferência de Modelo de Trabalho**\n",
                 "| Modelo | Candidatos | % |", "|--------|------------|---|"]

        for model, count in model_counts:
            pct = (count / total * 100) if total else 0
            lines.append(f"| {model.title()} | {count} | {pct:.1f}% |")

        return DomainResponse(success=True, message="\n".join(lines), data={"distribution": model_counts, "total": total}, suggestions=["Quantos aceitam apenas remoto?", "Distribuição por cidade"])

    @require_sourcing_id
    def language_distribution(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._language_from_aggregated(stats=aggregated_stats)
        return self._language_from_local(context)

    def _language_from_aggregated(self, stats: Dict) -> DomainResponse:
        lang_dist = stats.get("languages_distribution", {})
        english_dist = lang_dist.get("english_distribution", {})
        by_language = lang_dist.get("by_language", {})

        if not by_language and not english_dist:
            return DomainResponse(success=True, message="⚠️ Dados de idiomas não disponíveis", data={"languages": {}})

        lines = ["🌍 **Distribuição de Idiomas**\n"]

        if english_dist:
            lines.append("**Inglês:**")
            for level, count in english_dist.items():
                if count:
                    lines.append(f"  • {level}: {count} candidatos")
            lines.append("")

        for lang_name, levels in by_language.items():
            if lang_name.lower() == "english":
                continue
            lines.append(f"**{lang_name.title()}:**")
            if isinstance(levels, dict):
                for level, count in levels.items():
                    if count:
                        lines.append(f"  • {level}: {count} candidatos")
            lines.append("")

        return DomainResponse(success=True, message="\n".join(lines), data=lang_dist, suggestions=["Quantos têm inglês fluente?", "Skills mais comuns"])

    def _language_from_local(self, context: DomainContext) -> DomainResponse:
        languages_data = {}

        for c in context.current_data:
            for lang in (c.get("languages") or c.get("languages_data") or []):
                if not isinstance(lang, dict):
                    continue
                name = lang.get("name", "").lower()
                level = lang.get("level", "Não informado")
                if name:
                    languages_data.setdefault(name, Counter())[level] += 1

        if not languages_data:
            return DomainResponse(success=True, message="⚠️ Dados de idiomas não disponíveis ou campo não existe", data={"languages": {}}, suggestions=["Verifique se o campo 'languages' existe no banco de dados"])

        lines = ["🌍 **Distribuição de Idiomas**\n"]
        for lang_name, levels in sorted(languages_data.items()):
            lines.append(f"**{lang_name.title()}:**")
            for level, count in levels.most_common():
                lines.append(f"  • {level}: {count} candidatos")
            lines.append("")

        return DomainResponse(success=True, message="\n".join(lines), data={"languages": dict(languages_data)}, suggestions=["Quantos têm inglês fluente?", "Skills mais comuns"])

    @require_sourcing_id
    def education_distribution(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._education_from_aggregated(stats=aggregated_stats)
        return self._education_from_local(context)

    def _education_from_aggregated(self, stats: Dict) -> DomainResponse:
        edu_stats = stats.get("education_stats", {})
        top_institutions = edu_stats.get("top_institutions", {})
        by_degree = edu_stats.get("by_degree", {})

        if not top_institutions and not by_degree:
            return DomainResponse(success=True, message="⚠️ Dados de formação não disponíveis", data={"institutions": []})

        lines = ["🎓 **Origem de Formação**\n"]

        if by_degree:
            lines.append("**Por Grau:**")
            for degree, count in by_degree.items():
                if count:
                    lines.append(f"  • {degree}: {count}")
            lines.append("")

        if top_institutions:
            if isinstance(top_institutions, dict):
                sorted_institutions = sorted(
                    top_institutions.items(), key=lambda x: x[1], reverse=True)[:10]
            else:
                sorted_institutions = [
                    (item.get("name", "N/A"), item.get("count", 0)) for item in top_institutions[:10]]

            lines.extend(["**Principais Instituições:**",
                         "| Instituição | Candidatos |", "|-------------|------------|"])
            for name, count in sorted_institutions:
                lines.append(f"| {name.title()} | {count} |")

        return DomainResponse(success=True, message="\n".join(lines), data=edu_stats, suggestions=["Quantos são de universidades públicas?", "Skills mais comuns"])

    def _education_from_local(self, context: DomainContext) -> DomainResponse:
        institutions = []
        for c in context.current_data:
            education = c.get("education") or c.get("education_data") or []
            if isinstance(education, list):
                for edu in education:
                    if isinstance(edu, dict) and (inst := edu.get("institution")):
                        institutions.append(inst)
            elif isinstance(education, str) and education:
                institutions.append(education)

        if not institutions:
            return DomainResponse(success=True, message="⚠️ Dados de formação não disponíveis ou campo não existe", data={"institutions": []}, suggestions=["Verifique se o campo 'education' existe no banco de dados"])

        inst_counts = Counter(institutions).most_common(15)
        lines = ["🎓 **Origem de Formação**\n",
                 "| Instituição | Candidatos |", "|-------------|------------|"]
        for inst, count in inst_counts:
            lines.append(f"| {inst} | {count} |")

        return DomainResponse(success=True, message="\n".join(lines), data={"institutions": inst_counts}, suggestions=["Quantos são de universidades públicas?", "Skills mais comuns"])

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/insights.py

```python
from typing import Dict, Any, Optional, List
from collections import Counter

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id
from src.domains.sourced_profile_sourcing.fairness import FairnessGuard


class InsightsActions(BaseAction):

    @require_sourcing_id
    def score_above(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        threshold = params.get("threshold", 70)

        if aggregated_stats:
            return self._score_above_from_aggregated(threshold, aggregated_stats)
        return self._score_above_from_local(threshold, context)

    def _score_above_from_aggregated(self, threshold: int, stats: Dict) -> DomainResponse:
        score_stats = stats.get("score_stats", {})
        total = stats.get("counts", {}).get("total", 0)

        count = 0
        field_map = {90: "above_90", 80: "above_80",
                     70: "above_70", 60: "above_60", 50: "above_50"}

        if threshold in field_map:
            count = score_stats.get(field_map[threshold], 0)
        else:
            for t in sorted(field_map.keys(), reverse=True):
                if threshold >= t:
                    count = score_stats.get(field_map[t], 0)
                    break

        pct = (count / total * 100) if total else 0

        lines = [f"📊 **Candidatos com score ≥ {threshold}**\n"]
        lines.append(f"• **{count}** candidatos ({pct:.1f}% do total)")

        dist = score_stats.get("distribution", {})
        if dist:
            lines.append("\n**Distribuição completa:**")
            if dist.get("excellent"):
                lines.append(f"• 🟢 Excelente (90+): {dist['excellent']}")
            if dist.get("good"):
                lines.append(f"• 🟡 Bom (70-89): {dist['good']}")
            if dist.get("regular"):
                lines.append(f"• 🟠 Regular (50-69): {dist['regular']}")
            if dist.get("low"):
                lines.append(f"• 🔴 Baixo (<50): {dist['low']}")

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"threshold": threshold, "count": count, "percentage": pct},
            suggestions=[
                f"Liste os com score acima de {threshold}", "Compare os top 5"]
        )

    def _score_above_from_local(self, threshold: int, context: DomainContext) -> DomainResponse:
        candidates = [
            c for c in context.current_data
            if (c.get("score") or c.get("sourcing_score", 0)) >= threshold
        ]

        total = len(context.current_data)
        count = len(candidates)
        pct = (count / total * 100) if total else 0

        return DomainResponse(
            success=True,
            message=f"📊 **{count}** candidatos com score ≥ {threshold} ({pct:.1f}% do total)",
            data={"threshold": threshold, "count": count, "percentage": pct},
            suggestions=[
                f"Liste os com score acima de {threshold}", "Compare os top 5"]
        )

    @require_sourcing_id
    def common_strengths(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._common_strengths_from_aggregated(aggregated_stats)
        return self._common_strengths_from_local(context)

    def _common_strengths_from_aggregated(self, stats: Dict) -> DomainResponse:
        common = stats.get("common_strengths", {})
        most_common = common.get("most_common", {})
        shared_by_majority = common.get("shared_by_majority", {})
        avg_skills = common.get("avg_skills_per_profile", 0)

        if not most_common:
            skills_dist = stats.get("skills_distribution", {})
            most_common = skills_dist.get("top_skills", {})

        if not most_common:
            return DomainResponse(
                success=True,
                message="⚠️ Dados de pontos fortes não disponíveis",
                data={}
            )

        lines = ["💪 **Pontos Fortes em Comum**\n"]

        if shared_by_majority:
            lines.append("**Compartilhados pela maioria:**")
            for skill, count in list(shared_by_majority.items())[:5]:
                lines.append(f"• ✅ {skill.title()}: {count} candidatos")
            lines.append("")

        lines.append("**Skills mais frequentes:**")
        if isinstance(most_common, dict):
            sorted_skills = sorted(most_common.items(),
                                   key=lambda x: x[1], reverse=True)[:10]
        else:
            sorted_skills = [(s.get("name"), s.get("count"))
                             for s in most_common[:10]]

        for skill, count in sorted_skills:
            lines.append(f"• {skill.title()}: {count}")

        if avg_skills:
            lines.append(f"\n*Média de {avg_skills:.1f} skills por perfil*")

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"common": most_common,
                  "shared_by_majority": shared_by_majority},
            suggestions=["Quais gaps existem?", "Compare os top 3"]
        )

    def _common_strengths_from_local(self, context: DomainContext) -> DomainResponse:
        all_skills = []
        for c in context.current_data:
            skills = c.get("skills_data") or c.get("skills") or []
            for s in skills:
                if isinstance(s, dict):
                    all_skills.append(s.get("name", "").lower())
                elif isinstance(s, str):
                    all_skills.append(s.lower())

        if not all_skills:
            return DomainResponse(
                success=True,
                message="⚠️ Dados de skills não disponíveis",
                data={}
            )

        skill_counts = Counter(all_skills).most_common(10)
        total_candidates = len(context.current_data)

        lines = ["💪 **Pontos Fortes em Comum**\n"]

        shared_by_majority = [(s, c)
                              for s, c in skill_counts if c > total_candidates / 2]
        if shared_by_majority:
            lines.append("**Compartilhados pela maioria:**")
            for skill, count in shared_by_majority[:5]:
                lines.append(
                    f"• ✅ {skill.title()}: {count} ({count/total_candidates*100:.0f}%)")
            lines.append("")

        lines.append("**Skills mais frequentes:**")
        for skill, count in skill_counts:
            lines.append(f"• {skill.title()}: {count}")

        avg_skills = len(all_skills) / \
            total_candidates if total_candidates else 0
        lines.append(f"\n*Média de {avg_skills:.1f} skills por perfil*")

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"skills": skill_counts},
            suggestions=["Quais gaps existem?", "Compare os top 3"]
        )

    @require_sourcing_id
    def skill_gaps(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            return self._skill_gaps_from_aggregated(aggregated_stats)
        return self._skill_gaps_from_local(context)

    def _skill_gaps_from_aggregated(self, stats: Dict) -> DomainResponse:
        gaps = stats.get("skill_gaps", {})
        rare_skills = gaps.get("rare_skills", [])
        uncommon = gaps.get("uncommon_skills", {})
        profiles_with_few = gaps.get("profiles_with_few_skills", 0)
        profiles_without = gaps.get("profiles_without_skills", 0)
        coverage = gaps.get("skill_coverage", 0)

        if not rare_skills and not uncommon and not profiles_with_few:
            return DomainResponse(
                success=True,
                message="⚠️ Dados de gaps de competência não disponíveis",
                data={}
            )

        lines = ["🎯 **Gaps de Competência Identificados**\n"]

        if rare_skills:
            lines.append("**Skills raras (difíceis de encontrar):**")
            for skill in rare_skills[:8]:
                lines.append(
                    f"• ⚠️ {skill.title() if isinstance(skill, str) else skill}")
            lines.append("")

        if uncommon:
            lines.append("**Skills pouco comuns:**")
            if isinstance(uncommon, dict):
                for skill, count in list(uncommon.items())[:5]:
                    lines.append(
                        f"• {skill.title()}: apenas {count} candidatos")
            lines.append("")

        if profiles_with_few or profiles_without:
            lines.append("**Perfis incompletos:**")
            if profiles_without:
                lines.append(f"• ❌ {profiles_without} sem skills cadastradas")
            if profiles_with_few:
                lines.append(f"• ⚠️ {profiles_with_few} com poucas skills")

        if coverage:
            lines.append(f"\n*Cobertura de skills: {coverage:.1f}%*")

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data=gaps,
            suggestions=["Pontos fortes em comum", "Como melhorar a busca?"]
        )

    def _skill_gaps_from_local(self, context: DomainContext) -> DomainResponse:
        profiles_without_skills = 0
        profiles_with_few_skills = 0
        all_skills_count = []

        for c in context.current_data:
            skills = c.get("skills_data") or c.get("skills") or []
            count = len(skills)
            all_skills_count.append(count)
            if count == 0:
                profiles_without_skills += 1
            elif count < 3:
                profiles_with_few_skills += 1

        total = len(context.current_data)
        coverage = ((total - profiles_without_skills) /
                    total * 100) if total else 0

        lines = ["🎯 **Gaps de Competência Identificados**\n"]

        lines.append("**Perfis incompletos:**")
        if profiles_without_skills:
            lines.append(
                f"• ❌ {profiles_without_skills} sem skills cadastradas ({profiles_without_skills/total*100:.1f}%)")
        if profiles_with_few_skills:
            lines.append(
                f"• ⚠️ {profiles_with_few_skills} com poucas skills (<3)")

        if not profiles_without_skills and not profiles_with_few_skills:
            lines.append("• ✅ Todos os perfis têm skills cadastradas")

        lines.append(f"\n*Cobertura de skills: {coverage:.1f}%*")

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"profiles_without": profiles_without_skills,
                  "profiles_with_few": profiles_with_few_skills, "coverage": coverage},
            suggestions=["Pontos fortes em comum", "Como melhorar a busca?"]
        )

    @require_sourcing_id
    def top_by_experience(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        limit = params.get("limit", 5)

        if aggregated_stats:
            top_summary = aggregated_stats.get("top_candidates_summary", {})
            profiles = top_summary.get("profiles", [])
            exp_stats = aggregated_stats.get("experience_stats", {})

            has_experience_data = any(p.get("experience_years")
                                      for p in profiles)

            if profiles:
                if has_experience_data:
                    sorted_profiles = sorted(
                        profiles,
                        key=lambda x: x.get("experience_years") or 0,
                        reverse=True
                    )[:limit]
                    lines = [f"⏱️ **Top {limit} com Mais Experiência**\n"]
                else:
                    sorted_profiles = profiles[:limit]
                    lines = [f"⏱️ **Top {limit} Candidatos (por Score)**\n"]
                    lines.append(
                        "*Dados de anos de experiência não disponíveis, ordenado por score*\n")

                lines.append("| # | Nome | Score | Cargo | Empresa |")
                lines.append("|---|------|-------|-------|---------|")

                for i, p in enumerate(sorted_profiles, 1):
                    name = p.get('name', 'N/A')[:25]
                    score = p.get('score', '-')
                    title = (p.get('title') or '-')[:30]
                    company = (p.get('company') or '-')[:20]
                    lines.append(
                        f"| {i} | {name} | {score} | {title} | {company} |")

                if exp_stats.get("average"):
                    lines.append(
                        f"\n*Experiência média geral: {exp_stats['average']:.1f} anos*")

                return DomainResponse(
                    success=True,
                    message="\n".join(lines),
                    data={"profiles": sorted_profiles},
                    suggestions=["Detalhes do primeiro", "Compare os top 3"]
                )

        try:
            response = self.get_api_client(context).call(
                "sourced_profile_sourcings_search",
                {
                    "where": {"sourcing_id": int(context.sourcing_id), "is_deleted": False},
                    "order": {"sourcing_score": "desc"},
                    "per_page": limit
                }
            )

            data = [item.get("attributes", item)
                    for item in response.get("data", [])]

            if not data:
                return DomainResponse(success=True, message="⚠️ Nenhum candidato encontrado", data={})

            lines = [f"⏱️ **Top {limit} Candidatos**\n"]
            lines.append("| # | Nome | Score | Cargo | Empresa |")
            lines.append("|---|------|-------|-------|---------|")

            for i, c in enumerate(data, 1):
                name = c.get('name', 'N/A')[:25]
                score = c.get('sourcing_score') or c.get('score', '-')
                title = (c.get('title') or c.get(
                    'current_position') or '-')[:30]
                company = (c.get('current_company') or '-')[:20]
                lines.append(
                    f"| {i} | {name} | {score} | {title} | {company} |")

            return DomainResponse(
                success=True,
                message="\n".join(lines),
                data={"candidates": data},
                suggestions=["Detalhes do primeiro", "Compare os top 3"]
            )
        except Exception as e:
            return DomainResponse(success=False, message=f"❌ Erro: {str(e)}", data={})

    @require_sourcing_id
    def candidates_to_discard(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        threshold = params.get("threshold", 50)

        if aggregated_stats:
            score_stats = aggregated_stats.get("score_stats", {})
            dist = score_stats.get("distribution", {})
            low_count = dist.get("low", 0)
            total = aggregated_stats.get("counts", {}).get("total", 0)

            lines = ["🚫 **Candidatos para Considerar Descartar**\n"]
            lines.append(
                f"**{low_count}** candidatos com score baixo (<{threshold})\n")

            if low_count and total:
                lines.append(
                    f"Representam {low_count/total*100:.1f}% do total\n")

            lines.append("**Critérios de descarte sugeridos:**")
            lines.append("• Score abaixo de 50")
            lines.append("• Sem experiência relevante")
            lines.append("• Localização incompatível")
            lines.append("• Skills não alinhadas")

            message = FairnessGuard.add_discard_disclaimer("\n".join(lines))

            return DomainResponse(
                success=True,
                message=message,
                data={"low_score_count": low_count},
                suggestions=[
                    f"Liste os com score abaixo de {threshold}", "Quem precisa de triagem?"],
                warnings=[
                    "Esta é uma sugestão baseada em score algorítmico, não uma decisão final"]
            )

        candidates = [
            c for c in context.current_data
            if (c.get("score") or c.get("sourcing_score", 0)) < threshold
        ]

        lines = ["🚫 **Candidatos para Considerar Descartar**\n"]
        lines.append(
            f"**{len(candidates)}** candidatos com score abaixo de {threshold}\n")

        if candidates:
            lines.append("| Código | Nome | Score | Motivo |")
            lines.append("|--------|------|-------|--------|")
            for c in candidates[:10]:
                score = c.get("score") or c.get("sourcing_score", 0)
                lines.append(
                    f"| {c.get('id')} | {c.get('name', 'N/A')} | {score} | Score baixo |")

        message = FairnessGuard.add_discard_disclaimer("\n".join(lines))

        return DomainResponse(
            success=True,
            message=message,
            data={"candidates": candidates},
            suggestions=["Detalhes de algum", "Quem precisa de triagem?"],
            warnings=[
                "Esta é uma sugestão baseada em score algorítmico, não uma decisão final"]
        )

    @require_sourcing_id
    def needs_screening(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            score_stats = aggregated_stats.get("score_stats", {})
            dist = score_stats.get("distribution", {})
            regular_count = dist.get("regular", 0)
            contact_stats = aggregated_stats.get("contact_stats", {})
            not_contactable = contact_stats.get("not_contactable", 0)

            lines = ["🔍 **Candidatos que Precisam de Triagem**\n"]

            if regular_count:
                lines.append(
                    f"**Score médio (50-69):** {regular_count} candidatos")
                lines.append("→ Precisam de avaliação mais detalhada\n")

            if not_contactable:
                lines.append(f"**Sem contato:** {not_contactable} candidatos")
                lines.append("→ Buscar dados de contato\n")

            lines.append("**Recomendações:**")
            lines.append("• Revisar experiências manualmente")
            lines.append("• Verificar fit cultural")
            lines.append("• Analisar projetos/portfolio")
            lines.append("• Confirmar disponibilidade")

            return DomainResponse(
                success=True,
                message="\n".join(lines),
                data={"regular": regular_count,
                      "not_contactable": not_contactable},
                suggestions=["Liste os com score médio",
                             "Quem não tem contato?"]
            )

        candidates = [
            c for c in context.current_data
            if 50 <= (c.get("score") or c.get("sourcing_score", 0)) < 70
        ]

        lines = ["🔍 **Candidatos que Precisam de Triagem**\n"]
        lines.append(
            f"**{len(candidates)}** candidatos com score médio (50-69)\n")

        if candidates:
            lines.append("| Código | Nome | Score | Cargo |")
            lines.append("|--------|------|-------|-------|")
            for c in candidates[:10]:
                score = c.get("score") or c.get("sourcing_score", 0)
                lines.append(
                    f"| {c.get('id')} | {c.get('name', 'N/A')} | {score} | {c.get('title', '-')} |")

        return DomainResponse(
            success=True,
            message="\n".join(lines),
            data={"candidates": candidates},
            suggestions=["Detalhes de algum", "Quem tem score alto?"]
        )

    @require_sourcing_id
    def priority_ranking(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if aggregated_stats:
            score_stats = aggregated_stats.get("score_stats", {})
            dist = score_stats.get("distribution", {})
            total = aggregated_stats.get("counts", {}).get("total", 0)

            excellent = dist.get("excellent", 0)
            good = dist.get("good", 0)
            regular = dist.get("regular", 0)
            low = dist.get("low", 0)

            lines = ["📋 **Organização por Prioridade**\n"]

            lines.append("**🔴 Alta Prioridade (Contactar imediatamente):**")
            lines.append(f"• {excellent} candidatos com score 90+ (Excelente)")
            lines.append("")

            lines.append("**🟡 Média Prioridade (Avaliar esta semana):**")
            lines.append(f"• {good} candidatos com score 70-89 (Bom)")
            lines.append("")

            lines.append("**🟢 Baixa Prioridade (Triagem adicional):**")
            lines.append(f"• {regular} candidatos com score 50-69 (Regular)")
            lines.append("")

            if low:
                lines.append("**⚪ Considerar descartar:**")
                lines.append(f"• {low} candidatos com score <50")

            lines.append("\n**Recomendação:**")
            if excellent >= 3:
                lines.append(
                    "→ Foque nos top 3-5 candidatos excelentes primeiro")
            elif good >= 5:
                lines.append(
                    "→ Avalie os candidatos bons, podem ser ótimas opções")
            else:
                lines.append(
                    "→ Considere expandir a busca para mais candidatos")

            message = FairnessGuard.add_ranking_disclaimer("\n".join(lines))

            return DomainResponse(
                success=True,
                message=message,
                data={"distribution": dist, "total": total},
                suggestions=["Liste os de alta prioridade",
                             "Compare os top 5"],
                warnings=["Ranking baseado apenas em score técnico"]
            )

        candidates = sorted(
            context.current_data,
            key=lambda c: c.get("score") or c.get("sourcing_score", 0),
            reverse=True
        )

        high = [c for c in candidates if (
            c.get("score") or c.get("sourcing_score", 0)) >= 90]
        medium = [c for c in candidates if 70 <= (
            c.get("score") or c.get("sourcing_score", 0)) < 90]
        low = [c for c in candidates if (
            c.get("score") or c.get("sourcing_score", 0)) < 70]

        lines = ["📋 **Organização por Prioridade**\n"]
        lines.append(
            f"**🔴 Alta:** {len(high)} | **🟡 Média:** {len(medium)} | **🟢 Baixa:** {len(low)}")

        message = FairnessGuard.add_ranking_disclaimer("\n".join(lines))

        return DomainResponse(
            success=True,
            message=message,
            data={"high": len(high), "medium": len(medium), "low": len(low)},
            suggestions=["Liste os de alta prioridade", "Compare os top 5"],
            warnings=["Ranking baseado apenas em score técnico"]
        )

    @require_sourcing_id
    def work_model_specific(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        model_type = params.get("model_type", "hybrid")

        if aggregated_stats:
            work_stats = aggregated_stats.get("work_model_stats", {})
            total = work_stats.get("total", 0)

            if model_type == "remote":
                count = work_stats.get("accepts_remote", 0)
                only_remote = work_stats.get("only_remote", 0)
                pct = work_stats.get("accepts_remote_percent", 0)

                lines = ["🏠 **Candidatos que Aceitam Remoto**\n"]
                lines.append(
                    f"• **{count}** aceitam trabalho remoto ({pct:.1f}%)")
                if only_remote:
                    lines.append(f"• **{only_remote}** aceitam apenas remoto")

            elif model_type == "hybrid":
                count = work_stats.get("accepts_hybrid", 0)
                pct = work_stats.get("accepts_hybrid_percent", 0)

                lines = ["🔄 **Candidatos que Aceitam Híbrido**\n"]
                lines.append(
                    f"• **{count}** aceitam trabalho híbrido ({pct:.1f}%)")

            elif model_type == "onsite":
                count = work_stats.get("accepts_onsite", 0)
                only_onsite = work_stats.get("only_onsite", 0)
                pct = work_stats.get("accepts_onsite_percent", 0)

                lines = ["🏢 **Candidatos que Aceitam Presencial**\n"]
                lines.append(
                    f"• **{count}** aceitam trabalho presencial ({pct:.1f}%)")
                if only_onsite:
                    lines.append(
                        f"• **{only_onsite}** aceitam apenas presencial")
            else:
                flexible = work_stats.get("flexible", 0)
                flexible_pct = work_stats.get("flexible_percent", 0)

                lines = ["✅ **Candidatos Flexíveis**\n"]
                lines.append(
                    f"• **{flexible}** são flexíveis ({flexible_pct:.1f}%)")

            return DomainResponse(
                success=True,
                message="\n".join(lines),
                data=work_stats,
                suggestions=["Quantos aceitam remoto?",
                             "Distribuição por cidade"]
            )

        return DomainResponse(
            success=True,
            message="⚠️ Dados detalhados não disponíveis sem aggregated_stats",
            data={}
        )

```

---

## 📄 src/domains/sourced_profile_sourcing/actions/report.py

```python
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.actions.base import BaseAction, require_sourcing_id
from src.config.settings import get_settings
from src.utils.timing import get_timer

logger = logging.getLogger(__name__)


class ReportActions(BaseAction):

    def __init__(self):
        self._llm = None

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            settings = get_settings()
            self._llm = ChatGoogleGenerativeAI(
                model=settings.gemini.model,
                temperature=0.3,
                google_api_key=settings.gemini.api_key
            )
        return self._llm

    @require_sourcing_id
    def generate_executive_report(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        timer = get_timer()

        if timer:
            timer.step("report_planning")
        plan = self._plan_report(params, context)
        logger.info(f"📋 Report plan: {plan['report_type']}")

        if timer:
            timer.step("report_data_collection")
        collected_data = self._collect_data(plan, context)

        if timer:
            timer.step("report_analysis")
        analysis = self._analyze_data(collected_data, plan)

        if timer:
            timer.step("report_formatting")
        report = self._format_executive_report(collected_data, analysis, plan)

        chart_data = self._prepare_chart_data(collected_data, analysis)

        return DomainResponse(
            success=True,
            message=report,
            data={
                "report_type": plan["report_type"],
                "generated_at": datetime.now().isoformat(),
                "sourcing_id": context.sourcing_id,
                "metrics": collected_data.get("metrics", {}),
                "charts": chart_data,
                "top_candidates": collected_data.get("top_candidates", []),
                "insights": analysis.get("insights", []),
                "recommendations": analysis.get("recommendations", []),
                "raw_stats": collected_data.get("stats", {})
            },
            suggestions=[
                "Compare os melhores candidatos",
                "Detalhes do melhor candidato",
                "Exportar relatório"
            ]
        )

    @require_sourcing_id
    def generate_top_candidates_report(
        self,
        params: Dict[str, Any],
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        limit = params.get("limit", 5)
        min_score = params.get("min_score", 80)

        candidates = self._fetch_top_candidates(context, limit, min_score)

        if not candidates:
            return DomainResponse(
                success=False,
                message="❌ Nenhum candidato encontrado com os critérios especificados",
                error="no_candidates"
            )

        analysis = self._analyze_top_candidates(candidates)
        report = self._format_top_candidates_report(candidates, analysis)

        return DomainResponse(
            success=True,
            message=report,
            data={
                "report_type": "top_candidates",
                "generated_at": datetime.now().isoformat(),
                "sourcing_id": context.sourcing_id,
                "candidates": [self._candidate_to_dict(c) for c in candidates],
                "analysis": analysis,
                "charts": {
                    "score_distribution": self._build_score_chart(candidates),
                    "skills_radar": self._build_skills_radar(candidates),
                    "experience_comparison": self._build_experience_chart(candidates)
                }
            },
            suggestions=[
                f"Detalhes do candidato {candidates[0].get('id', '')}" if candidates else "",
                "Compare estes candidatos",
                "Gerar relatório completo"
            ]
        )

    def _plan_report(self, params: Dict[str, Any], context: DomainContext) -> Dict[str, Any]:
        report_type = params.get("type", "executive")

        return {
            "report_type": report_type,
            "data_needs": [
                "aggregated_stats",
                "top_candidates",
                "score_distribution",
                "skills_analysis",
                "experience_analysis",
                "location_distribution"
            ],
            "analysis_depth": params.get("depth", "detailed"),
            "top_n": params.get("top_n", 10),
            "include_recommendations": True
        }

    def _collect_data(self, plan: Dict[str, Any], context: DomainContext) -> Dict[str, Any]:
        collected = {
            "stats": {},
            "top_candidates": [],
            "all_candidates": [],
            "metrics": {}
        }

        try:
            response = self.get_api_client(context).call("sourced_profile_sourcings_search", {
                "where": {"sourcing_id": int(context.sourcing_id)},
                "order": {"sourcing_score": "desc"},
                "per_page": 100,
                "_single_page": True
            })
            all_data = response.get("data", [])
            collected["all_candidates"] = [
                item.get("attributes", item) for item in all_data]
            collected["top_candidates"] = collected["all_candidates"][:plan["top_n"]]
        except Exception as e:
            logger.error(f"Error fetching candidates: {e}")

        collected["metrics"] = self._calculate_metrics(
            collected["all_candidates"])
        collected["stats"] = self._calculate_stats(collected["all_candidates"])

        return collected

    def _calculate_metrics(self, candidates: List[Dict]) -> Dict[str, Any]:
        if not candidates:
            return {}

        scores = [c.get("score") or c.get("sourcing_score")
                  or 0 for c in candidates]
        valid_scores = [s for s in scores if s > 0]

        experiences = [c.get("total_experience_years")
                       or 0 for c in candidates]
        valid_experiences = [e for e in experiences if e > 0]

        return {
            "total_candidates": len(candidates),
            "with_score": len(valid_scores),
            "avg_score": round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0,
            "max_score": max(valid_scores) if valid_scores else 0,
            "min_score": min(valid_scores) if valid_scores else 0,
            "score_above_90": len([s for s in valid_scores if s >= 90]),
            "score_above_80": len([s for s in valid_scores if s >= 80]),
            "score_above_70": len([s for s in valid_scores if s >= 70]),
            "avg_experience": round(sum(valid_experiences) / len(valid_experiences), 1) if valid_experiences else 0,
            "max_experience": max(valid_experiences) if valid_experiences else 0
        }

    def _calculate_stats(self, candidates: List[Dict]) -> Dict[str, Any]:
        if not candidates:
            return {}

        locations = {}
        skills_count = {}
        companies = {}

        for c in candidates:
            city = c.get("city", "N/A")
            if city and city != "N/A":
                locations[city] = locations.get(city, 0) + 1

            company = c.get("current_company", "N/A")
            if company and company != "N/A":
                companies[company] = companies.get(company, 0) + 1

            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            skills = analysis.get("skills_assessment", {}).get("strong", [])
            for skill in skills:
                skill_lower = skill.lower()
                skills_count[skill_lower] = skills_count.get(
                    skill_lower, 0) + 1

        return {
            "by_location": dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_company": dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_skills": dict(sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:15])
        }

    def _analyze_data(self, collected: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        metrics = collected.get("metrics", {})
        stats = collected.get("stats", {})
        top_candidates = collected.get("top_candidates", [])

        try:
            prompt = f"""Você é um consultor de RH sênior analisando uma busca de talentos.

MÉTRICAS:
- Total de candidatos: {metrics.get('total_candidates', 0)}
- Score médio: {metrics.get('avg_score', 0)}
- Candidatos com score >= 90: {metrics.get('score_above_90', 0)}
- Candidatos com score >= 80: {metrics.get('score_above_80', 0)}
- Experiência média: {metrics.get('avg_experience', 0)} anos

TOP SKILLS ENCONTRADAS:
{list(stats.get('top_skills', {}).items())[:10]}

DISTRIBUIÇÃO POR CIDADE:
{list(stats.get('by_location', {}).items())[:5]}

TOP 3 CANDIDATOS:
{[{
                'nome': c.get('name'),
                'score': c.get('score') or c.get('sourcing_score'),
                'empresa': c.get('current_company'),
                'experiencia': c.get('total_experience_years')
            } for c in top_candidates[:3]]}

Gere uma análise executiva em JSON com:
1. "executive_summary": Resumo em 2-3 frases sobre a qualidade da pipeline
2. "insights": Array com 3-4 insights importantes (strings)
3. "recommendations": Array com 2-3 recomendações de ação (strings)
4. "pipeline_health": "excellent", "good", "moderate" ou "needs_attention"
5. "hiring_probability": "high", "medium" ou "low"

Responda APENAS o JSON, sem markdown."""

            response = self.llm.invoke([
                SystemMessage(
                    content="Você retorna apenas JSON válido, sem formatação markdown."),
                HumanMessage(content=prompt)
            ])

            import json
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            return json.loads(content)

        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {
                "executive_summary": f"Pipeline com {metrics.get('total_candidates', 0)} candidatos, score médio de {metrics.get('avg_score', 0)}.",
                "insights": [
                    f"{metrics.get('score_above_80', 0)} candidatos com score acima de 80",
                    f"Experiência média de {metrics.get('avg_experience', 0)} anos"
                ],
                "recommendations": ["Revisar os candidatos com maior score"],
                "pipeline_health": "good" if metrics.get('avg_score', 0) >= 70 else "moderate",
                "hiring_probability": "high" if metrics.get('score_above_90', 0) >= 3 else "medium"
            }

    def _format_executive_report(
        self,
        collected: Dict[str, Any],
        analysis: Dict[str, Any],
        plan: Dict[str, Any]
    ) -> str:
        metrics = collected.get("metrics", {})
        stats = collected.get("stats", {})
        top_candidates = collected.get("top_candidates", [])

        health_emoji = {
            "excellent": "🟢",
            "good": "🟡",
            "moderate": "🟠",
            "needs_attention": "🔴"
        }.get(analysis.get("pipeline_health", "moderate"), "⚪")

        lines = [
            "# 📊 Relatório Executivo de Sourcing",
            "",
            f"*Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}*",
            "",
            "---",
            "",
            "## 📝 Resumo Executivo",
            "",
            f"> {analysis.get('executive_summary', 'Análise não disponível')}",
            "",
            f"**Status da Pipeline:** {health_emoji} {analysis.get('pipeline_health', 'N/A').title()}",
            f"**Probabilidade de Contratação:** {analysis.get('hiring_probability', 'N/A').title()}",
            "",
            "---",
            "",
            "## 📈 Métricas Principais",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| 👥 Total de Candidatos | **{metrics.get('total_candidates', 0)}** |",
            f"| 📊 Score Médio | **{metrics.get('avg_score', 0)}** |",
            f"| ⭐ Score Máximo | **{metrics.get('max_score', 0)}** |",
            f"| 🎯 Score >= 90 | **{metrics.get('score_above_90', 0)}** |",
            f"| ✅ Score >= 80 | **{metrics.get('score_above_80', 0)}** |",
            f"| 📅 Exp. Média | **{metrics.get('avg_experience', 0)} anos** |",
            "",
            "---",
            "",
            "## 🏆 Top Candidatos",
            ""
        ]

        if top_candidates:
            lines.append("| # | Candidato | Score | Empresa | Exp. |")
            lines.append("|:-:|-----------|:-----:|---------|:----:|")

            for i, c in enumerate(top_candidates[:5], 1):
                name = c.get("name", "N/A")
                score = c.get("score") or c.get("sourcing_score") or "-"
                company = self._sanitize(c.get("current_company", "-"))
                exp = c.get("total_experience_years") or "-"
                lines.append(
                    f"| {i} | {name} | **{score}** | {company} | {exp} |")

        lines.extend([
            "",
            "---",
            "",
            "## 💡 Insights",
            ""
        ])

        for insight in analysis.get("insights", []):
            lines.append(f"- {insight}")

        lines.extend([
            "",
            "---",
            "",
            "## 🛠️ Skills Mais Encontradas",
            ""
        ])

        top_skills = list(stats.get("top_skills", {}).items())[:8]
        if top_skills:
            max_count = top_skills[0][1] if top_skills else 1
            for skill, count in top_skills:
                bar_len = int((count / max_count) * 10)
                bar = "█" * bar_len + "░" * (10 - bar_len)
                lines.append(f"- `{skill}` {bar} ({count})")

        lines.extend([
            "",
            "---",
            "",
            "## 📍 Distribuição Geográfica",
            ""
        ])

        locations = list(stats.get("by_location", {}).items())[:5]
        if locations:
            for city, count in locations:
                lines.append(f"- **{city}**: {count} candidatos")

        lines.extend([
            "",
            "---",
            "",
            "## ✅ Recomendações",
            ""
        ])

        for i, rec in enumerate(analysis.get("recommendations", []), 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def _prepare_chart_data(self, collected: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        metrics = collected.get("metrics", {})
        stats = collected.get("stats", {})
        candidates = collected.get("all_candidates", [])

        score_ranges = {"90-100": 0, "80-89": 0,
                        "70-79": 0, "60-69": 0, "<60": 0}
        for c in candidates:
            score = c.get("score") or c.get("sourcing_score") or 0
            if score >= 90:
                score_ranges["90-100"] += 1
            elif score >= 80:
                score_ranges["80-89"] += 1
            elif score >= 70:
                score_ranges["70-79"] += 1
            elif score >= 60:
                score_ranges["60-69"] += 1
            else:
                score_ranges["<60"] += 1

        exp_ranges = {"0-2": 0, "3-5": 0, "6-10": 0, "11-15": 0, "15+": 0}
        for c in candidates:
            exp = c.get("total_experience_years") or 0
            if exp <= 2:
                exp_ranges["0-2"] += 1
            elif exp <= 5:
                exp_ranges["3-5"] += 1
            elif exp <= 10:
                exp_ranges["6-10"] += 1
            elif exp <= 15:
                exp_ranges["11-15"] += 1
            else:
                exp_ranges["15+"] += 1

        return {
            "score_distribution": {
                "type": "bar",
                "title": "Distribuição de Scores",
                "labels": list(score_ranges.keys()),
                "values": list(score_ranges.values()),
                "colors": ["#22c55e", "#84cc16", "#eab308", "#f97316", "#ef4444"]
            },
            "experience_distribution": {
                "type": "bar",
                "title": "Distribuição de Experiência (anos)",
                "labels": list(exp_ranges.keys()),
                "values": list(exp_ranges.values())
            },
            "top_skills": {
                "type": "horizontal_bar",
                "title": "Skills Mais Encontradas",
                "labels": list(stats.get("top_skills", {}).keys())[:10],
                "values": list(stats.get("top_skills", {}).values())[:10]
            },
            "location_pie": {
                "type": "pie",
                "title": "Distribuição por Localização",
                "labels": list(stats.get("by_location", {}).keys())[:6],
                "values": list(stats.get("by_location", {}).values())[:6]
            },
            "pipeline_funnel": {
                "type": "funnel",
                "title": "Funil de Candidatos",
                "stages": [
                    {"label": "Total", "value": metrics.get(
                        "total_candidates", 0)},
                    {"label": "Score >= 70", "value": metrics.get(
                        "score_above_70", 0)},
                    {"label": "Score >= 80", "value": metrics.get(
                        "score_above_80", 0)},
                    {"label": "Score >= 90", "value": metrics.get(
                        "score_above_90", 0)}
                ]
            },
            "summary_kpis": {
                "type": "kpi_cards",
                "items": [
                    {"label": "Total Candidatos", "value": metrics.get(
                        "total_candidates", 0), "icon": "users"},
                    {"label": "Score Médio", "value": metrics.get(
                        "avg_score", 0), "icon": "chart"},
                    {"label": "Top Performers", "value": metrics.get(
                        "score_above_90", 0), "icon": "star"},
                    {"label": "Exp. Média",
                        "value": f"{metrics.get('avg_experience', 0)} anos", "icon": "briefcase"}
                ]
            }
        }

    def _fetch_top_candidates(self, context: DomainContext, limit: int, min_score: float) -> List[Dict]:
        try:
            response = self.get_api_client(context).call("sourced_profile_sourcings_search", {
                "where": {"sourcing_id": int(context.sourcing_id)},
                "order": {"sourcing_score": "desc"},
                "per_page": 50,
                "_single_page": True
            })
            data = response.get("data", [])
            candidates = [item.get("attributes", item) for item in data]

            filtered = [
                c for c in candidates
                if (c.get("score") or c.get("sourcing_score") or 0) >= min_score
            ]

            return filtered[:limit]
        except Exception as e:
            logger.error(f"Error fetching top candidates: {e}")
            return []

    def _analyze_top_candidates(self, candidates: List[Dict]) -> Dict[str, Any]:
        if not candidates:
            return {}

        try:
            candidates_info = [{
                "nome": c.get("name"),
                "score": c.get("score") or c.get("sourcing_score"),
                "experiencia": c.get("total_experience_years"),
                "empresa": c.get("current_company"),
                "destaques": (c.get("analysis") or {}).get("highlights", [])[:2],
                "alertas": (c.get("analysis") or {}).get("red_flags", [])[:1]
            } for c in candidates[:5]]

            prompt = f"""Analise estes top candidatos e forneça um parecer rápido em JSON:

CANDIDATOS:
{candidates_info}

Retorne JSON com:
1. "best_pick": Nome do melhor candidato e por quê (string)
2. "runner_up": Segundo melhor e por quê (string)  
3. "common_strengths": Array de 2-3 pontos fortes em comum
4. "hiring_advice": Conselho de 1 frase para o gestor

Apenas JSON, sem markdown."""

            response = self.llm.invoke([
                SystemMessage(content="Retorne apenas JSON válido."),
                HumanMessage(content=prompt)
            ])

            import json
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            return json.loads(content)

        except Exception as e:
            logger.error(f"Error analyzing candidates: {e}")
            return {
                "best_pick": f"{candidates[0].get('name', 'N/A')} - maior score",
                "common_strengths": ["Experiência na área"],
                "hiring_advice": "Entrevistar os candidatos com maior score primeiro."
            }

    def _format_top_candidates_report(self, candidates: List[Dict], analysis: Dict[str, Any]) -> str:
        lines = [
            "# 🏆 Relatório de Top Candidatos",
            "",
            f"*{len(candidates)} candidatos selecionados*",
            "",
            "---",
            "",
            "## 🎯 Parecer Rápido",
            "",
            f"**Melhor Escolha:** {analysis.get('best_pick', 'N/A')}",
            ""
        ]

        if analysis.get("runner_up"):
            lines.append(f"**Segunda Opção:** {analysis.get('runner_up')}")
            lines.append("")

        lines.extend([
            f"💡 **Conselho:** {analysis.get('hiring_advice', '')}",
            "",
            "---",
            "",
            "## 📋 Candidatos",
            ""
        ])

        for i, c in enumerate(candidates, 1):
            name = c.get("name", "N/A")
            score = c.get("score") or c.get("sourcing_score") or 0
            company = c.get("current_company", "N/A")
            exp = c.get("total_experience_years") or "N/A"

            analysis_data = c.get("analysis") or c.get("ai_analysis") or {}
            one_liner = analysis_data.get("one_liner", "")

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

            lines.append(f"### {medal} {name}")
            lines.append(
                f"**Score:** {score} | **Empresa:** {company} | **Exp:** {exp} anos")
            if one_liner:
                lines.append(f"> {one_liner}")
            lines.append("")

        if analysis.get("common_strengths"):
            lines.extend([
                "---",
                "",
                "## ✨ Pontos Fortes em Comum",
                ""
            ])
            for strength in analysis.get("common_strengths", []):
                lines.append(f"- {strength}")

        return "\n".join(lines)

    def _candidate_to_dict(self, candidate: Dict) -> Dict[str, Any]:
        analysis = candidate.get(
            "analysis") or candidate.get("ai_analysis") or {}
        return {
            "id": candidate.get("id"),
            "name": candidate.get("name"),
            "score": candidate.get("score") or candidate.get("sourcing_score"),
            "experience_years": candidate.get("total_experience_years"),
            "current_company": candidate.get("current_company"),
            "title": candidate.get("title") or candidate.get("role_name"),
            "city": candidate.get("city"),
            "state": candidate.get("state"),
            "skills": analysis.get("skills_assessment", {}).get("strong", []),
            "highlights": [h.get("description") for h in analysis.get("highlights", [])],
            "red_flags": [{"severity": f.get("severity"), "description": f.get("description")} for f in analysis.get("red_flags", [])]
        }

    def _build_score_chart(self, candidates: List[Dict]) -> Dict[str, Any]:
        return {
            "type": "bar",
            "labels": [c.get("name", "?").split()[0] for c in candidates],
            "values": [c.get("score") or c.get("sourcing_score") or 0 for c in candidates]
        }

    def _build_skills_radar(self, candidates: List[Dict]) -> Dict[str, Any]:
        all_skills = set()
        for c in candidates:
            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            skills = analysis.get("skills_assessment", {}).get("strong", [])
            all_skills.update(skills[:5])

        labels = list(all_skills)[:6]
        datasets = []

        for c in candidates:
            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            skills = set(s.lower() for s in analysis.get(
                "skills_assessment", {}).get("strong", []))
            values = [1 if label.lower() in skills else 0 for label in labels]
            datasets.append({
                "label": c.get("name", "?").split()[0],
                "values": values
            })

        return {
            "type": "radar",
            "labels": labels,
            "datasets": datasets
        }

    def _build_experience_chart(self, candidates: List[Dict]) -> Dict[str, Any]:
        return {
            "type": "horizontal_bar",
            "labels": [c.get("name", "?").split()[0] for c in candidates],
            "values": [c.get("total_experience_years") or 0 for c in candidates]
        }

    def _sanitize(self, value: Optional[str]) -> str:
        if not value:
            return "-"
        return str(value).replace("|", "/")

```

---



# RECRUITER_AGENT_V5 — Part 5: Sourcing Agents, Services, Tools, Workflow, Workers

---

## 📄 src/models/__init__.py

```python
"""Data models for the recruiter agent."""

from .state import QueryState
from .intent import Intent, IntentEntity, FilterCondition, Aggregation
from .api_plan import APIStep, APIPlan
from .response import QueryResponse

__all__ = [
    "QueryState",
    "Intent",
    "IntentEntity",
    "FilterCondition",
    "Aggregation",
    "APIStep",
    "APIPlan",
    "QueryResponse",
]

```

---

## 📄 src/services/memory_service.py

```python
"""
Memory Service for storing and retrieving conversation history.
Implements hybrid memory with PostgreSQL storage.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from ..config.settings import PostgresConfig


logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for managing conversation memory in PostgreSQL.
    Follows Repository pattern for data access.
    """
    
    def __init__(self, config: PostgresConfig):
        """
        Initialize memory service with database configuration.
        
        Args:
            config: PostgreSQL configuration.
        """
        self.config = config
        self._ensure_tables()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            Database connection.
        """
        conn = None
        try:
            conn = psycopg2.connect(self.config.connection_string)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _ensure_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS conversation_history (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255),
            question TEXT NOT NULL,
            answer TEXT,
            intent JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS query_metrics (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            execution_time_ms FLOAT,
            api_calls INTEGER,
            total_records INTEGER,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_conversation_session_id 
            ON conversation_history (session_id);
        CREATE INDEX IF NOT EXISTS idx_conversation_user_id 
            ON conversation_history (user_id);
        CREATE INDEX IF NOT EXISTS idx_conversation_created_at 
            ON conversation_history (created_at);
            
        CREATE INDEX IF NOT EXISTS idx_metrics_session_id 
            ON query_metrics (session_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_created_at 
            ON query_metrics (created_at);
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create tables
                    cursor.execute(create_tables_sql)
                    # Create indexes
                    cursor.execute(create_indexes_sql)
            logger.info("✓ Database tables and indexes created/verified")
        except Exception as e:
            logger.warning(f"Could not create tables/indexes: {e}")
    
    def save_conversation(
        self,
        session_id: str,
        question: str,
        answer: str,
        intent: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        Save a conversation turn to memory.
        
        Args:
            session_id: Unique session identifier.
            question: User's question.
            answer: System's answer.
            intent: Identified intent (optional).
            metadata: Additional metadata (optional).
            user_id: User identifier (optional).
            
        Returns:
            ID of the saved conversation record.
        """
        insert_sql = """
        INSERT INTO conversation_history 
        (session_id, user_id, question, answer, intent, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        insert_sql,
                        (
                            session_id,
                            user_id,
                            question,
                            answer,
                            psycopg2.extras.Json(intent) if intent else None,
                            psycopg2.extras.Json(metadata) if metadata else None
                        )
                    )
                    conversation_id = cursor.fetchone()[0]
            
            logger.debug(f"Saved conversation {conversation_id} for session {session_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            raise
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier.
            limit: Maximum number of records to retrieve.
            
        Returns:
            List of conversation records.
        """
        select_sql = """
        SELECT id, session_id, user_id, question, answer, intent, metadata, created_at
        FROM conversation_history
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(select_sql, (session_id, limit))
                    records = cursor.fetchall()
            
            logger.debug(f"Retrieved {len(records)} records for session {session_id}")
            return [dict(record) for record in records]
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    def save_metrics(
        self,
        session_id: str,
        execution_time_ms: float,
        api_calls: int,
        total_records: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """
        Save query execution metrics.
        
        Args:
            session_id: Session identifier.
            execution_time_ms: Execution time in milliseconds.
            api_calls: Number of API calls made.
            total_records: Total records processed.
            success: Whether query was successful.
            error_message: Error message if failed (optional).
        """
        insert_sql = """
        INSERT INTO query_metrics 
        (session_id, execution_time_ms, api_calls, total_records, success, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        insert_sql,
                        (session_id, execution_time_ms, api_calls, total_records, success, error_message)
                    )
            
            logger.debug(f"Saved metrics for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def get_recent_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent queries across all sessions.
        
        Args:
            limit: Maximum number of queries to retrieve.
            
        Returns:
            List of recent queries.
        """
        select_sql = """
        SELECT ch.question, ch.answer, ch.created_at, qm.execution_time_ms, qm.success
        FROM conversation_history ch
        LEFT JOIN query_metrics qm ON ch.session_id = qm.session_id
        ORDER BY ch.created_at DESC
        LIMIT %s
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(select_sql, (limit,))
                    records = cursor.fetchall()
            
            return [dict(record) for record in records]
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent queries: {e}")
            return []
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier to clear.
        """
        delete_sql = """
        DELETE FROM conversation_history WHERE session_id = %s;
        DELETE FROM query_metrics WHERE session_id = %s;
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(delete_sql, (session_id, session_id))
            
            logger.info(f"Cleared session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

```

---

## 📄 src/workflow/graph.py

```python
"""
LangGraph Workflow for orchestrating multi-agent query system.
Implements the complete agent pipeline.
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from ..models.state import QueryState
from ..agents import (
    IntentAnalyzerAgent,
    APIExecutorAgent,
    DataProcessorAgent,
    AnswerFormatterAgent,
    PlanValidatorAgent,
)
from ..agents.api_planner import APIPlannerAgent


logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph.
    Implements the complete query processing pipeline.
    """

    def __init__(self):
        """Initialize the workflow orchestrator with all agents."""
        self.intent_analyzer = IntentAnalyzerAgent()
        self.api_planner = APIPlannerAgent()
        self.api_executor = APIExecutorAgent()
        self.plan_validator = PlanValidatorAgent()
        self.data_processor = DataProcessorAgent()
        self.answer_formatter = AnswerFormatterAgent()

        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """
        Create the LangGraph workflow.

        Returns:
            Compiled workflow graph.
        """
        # Create graph
        workflow = StateGraph(QueryState)

        # Add nodes (agents)
        workflow.add_node("intent_analyzer", self.intent_analyzer)
        workflow.add_node("api_planner", self.api_planner)
        workflow.add_node("api_executor", self.api_executor)
        workflow.add_node("plan_validator", self.plan_validator)
        workflow.add_node("data_processor", self.data_processor)
        workflow.add_node("answer_formatter", self.answer_formatter)

        # Set entry point
        workflow.set_entry_point("intent_analyzer")

        # Define edges with conditional error handling
        workflow.add_conditional_edges(
            "intent_analyzer",
            self._should_continue,
            {
                "continue": "api_planner",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "api_planner",
            self._should_continue,
            {
                "continue": "api_executor",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "api_executor",
            self._should_continue_or_confirm,
            {
                "continue": "plan_validator",
                "confirm": END,
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "plan_validator",
            self._should_replan_or_continue,
            {
                "continue": "data_processor",
                "replan": "api_planner",
                "abort": "answer_formatter"
            }
        )

        workflow.add_conditional_edges(
            "data_processor",
            self._should_continue,
            {
                "continue": "answer_formatter",
                "end": END
            }
        )

        # Answer formatter always ends
        workflow.add_edge("answer_formatter", END)
        workflow.add_edge("answer_formatter", END)

        # Compile workflow
        return workflow.compile()

    def _should_continue(self, state: QueryState) -> Literal["continue", "end"]:
        """
        Determine if workflow should continue or end.

        Args:
            state: Current query state.

        Returns:
            "continue" to proceed to next agent, "end" to stop.
        """
        # If there's an error, proceed to formatter to format error message
        if state.get("error"):
            # Check if we're at answer_formatter already
            if state.get("final_answer"):
                return "end"
            # Otherwise, skip to formatter
            return "end"

        return "continue"

    def _should_continue_or_confirm(self, state: QueryState) -> Literal["continue", "confirm", "end"]:
        """
        Determine if workflow should continue, request confirmation, or end.

        Args:
            state: Current query state.

        Returns:
            "continue" to proceed, "confirm" if needs user confirmation, "end" to stop.
        """
        # Check if needs confirmation
        if state.get("needs_confirmation"):
            return "confirm"

        # If there's an error, end
        if state.get("error"):
            return "end"

        return "continue"

    def _should_replan_or_continue(self, state: QueryState) -> Literal["continue", "replan", "abort"]:
        """
        Determine if workflow should continue, replan, or abort.

        Args:
            state: Current query state.

        Returns:
            "continue" to proceed to data processor
            "replan" to go back to planner with feedback
            "abort" to format error message and end
        """
        if state.get("needs_replanning") and state.get("attempt_number", 1) < state.get("max_attempts", 3):
            return "replan"
        elif state.get("critical_failure") or state.get("error"):
            return "abort"
        return "continue"

    def process_query(self, question: str, context_state: QueryState = None) -> QueryState:
        """
        Process a user query through the workflow.

        Args:
            question: User question.
            context_state: Optional previous state for context (pagination, follow-up questions)

        Returns:
            Final state with answer and metadata.
        """
        logger.info(f"Processing query: {question}")

        # Initialize state
        initial_state: QueryState = {
            "question": question,
            "messages": [HumanMessage(content=question)],
            "intent": None,
            "api_plan": [],
            "plan_explanation": None,
            "api_results": {},
            "processed_data": {},
            "final_answer": "",
            "error": None,
            "needs_confirmation": False,
            "confirmation_request": None,
            "user_confirmation": None,
            "attempt_number": 1,
            "max_attempts": 3,
            "failed_strategies": [],
            "execution_feedback": [],
            "needs_replanning": False,
            "critical_failure": False,
            "last_query": None,
            "current_page": 1,
            "total_pages": 1,
            "page_size": 30,
            "metadata": {}
        }

        # Se houver contexto anterior, adicionar informações relevantes
        if context_state:
            initial_state["last_query"] = context_state.get("question")
            initial_state["current_page"] = context_state.get(
                "current_page", 1)
            initial_state["total_pages"] = context_state.get("total_pages", 1)
            initial_state["page_size"] = context_state.get("page_size", 30)

            # Adicionar contexto completo da query anterior nas mensagens
            if context_state.get("question"):
                context_msg = f"\n\n[CONTEXTO DA QUERY ANTERIOR]\n"
                context_msg += f"Query anterior: {context_state['question']}\n"
                context_msg += f"Página atual: {context_state.get('current_page', 1)}/{context_state.get('total_pages', 1)}\n"

                # Incluir intent anterior (entidades e ação)
                if context_state.get("intent"):
                    intent = context_state["intent"]
                    context_msg += f"\nAção anterior: {intent.get('main_action', 'N/A')}\n"
                    context_msg += f"Entidades anteriores: {', '.join(intent.get('entities', []))}\n"
                    if intent.get("filters"):
                        context_msg += f"Filtros anteriores: {intent.get('filters')}\n"

                # Se houver plano anterior, incluir detalhes
                if context_state.get("api_plan"):
                    context_msg += f"\nAPIs chamadas anteriormente:\n"
                    # Limitar a 3 steps
                    for i, step in enumerate(context_state["api_plan"][:3], 1):
                        api = step.get("api", "")
                        params = step.get("params", {})
                        context_msg += f"  {i}. {api}\n"
                        if params.get("where"):
                            context_msg += f"     Filtros: {params.get('where')}\n"

                # Incluir resultado anterior se houver
                if context_state.get("api_results"):
                    results_summary = []
                    # Limitar a 2 resultados
                    for key, result in list(context_state["api_results"].items())[:2]:
                        if isinstance(result, dict):
                            count = result.get("count", 0)
                            entity = result.get("entity_type", key)
                            results_summary.append(
                                f"{entity}: {count} registros")
                    if results_summary:
                        context_msg += f"\nResultados anteriores: {', '.join(results_summary)}\n"

                context_msg += "\n⚠️ IMPORTANTE: Se a pergunta atual faz referência à query anterior (ex: 'e do itau?', 'e da google?'), mantenha a mesma ação e entidades, apenas atualize os filtros.\n"

                initial_state["messages"][0] = HumanMessage(
                    content=question + context_msg)

        try:
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)

            logger.info("Query processed successfully")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Return error state
            initial_state["error"] = f"Erro interno: {str(e)}"
            initial_state[
                "final_answer"] = f"❌ Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"

            return initial_state

    def process_query_with_state(self, initial_state: QueryState) -> QueryState:
        """
        Process a query with an existing state (for continuing after confirmation).

        Args:
            initial_state: Pre-configured state with user confirmation.

        Returns:
            Final state with answer and metadata.
        """
        logger.info("Continuing query processing with confirmation")

        try:
            # Execute workflow from the beginning but with confirmation data
            final_state = self.workflow.invoke(initial_state)

            logger.info("Query processed successfully with confirmation")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Return error state
            initial_state["error"] = f"Erro interno: {str(e)}"
            initial_state[
                "final_answer"] = f"❌ Desculpe, ocorreu um erro ao processar sua escolha: {str(e)}"

            return initial_state

    def continue_after_confirmation(self, state: QueryState) -> QueryState:
        """
        Continue processing after user confirmation.
        Skips intent analysis and planning since we already have the plan.

        Args:
            state: State with user confirmation/choice.

        Returns:
            Final state with answer.
        """
        logger.info("Continuing after user confirmation")

        try:
            # Clear the confirmation flag
            state["needs_confirmation"] = False

            # Re-execute from executor onwards
            # The executor will use the user_confirmation to inject the selected item
            state = self.api_executor(state)

            # If still needs confirmation (multi-step), return
            if state.get("needs_confirmation"):
                return state

            # Validate results
            state = self.plan_validator(state)

            # If needs replanning, handle it
            if state.get("needs_replanning"):
                logger.warning("Replanning needed after confirmation")
                state = self.api_planner(state)
                state = self.api_executor(state)
                state = self.plan_validator(state)

            # Process data
            state = self.data_processor(state)

            # Format answer
            state = self.answer_formatter(state)

            logger.info("Query processed successfully after confirmation")
            return state

        except Exception as e:
            logger.error(
                f"Error continuing after confirmation: {e}", exc_info=True)
            state["error"] = f"Erro interno: {str(e)}"
            state["final_answer"] = f"❌ Desculpe, ocorreu um erro: {str(e)}"
            return state


def create_workflow() -> WorkflowOrchestrator:
    """
    Factory function to create workflow orchestrator.

    Returns:
        Configured WorkflowOrchestrator instance.
    """
    return WorkflowOrchestrator()

```

---

## 📄 chat.py

```python
#!/usr/bin/env python3

from src.utils.logger import setup_logging
from src.workflow.graph import create_workflow
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


setup_logging()
logger = logging.getLogger(__name__)


def print_banner():
    print("\n" + "="*80)
    print("🤖 RECRUITER AGENT - CHAT INTERATIVO")
    print("="*80)
    print("Digite suas perguntas e veja o agente trabalhando!")
    print("Comandos especiais:")
    print("  • /quit ou /exit  - Sair do chat")
    print("  • /clear          - Limpar histórico de conversa")
    print("  • /help           - Mostrar esta ajuda")
    print("  • /debug          - Alternar modo debug (verbose)")
    print("  • próxima/anterior - Navegar entre páginas de resultados")
    print("="*80 + "\n")


def print_response(state: dict, show_debug: bool = False):
    print("\n" + "─"*80)

    final_answer = state.get("final_answer", "")
    error = state.get("error")

    if error:
        print(f"❌ ERRO: {error}\n")

    if final_answer:
        print("💬 RESPOSTA:\n")
        print(final_answer)
    else:
        print("⚠️  Nenhuma resposta gerada")

    if show_debug:
        print("\n" + "─"*40 + " DEBUG INFO " + "─"*40)
        print(f"📊 API Calls: {len(state.get('api_plan', []))}")
        print(
            f"📄 Página: {state.get('current_page', 1)}/{state.get('total_pages', 1)}")
        print(
            f"🔄 Tentativas: {state.get('current_attempt', 1)}/{state.get('max_attempts', 3)}")

        api_results = state.get("api_results", {})
        if api_results:
            print(f"\n📦 Dados retornados:")
            for key, value in api_results.items():
                if isinstance(value, dict):
                    count = len(value.get("data", []))
                    total = value.get("total", count)
                    print(f"   • {key}: {count} registros (total: {total})")

    print("─"*80 + "\n")


def detect_pagination_command(user_input: str):
    """
    Detecta comandos de paginação de forma mais flexível.
    Suporta variações naturais de linguagem.
    """
    pagination_map = {
        "proxima pagina": "next", "próxima página": "next",
        "proxima": "next", "próxima": "next", "próximo": "next",
        "proximo": "next", "next": "next", "mais": "next",
        "pagina anterior": "prev", "página anterior": "prev",
        "anterior": "prev", "voltar": "prev", "prev": "prev",
        "previous": "prev"
    }

    user_lower = user_input.lower().strip()

    # Detecção exata
    if user_lower in pagination_map:
        return pagination_map[user_lower]

    # Detecção de número de página com regex flexível
    import re

    # "página 2", "pagina 5", "me mostra a página 2", "ir para página 3"
    page_patterns = [
        r'p[aá]gina\s+(\d+)',
        r'page\s+(\d+)',
        r'ir\s+para\s+(?:a\s+)?p[aá]gina\s+(\d+)',
        r'mostrar?\s+(?:a\s+)?p[aá]gina\s+(\d+)',
        r'ver\s+(?:a\s+)?p[aá]gina\s+(\d+)'
    ]

    for pattern in page_patterns:
        match = re.search(pattern, user_lower)
        if match:
            page_num = int(match.group(1))
            return ("goto", page_num)

    # Detecção de comandos de navegação por palavra-chave
    if any(word in user_lower for word in ["próxim", "proxim", "avançar", "seguinte"]):
        return "next"

    if any(word in user_lower for word in ["anterior", "voltar", "volta"]):
        return "prev"

    return None


def handle_pagination(orchestrator, last_state, action):
    if not last_state:
        print("\n⚠️  Não há contexto de pesquisa anterior para paginar\n")
        return None

    current_page = last_state.get("current_page", 1)
    total_pages = last_state.get("total_pages", 1)
    page_size = last_state.get("page_size", 30)

    if isinstance(action, tuple):
        action_type, page_num = action
        next_page = page_num
    elif action == "next":
        next_page = current_page + 1
    elif action == "prev":
        next_page = max(1, current_page - 1)
    else:
        next_page = current_page

    if next_page > total_pages:
        print(f"\n⚠️  Você já está na última página ({total_pages})\n")
        return None

    if next_page < 1:
        print("\n⚠️  Página inválida\n")
        return None

    print(f"\n📄 Carregando página {next_page}/{total_pages}...\n")

    api_plan = last_state.get("api_plan", [])
    if not api_plan:
        print("\n⚠️  Não há plano de API para re-executar\n")
        return None

    first_step = api_plan[0].copy()
    params = first_step.get("params", {}).copy()
    params["page"] = next_page
    params["limit"] = page_size
    params["_single_page"] = True
    first_step["params"] = params

    updated_plan = [first_step] + api_plan[1:]

    new_state = {
        **last_state,
        "current_page": next_page,
        "api_plan": updated_plan,
        "api_results": {},
        "processed_data": {},
        "final_answer": "",
        "error": None,
        "needs_confirmation": False
    }

    try:
        state = orchestrator.api_executor(new_state)
        if not state.get("error"):
            state = orchestrator.data_processor(state)
            state = orchestrator.answer_formatter(state)
        return state
    except Exception as e:
        print(f"\n❌ Erro ao paginar: {e}\n")
        return None


def main():
    print_banner()

    orchestrator = create_workflow()
    conversation_history = []
    debug_mode = False
    pending_state = None
    last_state = None

    print("✅ Agente inicializado e pronto!\n")

    while True:
        try:
            user_input = input("👤 Você: ").strip()

            if not user_input:
                continue

            if user_input in ["/quit", "/exit", "/q"]:
                print("\n👋 Até logo!\n")
                break

            if user_input == "/clear":
                conversation_history = []
                pending_state = None
                last_state = None
                print("\n🧹 Histórico de conversa limpo!\n")
                continue

            if user_input == "/help":
                print_banner()
                continue

            if user_input == "/debug":
                debug_mode = not debug_mode
                status = "ATIVADO" if debug_mode else "DESATIVADO"
                print(f"\n🔧 Modo debug {status}\n")
                continue

            print("\n🤔 Processando...\n")

            pagination_action = detect_pagination_command(user_input)
            if pagination_action and last_state:
                state = handle_pagination(
                    orchestrator, last_state, pagination_action)
                if state:
                    last_state = state
                    print_response(state, show_debug=debug_mode)
                continue

            if pending_state and pending_state.get("needs_confirmation"):
                confirmation_data = pending_state.get("confirmation_request")
                conf_type = confirmation_data.get("type")

                if conf_type == "input_required":
                    missing_fields = confirmation_data.get("fields", [])

                    print(
                        f"\n📝 {confirmation_data.get('message', 'Preciso de mais informações:')}")
                    print(f"Campos necessários: {', '.join(missing_fields)}")
                    print("\nPor favor, forneça os dados no formato:")
                    print(
                        f"  {missing_fields[0]}: valor, {missing_fields[1] if len(missing_fields) > 1 else 'campo'}: valor, ...")
                    print("Ou digite 'cancelar' para abortar.\n")

                    if user_input.lower() in ["cancelar", "cancel"]:
                        print("\n❌ Operação cancelada\n")
                        pending_state = None
                        continue

                    print(f"\n✅ Dados recebidos, processando criação...\n")
                    state = orchestrator.query(
                        user_input, context_state=pending_state)
                    last_state = state
                    pending_state = None
                    print_response(state, show_debug=debug_mode)
                    continue

                if conf_type == "disambiguation":
                    if user_input.lower() in ["cancelar", "cancel", "0"]:
                        print("\n❌ Operação cancelada\n")
                        pending_state = None
                        continue

                    try:
                        choice_idx = int(user_input)
                        options = confirmation_data.get("options", [])

                        if 1 <= choice_idx <= len(options):
                            selected = options[choice_idx - 1]

                            pending_state["user_confirmation"] = {
                                "save_as": confirmation_data.get("save_as"),
                                "selected_item": selected.get("item", selected)
                            }

                            print(f"\n✅ Selecionado: {selected['name']}")
                            print("\n🤔 Continuando processamento...\n")

                            state = orchestrator.continue_after_confirmation(
                                pending_state)

                            if state.get("needs_confirmation"):
                                pending_state = state
                                print_response(state, show_debug=debug_mode)
                                continue
                            else:
                                pending_state = None
                                last_state = state
                                print_response(state, show_debug=debug_mode)
                                continue
                        else:
                            print("\n❌ Número inválido. Tente novamente.\n")
                            continue
                    except ValueError:
                        print("\n❌ Digite um número válido ou 'cancelar'\n")
                        continue

                elif conf_type in ["bulk_operation", "destructive_action"]:
                    if user_input.lower() in ["s", "sim", "yes", "y", "confirmo"]:
                        pending_state["user_confirmed"] = True
                        pending_state["needs_confirmation"] = False
                        print("\n✅ Confirmado! Executando...\n")

                        state = orchestrator.continue_after_confirmation(
                            pending_state)
                        pending_state = None
                        last_state = state
                        print_response(state, show_debug=debug_mode)
                        continue
                    else:
                        print("\n❌ Operação cancelada\n")
                        pending_state = None
                        continue

            # Tentar detectar paginação primeiro
            pagination_action = detect_pagination_command(user_input)
            if pagination_action and last_state:
                state = handle_pagination(
                    orchestrator, last_state, pagination_action)
                if state:
                    last_state = state
                    print_response(state, show_debug=debug_mode)
                continue

            # Detectar paginação ou referência contextual
            pagination_keywords = ["página", "pagina",
                                   "page", "próxim", "proxim", "anterior"]
            contextual_keywords = ["e do", "e da", "e de", "e no",
                                   "e na", "consegui encontrar", "encontrou", "também"]

            has_pagination_intent = any(
                keyword in user_input.lower() for keyword in pagination_keywords)
            has_contextual_ref = any(keyword in user_input.lower()
                                     for keyword in contextual_keywords)

            # Usar contexto se for paginação OU referência contextual
            if (has_pagination_intent or has_contextual_ref) and last_state:
                if has_pagination_intent:
                    print(
                        "📄 Detectei intenção de paginação. Usando contexto da query anterior...\n")
                else:
                    print(
                        "🔄 Detectei referência ao contexto anterior. Mantendo contexto da conversa...\n")
                state = orchestrator.process_query(
                    user_input, context_state=last_state)
            else:
                state = orchestrator.process_query(user_input)

            conversation_history.append({
                "role": "user",
                "content": user_input
            })

            if state.get("final_answer"):
                conversation_history.append({
                    "role": "assistant",
                    "content": state["final_answer"]
                })

            if state.get("needs_confirmation"):
                pending_state = state
            else:
                last_state = state

            print_response(state, show_debug=debug_mode)

        except KeyboardInterrupt:
            print("\n\n👋 Chat interrompido. Até logo!\n")
            break

        except Exception as e:
            logger.error(f"Erro durante processamento: {e}", exc_info=True)
            print(f"\n❌ ERRO: {e}\n")
            print("Tente novamente ou digite /quit para sair.\n")


if __name__ == "__main__":
    main()

```

---

## 📄 celery_worker.py

```python
#!/usr/bin/env python3
from src.celery_app import app
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


if __name__ == "__main__":
    app.start()

```

---

## 📄 evaluation_worker.py

```python
#!/usr/bin/env python3
"""
Evaluation Worker - Independent RabbitMQ consumer for candidate evaluation.
Processes evaluation requests from the queue and publishes results.
"""

import os
import sys
import json
import time
import signal
import logging
from typing import Dict, Any, Optional

import pika
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.evaluation_service import EvaluationService
from src.utils.logger import setup_logging


# ==========================================
# Configuration & Environment
# ==========================================
load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EVAL_EXCHANGE = os.getenv("EVAL_EXCHANGE", "evaluations_exchange")
EVAL_QUEUE_IN = os.getenv("EVAL_QUEUE_IN", "evaluation_requests")
EVAL_QUEUE_OUT = os.getenv("EVAL_QUEUE_OUT", "evaluation_responses")
EVAL_ROUTING_IN = os.getenv("EVAL_ROUTING_IN", "evaluation_request")
EVAL_ROUTING_OUT = os.getenv("EVAL_ROUTING_OUT", "evaluation_response")

PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", "4"))
HEARTBEAT = int(os.getenv("RABBIT_HEARTBEAT", "60"))
SOCKET_TIMEOUT = int(os.getenv("RABBIT_SOCKET_TIMEOUT", "30"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==========================================
# Setup Logging
# ==========================================
setup_logging(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


# ==========================================
# Evaluation Worker Class
# ==========================================
class EvaluationWorker:
    """Independent worker for processing evaluation requests."""
    
    def __init__(self):
        """Initialize worker with evaluation service."""
        self.running = True
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.evaluation_service = EvaluationService()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        logger.info("✅ Evaluation Worker initialized")
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("⛔ Shutdown signal received, stopping worker...")
        self.running = False
        
        if self.channel:
            try:
                self.channel.stop_consuming()
            except Exception as e:
                logger.warning(f"Error stopping channel: {e}")
    
    def _connect(self) -> None:
        """Establish connection to RabbitMQ with retries."""
        retries = 0
        
        while self.running:
            try:
                logger.info(f"🔗 Connecting to RabbitMQ: {self._mask_url(RABBITMQ_URL)}")
                
                # Create connection parameters
                parameters = pika.URLParameters(RABBITMQ_URL)
                parameters.heartbeat = HEARTBEAT
                parameters.blocked_connection_timeout = 300
                parameters.socket_timeout = SOCKET_TIMEOUT
                parameters.connection_attempts = 10
                parameters.retry_delay = 5
                
                # Connect
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declare exchange
                self.channel.exchange_declare(
                    exchange=EVAL_EXCHANGE,
                    exchange_type="direct",
                    durable=True
                )
                
                # Declare queues
                self.channel.queue_declare(queue=EVAL_QUEUE_IN, durable=True)
                self.channel.queue_declare(queue=EVAL_QUEUE_OUT, durable=True)
                
                # Bind queues
                self.channel.queue_bind(
                    exchange=EVAL_EXCHANGE,
                    queue=EVAL_QUEUE_IN,
                    routing_key=EVAL_ROUTING_IN
                )
                self.channel.queue_bind(
                    exchange=EVAL_EXCHANGE,
                    queue=EVAL_QUEUE_OUT,
                    routing_key=EVAL_ROUTING_OUT
                )
                
                # Set QoS
                self.channel.basic_qos(prefetch_count=PREFETCH_COUNT)
                
                logger.info("✅ Connected to RabbitMQ successfully")
                return
                
            except Exception as e:
                retries += 1
                wait_time = min(30, 3 * retries)
                logger.error(
                    f"❌ Failed to connect to RabbitMQ (attempt {retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
    
    def _process_message(self, ch, method, properties, body):
        """Process incoming evaluation request."""
        correlation_id = self._get_correlation_id(properties)
        
        try:
            # Parse payload
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"❌ [{correlation_id}] Invalid JSON payload: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            logger.info(f"📦 [{correlation_id}] Processing evaluation request")
            logger.debug(f"📦 [{correlation_id}] Payload: {json.dumps(payload, ensure_ascii=False)}")
            
            # Enrich with chatbot_channel from headers if present
            if hasattr(properties, 'headers') and properties.headers:
                if 'chatbot_channel' not in payload and 'chatbot_channel' in properties.headers:
                    payload['chatbot_channel'] = properties.headers['chatbot_channel']
            
            # Process evaluation
            result = self.evaluation_service.evaluate_candidate_response(payload)
            
            if result:
                logger.info(f"✅ [{correlation_id}] Evaluation completed successfully")
                logger.debug(f"🚀 [{correlation_id}] Result: {json.dumps(result, ensure_ascii=False)}")
                
                # Publish result
                ch.basic_publish(
                    exchange=EVAL_EXCHANGE,
                    routing_key=EVAL_ROUTING_OUT,
                    body=json.dumps(result, ensure_ascii=False),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent
                        content_type='application/json',
                        correlation_id=correlation_id
                    )
                )
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.error(f"❌ [{correlation_id}] Evaluation returned None")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                
        except Exception as e:
            logger.error(f"❌ [{correlation_id}] Error processing message: {e}", exc_info=True)
            # Requeue on unexpected errors
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start(self):
        """Start the worker and begin consuming messages."""
        logger.info("🚀 Starting Evaluation Worker")
        logger.info(f"   Exchange: {EVAL_EXCHANGE}")
        logger.info(f"   Queue IN: {EVAL_QUEUE_IN} (routing: {EVAL_ROUTING_IN})")
        logger.info(f"   Queue OUT: {EVAL_QUEUE_OUT} (routing: {EVAL_ROUTING_OUT})")
        logger.info(f"   Prefetch: {PREFETCH_COUNT}")
        
        while self.running:
            try:
                # Connect/reconnect
                self._connect()
                
                if not self.running:
                    break
                
                # Start consuming
                logger.info(f"🎯 Listening for messages on queue: {EVAL_QUEUE_IN}")
                self.channel.basic_consume(
                    queue=EVAL_QUEUE_IN,
                    on_message_callback=self._process_message
                )
                
                self.channel.start_consuming()
                
            except KeyboardInterrupt:
                logger.info("⛔ Worker stopped by user")
                break
                
            except Exception as e:
                logger.error(f"⚠️ Consumer loop interrupted: {e}. Reconnecting in 5s...")
                
                # Close connections
                try:
                    if self.channel and self.channel.is_open:
                        self.channel.close()
                except Exception:
                    pass
                
                try:
                    if self.connection and self.connection.is_open:
                        self.connection.close()
                except Exception:
                    pass
                
                if self.running:
                    time.sleep(5)
        
        # Cleanup
        self._cleanup()
        logger.info("👋 Evaluation Worker stopped")
    
    def _cleanup(self):
        """Clean up connections."""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
        except Exception as e:
            logger.warning(f"Error closing channel: {e}")
        
        try:
            if self.connection and self.connection.is_open:
                self.connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")
    
    @staticmethod
    def _get_correlation_id(properties) -> str:
        """Extract correlation ID from message properties."""
        if hasattr(properties, 'correlation_id') and properties.correlation_id:
            return properties.correlation_id
        return "unknown"
    
    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask sensitive information in URL."""
        try:
            if "@" in url:
                before_at, after_at = url.split("@", 1)
                if ":" in before_at:
                    protocol_user = before_at.split(":", 1)[0]
                    return f"{protocol_user}:****@{after_at}"
            return url
        except Exception:
            return "URL masked"


# ==========================================
# Main Entry Point
# ==========================================
def main():
    """Main entry point for the evaluation worker."""
    try:
        worker = EvaluationWorker()
        worker.start()
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

```

---

## 📄 evaluation_celery_worker.py

```python
#!/usr/bin/env python3
"""
Celery Worker for Evaluation System
Consumes directly from RabbitMQ evaluation_requests queue and publishes to evaluation_responses.
Compatible with Rails ATS system + Celery distributed processing.
"""

from src.config.celery_config import get_celery_config
from src.services.evaluation_service import EvaluationService
import os
import sys
import json
import logging
from typing import Dict, Any, Optional

from celery import Celery, bootsteps
from kombu import Queue, Exchange, Consumer
from kombu.mixins import ConsumerMixin
import pika

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


logger = logging.getLogger(__name__)

# Get config
config = get_celery_config()

# Create Celery app
app = Celery("evaluation_worker")
app.conf.update(
    broker_url=config.broker_url,
    result_backend=config.result_backend,
    task_serializer=config.task_serializer,
    result_serializer=config.result_serializer,
    accept_content=list(config.accept_content) +
    ["application/octet-stream", "application/x-ruby-marshal"],
    timezone=config.timezone,
    enable_utc=config.enable_utc,
    task_track_started=config.task_track_started,
    task_time_limit=config.task_time_limit,
    task_soft_time_limit=config.task_soft_time_limit,
    worker_prefetch_multiplier=config.worker_prefetch_multiplier,
    worker_send_task_events=config.worker_send_task_events,
    task_send_sent_event=config.task_send_sent_event,
)

# RabbitMQ configuration for Rails compatibility
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EVAL_EXCHANGE = os.getenv("EVAL_EXCHANGE", "evaluations_exchange")
EVAL_QUEUE_IN = os.getenv("EVAL_QUEUE_IN", "evaluation_requests")
EVAL_QUEUE_OUT = os.getenv("EVAL_QUEUE_OUT", "evaluation_responses")
EVAL_ROUTING_IN = os.getenv("EVAL_ROUTING_IN", "evaluation_request")
EVAL_ROUTING_OUT = os.getenv("EVAL_ROUTING_OUT", "evaluation_response")


@app.task(bind=True, name="evaluate_candidate_rails")
def evaluate_candidate_rails(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task that processes evaluation and publishes to Rails queue.
    This is the main entry point for evaluations.
    """
    from src.config.settings import get_settings

    # Build correlation ID
    acc = payload.get("account_id", "acc?")
    ec = payload.get("evaluation_candidate_id", "ec?")
    mid = payload.get("message_id", "msg?")
    correlation_id = f"acc-{acc}|ec-{ec}|msg-{mid}"

    logger.info(
        f"📦 [{correlation_id}] Processing evaluation (task_id: {self.request.id})")

    try:
        # Process evaluation
        evaluation_service = EvaluationService()
        result = evaluation_service.evaluate_candidate_response(payload)

        if not result:
            logger.error(f"❌ [{correlation_id}] Evaluation returned None")
            return {"status": "error", "correlation_id": correlation_id}

        logger.info(f"✅ [{correlation_id}] Evaluation completed")

        # Publish result back to Rails queue
        settings = get_settings()

        try:
            params = pika.URLParameters(settings.rabbitmq.url)
            params.heartbeat = 60
            params.socket_timeout = 30

            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            # Declare exchange and output queue
            channel.exchange_declare(
                exchange=EVAL_EXCHANGE,
                exchange_type="direct",
                durable=True
            )
            channel.queue_declare(queue=EVAL_QUEUE_OUT, durable=True)
            channel.queue_bind(
                exchange=EVAL_EXCHANGE,
                queue=EVAL_QUEUE_OUT,
                routing_key=EVAL_ROUTING_OUT
            )

            # Publish result
            channel.basic_publish(
                exchange=EVAL_EXCHANGE,
                routing_key=EVAL_ROUTING_OUT,
                body=json.dumps(result, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                    correlation_id=correlation_id
                )
            )

            connection.close()
            logger.info(
                f"✅ [{correlation_id}] Result published to {EVAL_QUEUE_OUT}")

        except Exception as e:
            logger.error(f"❌ [{correlation_id}] Failed to publish result: {e}")
            raise

        return {"status": "success", "correlation_id": correlation_id}

    except Exception as e:
        logger.error(
            f"❌ [{correlation_id}] Error processing evaluation: {e}", exc_info=True)
        raise


# Custom bootstep to consume from Rails RabbitMQ queue
class RailsQueueConsumer(bootsteps.ConsumerStep):
    """
    Custom Celery consumer that listens to Rails RabbitMQ queue
    and dispatches to Celery tasks.
    """

    def __init__(self, consumer, **kwargs):
        self.consumer = consumer
        self.queue_name = EVAL_QUEUE_IN

    def get_consumers(self, channel):
        """Setup consumer for Rails queue."""
        logger.info(f"🎯 Setting up consumer for queue: {self.queue_name}")

        # Define exchange and queue
        exchange = Exchange(EVAL_EXCHANGE, type="direct", durable=True)
        queue = Queue(
            self.queue_name,
            exchange=exchange,
            routing_key=EVAL_ROUTING_IN,
            durable=True
        )

        # Get prefetch count from consumer
        prefetch = 10  # Default
        if hasattr(self.consumer, 'qos') and self.consumer.qos:
            if hasattr(self.consumer.qos, 'value'):
                prefetch = self.consumer.qos.value

        return [
            Consumer(
                channel,
                queues=[queue],
                callbacks=[self.handle_message],
                accept=["json", "application/json",
                        "application/octet-stream", "application/x-ruby-marshal"],
                prefetch_count=prefetch,
            )
        ]

    def handle_message(self, body, message):
        """Handle incoming message from Rails queue."""
        try:
            # Extract correlation ID
            correlation_id = message.properties.get(
                "correlation_id", "unknown")

            logger.info(
                f"📨 [{correlation_id}] Received message from Rails queue")

            # Parse payload
            if isinstance(body, bytes):
                payload = json.loads(body.decode("utf-8"))
            elif isinstance(body, str):
                payload = json.loads(body)
            else:
                payload = body

            # Enrich with chatbot_channel from headers if present
            headers = message.headers or {}
            if 'chatbot_channel' not in payload and 'chatbot_channel' in headers:
                payload['chatbot_channel'] = headers['chatbot_channel']

            # Dispatch to Celery task
            evaluate_candidate_rails.apply_async(
                args=[payload],
                task_id=f"eval-{correlation_id}",
            )

            # Acknowledge message
            message.ack()
            logger.info(
                f"✅ [{correlation_id}] Message dispatched to Celery worker")

        except Exception as e:
            logger.error(f"❌ Error handling message: {e}", exc_info=True)
            message.reject(requeue=True)


# Register the custom consumer
app.steps['consumer'].add(RailsQueueConsumer)


if __name__ == "__main__":
    # This allows running the worker with: python evaluation_celery_worker.py worker
    app.worker_main()

```

---



# RECRUITER_AGENT_V5 — Part 6: Scripts, Deploy, Examples, Setup

---

## 📄 examples.py

```python
"""
Example usage of the Recruiter Agent V5.
Demonstrates various ways to use the system.
"""

import logging
from pathlib import Path

from src.config.settings import get_settings
from src.workflow.graph import create_workflow
from src.utils.logger import setup_logging
from src.models.response import QueryResponse


def example_basic_query():
    """Example 1: Basic query processing."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Query Processing")
    print("=" * 60)
    
    # Setup
    setup_logging(level="INFO")
    workflow = create_workflow()
    
    # Process query
    question = "Quantos candidatos temos em São Paulo?"
    print(f"\n❓ Question: {question}")
    
    state = workflow.process_query(question)
    
    print(f"\n📊 Answer:\n{state['final_answer']}")
    print(f"\n⏱️  Execution time: {state.get('metadata', {}).get('execution_time_ms', 0):.2f}ms")


def example_multiple_queries():
    """Example 2: Processing multiple queries."""
    print("\n" + "=" * 60)
    print("Example 2: Multiple Queries")
    print("=" * 60)
    
    setup_logging(level="WARNING")  # Less verbose
    workflow = create_workflow()
    
    questions = [
        "Liste candidatos de São Paulo",
        "Quantas vagas remotas existem?",
        "Qual a média de expectativa salarial CLT?",
        "Candidatos que se aplicaram para vagas remotas"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. ❓ {question}")
        
        state = workflow.process_query(question)
        answer = state['final_answer']
        
        # Show first 200 characters
        if len(answer) > 200:
            answer = answer[:200] + "..."
        
        print(f"   📊 {answer}")


def example_with_error_handling():
    """Example 3: Query with error handling."""
    print("\n" + "=" * 60)
    print("Example 3: Error Handling")
    print("=" * 60)
    
    setup_logging(level="ERROR")
    workflow = create_workflow()
    
    # Try an invalid query
    question = "Calcule a correlação quântica dos candidatos"
    print(f"\n❓ Question: {question}")
    
    try:
        state = workflow.process_query(question)
        
        if state.get('error'):
            print(f"\n⚠️  Error detected: {state['error']}")
            print(f"📝 System still provided answer:\n{state['final_answer']}")
        else:
            print(f"\n✅ Success!\n{state['final_answer']}")
    
    except Exception as e:
        print(f"\n❌ Exception caught: {e}")


def example_metadata_analysis():
    """Example 4: Analyzing query metadata."""
    print("\n" + "=" * 60)
    print("Example 4: Metadata Analysis")
    print("=" * 60)
    
    setup_logging(level="WARNING")
    workflow = create_workflow()
    
    question = "Candidatos com expectativa CLT acima de 10000"
    print(f"\n❓ Question: {question}")
    
    state = workflow.process_query(question)
    
    # Analyze metadata
    print("\n📈 Query Metadata:")
    print(f"  - Intent: {state.get('intent', {}).get('main_action', 'N/A')}")
    print(f"  - Entities: {', '.join(state.get('intent', {}).get('entities', []))}")
    print(f"  - API Plan Steps: {len(state.get('api_plan', []))}")
    
    processed = state.get('processed_data', {})
    summary = processed.get('summary', {})
    
    print(f"  - API Calls: {summary.get('total_api_calls', 0)}")
    print(f"  - Records Processed: {summary.get('total_records', 0)}")
    
    if state.get('error'):
        print(f"  - Error: {state['error']}")
    else:
        print("  - Status: ✅ Success")


def main():
    """Run all examples."""
    print("\n" + "🤖 Recruiter Agent V5 - Usage Examples ".center(60, "="))
    
    try:
        example_basic_query()
        example_multiple_queries()
        example_with_error_handling()
        example_metadata_analysis()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    
    except Exception as e:
        print(f"\n\n❌ Error running examples: {e}")
        logging.exception("Error in examples")


if __name__ == "__main__":
    main()

```

---

## 📄 examples/demo_hallucination_prevention.py

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domains.sourced_profile_sourcing.validators import DataValidator
from src.domains.sourced_profile_sourcing.fact_checker import FactChecker

print("\n🛡️  SISTEMA DE PREVENÇÃO DE ALUCINAÇÕES 🛡️\n")

fact_checker = FactChecker()
sample_candidates = [
    {"id": 1, "name": "João", "score": 85},
    {"id": 2, "name": "Maria", "score": 90},
    {"id": 3, "name": "Pedro", "score": 75}
]

print("✅ Fact-checking: Contagem")
result = fact_checker.verify_count_claim(3, sample_candidates)
print(f"   Verificado: {result.verified}, Confidence: {result.confidence}")

print("\n✅ Fact-checking: Média")
result = fact_checker.verify_average_claim(83.33, sample_candidates, 'score')
print(f"   Verificado: {result.verified}, Confidence: {result.confidence:.2f}")

print("\n✅ Validação: Score Range")
validator = DataValidator()
result = validator.validate_score_range(70, 90)
print(f"   Válido: {result.valid}, Confidence: {result.confidence}")

print("\n🎉 Todas proteções funcionando!")

```

---

## 📄 scripts/README.md

```markdown
# Scripts do Sistema RAG

Este diretório contém todos os scripts necessários para configurar, manter e monitorar o sistema RAG.

## 📋 Scripts Disponíveis

### 🔧 Setup e Configuração

#### `setup_rag.sh` ⭐
**Setup automático completo do sistema RAG**

```bash
./scripts/setup_rag.sh
```

Executa sequencialmente:
1. `setup_database.py` - Cria database e extensões
2. `run_migrations.py` - Executa migrações SQL
3. `embed_documentation.py` - Gera embeddings
4. `analyze_rag_quality.py` - Testa qualidade

**Quando usar:** Primeira instalação ou reset completo

---

#### `setup_database.py`
**Cria database e habilita extensões PostgreSQL**

```bash
python scripts/setup_database.py
```

**O que faz:**
- Cria database `recruiter_agent_v5_development`
- Habilita extensão `vector` (pgvector)
- Habilita extensão `pg_trgm` (full-text search)

**Quando usar:** 
- Setup inicial
- Após reinstalar PostgreSQL
- Criar novo environment

---

#### `run_migrations.py`
**Executa migrações SQL**

```bash
python scripts/run_migrations.py
```

**O que faz:**
- Lê arquivos em `scripts/migrations/` (ordem alfabética)
- Executa cada migration no database
- Cria tabelas, índices, views, triggers

**Quando usar:**
- Após `setup_database.py`
- Quando adicionar novas migrations
- Para atualizar schema

---

### 🧠 Embeddings

#### `embed_documentation.py`
**Processa documentações YAML e gera embeddings**

```bash
python scripts/embed_documentation.py
```

**O que faz:**
1. Carrega todos `.yml` de `documentation/`
2. Extrai campos relevantes (summary, description, keywords)
3. Gera embeddings via OpenAI (text-embedding-3-small)
4. Insere/atualiza no banco (`api_docs` table)

**Quando usar:**
- Após adicionar/modificar YAMLs
- Periodicamente para refresh
- Após mudanças em synonyms/keywords

**Custo:** ~$0.02 por 1000 documentações

---

### 📊 Monitoramento e Qualidade

#### `analyze_rag_quality.py`
**Testa qualidade do retrieval com casos de teste**

```bash
python scripts/analyze_rag_quality.py
```

**O que faz:**
- Executa 10 queries de teste
- Compara busca híbrida vs semântica
- Calcula accuracy metrics
- Mostra resultados detalhados

**Métricas:**
- Hit rate (top-3, top-5)
- Hybrid vs Semantic accuracy
- Resultados por query

**Quando usar:**
- Após `embed_documentation.py`
- Para validar mudanças
- Monitoramento periódico

**Output esperado:**
```
Hybrid Search Accuracy: 85.0%
Semantic Search Accuracy: 75.0%
```

---

#### `validate_rag_setup.py`
**Valida configuração completa do sistema**

```bash
python scripts/validate_rag_setup.py
```

**O que verifica:**
1. ✅ Database criado e extensões habilitadas
2. ✅ Tabela `api_docs` e índices existem
3. ✅ Documentações carregadas
4. ✅ Embeddings gerados
5. ✅ EmbeddingService funcionando
6. ✅ RAGService funcionando
7. ✅ Agentes integrados
8. ✅ Arquivos YAML válidos

**Quando usar:**
- Após setup completo
- Para troubleshooting
- Antes de deploy

---

### 🗄️ Migrations

#### `migrations/001_create_api_docs.sql`
**Migration inicial do schema RAG**

**Cria:**
- Tabela `api_docs` com todos os campos
- Coluna `embedding` (vector 1536d)
- Índices HNSW e GIN
- Views de estatísticas
- Triggers e funções

**Estrutura principal:**
```sql
CREATE TABLE api_docs (
    id SERIAL PRIMARY KEY,
    api_id VARCHAR(255) UNIQUE,
    entity_group VARCHAR(100),
    category VARCHAR(50),
    method VARCHAR(10),
    path TEXT,
    summary TEXT,
    description TEXT,
    search_text TEXT,
    keywords TEXT[],
    embedding vector(1536),
    ...
);
```

---

## 🔄 Fluxo de Trabalho

### Setup Inicial

```bash
# 1. Setup completo (recomendado)
./scripts/setup_rag.sh

# OU passo a passo:

# 1a. Database
python scripts/setup_database.py

# 1b. Migrations
python scripts/run_migrations.py

# 1c. Embeddings
python scripts/embed_documentation.py

# 1d. Validação
python scripts/validate_rag_setup.py
```

---

### Adicionar Nova Documentação

```bash
# 1. Criar/editar YAML
nano documentation/new_api.yml

# 2. Re-gerar embeddings
python scripts/embed_documentation.py

# 3. Testar qualidade
python scripts/analyze_rag_quality.py
```

---

### Atualizar Documentações Existentes

```bash
# 1. Editar YAMLs
nano documentation/*.yml

# 2. Re-processar (upsert automático)
python scripts/embed_documentation.py

# 3. Validar
python scripts/validate_rag_setup.py
```

---

### Troubleshooting

```bash
# Validar setup completo
python scripts/validate_rag_setup.py

# Verificar embeddings
psql -d recruiter_agent_v5_development -c "
    SELECT COUNT(*) as total,
           COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings
    FROM api_docs;
"

# Re-gerar tudo
./scripts/setup_rag.sh
```

---

## 📁 Estrutura de Diretórios

```
scripts/
├── setup_rag.sh                  # Setup automático ⭐
├── setup_database.py             # Cria DB e extensões
├── run_migrations.py             # Executa migrations
├── embed_documentation.py        # Gera embeddings
├── analyze_rag_quality.py        # Testa qualidade
├── validate_rag_setup.py         # Valida setup
├── concat_python_files.py        # Concatena arquivos Python
├── concat_candidates_docs.py     # Concatena docs de candidatos
└── migrations/
    └── 001_create_api_docs.sql   # Schema inicial
```

---

## 🔑 Variáveis de Ambiente Necessárias

Adicione ao `.env`:

```bash
# OpenAI (para embeddings)
OPENAI_API_KEY=sk-proj-...

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=recruiter_agent_v5_development
```

---

## 📊 Comandos Úteis

### Verificar Status

```bash
# Contar documentações
psql -d recruiter_agent_v5_development -c "SELECT COUNT(*) FROM api_docs;"

# Docs sem embeddings
psql -d recruiter_agent_v5_development -c "SELECT * FROM api_docs_missing_embeddings;"

# Estatísticas
psql -d recruiter_agent_v5_development -c "SELECT * FROM api_docs_stats;"
```

### Resetar Sistema

```bash
# Dropar tabela
psql -d recruiter_agent_v5_development -c "DROP TABLE IF EXISTS api_docs CASCADE;"

# Re-executar setup
./scripts/setup_rag.sh
```

### Atualizar Índices

```bash
psql -d recruiter_agent_v5_development -c "
    REINDEX INDEX idx_api_docs_embedding_hnsw;
    REINDEX INDEX idx_api_docs_search_text_gin;
"
```

---

## 🐛 Erros Comuns

### "pgvector extension not found"

```bash
# Instalar pgvector
sudo apt install postgresql-14-pgvector
# OU compile manualmente (ver docs/RAG_SYSTEM.md)
```

### "OPENAI_API_KEY not configured"

```bash
# Verificar .env
cat .env | grep OPENAI_API_KEY

# Adicionar se não existir
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

### "Connection refused"

```bash
# Verificar PostgreSQL rodando
sudo systemctl status postgresql

# Verificar porta
sudo netstat -tlnp | grep 5433
```

### "No embeddings generated"

```bash
# Re-executar embedding
python scripts/embed_documentation.py

# Verificar logs para erros
```

---

## 📚 Documentação

- **Guia Rápido:** `docs/RAG_QUICKSTART.md`
- **Documentação Técnica:** `docs/RAG_SYSTEM.md`
- **Resumo Executivo:** `docs/RAG_SUMMARY.md`

---

## ✅ Checklist de Setup

Após executar os scripts, verifique:

- [ ] Database `recruiter_agent_v5_development` criado
- [ ] Extensões `vector` e `pg_trgm` habilitadas
- [ ] Tabela `api_docs` existe
- [ ] Índices HNSW e GIN criados
- [ ] Views `api_docs_stats` e `api_docs_missing_embeddings` criadas
- [ ] Documentações YAML processadas
- [ ] Embeddings gerados (nenhum NULL)
- [ ] Accuracy >80% nos testes
- [ ] Agentes integrados

---

**Última atualização:** Dezembro 2025  
**Versão:** 1.0.0

```

---

## 📄 .github/instructions/base.instructions.md

```markdown
---
applyTo: '**'
---
nunca faca comentario no codigo, ou documentacoes sem eu pedir
use conceitos como dry, solid, kISS, YAGNI, clean code, design patterns, boas praticas de desenvolvimento, early_return (evite fazer if else desnecessarios)

```

---

## 📄 setup.txt

```txt
"""
Multi-Agent Query System - Focado em APIs REST
Resolve perguntas usando APENAS os endpoints disponíveis
"""

from typing import TypedDict, Annotated, Sequence, Literal, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import json
import requests
from datetime import datetime
from collections import Counter, defaultdict


# ============================================================================
# STATE DEFINITION
# ============================================================================

class QueryState(TypedDict):
    """Estado compartilhado entre agentes"""
    question: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    intent: dict  # Intenção identificada
    api_plan: list  # Plano de chamadas de API
    api_results: list  # Resultados brutos das APIs
    processed_data: dict  # Dados processados
    final_answer: str
    error: str


# ============================================================================
# API CLIENT
# ============================================================================

class RecruitmentAPIClient:
    """Cliente para as APIs de recrutamento"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def candidates_search(self, params: dict) -> dict:
        """GET /v1/users/candidates"""
        url = f"{self.base_url}/v1/users/candidates"
        
        # Converte where para string se for dict
        if "where" in params and isinstance(params["where"], dict):
            params["where"] = json.dumps(params["where"])
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def candidates_show(self, candidate_id: int, includes: str = None) -> dict:
        """GET /v1/users/candidates/:id"""
        url = f"{self.base_url}/v1/users/candidates/{candidate_id}"
        params = {"includes": includes} if includes else {}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def jobs_search(self, params: dict) -> dict:
        """GET /v1/users/jobs"""
        url = f"{self.base_url}/v1/users/jobs"
        
        if "where" in params and isinstance(params["where"], dict):
            params["where"] = json.dumps(params["where"])
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def jobs_show(self, job_id: int) -> dict:
        """GET /v1/users/jobs/:id"""
        url = f"{self.base_url}/v1/users/jobs/{job_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def applies_search(self, params: dict) -> dict:
        """GET /v1/users/applies"""
        url = f"{self.base_url}/v1/users/applies"
        
        if "where" in params and isinstance(params["where"], dict):
            params["where"] = json.dumps(params["where"])
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def applies_show(self, apply_id: int) -> dict:
        """GET /v1/users/applies/:id"""
        url = f"{self.base_url}/v1/users/applies/{apply_id}"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


# ============================================================================
# AGENT 1: INTENT ANALYZER
# ============================================================================

def intent_analyzer_agent(state: QueryState) -> QueryState:
    """
    Analisa a pergunta e identifica a intenção
    """
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    
    system_prompt = """Você é o Intent Analyzer. Analise a pergunta e identifique:

1. **entities**: Quais tabelas são necessárias? (candidates, jobs, applies)
2. **main_action**: Qual a ação principal?
   - "list": listar registros
   - "count": contar registros
   - "filter": filtrar por critérios
   - "aggregate": calcular métricas (média, soma, etc)
   - "analyze": análise complexa (correlações, padrões)
   
3. **filters**: Filtros a serem aplicados
4. **aggregations**: Agregações necessárias (count, avg, sum, min, max, group_by)
5. **fields_needed**: Campos específicos necessários

**Tabelas disponíveis:**
- **candidates**: candidatos (name, email, role_name, city, state, clt_expectation, pj_expectation, remote_work, etc)
- **jobs**: vagas (title, description, city, state, is_remote, seniority, salary_from, salary_to, etc)
- **applies**: candidaturas (candidate_id, job_id, selective_process_id, selective_process_status, applied_at, etc)

**Exemplos de intenção:**

Pergunta: "Quantos candidatos se aplicaram para vagas remotas?"
```json
{
  "entities": ["applies", "jobs"],
  "main_action": "count",
  "filters": {"jobs.is_remote": true},
  "aggregations": [{"function": "count", "entity": "applies"}],
  "fields_needed": ["applies.id", "jobs.is_remote"]
}
```

Pergunta: "Liste candidatos de São Paulo com expectativa CLT acima de 10000"
```json
{
  "entities": ["candidates"],
  "main_action": "filter",
  "filters": {
    "city": {"ilike": "%são paulo%"},
    "clt_expectation": {"gt": 10000}
  },
  "aggregations": [],
  "fields_needed": ["id", "name", "email", "city", "clt_expectation"]
}
```

Pergunta: "Qual a média de expectativa salarial dos candidatos que se aplicaram para vaga X?"
```json
{
  "entities": ["applies", "candidates"],
  "main_action": "aggregate",
  "filters": {"applies.job_id": "X"},
  "aggregations": [{"function": "avg", "field": "candidates.clt_expectation"}],
  "fields_needed": ["candidates.clt_expectation"]
}
```

Retorne APENAS o JSON da intenção."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Pergunta: {state['question']}"}
    ]
    
    response = llm.invoke(messages)
    
    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        intent = json.loads(content)
        state["intent"] = intent
        state["messages"].append(AIMessage(
            content=f"✓ Intenção: {intent['main_action']} em {', '.join(intent['entities'])}"
        ))
    except json.JSONDecodeError as e:
        state["error"] = f"Erro ao parsear intenção: {e}"
        state["intent"] = {}
    
    return state


# ============================================================================
# AGENT 2: API PLANNER
# ============================================================================

def api_planner_agent(state: QueryState) -> QueryState:
    """
    Cria plano de execução usando as APIs disponíveis
    """
    intent = state.get("intent", {})
    if not intent or state.get("error"):
        return state
    
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    
    system_prompt = """Você é o API Planner. Converta a intenção em chamadas de API.

**APIs Disponíveis:**

1. **candidates_search**: GET /v1/users/candidates
   - Params: search, page, limit, where (JSON), compact (string), includes
   - Suporta filtros: where={"city": "São Paulo", "clt_expectation": {"gt": 10000}}
   - Compact: "id,name,email,role_name"

2. **jobs_search**: GET /v1/users/jobs
   - Params: search, page, limit, where (JSON), compact
   - Filtros: where={"is_remote": true, "city": "São Paulo"}

3. **applies_search**: GET /v1/users/applies
   - Params: search, page, limit, where (JSON), compact
   - Filtros: where={"job_id": 1, "candidate_id": 5}

4. **candidates_show**: GET /v1/users/candidates/:id
   - Params: id, includes (relacionamentos)

5. **jobs_show**: GET /v1/users/jobs/:id

6. **applies_show**: GET /v1/users/applies/:id

**Regras:**
- Para agregações (count, avg, sum), busque os dados e marque `post_process` para processar in-memory
- Para múltiplas entidades, faça chamadas sequenciais e use `$previous_result` para referências
- Use `compact` para reduzir dados transferidos
- Limite padrão: 100 registros (use paginação se necessário)

**Exemplo de plano:**

```json
[
  {
    "step": 1,
    "api": "applies_search",
    "params": {
      "where": {"job_id": 1},
      "compact": "id,candidate_id",
      "limit": 100
    },
    "save_as": "applies_data",
    "post_process": null
  },
  {
    "step": 2,
    "api": "candidates_search",
    "params": {
      "where": {"id": {"in": "$applies_data.candidate_ids"}},
      "compact": "id,name,clt_expectation"
    },
    "save_as": "candidates_data",
    "post_process": "calculate_avg:clt_expectation"
  }
]
```

Retorne APENAS o array JSON do plano."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Intenção: {json.dumps(intent, indent=2)}\n\nCrie o plano de APIs."}
    ]
    
    response = llm.invoke(messages)
    
    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        plan = json.loads(content)
        state["api_plan"] = plan
        state["messages"].append(AIMessage(
            content=f"✓ Plano: {len(plan)} chamadas de API"
        ))
    except json.JSONDecodeError as e:
        state["error"] = f"Erro ao criar plano: {e}"
        state["api_plan"] = []
    
    return state


# ============================================================================
# AGENT 3: API EXECUTOR
# ============================================================================

def api_executor_agent(state: QueryState) -> QueryState:
    """
    Executa as chamadas de API sequencialmente
    """
    plan = state.get("api_plan", [])
    if not plan or state.get("error"):
        return state
    
    client = RecruitmentAPIClient()
    results = {}
    
    for step in plan:
        step_num = step.get("step", 0)
        api_name = step.get("api", "")
        params = step.get("params", {})
        save_as = step.get("save_as", f"step_{step_num}")
        
        # Substitui variáveis de resultados anteriores
        params = substitute_variables(params, results)
        
        try:
            # Executa API correspondente
            if api_name == "candidates_search":
                result = client.candidates_search(params)
                data = result.get("candidates", [])
                
            elif api_name == "candidates_show":
                candidate_id = params.get("id")
                includes = params.get("includes")
                result = client.candidates_show(candidate_id, includes)
                data = [result]
                
            elif api_name == "jobs_search":
                result = client.jobs_search(params)
                data = result.get("jobs", [])
                
            elif api_name == "jobs_show":
                job_id = params.get("id")
                result = client.jobs_show(job_id)
                data = [result]
                
            elif api_name == "applies_search":
                result = client.applies_search(params)
                data = result.get("applies", [])
                
            elif api_name == "applies_show":
                apply_id = params.get("id")
                result = client.applies_show(apply_id)
                data = [result]
                
            else:
                state["error"] = f"API desconhecida: {api_name}"
                return state
            
            # Salva resultado
            results[save_as] = {
                "api": api_name,
                "params": params,
                "data": data,
                "count": len(data),
                "post_process": step.get("post_process")
            }
            
        except requests.RequestException as e:
            state["error"] = f"Erro ao executar {api_name}: {str(e)}"
            return state
    
    state["api_results"] = results
    state["messages"].append(AIMessage(
        content=f"✓ Executadas {len(results)} chamadas com sucesso"
    ))
    
    return state


def substitute_variables(params: dict, results: dict) -> dict:
    """
    Substitui variáveis $previous_result nos parâmetros
    """
    params_str = json.dumps(params)
    
    # Procura por padrões $variable_name.field
    import re
    variables = re.findall(r'\$([a-zA-Z_]+)\.([a-zA-Z_]+)', params_str)
    
    for var_name, field in variables:
        if var_name in results:
            data = results[var_name]["data"]
            
            # Extrai valores do campo
            if field.endswith("_ids"):
                # Lista de IDs
                field_base = field[:-4]  # Remove "_ids"
                values = [item.get(field_base) for item in data if item.get(field_base)]
            else:
                values = [item.get(field) for item in data if item.get(field)]
            
            # Substitui no JSON
            placeholder = f'"${var_name}.{field}"'
            replacement = json.dumps(values)
            params_str = params_str.replace(placeholder, replacement)
    
    return json.loads(params_str)


# ============================================================================
# AGENT 4: DATA PROCESSOR
# ============================================================================

def data_processor_agent(state: QueryState) -> QueryState:
    """
    Processa dados e executa agregações in-memory
    """
    results = state.get("api_results", {})
    intent = state.get("intent", {})
    
    if not results or state.get("error"):
        return state
    
    processed = {
        "raw_data": results,
        "aggregations": {},
        "summary": {}
    }
    
    # Processa post_process de cada step
    for key, result in results.items():
        data = result["data"]
        post_process = result.get("post_process")
        
        if post_process:
            processed["aggregations"][key] = execute_post_process(data, post_process)
    
    # Calcula agregações solicitadas na intenção
    for agg in intent.get("aggregations", []):
        func = agg.get("function")
        field = agg.get("field", "")
        entity = agg.get("entity")
        
        # Encontra dados da entidade
        entity_data = []
        for result in results.values():
            if entity in result.get("api", ""):
                entity_data = result["data"]
                break
        
        if func == "count":
            processed["aggregations"][f"count_{entity}"] = len(entity_data)
            
        elif func == "avg" and field:
            field_name = field.split(".")[-1]  # Remove prefixo da tabela
            values = [item.get(field_name) for item in entity_data if item.get(field_name)]
            if values:
                processed["aggregations"][f"avg_{field_name}"] = sum(values) / len(values)
        
        elif func == "sum" and field:
            field_name = field.split(".")[-1]
            values = [item.get(field_name) for item in entity_data if item.get(field_name)]
            processed["aggregations"][f"sum_{field_name}"] = sum(values)
        
        elif func == "min" and field:
            field_name = field.split(".")[-1]
            values = [item.get(field_name) for item in entity_data if item.get(field_name)]
            if values:
                processed["aggregations"][f"min_{field_name}"] = min(values)
        
        elif func == "max" and field:
            field_name = field.split(".")[-1]
            values = [item.get(field_name) for item in entity_data if item.get(field_name)]
            if values:
                processed["aggregations"][f"max_{field_name}"] = max(values)
        
        elif func == "group_by" and field:
            field_name = field.split(".")[-1]
            groups = defaultdict(int)
            for item in entity_data:
                key = item.get(field_name)
                if key:
                    groups[key] += 1
            processed["aggregations"][f"group_by_{field_name}"] = dict(groups)
    
    # Resumo geral
    processed["summary"] = {
        "total_records": sum(r["count"] for r in results.values()),
        "apis_called": len(results),
        "aggregations_count": len(processed["aggregations"])
    }
    
    state["processed_data"] = processed
    state["messages"].append(AIMessage(
        content=f"✓ Processados {processed['summary']['total_records']} registros"
    ))
    
    return state


def execute_post_process(data: List[dict], instruction: str) -> Any:
    """
    Executa instruções de pós-processamento
    """
    if not instruction:
        return None
    
    parts = instruction.split(":")
    operation = parts[0]
    
    if operation == "calculate_avg" and len(parts) > 1:
        field = parts[1]
        values = [item.get(field) for item in data if item.get(field)]
        return sum(values) / len(values) if values else 0
    
    elif operation == "count":
        return len(data)
    
    elif operation == "extract_ids":
        return [item.get("id") for item in data if item.get("id")]
    
    elif operation == "group_by" and len(parts) > 1:
        field = parts[1]
        groups = defaultdict(list)
        for item in data:
            key = item.get(field)
            if key:
                groups[key].append(item)
        return {k: len(v) for k, v in groups.items()}
    
    return None


# ============================================================================
# AGENT 5: ANSWER FORMATTER
# ============================================================================

def answer_formatter_agent(state: QueryState) -> QueryState:
    """
    Formata resposta final em linguagem natural
    """
    processed = state.get("processed_data", {})
    intent = state.get("intent", {})
    question = state.get("question", "")
    
    if not processed or state.get("error"):
        if state.get("error"):
            state["final_answer"] = f"❌ Erro: {state['error']}"
        else:
            state["final_answer"] = "❌ Não foi possível processar a pergunta"
        return state
    
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    
    system_prompt = """Você é o Answer Formatter. Formate a resposta de forma clara e objetiva.

**Diretrizes:**
- Use emojis para melhor visualização
- Para listas, mostre no máximo 10 itens principais
- Para números, use formatação brasileira (10.000,00)
- Inclua resumos quantitativos no início
- Se houver muitos resultados, mencione o total e mostre apenas os principais

**Exemplos:**

Pergunta: "Quantos candidatos se aplicaram para vagas remotas?"
```
📊 Total de Candidaturas: 45

🎯 Resumo:
- Candidatos únicos: 32
- Vagas com aplicações: 8
- Média de aplicações por vaga: 5.6
```

Pergunta: "Liste candidatos de São Paulo"
```
👥 Encontrados 12 candidatos em São Paulo:

Top 10:
1. João Silva - Desenvolvedor Full Stack
2. Maria Santos - Designer UX
3. Pedro Costa - Engenheiro de Dados
...

💡 Total: 12 candidatos
```
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""
Pergunta: {question}

Dados processados:
{json.dumps(processed, indent=2, ensure_ascii=False)}

Formate uma resposta clara e objetiva."""}
    ]
    
    response = llm.invoke(messages)
    
    state["final_answer"] = response.content
    state["messages"].append(AIMessage(content="✓ Resposta formatada"))
    
    return state


# ============================================================================
# WORKFLOW GRAPH
# ============================================================================

def create_workflow() -> StateGraph:
    """Cria o grafo de workflow"""
    
    workflow = StateGraph(QueryState)
    
    # Adiciona agentes
    workflow.add_node("intent", intent_analyzer_agent)
    workflow.add_node("planner", api_planner_agent)
    workflow.add_node("executor", api_executor_agent)
    workflow.add_node("processor", data_processor_agent)
    workflow.add_node("formatter", answer_formatter_agent)
    
    # Define fluxo
    workflow.set_entry_point("intent")
    workflow.add_edge("intent", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "processor")
    workflow.add_edge("processor", "formatter")
    workflow.add_edge("formatter", END)
    
    # Adiciona tratamento de erros
    workflow.add_conditional_edges(
        "intent",
        lambda s: "planner" if not s.get("error") else END
    )
    workflow.add_conditional_edges(
        "planner",
        lambda s: "executor" if not s.get("error") else END
    )
    workflow.add_conditional_edges(
        "executor",
        lambda s: "processor" if not s.get("error") else END
    )
    
    return workflow.compile()


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def query_system(question: str, base_url: str = "http://localhost:8080") -> dict:
    """
    Executa uma query no sistema
    
    Args:
        question: Pergunta em linguagem natural
        base_url: URL base da API
    
    Returns:
        dict com resposta e metadados
    """
    workflow = create_workflow()
    
    initial_state = {
        "question": question,
        "messages": [HumanMessage(content=question)],
        "intent": {},
        "api_plan": [],
        "api_results": {},
        "processed_data": {},
        "final_answer": "",
        "error": ""
    }
    
    result = workflow.invoke(initial_state)
    
    return {
        "question": question,
        "answer": result.get("final_answer", "Erro ao processar"),
        "intent": result.get("intent", {}),
        "api_calls": len(result.get("api_results", {})),
        "total_records": result.get("processed_data", {}).get("summary", {}).get("total_records", 0),
        "execution_time": datetime.now().isoformat(),
        "error": result.get("error")
    }


# ============================================================================
# EXEMPLOS DE USO
# ============================================================================

if __name__ == "__main__":
    # Exemplos de perguntas que PODEMOS responder
    
    questions = [
        # Perguntas simples de listagem
        "Liste os candidatos de São Paulo",
        "Mostre as vagas remotas disponíveis",
        "Quais candidatos se aplicaram para a vaga 1?",
        
        # Perguntas com filtros
        "Candidatos com expectativa CLT acima de 10000",
        "Vagas em São Paulo que não são remotas",
        "Candidatos que aceitam trabalho remoto",
        
        # Perguntas de contagem
        "Quantos candidatos se aplicaram para cada vaga?",
        "Quantas vagas remotas existem?",
        "Quantos candidatos temos em cada cidade?",
        
        # Perguntas com agregação
        "Qual a média de expectativa salarial CLT dos candidatos?",
        "Qual a média de aplicações por vaga?",
        "Qual o salário máximo oferecido nas vagas?",
        
        # Perguntas combinadas
        "Quantos candidatos de São Paulo se aplicaram para vagas remotas?",
        "Liste candidatos com GitHub preenchido que se aplicaram para vagas de tecnologia",
    ]
    
    print("🤖 Sistema Multi-Agente - Focado em APIs REST\n")
    print("=" * 60)
    
    # Testa primeira pergunta
    question = questions[0]
    print(f"\n🔍 Pergunta: {question}\n")
    
    result = query_system(question)
    
    print(f"📊 Resposta:\n{result['answer']}\n")
    print(f"📋 Metadados:")
    print(f"  - Chamadas de API: {result['api_calls']}")
    print(f"  - Registros processados: {result['total_records']}")
    print(f"  - Intenção identificada: {result['intent'].get('main_action', 'N/A')}")
    
    if result.get("error"):
        print(f"\n❌ Erro: {result['error']}")
    
    print("\n" + "=" * 60)
    print("\n💡 Outras perguntas que este sistema pode responder:")
    for i, q in enumerate(questions[1:6], 1):
        print(f"  {i}. {q}")

```

---

## 📄 docker-compose.workers.yml

```yaml
version: "3.8"

x-common-env: &common-env
  RABBITMQ_URL: ${RABBITMQ_URL:-amqp://guest:guest@rabbitmq:5672/}
  REDIS_URL: ${REDIS_URL:-redis://redis:6379/0}
  CELERY_BROKER_URL: ${CELERY_BROKER_URL:-amqp://guest:guest@rabbitmq:5672/}
  CELERY_RESULT_BACKEND: ${CELERY_RESULT_BACKEND:-redis://redis:6379/0}
  GEMINI_API_KEY: ${GEMINI_API_KEY}
  GEMINI_MODEL: ${GEMINI_MODEL:-gemini-2.5-flash}
  API_BASE_URL: ${API_BASE_URL}
  ATS_USERNAME: ${ATS_USERNAME}
  ATS_PASSWORD: ${ATS_PASSWORD}
  POSTGRES_HOST: ${POSTGRES_HOST:-postgres}
  POSTGRES_PORT: ${POSTGRES_PORT:-5432}
  POSTGRES_USER: ${POSTGRES_USER:-postgres}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  POSTGRES_DB: ${POSTGRES_DB:-recruiter_agent}

services:
  # ===========================================
  # SOURCING WORKERS (HIGH PRIORITY)
  # ===========================================
  sourcing-dispatcher:
    build: .
    container_name: recruiter-sourcing-dispatcher
    environment:
      <<: *common-env
    command: ["python", "-m", "src.domains.sourced_profile_sourcing.dispatcher"]
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  sourcing-worker-1:
    build: .
    container_name: recruiter-sourcing-worker-1
    environment:
      <<: *common-env
      CELERY_CONCURRENCY: 4
    command: >
      celery -A src.celery_app worker
      --loglevel=info
      --queues=sourcing_high
      --concurrency=4
      --hostname=sourcing-worker-1@%h
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  sourcing-worker-2:
    build: .
    container_name: recruiter-sourcing-worker-2
    environment:
      <<: *common-env
      CELERY_CONCURRENCY: 4
    command: >
      celery -A src.celery_app worker
      --loglevel=info
      --queues=sourcing_high
      --concurrency=4
      --hostname=sourcing-worker-2@%h
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  # ===========================================
  # EVALUATION WORKERS (NORMAL PRIORITY)
  # ===========================================
  evaluation-dispatcher:
    build: .
    container_name: recruiter-evaluation-dispatcher
    environment:
      <<: *common-env
      EVAL_ENABLED: "true"
    command: ["python", "evaluation_dispatcher.py"]
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  evaluation-worker-1:
    build: .
    container_name: recruiter-evaluation-worker-1
    environment:
      <<: *common-env
      CELERY_CONCURRENCY: 4
    command: >
      celery -A src.celery_app worker
      --loglevel=info
      --queues=evaluation_normal
      --concurrency=4
      --hostname=evaluation-worker-1@%h
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  evaluation-worker-2:
    build: .
    container_name: recruiter-evaluation-worker-2
    environment:
      <<: *common-env
      CELERY_CONCURRENCY: 4
    command: >
      celery -A src.celery_app worker
      --loglevel=info
      --queues=evaluation_normal
      --concurrency=4
      --hostname=evaluation-worker-2@%h
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  # ===========================================
  # MIXED WORKERS (ALL QUEUES WITH PRIORITY)
  # ===========================================
  mixed-worker-1:
    build: .
    container_name: recruiter-mixed-worker-1
    environment:
      <<: *common-env
      CELERY_CONCURRENCY: 4
    command: >
      celery -A src.celery_app worker
      --loglevel=info
      --queues=sourcing_high,evaluation_normal,default
      --concurrency=4
      --hostname=mixed-worker-1@%h
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  # ===========================================
  # MONITORING
  # ===========================================
  celery-flower:
    build: .
    container_name: recruiter-celery-flower
    environment:
      <<: *common-env
    command: >
      celery -A src.celery_app flower
      --port=5555
      --broker=${CELERY_BROKER_URL:-amqp://guest:guest@rabbitmq:5672/}
    ports:
      - "5555:5555"
    restart: unless-stopped
    depends_on:
      - rabbitmq
      - redis
    networks:
      - recruiter_network

  # ===========================================
  # INFRASTRUCTURE
  # ===========================================
  rabbitmq:
    image: rabbitmq:3-management
    container_name: recruiter-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - recruiter_network

  redis:
    image: redis:7-alpine
    container_name: recruiter-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - recruiter_network

volumes:
  rabbitmq_data:
  redis_data:

networks:
  recruiter_network:
    driver: bridge

```

---

## 📄 deploy/deploy_prod.sh

```bash
#!/bin/bash
#
# Deploy Script for Recruiter Agent V5
# Usage: ./deploy_prod.sh [branch]
#
# Examples:
#   ./deploy_prod.sh          # Deploy from main branch
#   ./deploy_prod.sh develop  # Deploy from develop branch
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BRANCH="${1:-main}"
# Get the absolute path to the script's directory to resolve repo root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="/opt/recruiter/app"
BACKUP_DIR="/opt/recruiter/backups"
VENV_DIR="/opt/recruiter/venv"
LOG_DIR="/opt/recruiter/logs"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Recruiter Agent V5 - Deploy Script  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running as correct user or with sudo
if [ "$EUID" -ne 0 ] && [ "$(whoami)" != "recruiter" ]; then
    echo -e "${YELLOW}⚠️  Script needs sudo for some operations${NC}"
    echo -e "${YELLOW}   Re-running with sudo...${NC}"
    exec sudo bash "$0" "$@"
fi

# Step 1: Navigate to repo
echo -e "${BLUE}📂 Step 1: Navigating to repository...${NC}"
if [ ! -d "$REPO_DIR" ]; then
    echo -e "${RED}❌ Repository not found at $REPO_DIR${NC}"
    exit 1
fi
cd "$REPO_DIR"
echo -e "${GREEN}✅ In repository: $(pwd)${NC}"

# Step 2: Fetch latest changes
echo -e "${BLUE}📥 Step 2: Fetching latest changes...${NC}"
git fetch origin
echo -e "${GREEN}✅ Fetched latest changes${NC}"

# Step 3: Checkout branch
echo -e "${BLUE}🔀 Step 3: Checking out branch '$BRANCH'...${NC}"
git checkout "$BRANCH"
git pull origin "$BRANCH"
CURRENT_COMMIT=$(git rev-parse --short HEAD)
echo -e "${GREEN}✅ On branch '$BRANCH' at commit $CURRENT_COMMIT${NC}"

# Step 4: Create backup
echo -e "${BLUE}💾 Step 4: Creating backup...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"
if [ -d "$DEPLOY_DIR" ]; then
    cp -r "$DEPLOY_DIR" "$BACKUP_PATH" 2>/dev/null || true
    echo -e "${GREEN}✅ Backup created at $BACKUP_PATH${NC}"
else
    echo -e "${YELLOW}⚠️  No existing deployment to backup${NC}"
fi

# Step 5: Stop workers
echo -e "${BLUE}🛑 Step 5: Stopping workers...${NC}"
supervisorctl stop all 2>/dev/null || true
sleep 2

echo -e "${BLUE}🔪 Killing any remaining Celery processes...${NC}"
pkill -9 -f "celery.*worker" 2>/dev/null || true
pkill -9 -f "celery.*beat" 2>/dev/null || true
sleep 1
echo -e "${GREEN}✅ Workers stopped${NC}"

# Step 6: Deploy code
echo -e "${BLUE}📦 Step 6: Deploying code...${NC}"
mkdir -p "$DEPLOY_DIR"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}🧹 Cleaning Python cache in deploy dir...${NC}"
find "$DEPLOY_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$DEPLOY_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Copy all files (excluding .git, __pycache__, .env, venv)
rsync -av --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.env' \
    --exclude 'venv' \
    --exclude '.venv' \
    --exclude 'node_modules' \
    --exclude '.pytest_cache' \
    --exclude '.mypy_cache' \
    "$REPO_DIR/" "$DEPLOY_DIR/"

echo -e "${GREEN}✅ Code deployed${NC}"

# Step 7: Copy .env if it doesn't exist in deploy dir
echo -e "${BLUE}🔐 Step 7: Checking .env...${NC}"
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    if [ -f "$REPO_DIR/.env" ]; then
        cp "$REPO_DIR/.env" "$DEPLOY_DIR/.env"
        echo -e "${GREEN}✅ .env copied${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env file found - please configure manually${NC}"
    fi
else
    echo -e "${GREEN}✅ .env already exists${NC}"
fi

# Step 8: Fix permissions
echo -e "${BLUE}🔑 Step 8: Fixing permissions...${NC}"
chown -R recruiter:recruiter "$DEPLOY_DIR"
chown -R recruiter:recruiter "$LOG_DIR"
chmod -R 755 "$DEPLOY_DIR"
echo -e "${GREEN}✅ Permissions fixed${NC}"

# Step 9: Install/update dependencies
echo -e "${BLUE}📚 Step 9: Installing dependencies...${NC}"
if [ -f "$DEPLOY_DIR/requirements.txt" ]; then
    sudo -u recruiter "$VENV_DIR/bin/pip" install -r "$DEPLOY_DIR/requirements.txt" --quiet 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Some dependencies may have failed - continuing...${NC}"
    }
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  No requirements.txt found${NC}"
fi

# Step 10: Test import
echo -e "${BLUE}🧪 Step 10: Testing import...${NC}"
cd "$DEPLOY_DIR"
if sudo -u recruiter "$VENV_DIR/bin/python" -c "import src.celery_app" 2>/dev/null; then
    echo -e "${GREEN}✅ Import test passed${NC}"
else
    echo -e "${RED}❌ Import test failed!${NC}"
    echo -e "${YELLOW}   Showing error details...${NC}"
    sudo -u recruiter "$VENV_DIR/bin/python" -c "import src.celery_app" 2>&1 | tail -20
    echo -e "${YELLOW}   Rolling back...${NC}"
    
    if [ -d "$BACKUP_PATH" ]; then
        rm -rf "$DEPLOY_DIR"
        mv "$BACKUP_PATH" "$DEPLOY_DIR"
        echo -e "${YELLOW}   Restored from backup${NC}"
    fi
    
    supervisorctl start all 2>/dev/null || true
    exit 1
fi

# Step 10.5: Rotate logs
echo -e "${BLUE}📜 Rotating logs...${NC}"
for logfile in "$LOG_DIR"/*.log; do
    if [ -f "$logfile" ] && [ -s "$logfile" ]; then
        mv "$logfile" "${logfile}.${TIMESTAMP}" 2>/dev/null || true
    fi
done
echo -e "${GREEN}✅ Logs rotated${NC}"

# Step 11: Start workers
echo -e "${BLUE}🚀 Step 11: Starting workers...${NC}"
supervisorctl reread
supervisorctl update
supervisorctl start main_worker:
supervisorctl start celery_sourcing:
supervisorctl start celery_evaluation:
supervisorctl start celery_mixed:
supervisorctl start celery_beat
# supervisorctl start celery_flower  # DISABLED: Flower causes excessive RabbitMQ message usage

# Wait for workers to start (up to 30s)
echo -e "${BLUE}⏳ Step 12: Waiting for workers to start...${NC}"
for i in {1..6}; do
    sleep 5
    WORKER_STATUS=$(supervisorctl status 2>/dev/null | grep -c "RUNNING" || true)
    if [ "$WORKER_STATUS" -gt 0 ]; then
        break
    fi
    echo -e "${YELLOW}   Waiting for workers... ($i/6)${NC}"
done

# Step 13: Verify workers
echo -e "${BLUE}✔️  Step 13: Verifying workers...${NC}"
TOTAL_WORKERS=$(supervisorctl status 2>/dev/null | wc -l || echo "0")

echo ""
supervisorctl status
echo ""

DEPLOYED_COMMIT=$(cd "$DEPLOY_DIR" && cat .git_commit 2>/dev/null || echo "unknown")

if [ "$WORKER_STATUS" -gt 0 ]; then
    echo "$CURRENT_COMMIT" > "$DEPLOY_DIR/.git_commit"
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   ✅ DEPLOY SUCCESSFUL!               ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}   Branch: $BRANCH${NC}"
    echo -e "${GREEN}   Commit: $CURRENT_COMMIT${NC}"
    echo -e "${GREEN}   Workers: $WORKER_STATUS/$TOTAL_WORKERS running${NC}"
    echo -e "${GREEN}   Time: $(date)${NC}"
    echo -e "${GREEN}   Logs: $LOG_DIR/*.log${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}   ❌ DEPLOY FAILED!                   ${NC}"
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}   No workers started successfully${NC}"
    echo -e "${RED}   Check logs: tail -f $LOG_DIR/*.log${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

# Cleanup old backups (keep last 5)
echo -e "${BLUE}🧹 Cleaning old backups...${NC}"
cd "$BACKUP_DIR"
ls -t | tail -n +6 | xargs -r rm -rf 2>/dev/null || true

echo -e "${BLUE}🧹 Cleaning old rotated logs (keep last 3)...${NC}"
cd "$LOG_DIR"
for base in celery_sourcing celery_evaluation celery_mixed celery_beat; do
    ls -t ${base}*.log.* 2>/dev/null | tail -n +4 | xargs -r rm -f 2>/dev/null || true
done
echo -e "${GREEN}✅ Cleanup complete${NC}"

echo ""
echo -e "${BLUE}📝 Useful commands:${NC}"
echo "   sudo supervisorctl status          - Check worker status"
echo "   sudo tail -f $LOG_DIR/*.log        - View fresh logs"
echo "   sudo supervisorctl restart all     - Restart workers"
echo "   cat $DEPLOY_DIR/.git_commit        - Check deployed commit"
echo ""

```

---

## 📄 deploy/gcp_vm_setup.sh

```bash
#!/bin/bash
#
# Deploy Script para Recruiter Agent com Celery Workers
# Google Cloud VM (Debian/Ubuntu)
#
# Uso:
#   chmod +x deploy/gcp_vm_setup.sh
#   ./deploy/gcp_vm_setup.sh
#

set -e

echo "=========================================="
echo "  Recruiter Agent - GCP VM Setup"
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==========================================
# 1. ATUALIZAR SISTEMA
# ==========================================
log_info "Atualizando sistema..."
sudo apt-get update && sudo apt-get upgrade -y

# ==========================================
# 2. INSTALAR DEPENDÊNCIAS
# ==========================================
log_info "Instalando dependências do sistema..."
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    curl \
    wget \
    htop \
    supervisor \
    nginx \
    redis-server \
    postgresql-client \
    libpq-dev \
    build-essential

# ==========================================
# 3. INSTALAR DOCKER (opcional, para RabbitMQ)
# ==========================================
log_info "Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# ==========================================
# 4. CRIAR USUÁRIO DA APLICAÇÃO
# ==========================================
log_info "Criando usuário da aplicação..."
sudo useradd -r -s /bin/bash -m -d /opt/recruiter recruiter || true
sudo mkdir -p /opt/recruiter/app
sudo mkdir -p /opt/recruiter/logs
sudo mkdir -p /opt/recruiter/venv

# ==========================================
# 5. CLONAR/COPIAR APLICAÇÃO
# ==========================================
log_info "Configurando aplicação..."
# Se estiver fazendo deploy do repositório:
# sudo -u recruiter git clone <repo_url> /opt/recruiter/app

# Ou copie os arquivos manualmente:
# sudo cp -r /path/to/local/recruiter_agent_v5/* /opt/recruiter/app/

# ==========================================
# 6. CRIAR VIRTUAL ENVIRONMENT
# ==========================================
log_info "Criando virtual environment..."
sudo -u recruiter python3.11 -m venv /opt/recruiter/venv
sudo -u recruiter /opt/recruiter/venv/bin/pip install --upgrade pip wheel setuptools

# ==========================================
# 7. INSTALAR DEPENDÊNCIAS PYTHON
# ==========================================
log_info "Instalando dependências Python..."
sudo -u recruiter /opt/recruiter/venv/bin/pip install -r /opt/recruiter/app/requirements.txt

# ==========================================
# 8. CONFIGURAR VARIÁVEIS DE AMBIENTE
# ==========================================
log_info "Criando arquivo de environment..."
cat << 'EOF' | sudo tee /opt/recruiter/.env
# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672/
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_CONCURRENCY=4
CELERY_PREFETCH_MULTIPLIER=1
CELERY_TASK_TIME_LIMIT=300
CELERY_TASK_SOFT_TIME_LIMIT=240

# API
API_BASE_URL=https://your-api.com
ATS_USERNAME=your_username
ATS_PASSWORD=your_password

# Gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# PostgreSQL (para RAG)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=recruiter
POSTGRES_PASSWORD=your_password
POSTGRES_DB=recruiter_agent

# Logging
LOG_LEVEL=INFO
EOF

sudo chown recruiter:recruiter /opt/recruiter/.env
sudo chmod 600 /opt/recruiter/.env

echo ""
log_warn "⚠️  IMPORTANTE: Edite /opt/recruiter/.env com suas credenciais reais!"
echo ""

# ==========================================
# 9. INICIAR RABBITMQ VIA DOCKER
# ==========================================
log_info "Iniciando RabbitMQ..."
sudo docker run -d \
    --name rabbitmq \
    --restart unless-stopped \
    -p 5672:5672 \
    -p 15672:15672 \
    -e RABBITMQ_DEFAULT_USER=guest \
    -e RABBITMQ_DEFAULT_PASS=guest \
    rabbitmq:3-management || true

# ==========================================
# 10. CONFIGURAR REDIS
# ==========================================
log_info "Configurando Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# ==========================================
# 11. CONFIGURAR SUPERVISOR
# ==========================================
log_info "Configurando Supervisor para Celery Workers..."

# Main Worker (RabbitMQ consumer - processa mensagens do Rails)
cat << 'EOF' | sudo tee /etc/supervisor/conf.d/main_worker.conf
[program:main_worker]
command=/opt/recruiter/venv/bin/python -u main.py worker --log-level=INFO
directory=/opt/recruiter/app
user=recruiter
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
startsecs=5
stopwaitsecs=30
stopasgroup=true
killasgroup=true
priority=5
environment=PYTHONPATH="/opt/recruiter/app",HOME="/opt/recruiter"
stdout_logfile=/opt/recruiter/logs/main_worker_%(process_num)02d.log
stderr_logfile=/opt/recruiter/logs/main_worker_%(process_num)02d_error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
EOF

# Worker para sourced_profile_sourcing (HIGH PRIORITY)
cat << 'EOF' | sudo tee /etc/supervisor/conf.d/celery_sourcing.conf
[program:celery_sourcing]
command=/opt/recruiter/venv/bin/celery -A src.celery_app worker --loglevel=info --queues=sourcing_high --concurrency=4 --hostname=sourcing-worker-%(process_num)02d@%%h
directory=/opt/recruiter/app
user=recruiter
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
stopasgroup=true
killasgroup=true
priority=10
environment=PYTHONPATH="/opt/recruiter/app",HOME="/opt/recruiter"
stdout_logfile=/opt/recruiter/logs/celery_sourcing_%(process_num)02d.log
stderr_logfile=/opt/recruiter/logs/celery_sourcing_%(process_num)02d_error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
EOF

# Worker para evaluation (NORMAL PRIORITY)
cat << 'EOF' | sudo tee /etc/supervisor/conf.d/celery_evaluation.conf
[program:celery_evaluation]
command=/opt/recruiter/venv/bin/celery -A src.celery_app worker --loglevel=info --queues=evaluation_normal --concurrency=4 --hostname=evaluation-worker-%(process_num)02d@%%h
directory=/opt/recruiter/app
user=recruiter
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
stopasgroup=true
killasgroup=true
priority=20
environment=PYTHONPATH="/opt/recruiter/app",HOME="/opt/recruiter"
stdout_logfile=/opt/recruiter/logs/celery_evaluation_%(process_num)02d.log
stderr_logfile=/opt/recruiter/logs/celery_evaluation_%(process_num)02d_error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
EOF

# Worker misto (fallback)
cat << 'EOF' | sudo tee /etc/supervisor/conf.d/celery_mixed.conf
[program:celery_mixed]
command=/opt/recruiter/venv/bin/celery -A src.celery_app worker --loglevel=info --queues=sourcing_high,evaluation_normal,default --concurrency=2 --hostname=mixed-worker-%(process_num)02d@%%h
directory=/opt/recruiter/app
user=recruiter
numprocs=1
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
stopasgroup=true
killasgroup=true
priority=30
environment=PYTHONPATH="/opt/recruiter/app",HOME="/opt/recruiter"
stdout_logfile=/opt/recruiter/logs/celery_mixed_%(process_num)02d.log
stderr_logfile=/opt/recruiter/logs/celery_mixed_%(process_num)02d_error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
EOF

# Celery Flower (Monitoramento)
cat << 'EOF' | sudo tee /etc/supervisor/conf.d/celery_flower.conf
[program:celery_flower]
command=/opt/recruiter/venv/bin/celery -A src.celery_app flower --port=5555
directory=/opt/recruiter/app
user=recruiter
numprocs=1
autostart=true
autorestart=true
startsecs=10
priority=40
environment=PYTHONPATH="/opt/recruiter/app",HOME="/opt/recruiter"
stdout_logfile=/opt/recruiter/logs/flower.log
stderr_logfile=/opt/recruiter/logs/flower_error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
EOF

# Celery Beat (Agendador - opcional)
cat << 'EOF' | sudo tee /etc/supervisor/conf.d/celery_beat.conf
[program:celery_beat]
command=/opt/recruiter/venv/bin/celery -A src.celery_app beat --loglevel=info
directory=/opt/recruiter/app
user=recruiter
numprocs=1
autostart=false
autorestart=true
startsecs=10
priority=50
environment=PYTHONPATH="/opt/recruiter/app",HOME="/opt/recruiter"
stdout_logfile=/opt/recruiter/logs/celery_beat.log
stderr_logfile=/opt/recruiter/logs/celery_beat_error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
EOF

# Recarregar supervisor
sudo supervisorctl reread
sudo supervisorctl update

# ==========================================
# 12. CONFIGURAR NGINX (proxy para Flower)
# ==========================================
log_info "Configurando Nginx..."

cat << 'EOF' | sudo tee /etc/nginx/sites-available/recruiter
server {
    listen 80;
    server_name _;

    # Flower Dashboard
    location /flower/ {
        rewrite ^/flower/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
        
        # Basic Auth (recomendado)
        # auth_basic "Restricted";
        # auth_basic_user_file /etc/nginx/.htpasswd;
    }

    # RabbitMQ Management
    location /rabbitmq/ {
        rewrite ^/rabbitmq/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:15672;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/recruiter /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# ==========================================
# 13. CONFIGURAR FIREWALL
# ==========================================
log_info "Configurando firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Nginx)
sudo ufw allow 443/tcp   # HTTPS
# sudo ufw enable        # Descomente para ativar

# ==========================================
# 14. INICIAR SERVIÇOS
# ==========================================
log_info "Iniciando serviços..."
sudo supervisorctl start all

# ==========================================
# RESUMO
# ==========================================
echo ""
echo "=========================================="
echo "  ✅ Setup Completo!"
echo "=========================================="
echo ""
echo "📊 Workers configurados:"
echo "   • 2x celery_sourcing (HIGH PRIORITY, 4 workers cada)"
echo "   • 2x celery_evaluation (NORMAL PRIORITY, 4 workers cada)"
echo "   • 1x celery_mixed (FALLBACK, 2 workers)"
echo "   • 1x celery_flower (Monitoramento)"
echo ""
echo "🔗 URLs:"
echo "   • Flower Dashboard: http://<VM_IP>/flower/"
echo "   • RabbitMQ Dashboard: http://<VM_IP>/rabbitmq/"
echo ""
echo "📝 Comandos úteis:"
echo "   • Ver status: sudo supervisorctl status"
echo "   • Reiniciar: sudo supervisorctl restart all"
echo "   • Logs: tail -f /opt/recruiter/logs/*.log"
echo "   • Escalar: sudo supervisorctl start celery_sourcing:*"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   1. Edite /opt/recruiter/.env com suas credenciais"
echo "   2. Copie o código para /opt/recruiter/app"
echo "   3. Execute: sudo supervisorctl restart all"
echo ""

```

---

## 📄 deploy/add_main_worker.sh

```bash
#!/bin/bash
#
# Adiciona o main_worker ao supervisor
# Execute no servidor: sudo bash add_main_worker.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Adding Main Worker to Supervisor    ${NC}"
echo -e "${BLUE}========================================${NC}"

cat << 'EOF' | sudo tee /etc/supervisor/conf.d/main_worker.conf
[program:main_worker]
command=/opt/recruiter/venv/bin/python -u main.py worker --log-level=INFO
directory=/opt/recruiter/app
user=recruiter
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
startsecs=5
stopwaitsecs=30
stopasgroup=true
killasgroup=true
priority=5
environment=PYTHONPATH="/opt/recruiter/app",HOME="/opt/recruiter"
stdout_logfile=/opt/recruiter/logs/main_worker_%(process_num)02d.log
stderr_logfile=/opt/recruiter/logs/main_worker_%(process_num)02d_error.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
EOF

echo -e "${GREEN}✅ Config created${NC}"

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start main_worker:*

echo ""
sudo supervisorctl status

echo ""
echo -e "${GREEN}✅ Main worker added!${NC}"
echo -e "${BLUE}📝 View logs: sudo tail -f /opt/recruiter/logs/main_worker_*.log${NC}"

```

---



# RECRUITER_AGENT_V5 — Part 5b: Remaining Source Files

---

## 📄 src/api_controllers/__init__.py

```python
"""
API Controllers module for HTTP endpoints.
"""

from .evaluation_controller import evaluation_bp

__all__ = ['evaluation_bp']

```

---

## 📄 src/api_controllers/evaluation_controller.py

```python
"""
Evaluation Controller - HTTP API for evaluation requests.
Receives HTTP requests and publishes to RabbitMQ queue.
"""

import os
import json
import uuid
import logging
from typing import Dict, Any

from flask import Blueprint, request, jsonify, current_app
import pika

from ..config.settings import get_settings


logger = logging.getLogger(__name__)

# Create Blueprint
evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/v1/evaluations')


def require_api_key(f):
    """Decorator to validate API authentication token."""
    def decorator(*args, **kwargs):
        secret_token = os.getenv('INTERNAL_API_SECRET')
        if not secret_token:
            logger.warning("INTERNAL_API_SECRET not configured - API is unprotected!")
        else:
            auth_header = request.headers.get('Authorization')
            if not auth_header or auth_header != f"Bearer {secret_token}":
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorator.__name__ = f.__name__
    return decorator


class RabbitMQPublisher:
    """Helper class for publishing messages to RabbitMQ."""
    
    def __init__(self):
        """Initialize publisher with settings."""
        self.settings = get_settings()
        self.eval_exchange = os.getenv("EVAL_EXCHANGE", "evaluations_exchange")
        self.eval_routing_key = os.getenv("EVAL_ROUTING_IN", "evaluation_request")
    
    def publish_evaluation_request(self, payload: Dict[str, Any]) -> bool:
        """
        Publish evaluation request to RabbitMQ.
        
        Args:
            payload: Evaluation request payload.
            
        Returns:
            True if published successfully, False otherwise.
        """
        connection = None
        channel = None
        
        try:
            # Create connection
            parameters = pika.URLParameters(self.settings.rabbitmq.url)
            parameters.heartbeat = 60
            parameters.blocked_connection_timeout = 300
            parameters.socket_timeout = 30
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Ensure exchange exists
            channel.exchange_declare(
                exchange=self.eval_exchange,
                exchange_type="direct",
                durable=True
            )
            
            # Publish message
            channel.basic_publish(
                exchange=self.eval_exchange,
                routing_key=self.eval_routing_key,
                body=json.dumps(payload, ensure_ascii=False),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json',
                    correlation_id=payload.get('correlation_id', str(uuid.uuid4()))
                )
            )
            
            logger.info(f"✅ Published evaluation request: {payload.get('correlation_id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish evaluation request: {e}", exc_info=True)
            return False
            
        finally:
            # Cleanup
            if channel and channel.is_open:
                try:
                    channel.close()
                except Exception:
                    pass
            
            if connection and connection.is_open:
                try:
                    connection.close()
                except Exception:
                    pass


# Global publisher instance
publisher = RabbitMQPublisher()


@evaluation_bp.route('/request', methods=['POST'])
@require_api_key
def create_evaluation_request():
    """
    Create an evaluation request and publish to queue.
    
    Expected payload:
    {
        "account_id": 123,
        "evaluation_candidate_id": 456,
        "message_id": "msg-789",
        "job_description": "Job description text...",
        "question_text": "What is your experience with Python?",
        "expected_response": "Expected answer (optional)",
        "candidate_answer": "I have 5 years of experience...",
        "history": [
            {"role": "interviewer", "content": "Hello!"},
            {"role": "candidate", "content": "Hi!"}
        ],
        "next_question_hint": {
            "id": 2,
            "text": "Tell me about your projects"
        },
        "style": {
            "persona": "cordial e técnico",
            "pt_br": true
        },
        "is_introduction": false,
        "chatbot_channel": "whatsapp"
    }
    
    Returns:
    {
        "status": "success",
        "message": "Evaluation request published",
        "correlation_id": "uuid",
        "queue": "evaluation_requests"
    }
    """
    correlation_id = str(uuid.uuid4())
    
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Invalid JSON payload",
                "correlation_id": correlation_id
            }), 400
        
        # Add correlation ID
        data['correlation_id'] = correlation_id
        
        # Validate required fields
        required_fields = [
            'job_description',
            'question_text',
            'candidate_answer'
        ]
        
        missing_fields = [f for f in required_fields if not data.get(f)]
        if missing_fields:
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "correlation_id": correlation_id
            }), 400
        
        # Log request
        logger.info(
            f"📨 Received evaluation request: "
            f"account={data.get('account_id')}, "
            f"eval_candidate={data.get('evaluation_candidate_id')}, "
            f"correlation_id={correlation_id}"
        )
        
        # Publish to queue
        success = publisher.publish_evaluation_request(data)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Evaluation request published to queue",
                "correlation_id": correlation_id,
                "queue": os.getenv("EVAL_QUEUE_IN", "evaluation_requests")
            }), 202  # Accepted
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to publish evaluation request",
                "correlation_id": correlation_id
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error in create_evaluation_request: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "correlation_id": correlation_id,
            "details": str(e) if current_app.debug else None
        }), 500


@evaluation_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
    {
        "status": "healthy",
        "service": "evaluation-api",
        "version": "1.0.0"
    }
    """
    return jsonify({
        "status": "healthy",
        "service": "evaluation-api",
        "version": "1.0.0"
    }), 200


@evaluation_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint."""
    return jsonify({"message": "pong"}), 200

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/__init__.py

```python
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse
from src.domains.sourced_profile_sourcing.agents.router import RouterAgent
from src.domains.sourced_profile_sourcing.agents.analytics import AnalyticsAgent
from src.domains.sourced_profile_sourcing.agents.search import SearchAgent
from src.domains.sourced_profile_sourcing.agents.detail import DetailAgent
from src.domains.sourced_profile_sourcing.agents.comparison import ComparisonAgent
from src.domains.sourced_profile_sourcing.agents.report import ReportAgent
from src.domains.sourced_profile_sourcing.agents.action import ActionAgent
from src.domains.sourced_profile_sourcing.agents.orchestrator import MultiAgentOrchestrator

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "RouterAgent",
    "AnalyticsAgent",
    "SearchAgent",
    "DetailAgent",
    "ComparisonAgent",
    "ReportAgent",
    "ActionAgent",
    "MultiAgentOrchestrator",
]

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/action.py

```python
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import re

from src.domains.base import DomainContext
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class ActionType(Enum):
    CONVERT_TO_CANDIDATE = "convert_to_candidate"
    ADD_TO_LIST = "add_to_list"
    CREATE_APPLY = "create_apply"
    UPDATE_PROFILE = "update_profile"
    REMOVE_PROFILE = "remove_profile"


@dataclass
class ActionIntent:
    action_type: ActionType
    target_ids: List[int]
    params: Dict[str, Any]
    confidence: float = 1.0


ACTION_PATTERNS = {
    ActionType.CONVERT_TO_CANDIDATE: [
        r"(?:converter?|importar?|adicionar?)\s+(?:esse?s?|o|a|os|as)?\s*(?:perfis?|candidatos?)\s+(?:para|na|à|a)\s+(?:base|minha base|sistema)",
        r"(?:transformar?|tornar?)\s+(?:em|para)\s+candidatos?",
        r"importar?\s+(?:esse?s?|perfis?|candidatos?)",
        r"(?:trazer?|incluir?)\s+(?:para|na)\s+(?:base|minha base)",
        r"converter?\s+(?:esse?s?|perfis?)",
    ],
    ActionType.ADD_TO_LIST: [
        r"(?:adicionar?|colocar?|incluir?|salvar?)\s+(?:esse?s?|o|a|os|as)?\s*(?:perfis?|candidatos?)?\s*(?:na|em|à)\s+lista",
        r"(?:mover?|enviar?)\s+(?:para|pra)\s+(?:a\s+)?lista",
        r"(?:salvar?|favoritar?)\s+(?:na|em)\s+(?:lista|favoritos)",
        r"lista[rs]?\s+(?:esse?s?|candidatos?)",
        r"(?:criar?|nova)\s+lista\s+com",
    ],
    ActionType.CREATE_APPLY: [
        r"(?:adicionar?|incluir?|colocar?|inscrever?)\s+(?:esse?s?|o|a|os|as)?\s*(?:perfis?|candidatos?)?\s*(?:na|em|à|no)\s+(?:vaga|processo|seletivo)",
        r"(?:criar?|fazer?)\s+(?:candidatura|apply|inscrição|aplicação)",
        r"(?:enviar?|mandar?)\s+(?:para|pra)\s+(?:a\s+)?vaga",
        r"(?:aplicar?|candidatar?)\s+(?:na|em|à)\s+vaga",
        r"(?:mover?|colocar?)\s+(?:no|em)\s+(?:processo|funil|kanban)",
    ],
    ActionType.UPDATE_PROFILE: [
        r"(?:atualizar?|alterar?|mudar?|editar?)\s+(?:o\s+)?score",
        r"(?:definir?|setar?|colocar?)\s+score\s+(?:em|para|como)",
        r"(?:adicionar?|incluir?)\s+(?:nota|comentário|observação)",
        r"(?:mudar?|alterar?)\s+(?:análise|avaliação)",
    ],
    ActionType.REMOVE_PROFILE: [
        r"(?:remover?|excluir?|deletar?|tirar?)\s+(?:esse?s?|o|a|os|as)?\s*(?:perfis?|candidatos?)",
        r"(?:apagar?|eliminar?)\s+(?:da|dessa?)\s+(?:busca|pesquisa|lista)",
        r"(?:descartar?|ignorar?)\s+(?:esse?s?|perfis?|candidatos?)",
        r"não\s+(?:quero|gostei|serve)",
    ],
}


class ActionAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "action"

    @property
    def agent_name(self) -> str:
        return "Action Agent"

    @property
    def description(self) -> str:
        return "Executa ações como converter candidatos, adicionar em listas, criar applies e atualizar perfis"

    @property
    def capabilities(self) -> List[str]:
        return [
            "Converter perfis em candidatos",
            "Adicionar perfis a listas",
            "Criar candidaturas/applies em vagas",
            "Atualizar score e análise",
            "Remover perfis da busca"
        ]

    def get_system_prompt(self, context: DomainContext) -> str:
        return f"""Você é um agente de ações para operações em perfis de sourcing.

**CONTEXTO:**
- Sourcing ID: {context.sourcing_id}

**AÇÕES DISPONÍVEIS:**
- convert_to_candidate: Converter perfis em candidatos
- add_to_list: Adicionar a uma lista
- create_apply: Criar candidatura em vaga
- update_profile: Atualizar score/análise
- remove_profile: Remover da busca"""

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        params = params or {}

        intent = self._identify_action_intent(query, params, context)
        if not intent:
            return AgentResponse(
                success=False,
                message="❌ Não consegui identificar qual ação você deseja realizar.",
                suggestions=[
                    "Converter candidato para base",
                    "Adicionar à lista",
                    "Criar aplicação em vaga"
                ]
            )

        handlers = {
            ActionType.CONVERT_TO_CANDIDATE: self._handle_convert,
            ActionType.ADD_TO_LIST: self._handle_add_to_list,
            ActionType.CREATE_APPLY: self._handle_create_apply,
            ActionType.UPDATE_PROFILE: self._handle_update,
            ActionType.REMOVE_PROFILE: self._handle_remove,
        }

        handler = handlers.get(intent.action_type)
        return handler(intent, context, params)

    def _identify_action_intent(
        self,
        query: str,
        params: Dict[str, Any],
        context: DomainContext
    ) -> Optional[ActionIntent]:
        query_lower = query.lower()

        for action_type, patterns in ACTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    target_ids = self._extract_target_ids(
                        query, params, context)
                    action_params = self._extract_action_params(
                        query, action_type, params)
                    return ActionIntent(
                        action_type=action_type,
                        target_ids=target_ids,
                        params=action_params
                    )

        return None

    def _extract_target_ids(
        self,
        query: str,
        params: Dict[str, Any],
        context: DomainContext
    ) -> List[int]:
        if params.get("candidate_ids"):
            return params["candidate_ids"]

        if params.get("_candidates"):
            return [c.get("id") for c in params["_candidates"] if c.get("id")]

        numbers = re.findall(r'\b(\d+)\b', query)
        explicit_ids = [int(n) for n in numbers if 10 < int(n) < 1000000]
        if explicit_ids:
            return explicit_ids

        if self._mentions_current_selection(query):
            return context.selected_ids or []

        return []

    def _mentions_current_selection(self, query: str) -> bool:
        selection_patterns = [
            r"esse[s]?\s+(?:candidato|perfil)",
            r"ele[s]?",
            r"ela[s]?",
            r"o[s]?\s+(?:selecionado|escolhido|top)",
            r"a[s]?\s+(?:selecionada|escolhida)",
            r"(?:esse|essa|esses|essas)",
        ]
        query_lower = query.lower()
        return any(re.search(p, query_lower) for p in selection_patterns)

    def _extract_action_params(
        self,
        query: str,
        action_type: ActionType,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        extracted = {}
        query_lower = query.lower()

        if action_type == ActionType.ADD_TO_LIST:
            extracted.update(self._extract_list_params(query_lower, params))

        if action_type == ActionType.CREATE_APPLY:
            extracted.update(self._extract_apply_params(query_lower, params))

        if action_type == ActionType.UPDATE_PROFILE:
            extracted.update(self._extract_update_params(query_lower, params))

        return extracted

    def _extract_list_params(self, query: str, params: Dict) -> Dict[str, Any]:
        if params.get("list_id"):
            return {"list_id": params["list_id"]}

        list_match = re.search(r'lista\s+["\']?([^"\']+)["\']?', query)
        if list_match:
            return {"list_name": list_match.group(1).strip()}

        return {}

    def _extract_apply_params(self, query: str, params: Dict) -> Dict[str, Any]:
        result = {}

        if params.get("job_id"):
            result["job_id"] = params["job_id"]

        if params.get("selective_process_id"):
            result["selective_process_id"] = params["selective_process_id"]

        job_match = re.search(r'vaga\s+(?:de\s+)?["\']?([^"\']+)["\']?', query)
        if job_match and "job_id" not in result:
            result["job_name"] = job_match.group(1).strip()

        return result

    def _extract_update_params(self, query: str, params: Dict) -> Dict[str, Any]:
        result = {}

        score_match = re.search(r'score\s+(?:para|em|como|de)?\s*(\d+)', query)
        if score_match:
            result["new_score"] = int(score_match.group(1))

        note_match = re.search(
            r'(?:nota|comentário|observação)[:\s]+["\']?(.+)["\']?$', query)
        if note_match:
            result["note"] = note_match.group(1).strip()

        return result

    def _handle_convert(
        self,
        intent: ActionIntent,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> AgentResponse:
        if not intent.target_ids:
            return self._request_target_selection(
                "converter para candidato",
                context,
                "Qual(is) perfil(s) você quer converter para a base de candidatos?"
            )

        try:
            results = self._execute_conversion(intent.target_ids, context)
            return self._format_conversion_response(results, intent.target_ids)
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return AgentResponse(
                success=False,
                message=f"❌ Erro ao converter: {str(e)}",
                error=str(e)
            )

    def _execute_conversion(
        self,
        profile_ids: List[int],
        context: DomainContext
    ) -> Dict[str, Any]:
        api = self.get_api_operations(context)

        sourced_profile_ids = self._get_sourced_profile_ids(
            profile_ids, context)

        if len(sourced_profile_ids) == 1:
            result = api.convert_to_candidate(sourced_profile_ids[0])
        else:
            result = api.import_to_candidates(sourced_profile_ids)

        return {"data": result.data} if result.success else {"error": result.error}

    def _get_sourced_profile_ids(
        self,
        sps_ids: List[int],
        context: DomainContext
    ) -> List[int]:
        candidates = self._fetch_candidates(
            context,
            limit=len(sps_ids),
            where={"id": {"in": sps_ids}}
        )

        return [c.get("sourced_profile_id") for c in candidates if c.get("sourced_profile_id")]

    def _format_conversion_response(
        self,
        results: Dict[str, Any],
        target_ids: List[int]
    ) -> AgentResponse:
        if results.get("data", {}).get("candidate"):
            candidate = results["data"]["candidate"].get(
                "data", {}).get("attributes", {})
            return AgentResponse(
                success=True,
                message=f"""✅ **Candidato importado com sucesso!**

👤 **{candidate.get('name', 'Candidato')}**
   🆔 ID: #{candidate.get('id')}
   📧 {candidate.get('email', '-')}

O perfil foi adicionado à base de candidatos e já pode ser incluído em processos seletivos.""",
                data={"candidate": candidate, "created": True},
                suggestions=[
                    "Adicionar em uma vaga",
                    "Ver detalhes do candidato",
                    "Adicionar em uma lista"
                ]
            )

        total = results.get("data", {}).get("total", len(target_ids))
        return AgentResponse(
            success=True,
            message=f"""✅ **Conversão iniciada!**

📊 **{total} perfil(s)** sendo convertido(s) para candidatos.

⏳ O processo está rodando em background.
Os candidatos aparecerão na base em alguns instantes.""",
            data={"total": total, "processing": True},
            suggestions=["Verificar candidatos convertidos",
                         "Continuar buscando"]
        )

    def _handle_add_to_list(
        self,
        intent: ActionIntent,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> AgentResponse:
        if not intent.target_ids:
            return self._request_target_selection(
                "adicionar à lista",
                context,
                "Qual(is) perfil(s) você quer adicionar à lista?"
            )

        list_id = intent.params.get("list_id")
        list_name = intent.params.get("list_name")

        if not list_id and not list_name:
            return AgentResponse(
                success=False,
                message="""❓ **Qual lista você quer usar?**

Por favor, especifique:
- O nome da lista: "Adicione na lista Favoritos"
- Ou o ID da lista: "Adicione na lista 123" """,
                suggestions=[
                    "Adicionar na lista Shortlist",
                    "Criar nova lista com esses candidatos"
                ]
            )

        try:
            results = self._execute_add_to_list(
                intent.target_ids, list_id, list_name, context)
            return self._format_list_response(results, intent.target_ids, list_name or f"#{list_id}")
        except Exception as e:
            logger.error(f"Add to list failed: {e}")
            return AgentResponse(
                success=False,
                message=f"❌ Erro ao adicionar à lista: {str(e)}",
                error=str(e)
            )

    def _execute_add_to_list(
        self,
        profile_ids: List[int],
        list_id: Optional[int],
        list_name: Optional[str],
        context: DomainContext
    ) -> Dict[str, Any]:
        api = self.get_api_operations(context)

        if not list_id and list_name:
            list_id = self._resolve_list_id(list_name, context)

        result = api.add_to_list(
            candidate_ids=profile_ids,
            list_id=list_id,
            list_name=list_name
        )
        return {"data": result.data} if result.success else {"error": result.error}

    def _resolve_list_id(self, list_name: str, context: DomainContext) -> int:
        api = self.get_api_operations(context)
        result = api.search_lists(search=list_name)
        if not result.success or not result.data:
            raise ValueError(f"Lista '{list_name}' não encontrada")
        return result.data[0].get("id")

    def _format_list_response(
        self,
        results: Dict[str, Any],
        target_ids: List[int],
        list_identifier: str
    ) -> AgentResponse:
        count = len(target_ids)
        return AgentResponse(
            success=True,
            message=f"""✅ **{count} candidato(s) adicionado(s) à lista!**

📋 Lista: **{list_identifier}**

Os perfis foram salvos e podem ser acessados a qualquer momento.""",
            data={"count": count, "list": list_identifier},
            suggestions=[
                "Ver lista completa",
                "Adicionar mais candidatos",
                "Criar apply com essa lista"
            ]
        )

    def _handle_create_apply(
        self,
        intent: ActionIntent,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> AgentResponse:
        if not intent.target_ids:
            return self._request_target_selection(
                "criar candidatura",
                context,
                "Qual(is) perfil(s) você quer adicionar ao processo seletivo?"
            )

        job_id = intent.params.get("job_id")
        job_name = intent.params.get("job_name")
        selective_process_id = intent.params.get("selective_process_id")

        if not job_id and not job_name:
            return AgentResponse(
                success=False,
                message="""❓ **Qual vaga você quer usar?**

Por favor, especifique:
- O nome da vaga: "Adicione na vaga Python Developer"
- Ou o ID da vaga: "Adicione na vaga 50" """,
                suggestions=[
                    "Ver vagas abertas",
                    "Criar nova vaga"
                ]
            )

        try:
            results = self._execute_create_apply(
                intent.target_ids, job_id, job_name, selective_process_id, context
            )
            return self._format_apply_response(results, intent.target_ids, job_name or f"#{job_id}")
        except Exception as e:
            logger.error(f"Create apply failed: {e}")
            return AgentResponse(
                success=False,
                message=f"❌ Erro ao criar candidatura: {str(e)}",
                error=str(e)
            )

    def _execute_create_apply(
        self,
        profile_ids: List[int],
        job_id: Optional[int],
        job_name: Optional[str],
        selective_process_id: Optional[int],
        context: DomainContext
    ) -> Dict[str, Any]:
        api = self.get_api_operations(context)

        if not job_id and job_name:
            job_id, selective_process_id = self._resolve_job(job_name, context)

        if not selective_process_id:
            selective_process_id = self._get_first_selective_process(
                job_id, context)

        results = []
        for pid in profile_ids:
            result = api.create_apply(
                candidate_id=pid,
                selective_process_id=selective_process_id
            )
            if result.success:
                results.append(result.data)

        return {"data": {"applies": results, "message": f"{len(results)} aplicações criadas"}}

    def _resolve_job(self, job_name: str, context: DomainContext) -> Tuple[int, Optional[int]]:
        api = self.get_api_operations(context)
        result = api.search_jobs(search=job_name)
        if not result.success or not result.data:
            raise ValueError(f"Vaga '{job_name}' não encontrada")

        job = result.data[0]
        return job.get("id"), None

    def _get_first_selective_process(self, job_id: int, context: DomainContext) -> int:
        api = self.get_api_operations(context)
        result = api.search_selective_processes(job_id)
        if not result.success or not result.data:
            raise ValueError(
                f"Nenhum processo seletivo encontrado para a vaga #{job_id}")

        return result.data[0].get("id")

    def _format_apply_response(
        self,
        results: Dict[str, Any],
        target_ids: List[int],
        job_identifier: str
    ) -> AgentResponse:
        count = len(target_ids)
        message = results.get("data", {}).get(
            "message", f"{count} aplicações criadas")

        return AgentResponse(
            success=True,
            message=f"""✅ **{count} candidato(s) adicionado(s) ao processo seletivo!**

📋 Vaga: **{job_identifier}**

{message}

💡 Os candidatos já aparecem no kanban da vaga e podem ser movidos entre as etapas.""",
            data={"count": count, "job": job_identifier},
            suggestions=[
                "Ver candidatos na vaga",
                "Adicionar mais candidatos",
                "Ver outras vagas"
            ]
        )

    def _handle_update(
        self,
        intent: ActionIntent,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> AgentResponse:
        if not intent.target_ids:
            return self._request_target_selection(
                "atualizar",
                context,
                "Qual perfil você quer atualizar?"
            )

        if len(intent.target_ids) > 1:
            return AgentResponse(
                success=False,
                message="❌ Por favor, selecione apenas um perfil para atualizar por vez.",
                suggestions=["Atualizar o primeiro", "Ver lista de perfis"]
            )

        new_score = intent.params.get("new_score")
        note = intent.params.get("note")

        if not new_score and not note:
            return AgentResponse(
                success=False,
                message="""❓ **O que você quer atualizar?**

Por favor, especifique:
- Novo score: "Atualizar score para 85"
- Nova nota: "Adicionar nota: Candidato promissor" """,
                suggestions=["Atualizar score para 80", "Adicionar observação"]
            )

        try:
            results = self._execute_update(
                intent.target_ids[0], new_score, note, context)
            return self._format_update_response(results, new_score, note)
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return AgentResponse(
                success=False,
                message=f"❌ Erro ao atualizar: {str(e)}",
                error=str(e)
            )

    def _execute_update(
        self,
        profile_id: int,
        new_score: Optional[int],
        note: Optional[str],
        context: DomainContext
    ) -> Dict[str, Any]:
        api = self.get_api_operations(context)

        updates = {}
        if new_score is not None:
            updates["score"] = new_score

        if note:
            updates["analysis"] = {
                "manual_review": True,
                "reviewer_notes": note
            }

        result = api.update_sourced_profile(
            profile_id, {"sourced_profile_sourcing": updates})
        return {"data": result.data} if result.success else {"error": result.error}

    def _format_update_response(
        self,
        results: Dict[str, Any],
        new_score: Optional[int],
        note: Optional[str]
    ) -> AgentResponse:
        updates = []
        if new_score is not None:
            updates.append(f"📊 Score atualizado para **{new_score}**")
        if note:
            updates.append(f"📝 Nota adicionada: \"{note}\"")

        return AgentResponse(
            success=True,
            message=f"""✅ **Perfil atualizado!**

{chr(10).join(updates)}""",
            data={"updated": True, "new_score": new_score, "note": note},
            suggestions=["Ver perfil atualizado", "Atualizar outro perfil"]
        )

    def _handle_remove(
        self,
        intent: ActionIntent,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> AgentResponse:
        if not intent.target_ids:
            return self._request_target_selection(
                "remover",
                context,
                "Qual(is) perfil(s) você quer remover da busca?"
            )

        try:
            count = 0
            for profile_id in intent.target_ids:
                self._execute_remove(profile_id, context)
                count += 1

            return self._format_remove_response(count)
        except Exception as e:
            logger.error(f"Remove failed: {e}")
            return AgentResponse(
                success=False,
                message=f"❌ Erro ao remover: {str(e)}",
                error=str(e)
            )

    def _execute_remove(self, profile_id: int, context: DomainContext) -> Dict[str, Any]:
        api = self.get_api_operations(context)
        result = api.delete_sourced_profile(profile_id)
        return {"data": result.data} if result.success else {"error": result.error}

    def _format_remove_response(self, count: int) -> AgentResponse:
        return AgentResponse(
            success=True,
            message=f"""✅ **{count} perfil(s) removido(s) da busca**

Os perfis foram removidos dos resultados desta busca.
Eles ainda existem na base e podem aparecer em outras buscas.""",
            data={"removed_count": count},
            suggestions=["Ver candidatos restantes", "Continuar filtrando"]
        )

    def _request_target_selection(
        self,
        action_name: str,
        context: DomainContext,
        question: str
    ) -> AgentResponse:
        top_candidates = self._fetch_candidates(
            context, limit=5, order={"sourcing_score": "desc"}
        )

        if not top_candidates:
            return AgentResponse(
                success=False,
                message="❌ Nenhum candidato encontrado nesta busca.",
                suggestions=["Fazer nova busca"]
            )

        lines = [f"❓ **{question}**", "",
                 "📋 **Top candidatos disponíveis:**", ""]
        for i, c in enumerate(top_candidates, 1):
            name = c.get("name", "Sem nome")
            score = c.get("score") or c.get("sourcing_score") or "-"
            cid = c.get("id")
            lines.append(f"{i}. **{name}** (Score: {score}) - ID: {cid}")

        lines.extend([
            "",
            "💡 Você pode:",
            f"- Informar o ID: \"{action_name.capitalize()} o candidato 123\"",
            f"- Usar posição: \"{action_name.capitalize()} o primeiro\"",
            f"- Selecionar múltiplos: \"{action_name.capitalize()} os 3 primeiros\""
        ])

        return AgentResponse(
            success=False,
            message="\n".join(lines),
            data={"candidates": top_candidates},
            suggestions=[
                f"{action_name.capitalize()} o primeiro",
                f"{action_name.capitalize()} os top 3",
                "Ver mais candidatos"
            ]
        )

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/analytics.py

```python
from typing import Dict, Any, Optional, List
import logging

from src.domains.base import DomainContext
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "analytics"

    @property
    def agent_name(self) -> str:
        return "Analytics Agent"

    @property
    def description(self) -> str:
        return "Especialista em estatísticas, contagens, médias e distribuições de candidatos"

    @property
    def capabilities(self) -> List[str]:
        return [
            "Contar candidatos (total, com filtro)",
            "Calcular médias (score, experiência, salário)",
            "Distribuições (localização, gênero, skills, idiomas)",
            "Análise de diversidade"
        ]

    def get_system_prompt(self, context: DomainContext) -> str:
        return f"""Você é um analista de dados especializado em métricas de recrutamento.

**CONTEXTO:**
- Sourcing ID: {context.sourcing_id}

**SUAS CAPACIDADES:**
- count: Contar candidatos (total ou com filtro)
- average_score: Calcular score médio
- average_experience: Calcular experiência média
- location_distribution: Distribuição por cidade/estado
- gender_distribution: Distribuição por gênero
- skills_distribution: Skills mais comuns
- language_distribution: Níveis de idioma
- salary_average: Pretensão salarial média
- diversity_analysis: Análise de diversidade

**RESPOSTA (JSON):**
{{
    "action": "nome_da_acao",
    "params": {{"filter": "opcional"}},
    "reasoning": "motivo"
}}"""

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        params = params or {}

        action = self._identify_action(query, params)

        handlers = {
            "count": self._count_candidates,
            "count_by_score": self._count_by_score,
            "average_score": self._average_score,
            "average_experience": self._average_experience,
            "location_distribution": self._location_distribution,
            "gender_distribution": self._gender_distribution,
            "skills_distribution": self._skills_distribution,
            "language_distribution": self._language_distribution,
            "salary_average": self._salary_average,
            "diversity_analysis": self._diversity_analysis,
            "summarize": self._summarize,
        }

        handler = handlers.get(action, self._summarize)

        pre_filtered = params.get("_candidates")
        if pre_filtered:
            return self._analyze_pre_filtered(pre_filtered, action, params)

        if action == "count_by_score":
            return self._count_by_score(context, aggregated_stats, params, query)

        return handler(context, aggregated_stats, params)

    def _analyze_pre_filtered(
        self,
        candidates: List[Dict],
        action: str,
        params: Dict
    ) -> AgentResponse:
        total = len(candidates)

        if action == "count":
            return AgentResponse(
                success=True,
                message=f"📊 **Total de candidatos (filtrados):** {total}",
                data={"count": total, "filtered": True}
            )

        scores = [c.get("score") or c.get("sourcing_score")
                  or 0 for c in candidates]
        avg_score = sum(scores) / len(scores) if scores else 0

        experiences = []
        for c in candidates:
            exp = c.get("total_experience") or c.get("years_experience") or 0
            experiences.append(exp)
        avg_exp = sum(experiences) / len(experiences) if experiences else 0

        summary = f"""📊 **Análise dos {total} Candidatos Filtrados**

| Métrica | Valor |
|---------|-------|
| Total | {total} |
| Score Médio | {avg_score:.1f} |
| Experiência Média | {avg_exp:.1f} anos |
"""

        return AgentResponse(
            success=True,
            message=summary,
            data={
                "count": total,
                "avg_score": round(avg_score, 1),
                "avg_experience": round(avg_exp, 1),
                "filtered": True
            }
        )

    def _identify_action(self, query: str, params: Dict) -> str:
        query_lower = query.lower()

        if "quantos" in query_lower or "total" in query_lower:
            if "score" in query_lower and ("acima" in query_lower or "maior" in query_lower or ">" in query):
                return "count_by_score"
            return "count"
        if "média" in query_lower or "media" in query_lower:
            if "score" in query_lower:
                return "average_score"
            if "experiência" in query_lower or "experiencia" in query_lower:
                return "average_experience"
            if "salário" in query_lower or "salario" in query_lower:
                return "salary_average"
        if "cidade" in query_lower or "localização" in query_lower or "localizacao" in query_lower:
            return "location_distribution"
        if "gênero" in query_lower or "genero" in query_lower:
            return "gender_distribution"
        if "skill" in query_lower or "habilidade" in query_lower:
            return "skills_distribution"
        if "idioma" in query_lower or "inglês" in query_lower or "ingles" in query_lower:
            return "language_distribution"
        if "diversidade" in query_lower:
            return "diversity_analysis"

        return "summarize"

    def _count_candidates(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "counts" in stats:
            total = stats["counts"].get("total", 0)
            with_score = stats["counts"].get("with_score", 0)

            message = f"""## 📊 Contagem de Candidatos

| Métrica | Valor |
|---------|-------|
| **Total** | {total} |
| **Com score** | {with_score} |
| **Sem score** | {total - with_score} |
"""
            return AgentResponse(
                success=True,
                message=message,
                data={"total": total, "with_score": with_score},
                suggestions=["Qual a média de score?", "Top 10 candidatos"]
            )

        candidates = self._fetch_candidates(context, limit=100)
        total = len(candidates)
        with_score = len([c for c in candidates if c.get(
            "score") or c.get("sourcing_score")])

        message = f"""## 📊 Contagem de Candidatos

| Métrica | Valor |
|---------|-------|
| **Total** | {total} |
| **Com score** | {with_score} |
"""
        return AgentResponse(
            success=True,
            message=message,
            data={"total": total, "with_score": with_score},
            suggestions=["Qual a média de score?", "Top 10 candidatos"]
        )

    def _count_by_score(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict,
        query: str
    ) -> AgentResponse:
        import re
        numbers = re.findall(r'\b(\d+)\b', query)
        min_score = 80

        for n in numbers:
            if 50 <= int(n) <= 100:
                min_score = int(n)
                break

        where = {
            "sourcing_id": int(context.sourcing_id),
            "sourcing_score": {"gte": min_score},
            "is_deleted": False
        }

        candidates = self._fetch_candidates(
            context,
            limit=100,
            order={"sourcing_score": "desc"},
            where=where
        )

        total = len(candidates)

        if total == 0:
            message = f"## 📊 Candidatos com Score >= {min_score}\n\n⚠️ Nenhum candidato encontrado com score acima de {min_score}"
        else:
            scores = [c.get('sourcing_score') or c.get(
                'score') or 0 for c in candidates]
            message = f"""## 📊 Candidatos com Score >= {min_score}

| Métrica | Valor |
|---------|-------|
| **Total** | {total} candidatos |
| **Score mínimo encontrado** | {min(scores):.0f} |
| **Score máximo encontrado** | {max(scores):.0f} |
"""

        return AgentResponse(
            success=True,
            message=message,
            data={
                "count": total,
                "min_score_filter": min_score,
                "candidates": [
                    {"id": c.get("id"), "name": c.get(
                        "name"), "score": c.get("score")}
                    for c in candidates[:10]
                ]
            },
            suggestions=["Quem são eles?", "Qual a média de score deles?"]
        )

    def _average_score(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "score_stats" in stats:
            s = stats["score_stats"]
            message = f"""## 📈 Estatísticas de Score

| Métrica | Valor |
|---------|-------|
| **Média** | {s.get('average', 0):.1f} |
| **Mediana** | {s.get('median', 0):.1f} |
| **Mínimo** | {s.get('min', 0)} |
| **Máximo** | {s.get('max', 0)} |
| **Acima de 80** | {s.get('above_80', 0)} |
"""
            return AgentResponse(
                success=True,
                message=message,
                data=s,
                suggestions=["Quem tem score acima de 80?", "Top 5 candidatos"]
            )

        candidates = self._fetch_candidates(context, limit=100)
        scores = [c.get("score") or c.get("sourcing_score")
                  or 0 for c in candidates]
        valid = [s for s in scores if s > 0]

        if not valid:
            return AgentResponse(
                success=True,
                message="⚠️ Nenhum candidato com score definido",
                data={"average": 0}
            )

        avg = sum(valid) / len(valid)
        message = f"""## 📈 Estatísticas de Score

| Métrica | Valor |
|---------|-------|
| **Média** | {avg:.1f} |
| **Mínimo** | {min(valid)} |
| **Máximo** | {max(valid)} |
| **Com score** | {len(valid)} |
"""
        return AgentResponse(
            success=True,
            message=message,
            data={"average": avg, "min": min(valid), "max": max(valid)},
            suggestions=["Top 5 candidatos", "Quem tem score acima de 80?"]
        )

    def _average_experience(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "experience_stats" in stats:
            s = stats["experience_stats"]
            message = f"""## 📅 Estatísticas de Experiência

| Métrica | Valor |
|---------|-------|
| **Média** | {s.get('average', 0):.1f} anos |
| **Mediana** | {s.get('median', 0):.1f} anos |
| **Mínimo** | {s.get('min', 0)} anos |
| **Máximo** | {s.get('max', 0)} anos |
"""
            return AgentResponse(success=True, message=message, data=s)

        candidates = self._fetch_candidates(context, limit=100)
        exp = [c.get("total_experience_years") or 0 for c in candidates]
        valid = [e for e in exp if e > 0]

        if not valid:
            return AgentResponse(
                success=True,
                message="⚠️ Nenhum candidato com experiência definida",
                data={"average": 0}
            )

        avg = sum(valid) / len(valid)
        message = f"""## 📅 Estatísticas de Experiência

| Métrica | Valor |
|---------|-------|
| **Média** | {avg:.1f} anos |
| **Mínimo** | {min(valid)} anos |
| **Máximo** | {max(valid)} anos |
"""
        return AgentResponse(success=True, message=message, data={"average": avg})

    def _location_distribution(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "location_distribution" in stats:
            dist = stats["location_distribution"].get("by_city", {})
        else:
            candidates = self._fetch_candidates(context, limit=100)
            dist = {}
            for c in candidates:
                city = c.get("city", "N/A")
                if city and city != "N/A":
                    dist[city] = dist.get(city, 0) + 1

        sorted_dist = sorted(
            dist.items(), key=lambda x: x[1], reverse=True)[:10]

        lines = ["## 📍 Distribuição por Localização", ""]
        lines.append("| Cidade | Candidatos |")
        lines.append("|--------|------------|")
        for city, count in sorted_dist:
            lines.append(f"| {city} | {count} |")

        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={"distribution": dict(sorted_dist)},
            suggestions=["Candidatos de São Paulo", "Distribuição por gênero"]
        )

    def _gender_distribution(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "diversity_stats" in stats:
            dist = stats["diversity_stats"].get("by_gender", {})
        else:
            candidates = self._fetch_candidates(context, limit=100)
            dist = {}
            for c in candidates:
                gender = c.get("gender", "Não informado")
                if not gender:
                    gender = "Não informado"
                dist[gender] = dist.get(gender, 0) + 1

        lines = ["## 👥 Distribuição por Gênero", ""]
        lines.append("| Gênero | Candidatos |")
        lines.append("|--------|------------|")
        for gender, count in dist.items():
            lines.append(f"| {gender} | {count} |")

        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={"distribution": dist}
        )

    def _skills_distribution(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "skills_distribution" in stats:
            skills = stats["skills_distribution"].get("top_skills", {})
        else:
            candidates = self._fetch_candidates(context, limit=100)
            skills = {}
            for c in candidates:
                analysis = c.get("analysis") or c.get("ai_analysis") or {}
                for skill in analysis.get("skills_assessment", {}).get("strong", []):
                    skill_lower = skill.lower()
                    skills[skill_lower] = skills.get(skill_lower, 0) + 1

        sorted_skills = sorted(
            skills.items(), key=lambda x: x[1], reverse=True)[:15]

        lines = ["## 🛠️ Skills Mais Comuns", ""]
        if sorted_skills:
            max_count = sorted_skills[0][1] if sorted_skills else 1
            for skill, count in sorted_skills:
                bar_len = int((count / max_count) * 10)
                bar = "█" * bar_len + "░" * (10 - bar_len)
                lines.append(f"- `{skill}` {bar} ({count})")
        else:
            lines.append("⚠️ Nenhuma skill identificada")

        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={"skills": dict(sorted_skills)}
        )

    def _language_distribution(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "languages_distribution" in stats:
            dist = stats["languages_distribution"]
            english = dist.get("english_distribution", {})
        else:
            candidates = self._fetch_candidates(context, limit=100)
            english = {}
            for c in candidates:
                langs = c.get("languages") or []
                for lang in langs:
                    if "ingl" in lang.get("language", "").lower() or "engl" in lang.get("language", "").lower():
                        level = lang.get("proficiency", "N/A")
                        english[level] = english.get(level, 0) + 1

        lines = ["## 🌐 Distribuição de Inglês", ""]
        lines.append("| Nível | Candidatos |")
        lines.append("|-------|------------|")
        for level, count in sorted(english.items()):
            lines.append(f"| {level} | {count} |")

        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={"english": english}
        )

    def _salary_average(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "salary_stats" in stats:
            s = stats["salary_stats"]
            clt = s.get("clt", {}).get("average", 0)
            pj = s.get("pj", {}).get("average", 0)

            message = f"""## 💰 Pretensão Salarial Média

| Tipo | Valor |
|------|-------|
| **CLT** | R$ {clt:,.0f} |
| **PJ** | R$ {pj:,.0f} |
"""
            return AgentResponse(success=True, message=message, data=s)

        return AgentResponse(
            success=True,
            message="⚠️ Dados de pretensão salarial não disponíveis",
            data={}
        )

    def _diversity_analysis(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        if stats and "diversity_stats" in stats:
            d = stats["diversity_stats"]
            gender = d.get("by_gender", {})
            ethnicity = d.get("by_ethnicity", {})

            lines = ["## 🌈 Análise de Diversidade", ""]

            lines.append("### Por Gênero")
            for g, count in gender.items():
                lines.append(f"- {g}: {count}")

            if ethnicity:
                lines.append("")
                lines.append("### Por Etnia")
                for e, count in ethnicity.items():
                    lines.append(f"- {e}: {count}")

            return AgentResponse(
                success=True,
                message="\n".join(lines),
                data=d
            )

        return self._gender_distribution(context, stats, params)

    def _summarize(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict
    ) -> AgentResponse:
        candidates = self._fetch_candidates(context, limit=100)

        total = len(candidates)
        scores = [c.get("score") or c.get("sourcing_score")
                  or 0 for c in candidates]
        valid_scores = [s for s in scores if s > 0]
        avg_score = sum(valid_scores) / \
            len(valid_scores) if valid_scores else 0

        exp = [c.get("total_experience_years") or 0 for c in candidates]
        valid_exp = [e for e in exp if e > 0]
        avg_exp = sum(valid_exp) / len(valid_exp) if valid_exp else 0

        message = f"""## 📊 Resumo do Sourcing

| Métrica | Valor |
|---------|-------|
| **Total de candidatos** | {total} |
| **Score médio** | {avg_score:.1f} |
| **Experiência média** | {avg_exp:.1f} anos |
| **Com score** | {len(valid_scores)} |
"""

        return AgentResponse(
            success=True,
            message=message,
            data={
                "total": total,
                "avg_score": avg_score,
                "avg_experience": avg_exp
            },
            suggestions=[
                "Top 5 candidatos",
                "Distribuição por cidade",
                "Skills mais comuns"
            ]
        )

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/base.py

```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.api_client import SourcingAPIClient
from src.domains.sourced_profile_sourcing.api_operations import SourcingAPIOperations, get_api_operations
from src.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None
    confidence: float = 1.0
    warnings: Optional[List[str]] = None

    def to_domain_response(self) -> DomainResponse:
        message = self.message
        if self.warnings:
            message += f"\n\n⚠️ **Avisos:**\n" + \
                "\n".join(f"- {w}" for w in self.warnings)

        return DomainResponse(
            success=self.success,
            message=message,
            data=self.data,
            suggestions=self.suggestions,
            error=self.error
        )


class BaseAgent(ABC):

    def __init__(self):
        self._llm = None
        self._settings = None
        self._validator = None
        self._fact_checker = None

    def get_api_client(self, context: DomainContext = None) -> SourcingAPIClient:
        return SourcingAPIClient(context)

    def get_api_operations(self, context: DomainContext) -> SourcingAPIOperations:
        return get_api_operations(context)

    @property
    def settings(self):
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=self.settings.gemini.model,
                temperature=0.0,
                google_api_key=self.settings.gemini.api_key
            )
        return self._llm

    @property
    def validator(self):
        if self._validator is None:
            from src.domains.sourced_profile_sourcing.validators import get_validator
            self._validator = get_validator()
        return self._validator

    @property
    def fact_checker(self):
        if self._fact_checker is None:
            from src.domains.sourced_profile_sourcing.fact_checker import get_fact_checker
            self._fact_checker = get_fact_checker()
        return self._fact_checker

    @property
    @abstractmethod
    def agent_id(self) -> str:
        pass

    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        pass

    @abstractmethod
    def get_system_prompt(self, context: DomainContext) -> str:
        pass

    @abstractmethod
    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        pass

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        return response.content.strip()

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        import json

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return json.loads(content.strip())

    def _fetch_candidates(
        self,
        context: DomainContext,
        limit: int = 50,
        order: Optional[Dict] = None,
        where: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        if not context.sourcing_id:
            return []

        api = self.get_api_operations(context)
        result = api.search_candidates(
            where=where,
            order=order or {"sourcing_score": "desc"},
            limit=limit
        )
        return result.data if result.success else []

    def _sanitize(self, value: Optional[str], max_len: Optional[int] = None) -> str:
        if not value:
            return "-"
        clean = str(value).replace("|", "/")
        if max_len:
            return clean[:max_len]
        return clean

    def _validate_and_correct_params(
        self,
        params: Dict[str, Any],
        context: DomainContext
    ) -> tuple[bool, Dict[str, Any], List[str]]:
        if not context.sourcing_id:
            return False, params, ["Sourcing ID é obrigatório"]

        success, validated_params, error = self.validator.validate_params(
            params,
            context.sourcing_id
        )

        warnings = []
        if error:
            warnings.append(error)

        if "name" in params and "candidate_id" in validated_params:
            warnings.append(
                f"Nome '{params['name']}' resolvido para candidato #{validated_params['candidate_id']}")

        return success, validated_params, warnings

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/comparison.py

```python
from typing import Dict, Any, Optional, List
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from src.domains.base import DomainContext
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class ComparisonAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "comparison"

    @property
    def agent_name(self) -> str:
        return "Comparison Agent"

    @property
    def description(self) -> str:
        return "Especialista em comparar candidatos lado a lado com análise detalhada"

    @property
    def capabilities(self) -> List[str]:
        return [
            "Comparar top N candidatos",
            "Comparar candidatos específicos por nome",
            "Comparar por IDs",
            "Comparar candidatos com perfil da vaga",
            "Gerar análise comparativa com recomendação"
        ]

    def get_system_prompt(self, context: DomainContext) -> str:
        return f"""Você é um especialista em comparar candidatos para contratação.

**CONTEXTO:**
- Sourcing ID: {context.sourcing_id}

**SUAS CAPACIDADES:**
- compare_top: Comparar os N melhores candidatos
- compare_names: Comparar candidatos por nome
- compare_ids: Comparar candidatos por ID
- compare_with_job: Comparar candidatos com perfil da vaga

**RESPOSTA (JSON):**
{{
    "action": "compare_top",
    "params": {{"top_n": 3, "names": [], "ids": [], "job_id": null, "job_name": null}},
    "reasoning": "motivo"
}}"""

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        params = params or {}

        success, validated_params, warnings = self._validate_and_correct_params(
            params, context)

        if not success:
            return AgentResponse(
                success=False,
                message=f"❌ {'; '.join(warnings)}",
                error="validation_failed",
                confidence=0.0
            )

        # Verificar se é comparação com vaga
        if self._is_job_comparison(query, validated_params):
            return self._compare_with_job(query, context, validated_params)

        pre_filtered = validated_params.get("_candidates")

        if pre_filtered and len(pre_filtered) >= 2:
            return self._generate_comparison(pre_filtered, warnings)

        strategy, extracted = self._identify_strategy(query, validated_params)
        validated_params.update(extracted)

        candidates = self._fetch_candidates_for_comparison(
            context, strategy, validated_params)

        if len(candidates) < 2:
            return AgentResponse(
                success=False,
                message="❌ Preciso de pelo menos 2 candidatos para comparar",
                error="insufficient_candidates",
                confidence=0.0
            )

        return self._generate_comparison(candidates, warnings)

    def _identify_strategy(self, query: str, params: Dict) -> tuple[str, Dict]:
        query_lower = query.lower()
        extracted = {}

        import re
        numbers = re.findall(r'\b(\d+)\b', query)

        if "top" in query_lower or "melhores" in query_lower:
            if numbers:
                for n in numbers:
                    if int(n) <= 20:
                        extracted["top_n"] = int(n)
                        break
            if "top_n" not in extracted:
                extracted["top_n"] = params.get("top_n", 3)
            return "top_n", extracted

        name_patterns = [
            r"compar[ae]\s+(?:o|a|os|as)?\s*(\w+).*?(?:com|e|,)\s+(?:o|a|os|as)?\s*(\w+)",
            r"(\w+)\s+(?:vs|versus|x)\s+(\w+)",
            r"(?:entre|diferença entre)\s+(\w+)\s+e\s+(\w+)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                names = [match.group(1).strip(), match.group(2).strip()]
                stopwords = {"o", "a", "os", "as", "com", "e", "de", "do",
                             "da", "dos", "das", "top", "candidato", "candidatos"}
                names = [n for n in names if n.lower(
                ) not in stopwords and len(n) > 1]
                if len(names) >= 2:
                    extracted["names"] = names[:2]
                    return "by_names", extracted

        if numbers and len(numbers) >= 2:
            extracted["ids"] = [int(n) for n in numbers[:5]]
            return "by_ids", extracted

        extracted["top_n"] = 3
        return "top_n", extracted

    def _fetch_candidates_for_comparison(
        self,
        context: DomainContext,
        strategy: str,
        params: Dict
    ) -> List[Dict]:
        api = self.get_api_operations(context)

        if strategy == "top_n":
            n = params.get("top_n", 3)
            result = api.get_top_candidates(limit=n)
            return result.data if result.success else []

        if strategy == "by_names":
            names = params.get("names", [])
            result = api.search_candidates_by_names(names)
            return result.data if result.success else []

        if strategy == "by_ids":
            ids = params.get("ids", [])
            result = api.get_candidates_by_ids(ids)
            return result.data if result.success else []

        result = api.get_top_candidates(limit=3)
        return result.data if result.success else []

    def _generate_comparison(self, candidates: List[Dict], warnings: Optional[List[str]] = None) -> AgentResponse:
        table = self._build_comparison_table(candidates)

        llm_analysis = self._generate_llm_analysis(candidates)

        lines = [
            "# 📊 Comparativo de Candidatos",
            "",
            f"*{len(candidates)} candidatos comparados*",
            "",
            "---",
            "",
            "## 📋 Tabela Comparativa",
            "",
            table,
            "",
            "---",
            "",
            "## 🧠 Análise Comparativa (IA)",
            "",
        ]
        lines.extend(llm_analysis)

        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={
                "candidates": [self._candidate_summary(c) for c in candidates],
                "comparison_type": "side_by_side"
            },
            suggestions=[
                f"Detalhes do candidato {candidates[0].get('id', '')}" if candidates else "",
                "Gerar relatório executivo"
            ]
        )

    def _build_comparison_table(self, candidates: List[Dict]) -> str:
        headers = ["Critério"] + \
            [self._sanitize(c.get("name", "?").split()[0])
             for c in candidates]
        separator = [":---"] + [":---:"] * len(candidates)

        rows = [
            self._table_row("ID", candidates, lambda c: str(c.get("id", "-"))),
            self._table_row(
                "Score", candidates, lambda c: f"**{c.get('score') or c.get('sourcing_score') or '-'}**"),
            self._table_row("Experiência", candidates,
                            lambda c: f"{c.get('total_experience_years') or '-'} anos"),
            self._table_row("Empresa", candidates, lambda c: self._sanitize(
                c.get("current_company"))),
            self._table_row("Cargo", candidates, lambda c: self._sanitize(
                c.get("title") or c.get("current_title"))),
            self._table_row("Cidade", candidates,
                            lambda c: self._sanitize(c.get("city"))),
            self._table_row("Top Skills", candidates, self._get_top_skills),
            self._table_row("Destaque", candidates, self._get_highlight),
            self._table_row("Alerta", candidates, self._get_alert),
        ]

        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(separator) + " |",
        ]
        lines.extend(rows)

        return "\n".join(lines)

    def _table_row(self, label: str, candidates: List[Dict], extractor) -> str:
        values = [extractor(c) for c in candidates]
        return f"| **{label}** | " + " | ".join(values) + " |"

    def _get_top_skills(self, c: Dict) -> str:
        analysis = c.get("analysis") or c.get("ai_analysis") or {}
        skills = analysis.get("skills_assessment", {}).get("strong", [])
        if skills:
            return ", ".join(skills[:3])

        expertise = c.get("expertise", [])
        return ", ".join(expertise[:3]) if expertise else "-"

    def _get_highlight(self, c: Dict) -> str:
        analysis = c.get("analysis") or c.get("ai_analysis") or {}
        highlights = analysis.get("highlights", [])
        if highlights:
            h = highlights[0]
            desc = h.get("description") if isinstance(h, dict) else str(h)
            return self._sanitize(desc)
        return "-"

    def _get_alert(self, c: Dict) -> str:
        analysis = c.get("analysis") or c.get("ai_analysis") or {}
        flags = analysis.get("red_flags", [])
        if flags:
            rf = flags[0]
            if isinstance(rf, dict):
                severity = rf.get("severity", "medium")
                desc = rf.get("description", "")
                emoji = {"high": "🔴", "medium": "🟡",
                         "low": "🟢"}.get(severity, "⚪")
                return f"{emoji} {self._sanitize(desc)}"
            return self._sanitize(str(rf))
        return "✅ Nenhum"

    def _generate_llm_analysis(self, candidates: List[Dict]) -> List[str]:
        from src.domains.sourced_profile_sourcing.fairness import anonymize_for_llm

        anonymized, _ = anonymize_for_llm(
            candidates,
            fields_to_keep=["score", "sourcing_score",
                            "total_experience_years", "analysis", "ai_analysis"]
        )

        summaries = []
        for c in anonymized:
            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            summaries.append({
                "candidato": c.get("candidate_code"),
                "score": c.get("score") or c.get("sourcing_score"),
                "experiencia": c.get("total_experience_years"),
                "destaques": [h.get("description") if isinstance(h, dict) else str(h) for h in analysis.get("highlights", [])[:2]],
                "alertas": [f.get("description") if isinstance(f, dict) else str(f) for f in analysis.get("red_flags", [])[:2]],
                "skills": analysis.get("skills_assessment", {}).get("strong", [])[:5]
            })

        prompt = f"""Você é um consultor de RH sênior. Analise estes candidatos e forneça uma comparação objetiva:

CANDIDATOS:
{summaries}

Forneça:
1. **Resumo da Comparação** (2-3 frases comparando os perfis)
2. **Quem Contratar?** (recomendação clara com justificativa baseada em habilidades e experiência)
3. **Pontos de Atenção** (1 ponto específico para cada candidato na entrevista)

Seja direto e objetivo. Use os códigos dos candidatos (C001, C002, etc)."""

        try:
            response = self.llm.invoke([
                SystemMessage(
                    content="Você é um consultor de RH experiente. Seja direto e objetivo. Use APENAS os dados fornecidos. Use códigos de candidato (C001, C002) em vez de nomes."),
                HumanMessage(content=prompt)
            ])

            analysis_text = response.content.strip()

            fact_results = self.fact_checker.verify_claims_in_analysis(
                analysis_text,
                candidates
            )

            for result in fact_results:
                if not result.verified:
                    logger.warning(
                        f"Fact check failed: {result.claim} - {result.correction}")

            return analysis_text.split("\n")
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return ["⚠️ Análise automática não disponível"]

    def _candidate_summary(self, c: Dict) -> Dict:
        analysis = c.get("analysis") or c.get("ai_analysis") or {}
        return {
            "id": c.get("id"),
            "name": c.get("name"),
            "score": c.get("score") or c.get("sourcing_score"),
            "experience": c.get("total_experience_years"),
            "company": c.get("current_company"),
            "city": c.get("city"),
            "skills": analysis.get("skills_assessment", {}).get("strong", []),
            "highlights": analysis.get("highlights", []),
            "red_flags": analysis.get("red_flags", [])
        }

    def _is_job_comparison(self, query: str, params: Dict) -> bool:
        """Verifica se a query é sobre comparar com vaga."""
        query_lower = query.lower()
        
        job_keywords = [
            "vaga", "job", "perfil da vaga", "perfil ideal", 
            "com a vaga", "com o job", "match com", "fit com"
        ]
        
        comparison_keywords = [
            "compar", "match", "fit", "alinh", "adequad"
        ]
        
        has_job_keyword = any(kw in query_lower for kw in job_keywords)
        has_comparison_keyword = any(kw in query_lower for kw in comparison_keywords)
        
        # Se tem palavra de vaga E palavra de comparação, ou se tem job_id/job_name nos params
        return (has_job_keyword and has_comparison_keyword) or params.get("job_id") or params.get("job_name")

    def _compare_with_job(
        self,
        query: str,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> AgentResponse:
        """Compara candidato(s) com perfil da vaga."""
        memory = context.get_memory()
        
        # 1. Identificar candidato(s)
        candidates = self._extract_candidates_for_job_comparison(query, context, params)
        
        if not candidates:
            return AgentResponse(
                success=False,
                message="""❓ **Qual candidato você quer comparar com a vaga?**

💡 Você pode:
- Mencionar o candidato na pergunta: "Compare o candidato 123 com a vaga"
- Selecionar o candidato no frontend
- Usar referência: "Compare ele com a vaga" (após ver um candidato)""",
                error="missing_candidate",
                suggestions=["Top 5 candidatos", "Listar candidatos"]
            )
        
        # 2. Identificar vaga
        job_id = params.get("job_id")
        job_name = params.get("job_name")
        
        # Tentar extrair da query se não fornecido
        if not job_id and not job_name:
            job_id, job_name = self._extract_job_from_query(query)
        
        # Se ainda não tem, perguntar
        if not job_id and not job_name:
            # Verificar memória para ver se há vaga mencionada anteriormente
            if hasattr(memory, 'last_job_id') and memory.last_job_id:
                job_id = memory.last_job_id
            else:
                return self._ask_for_job(candidates)
        
        # 3. Buscar vaga
        job = self._fetch_job(context, job_id, job_name)
        
        if not job:
            if job_name:
                return AgentResponse(
                    success=False,
                    message=f"❌ Não encontrei a vaga '{job_name}'. Pode verificar o nome ou fornecer o ID?",
                    error="job_not_found",
                    suggestions=["Listar vagas disponíveis", "Tentar com ID da vaga"]
                )
            return AgentResponse(
                success=False,
                message=f"❌ Não encontrei a vaga com ID {job_id}.",
                error="job_not_found"
            )
        
        # 4. Confirmar vaga se necessário (múltiplas opções ou nome ambíguo)
        if not job_id and job_name:
            confirmation_needed = self._needs_job_confirmation(job, context)
            if confirmation_needed:
                return confirmation_needed
        
        # 5. Salvar vaga na memória
        if not hasattr(memory, 'last_job_id'):
            memory.last_job_id = job.get("id")
        else:
            memory.last_job_id = job.get("id")
        
        # 6. Comparar
        comparison_result = self._generate_job_comparison(candidates, job, context)
        
        # 7. Avaliar match e sugerir apply se bom
        match_score = comparison_result.get("match_score", 0)
        suggestions = comparison_result.get("suggestions", [])
        
        if match_score >= 70 and candidates:
            # Sugerir criar apply
            candidate_ids = [c.get("id") for c in candidates if c.get("id")]
            if candidate_ids:
                suggestions.insert(0, f"Adicionar candidato(s) à vaga '{job.get('title', 'N/A')}'")
        
        return AgentResponse(
            success=True,
            message=comparison_result.get("message", ""),
            data={
                "comparison_type": "job_comparison",
                "candidates": [self._candidate_summary(c) for c in candidates],
                "job": {
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "description": job.get("description")
                },
                "match_score": match_score,
                "comparison_details": comparison_result.get("details", {})
            },
            suggestions=suggestions,
            needs_confirmation=match_score >= 70 and len(candidates) == 1,
            confirmation_message=f"Deseja adicionar o candidato à vaga '{job.get('title')}'?" if match_score >= 70 and len(candidates) == 1 else None
        )

    def _extract_candidates_for_job_comparison(
        self,
        query: str,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> List[Dict]:
        """Extrai candidato(s) da query ou metadados."""
        memory = context.get_memory()
        candidates = []
        
        # 1. Verificar se há candidatos pré-filtrados (do frontend)
        if params.get("_candidates"):
            return params["_candidates"]
        
        # 2. Verificar se há candidate_id nos params (do frontend)
        if params.get("candidate_id"):
            api = self.get_api_operations(context)
            result = api.get_candidate_by_id(params["candidate_id"])
            if result.success and result.data:
                return [result.data]
        
        # 3. Tentar extrair da query
        import re
        numbers = re.findall(r'\b(\d+)\b', query)
        
        # IDs explícitos
        if numbers:
            for n in numbers:
                candidate_id = int(n)
                if 10 < candidate_id < 1000000:  # Range razoável para ID
                    api = self.get_api_operations(context)
                    result = api.get_candidate_by_id(candidate_id)
                    if result.success and result.data:
                        candidates.append(result.data)
        
        # 4. Verificar memória (referências como "ele", "esse", etc.)
        if not candidates:
            resolved_id = memory.resolve_reference(query)
            if resolved_id:
                api = self.get_api_operations(context)
                result = api.get_candidate_by_id(resolved_id)
                if result.success and result.data:
                    candidates.append(result.data)
        
        # 5. Se ainda não tem, usar último candidato detalhado
        if not candidates and memory.last_candidate_detailed:
            api = self.get_api_operations(context)
            result = api.get_candidate_by_id(memory.last_candidate_detailed)
            if result.success and result.data:
                candidates.append(result.data)
        
        # 6. Se ainda não tem, usar top N (padrão: top 3)
        if not candidates:
            api = self.get_api_operations(context)
            result = api.get_top_candidates(limit=3)
            if result.success and result.data:
                candidates = result.data[:3]
        
        return candidates

    def _extract_job_from_query(self, query: str) -> tuple[Optional[int], Optional[str]]:
        """Extrai job_id ou job_name da query."""
        import re
        
        # Tentar extrair ID
        numbers = re.findall(r'\b(\d+)\b', query)
        for n in numbers:
            job_id = int(n)
            if 1 <= job_id <= 1000000:  # Range razoável
                # Verificar contexto - se tem "vaga" antes do número
                query_lower = query.lower()
                idx = query_lower.find(str(job_id))
                if idx > 0:
                    before = query_lower[max(0, idx-20):idx]
                    if "vaga" in before or "job" in before:
                        return job_id, None
        
        # Tentar extrair nome da vaga
        patterns = [
            r"vaga\s+(?:de\s+)?['\"]?([^'\"]+)['\"]?",
            r"job\s+(?:de\s+)?['\"]?([^'\"]+)['\"]?",
            r"perfil\s+(?:da\s+)?vaga\s+(?:de\s+)?['\"]?([^'\"]+)['\"]?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                job_name = match.group(1).strip()
                if len(job_name) > 2:
                    return None, job_name
        
        return None, None

    def _ask_for_job(self, candidates: List[Dict]) -> AgentResponse:
        """Pergunta qual vaga usar."""
        candidate_info = []
        for c in candidates[:3]:
            name = c.get("name", "N/A")
            score = c.get("score") or c.get("sourcing_score") or "-"
            candidate_info.append(f"- **{name}** (Score: {score})")
        
        lines = [
            "❓ **Qual vaga você quer usar para comparar?**",
            "",
            f"**Candidato(s) selecionado(s):**",
            *candidate_info,
            "",
            "💡 Você pode:",
            "- Informar o nome: \"Compare com a vaga Python Developer\"",
            "- Informar o ID: \"Compare com a vaga 123\"",
            "- Ou selecionar a vaga no frontend"
        ]
        
        return AgentResponse(
            success=False,
            message="\n".join(lines),
            error="missing_job",
            data={"candidates": [self._candidate_summary(c) for c in candidates]},
            suggestions=["Listar vagas disponíveis"]
        )

    def _fetch_job(
        self,
        context: DomainContext,
        job_id: Optional[int],
        job_name: Optional[str]
    ) -> Optional[Dict]:
        """Busca vaga por ID ou nome."""
        api = self.get_api_operations(context)
        
        if job_id:
            result = api.get_job_by_id(job_id)
            if result.success and result.data:
                return result.data
        
        if job_name:
            result = api.search_jobs(search=job_name)
            if result.success and result.data:
                # Retornar o primeiro match
                return result.data[0]
        
        return None

    def _needs_job_confirmation(
        self,
        job: Dict,
        context: DomainContext
    ) -> Optional[AgentResponse]:
        """Verifica se precisa confirmar a vaga (múltiplas opções)."""
        # Se encontrou apenas uma vaga, não precisa confirmar
        # Mas se o nome é muito genérico, pode perguntar
        return None

    def _generate_job_comparison(
        self,
        candidates: List[Dict],
        job: Dict,
        context: DomainContext
    ) -> Dict[str, Any]:
        """Gera comparação entre candidatos e vaga."""
        # Extrair informações da vaga
        job_title = job.get("title", "N/A")
        job_description = job.get("description", "")
        job_skills = self._extract_job_skills(job)
        job_requirements = self._extract_job_requirements(job)
        
        # Comparar cada candidato
        comparisons = []
        total_match_score = 0
        
        for candidate in candidates:
            comparison = self._compare_candidate_with_job(
                candidate, job, job_skills, job_requirements
            )
            comparisons.append(comparison)
            total_match_score += comparison.get("match_score", 0)
        
        avg_match_score = total_match_score / len(candidates) if candidates else 0
        
        # Gerar tabela comparativa
        table = self._build_job_comparison_table(candidates, job, comparisons)
        
        # Gerar análise com LLM
        llm_analysis = self._generate_job_comparison_llm_analysis(
            candidates, job, comparisons
        )
        
        # Montar mensagem
        lines = [
            f"# 🎯 Comparação: Candidato(s) vs Vaga",
            "",
            f"**Vaga:** {job_title}",
            f"**Candidatos comparados:** {len(candidates)}",
            "",
            "---",
            "",
            "## 📊 Tabela Comparativa",
            "",
            table,
            "",
            "---",
            "",
            "## 🧠 Análise de Match",
            "",
            *llm_analysis
        ]
        
        suggestions = []
        if avg_match_score >= 80:
            suggestions.append(f"✅ Excelente match! Adicionar à vaga '{job_title}'")
        elif avg_match_score >= 70:
            suggestions.append(f"✅ Bom match! Considerar adicionar à vaga '{job_title}'")
        else:
            suggestions.append("Ver outros candidatos")
            suggestions.append("Ajustar critérios de busca")
        
        return {
            "message": "\n".join(lines),
            "match_score": round(avg_match_score, 1),
            "details": {
                "comparisons": comparisons,
                "job_skills": job_skills,
                "job_requirements": job_requirements
            },
            "suggestions": suggestions
        }

    def _extract_job_skills(self, job: Dict) -> List[str]:
        """Extrai skills da vaga."""
        skills = []
        
        # Skills diretas
        job_skills = job.get("skills", [])
        if isinstance(job_skills, list):
            for skill in job_skills:
                if isinstance(skill, dict):
                    skills.append(skill.get("name", ""))
                elif isinstance(skill, str):
                    skills.append(skill)
        
        # Skills da descrição (básico)
        description = job.get("description", "").lower()
        common_skills = ["python", "java", "javascript", "react", "node", "aws", 
                        "docker", "kubernetes", "sql", "django", "flask"]
        for skill in common_skills:
            if skill in description and skill not in skills:
                skills.append(skill)
        
        return [s for s in skills if s]

    def _extract_job_requirements(self, job: Dict) -> Dict[str, Any]:
        """Extrai requisitos da vaga."""
        return {
            "is_remote": job.get("is_remote", False),
            "city": job.get("city"),
            "state": job.get("state"),
            "salary_from": job.get("salary_from"),
            "salary_to": job.get("salary_to"),
            "experience_years": None,  # Pode ser extraído da descrição
        }

    def _compare_candidate_with_job(
        self,
        candidate: Dict,
        job: Dict,
        job_skills: List[str],
        job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compara um candidato com a vaga."""
        # Extrair skills do candidato
        candidate_analysis = candidate.get("analysis") or candidate.get("ai_analysis") or {}
        candidate_skills = candidate_analysis.get("skills_assessment", {}).get("strong", [])
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        
        # Calcular match de skills
        job_skills_lower = [s.lower() for s in job_skills]
        matched_skills = [s for s in candidate_skills_lower if s in job_skills_lower]
        skill_match_percentage = (len(matched_skills) / len(job_skills_lower) * 100) if job_skills_lower else 0
        
        # Calcular match de localização
        location_match = True
        if job_requirements.get("city"):
            candidate_city = (candidate.get("city") or "").lower()
            job_city = job_requirements["city"].lower()
            location_match = job_city in candidate_city or candidate_city in job_city
        
        # Calcular match de experiência
        experience_match = True
        candidate_exp = candidate.get("total_experience_years") or 0
        required_exp = job_requirements.get("experience_years") or 0
        if required_exp > 0:
            experience_match = candidate_exp >= required_exp
        
        # Score do candidato (já calculado pelo sistema)
        candidate_score = candidate.get("score") or candidate.get("sourcing_score") or 0
        
        # Calcular match score geral (0-100)
        match_score = (
            (skill_match_percentage * 0.5) +  # 50% peso em skills
            (candidate_score * 0.3) +  # 30% peso no score do sistema
            (20 if location_match else 0) +  # 10% localização
            (10 if experience_match else 0)  # 10% experiência
        )
        
        match_score = min(100, max(0, match_score))
        
        return {
            "candidate_id": candidate.get("id"),
            "candidate_name": candidate.get("name"),
            "match_score": round(match_score, 1),
            "skill_match": {
                "matched": matched_skills,
                "missing": [s for s in job_skills_lower if s not in candidate_skills_lower],
                "percentage": round(skill_match_percentage, 1)
            },
            "location_match": location_match,
            "experience_match": experience_match,
            "candidate_score": candidate_score
        }

    def _build_job_comparison_table(
        self,
        candidates: List[Dict],
        job: Dict,
        comparisons: List[Dict]
    ) -> str:
        """Constrói tabela comparativa com vaga."""
        headers = ["Critério"] + [self._sanitize(c.get("name", "?").split()[0]) for c in candidates] + ["Vaga"]
        separator = [":---"] + [":---:"] * (len(candidates) + 1)
        
        job_skills = self._extract_job_skills(job)
        job_skills_str = ", ".join(job_skills[:5]) if job_skills else "-"
        
        rows = [
            self._table_row("Score", candidates, lambda c: f"**{c.get('score') or c.get('sourcing_score') or '-'}**") + " | - |",
            self._table_row("Experiência", candidates, lambda c: f"{c.get('total_experience_years') or '-'} anos") + f" | {job.get('experience_required', '-')} |",
            self._table_row("Localização", candidates, lambda c: self._sanitize(c.get("city"))) + f" | {self._sanitize(job.get('city', '-'))} |",
            self._table_row("Top Skills", candidates, self._get_top_skills) + f" | {job_skills_str} |",
        ]
        
        # Adicionar linha de match score
        match_scores = [f"**{comp.get('match_score', 0):.1f}%**" for comp in comparisons]
        match_row = "| **Match Score** | " + " | ".join(match_scores) + " | - |"
        rows.append(match_row)
        
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(separator) + " |",
        ]
        lines.extend(rows)
        
        return "\n".join(lines)

    def _generate_job_comparison_llm_analysis(
        self,
        candidates: List[Dict],
        job: Dict,
        comparisons: List[Dict]
    ) -> List[str]:
        """Gera análise LLM da comparação com vaga."""
        from src.domains.sourced_profile_sourcing.fairness import anonymize_for_llm
        
        anonymized_candidates, _ = anonymize_for_llm(
            candidates,
            fields_to_keep=["score", "sourcing_score", "total_experience_years", 
                           "analysis", "ai_analysis", "city"]
        )
        
        job_title = job.get("title", "N/A")
        job_skills = self._extract_job_skills(job)
        
        summaries = []
        for i, (c, comp) in enumerate(zip(anonymized_candidates, comparisons)):
            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            summaries.append({
                "candidato": f"C{i+1}",
                "match_score": comp.get("match_score", 0),
                "skills_match": comp.get("skill_match", {}).get("percentage", 0),
                "skills": analysis.get("skills_assessment", {}).get("strong", [])[:5],
                "experiencia": c.get("total_experience_years", 0),
                "location_match": comp.get("location_match", False)
            })
        
        prompt = f"""Você é um consultor de RH sênior. Analise a comparação entre candidatos e a vaga:

VAGA: {job_title}
SKILLS REQUERIDAS: {', '.join(job_skills[:10])}

CANDIDATOS:
{summaries}

Forneça:
1. **Resumo do Match** (2-3 frases sobre o alinhamento geral)
2. **Recomendação** (qual candidato tem melhor fit e por quê)
3. **Pontos de Atenção** (gaps ou pontos a verificar na entrevista)

Seja direto e objetivo. Use códigos de candidato (C1, C2, etc)."""
        
        try:
            response = self.llm.invoke([
                SystemMessage(
                    content="Você é um consultor de RH experiente. Seja direto e objetivo. Use APENAS os dados fornecidos. Use códigos de candidato (C1, C2) em vez de nomes."),
                HumanMessage(content=prompt)
            ])
            
            analysis_text = response.content.strip()
            return analysis_text.split("\n")
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return ["⚠️ Análise automática não disponível"]

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/detail.py

```python
from typing import Dict, Any, Optional, List
import logging

from src.domains.base import DomainContext
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse

logger = logging.getLogger(__name__)


class DetailAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "detail"

    @property
    def agent_name(self) -> str:
        return "Detail Agent"

    @property
    def description(self) -> str:
        return "Especialista em mostrar detalhes completos de um candidato específico"

    @property
    def capabilities(self) -> List[str]:
        return [
            "Mostrar perfil completo do candidato",
            "Exibir análise da IA (Lia)",
            "Mostrar experiências e skills",
            "Exibir alertas e destaques"
        ]

    def get_system_prompt(self, context: DomainContext) -> str:
        return f"""Você é um especialista em analisar perfis de candidatos.

**CONTEXTO:**
- Sourcing ID: {context.sourcing_id}

**SUAS CAPACIDADES:**
- show_details: Mostrar detalhes completos de um candidato

**RESPOSTA (JSON):**
{{
    "action": "show_details",
    "params": {{"candidate_id": 123, "name": "opcional"}},
    "reasoning": "motivo"
}}"""

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        params = params or {}

        candidate_id = params.get("candidate_id")
        name = params.get("name")
        resolved_from = params.get("_resolved_from")

        if not candidate_id and not name:
            candidate_id, name = self._extract_identifier(query)

        if not candidate_id and not name:
            memory = context.get_memory()
            if memory.last_candidate_detailed:
                candidate_id = memory.last_candidate_detailed
                resolved_from = "memory_last"

        if not candidate_id and not name:
            return AgentResponse(
                success=False,
                message="❌ Não consegui identificar qual candidato você quer ver.\n\n"
                        "💡 Diga algo como:\n"
                        "- 'Detalhes do candidato 123'\n"
                        "- 'Me fale sobre o primeiro da lista'\n"
                        "- 'Detalhes dele' (após ver um candidato)",
                error="missing_identifier",
                suggestions=["Top 5 candidatos", "Listar candidatos"]
            )

        response = self._show_candidate_details(context, candidate_id, name)

        if response.success and resolved_from:
            self._log_resolution(resolved_from, candidate_id)

        return response

    def _log_resolution(self, resolved_from: str, candidate_id: int):
        logger.debug(
            f"Candidate {candidate_id} resolved from: {resolved_from}")

    def _extract_identifier(self, query: str) -> tuple[Optional[int], Optional[str]]:
        import re

        numbers = re.findall(r'\b(\d+)\b', query)
        if numbers:
            return int(numbers[0]), None

        name_patterns = [
            r"(?:sobre|do|da|detalhes de)\s+(?:o|a)?\s*([A-Z][a-záéíóúâêîôûãõç]+(?:\s+[A-Z][a-záéíóúâêîôûãõç]+)*)",
            r"candidato\s+([A-Z][a-záéíóúâêîôûãõç]+(?:\s+[A-Z][a-záéíóúâêîôûãõç]+)*)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return None, match.group(1)

        return None, None

    def _show_candidate_details(
        self,
        context: DomainContext,
        candidate_id: Optional[int],
        name: Optional[str]
    ) -> AgentResponse:
        candidate = self._fetch_candidate(context, candidate_id, name)

        if not candidate:
            return AgentResponse(
                success=False,
                message=f"❌ Candidato não encontrado (ID: {candidate_id or name})",
                error="not_found"
            )

        message = self._format_candidate_details(candidate)

        return AgentResponse(
            success=True,
            message=message,
            data={"candidate": candidate},
            suggestions=[
                "Compare com outros candidatos",
                "Buscar candidatos similares"
            ]
        )

    def _fetch_candidate(
        self,
        context: DomainContext,
        candidate_id: Optional[int],
        name: Optional[str]
    ) -> Optional[Dict]:
        try:
            params = {
                "where": {"sourcing_id": int(context.sourcing_id)},
                "per_page": 50,
                "_single_page": True
            }

            if candidate_id:
                params["where"]["id"] = candidate_id

            response = self.get_api_client(context).call(
                "sourced_profile_sourcings_search", params)
            data = response.get("data", [])

            if not data:
                return None

            if candidate_id:
                for item in data:
                    attrs = item.get("attributes", item)
                    if attrs.get("id") == candidate_id:
                        return attrs

            if name:
                name_lower = name.lower()
                for item in data:
                    attrs = item.get("attributes", item)
                    candidate_name = (attrs.get("name") or "").lower()
                    if name_lower in candidate_name:
                        return attrs

            return data[0].get("attributes", data[0]) if data else None

        except Exception as e:
            logger.error(f"Error fetching candidate: {e}")
            return None

    def _format_candidate_details(self, c: Dict) -> str:
        name = c.get("name", "N/A")
        score = c.get("score") or c.get("sourcing_score") or "N/A"
        title = c.get("title") or c.get("current_title") or "N/A"
        company = c.get("current_company") or "N/A"
        city = c.get("city") or "N/A"
        state = c.get("state") or ""
        exp_years = c.get("total_experience_years") or "N/A"

        lines = [
            f"# 👤 {name}",
            "",
            f"**{title}**",
            f"📍 {city}{', ' + state if state else ''} | 🏢 {company}",
            "",
            "---",
            "",
            "## 📊 Resumo",
            "",
            f"| Métrica | Valor |",
            f"|---------|-------|",
            f"| **Score** | {score} |",
            f"| **Experiência** | {exp_years} anos |",
            f"| **Empresa Atual** | {company} |",
        ]

        summary = c.get("summary")
        if summary:
            lines.extend(["", "## 📝 Sobre", "", f"> {summary[:500]}"])

        analysis = c.get("analysis") or c.get("ai_analysis") or {}

        if analysis:
            lines.extend(["", "---", "", "## 🤖 Análise da Lia (IA)", ""])

            one_liner = analysis.get("one_liner")
            if one_liner:
                lines.append(f"> *{one_liner}*")
                lines.append("")

            eval_data = analysis.get("evaluation") or {}
            if eval_data:
                points = eval_data.get("points", "N/A")
                priority = eval_data.get("priority", "N/A")
                confidence = eval_data.get("confidence", "N/A")

                priority_emoji = {"high": "🔴", "medium": "🟡",
                                  "low": "🟢"}.get(priority, "⚪")

                lines.append("### 📈 Avaliação")
                lines.append(f"- **Pontuação:** {points}/100")
                lines.append(f"- **Prioridade:** {priority_emoji} {priority}")
                lines.append(f"- **Confiança:** {confidence}")

                rationale = eval_data.get("rationale")
                if rationale:
                    lines.append(f"- **Parecer:** {rationale}")

            skills = analysis.get("skills_assessment", {})
            if skills:
                lines.extend(["", "### 🛠️ Skills"])

                strong = skills.get("strong", [])
                if strong:
                    lines.append(f"- **Fortes:** {', '.join(strong[:8])}")

                mentioned = skills.get("mentioned", [])
                if mentioned:
                    lines.append(
                        f"- **Mencionadas:** {', '.join(mentioned[:8])}")

                missing = skills.get("missing", [])
                if missing:
                    lines.append(f"- **Faltantes:** {', '.join(missing[:5])}")

            highlights = analysis.get("highlights", [])
            if highlights:
                lines.extend(["", "### ✨ Destaques"])
                for h in highlights[:5]:
                    desc = h.get("description") if isinstance(
                        h, dict) else str(h)
                    lines.append(f"- {desc}")

            red_flags = analysis.get("red_flags", [])
            if red_flags:
                lines.extend(["", "### ⚠️ Alertas"])
                for rf in red_flags[:3]:
                    if isinstance(rf, dict):
                        severity = rf.get("severity", "medium")
                        desc = rf.get("description", "")
                        emoji = {"high": "🔴", "medium": "🟡",
                                 "low": "🟢"}.get(severity, "⚪")
                        lines.append(f"- {emoji} {desc}")
                    else:
                        lines.append(f"- {rf}")

        experiences = c.get("experiences", [])
        if experiences:
            lines.extend(["", "---", "", "## 💼 Experiências", ""])
            for exp in experiences[:5]:
                role = exp.get("role", "N/A")
                comp = exp.get("company", "N/A")
                duration = exp.get("duration_years", 0)
                is_current = exp.get("is_current", False)

                current_badge = " *(atual)*" if is_current else ""
                lines.append(
                    f"- **{role}** @ {comp} ({duration:.1f} anos){current_badge}")

        educations = c.get("educations", [])
        if educations:
            lines.extend(["", "---", "", "## 🎓 Formação", ""])
            for edu in educations[:3]:
                institution = edu.get("institution", "N/A")
                degree = edu.get("degree", "")
                lines.append(f"- **{institution}** - {degree}")

        return "\n".join(lines)

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/orchestrator.py

```python
from typing import Dict, Any, Optional, List
import logging
import re

from src.domains.base import DomainContext, DomainResponse
from src.domains.sourced_profile_sourcing.agents.router import RouterAgent
from src.domains.sourced_profile_sourcing.agents.analytics import AnalyticsAgent
from src.domains.sourced_profile_sourcing.agents.search import SearchAgent
from src.domains.sourced_profile_sourcing.agents.detail import DetailAgent
from src.domains.sourced_profile_sourcing.agents.comparison import ComparisonAgent
from src.domains.sourced_profile_sourcing.agents.report import ReportAgent
from src.domains.sourced_profile_sourcing.agents.action import ActionAgent
from src.domains.sourced_profile_sourcing.agents.planner import (
    ExecutionPlan, AgentTask, TaskStatus, QUERY_PATTERNS
)
from src.domains.sourced_profile_sourcing.config.domain_settings import get_domain_settings

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:

    def __init__(self):
        self._settings = get_domain_settings()
        self._router = RouterAgent()

        self._agents = {
            "analytics": AnalyticsAgent(),
            "search": SearchAgent(),
            "detail": DetailAgent(),
            "comparison": ComparisonAgent(),
            "report": ReportAgent(),
            "action": ActionAgent(),
        }

        for agent in self._agents.values():
            self._router.register_agent(agent)

        logger.info(
            "🤖 Multi-Agent Orchestrator initialized with 6 specialized agents")

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> DomainResponse:
        if not context.sourcing_id:
            return DomainResponse(
                success=False,
                message="❌ Sourcing ID é obrigatório",
                error="missing_sourcing_id"
            )

        logger.info(f"🎯 Processing query: {query[:50]}...")

        plan = self._analyze_query_complexity(query)

        if plan and len(plan.tasks) > 1:
            logger.info(f"📋 Multi-step plan detected: {len(plan.tasks)} tasks")
            return self._execute_plan(plan, query, context, aggregated_stats)

        response = self._router.process(query, context, aggregated_stats)
        return response.to_domain_response()

    def _analyze_query_complexity(self, query: str) -> Optional[ExecutionPlan]:
        query_lower = query.lower()

        for pattern_name, config in QUERY_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, query_lower):
                    logger.info(f"🔍 Matched pattern: {pattern_name}")
                    return self._create_plan_from_pattern(config["pipeline"], query)

        return None

    def _create_plan_from_pattern(
        self,
        pipeline: List[Dict],
        query: str
    ) -> ExecutionPlan:
        plan = ExecutionPlan()

        params = self._extract_params_from_query(query)

        prev_task_id = None
        for step in pipeline:
            task_params = {**params, **step.get("params", {})}

            if step.get("input") and prev_task_id:
                task_params["_input_from"] = step["input"]

            task = AgentTask(
                agent_id=step["agent"],
                action=step["action"],
                params=task_params,
                depends_on=prev_task_id
            )

            plan.add_task(task)

            if step.get("output"):
                prev_task_id = f"{step['agent']}:{step['action']}"

        return plan

    def _extract_params_from_query(self, query: str) -> Dict[str, Any]:
        params = {}
        query_lower = query.lower()

        import re
        numbers = re.findall(r'\b(\d+)\b', query)

        skills = ["python", "java", "javascript", "react", "node", "aws",
                  "docker", "kubernetes", "sql", "django", "flask", "fastapi"]
        for skill in skills:
            if skill in query_lower:
                params["skill"] = skill
                break

        cities = {
            "são paulo": "São Paulo", "sp": "São Paulo",
            "rio": "Rio de Janeiro", "rj": "Rio de Janeiro",
            "bh": "Belo Horizonte", "curitiba": "Curitiba",
            "brasília": "Brasília", "brasilia": "Brasília"
        }
        for key, city in cities.items():
            if key in query_lower:
                params["location"] = city
                break

        if "score" in query_lower:
            for n in numbers:
                if 50 <= int(n) <= 100:
                    params["min_score"] = int(n)
                    break

        if "top" in query_lower:
            for n in numbers:
                if int(n) <= 20:
                    params["limit"] = int(n)
                    break

        return params

    def _execute_plan(
        self,
        plan: ExecutionPlan,
        original_query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]]
    ) -> DomainResponse:
        iteration = 0
        final_response = None

        while not plan.is_complete() and iteration < self._settings.orchestrator.max_iterations:
            iteration += 1
            task = plan.get_next_task()

            if not task:
                logger.warning("No executable task found")
                break

            logger.info(f"🔄 Step {iteration}: {task.agent_id}:{task.action}")
            task.status = TaskStatus.IN_PROGRESS

            try:
                if task.params.get("_input_from"):
                    input_key = task.params.pop("_input_from")
                    input_data = plan.get_stored(input_key)
                    if input_data:
                        task.params["_candidates"] = input_data

                agent = self._agents.get(task.agent_id)
                if not agent:
                    task.status = TaskStatus.FAILED
                    task.error = f"Agent {task.agent_id} not found"
                    continue

                response = agent.process(
                    original_query,
                    context,
                    aggregated_stats,
                    task.params
                )

                task.status = TaskStatus.COMPLETED
                task.result = response.data
                final_response = response

                if response.data and "candidates" in response.data:
                    for t in plan.tasks:
                        if t.depends_on == f"{task.agent_id}:{task.action}":
                            plan.store_result(
                                f"{task.agent_id}_output",
                                response.data["candidates"]
                            )

            except Exception as e:
                logger.error(f"Error executing task: {e}", exc_info=True)
                task.status = TaskStatus.FAILED
                task.error = str(e)
                return DomainResponse(
                    success=False,
                    message=f"❌ Erro ao executar {task.agent_id}: {str(e)}",
                    error="task_execution_failed",
                    data={"failed_task": task.action, "agent": task.agent_id}
                )

        if final_response:
            return final_response.to_domain_response()

        return DomainResponse(
            success=False,
            message="❌ Não foi possível completar a operação",
            error="plan_execution_failed"
        )

    def process_with_callback(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None,
        on_step: Optional[callable] = None
    ) -> DomainResponse:
        if not context.sourcing_id:
            return DomainResponse(
                success=False,
                message="❌ Sourcing ID é obrigatório",
                error="missing_sourcing_id"
            )

        plan = self._analyze_query_complexity(query)

        if not plan or len(plan.tasks) <= 1:
            response = self._router.process(query, context, aggregated_stats)
            return response.to_domain_response()

        iteration = 0
        final_response = None

        while not plan.is_complete() and iteration < self._settings.orchestrator.max_iterations:
            iteration += 1
            task = plan.get_next_task()

            if not task:
                break

            if on_step:
                on_step({
                    "step": iteration,
                    "total_steps": len(plan.tasks),
                    "agent": task.agent_id,
                    "action": task.action,
                    "status": "starting"
                })

            task.status = TaskStatus.IN_PROGRESS

            try:
                if task.params.get("_input_from"):
                    input_key = task.params.pop("_input_from")
                    input_data = plan.get_stored(input_key)
                    if input_data:
                        task.params["_candidates"] = input_data

                agent = self._agents.get(task.agent_id)
                if not agent:
                    task.status = TaskStatus.FAILED
                    continue

                response = agent.process(
                    query, context, aggregated_stats, task.params)

                task.status = TaskStatus.COMPLETED
                task.result = response.data
                final_response = response

                if on_step:
                    on_step({
                        "step": iteration,
                        "agent": task.agent_id,
                        "status": "completed",
                        "preview": response.message[:200] if response.message else None
                    })

                if response.data and "candidates" in response.data:
                    plan.store_result(
                        f"{task.agent_id}_output", response.data["candidates"])

            except Exception as e:
                task.status = TaskStatus.FAILED
                if on_step:
                    on_step({"step": iteration, "agent": task.agent_id,
                            "status": "failed", "error": str(e)})

        if final_response:
            return final_response.to_domain_response()

        return DomainResponse(success=False, message="❌ Falha na execução", error="failed")

    @property
    def agents(self) -> Dict[str, Any]:
        return {"router": self._router, **self._agents}

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/planner.py

```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_MORE_DATA = "needs_more_data"


@dataclass
class AgentTask:
    agent_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    tasks: List[AgentTask] = field(default_factory=list)
    current_step: int = 0
    max_steps: int = 5
    context_data: Dict[str, Any] = field(default_factory=dict)

    def add_task(self, task: AgentTask):
        self.tasks.append(task)

    def get_next_task(self) -> Optional[AgentTask]:
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                if task.depends_on:
                    dep_task = self.get_task_by_id(task.depends_on)
                    if dep_task and dep_task.status != TaskStatus.COMPLETED:
                        continue
                return task
        return None

    def get_task_by_id(self, task_id: str) -> Optional[AgentTask]:
        for task in self.tasks:
            if f"{task.agent_id}:{task.action}" == task_id:
                return task
        return None

    def is_complete(self) -> bool:
        return all(t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED) for t in self.tasks)

    def store_result(self, key: str, data: Any):
        self.context_data[key] = data

    def get_stored(self, key: str) -> Optional[Any]:
        return self.context_data.get(key)


QUERY_PATTERNS = {
    "apply_top_candidates": {
        "patterns": [
            r"(?:adicione?|inclua?|coloque?).*top.*(?:vaga|processo)",
            r"(?:inscreva?|aplique?).*(?:melhores|top).*(?:na|em)\s+vaga",
            r"(?:envie?|mande?).*(?:top|melhores).*(?:para|pra).*vaga",
            r"top\s+\d+.*(?:na|em|para)\s+(?:vaga|processo)",
        ],
        "pipeline": [
            {"agent": "search", "action": "top", "output": "top_candidates"},
            {"agent": "action", "action": "create_apply", "input": "top_candidates"}
        ]
    },
    "convert_filtered": {
        "patterns": [
            r"(?:converta?|importe?).*(?:que|quem).*(?:sabe|tem|conhece)",
            r"(?:adicione?|traga?).*(?:base|candidatos).*(?:que|quem).*sabe",
            r"(?:importe?).*(?:python|java|skill).*(?:para|na)\s+base",
        ],
        "pipeline": [
            {"agent": "search", "action": "filter",
                "output": "filtered_candidates"},
            {"agent": "action", "action": "convert_to_candidate",
                "input": "filtered_candidates"}
        ]
    },
    "add_filtered_to_list": {
        "patterns": [
            r"(?:adicione?|salve?).*(?:que|quem).*(?:sabe|tem).*(?:na|em)\s+lista",
            r"(?:coloque?|inclua?).*(?:python|java|skill).*(?:na|em)\s+lista",
            r"lista.*(?:com|de).*(?:que|quem).*sabe",
        ],
        "pipeline": [
            {"agent": "search", "action": "filter",
                "output": "filtered_candidates"},
            {"agent": "action", "action": "add_to_list",
                "input": "filtered_candidates"}
        ]
    },
    "apply_filtered": {
        "patterns": [
            r"(?:adicione?|inclua?).*(?:que|quem).*(?:sabe|tem).*(?:na|em)\s+vaga",
            r"(?:inscreva?|aplique?).*(?:python|java|skill).*(?:na|em)\s+vaga",
            r"(?:envie?).*(?:candidatos|perfis).*(?:com|que).*(?:para|pra)\s+vaga",
        ],
        "pipeline": [
            {"agent": "search", "action": "filter",
                "output": "filtered_candidates"},
            {"agent": "action", "action": "create_apply",
                "input": "filtered_candidates"}
        ]
    },
    "report_filtered": {
        "patterns": [
            r"relat[oó]rio.*(?:dos|de|com).*(?:que|quem).*(?:sabe|tem|conhece)",
            r"report.*(?:candidatos|de).*(?:python|java|react|skill)",
            r"gere.*relat[oó]rio.*filtrado",
        ],
        "pipeline": [
            {"agent": "search", "action": "filter",
                "output": "filtered_candidates"},
            {"agent": "report", "action": "generate",
                "input": "filtered_candidates"}
        ]
    },
    "compare_filtered": {
        "patterns": [
            r"compare.*(?:candidatos|os).*(?:de|que|com).*(?:são paulo|sp|python|score)",
            r"comparar.*filtrado",
        ],
        "pipeline": [
            {"agent": "search", "action": "filter",
                "output": "filtered_candidates"},
            {"agent": "comparison", "action": "compare",
                "input": "filtered_candidates"}
        ]
    },
    "detail_best": {
        "patterns": [
            r"detalhes.*(?:do|da).*melhor",
            r"mais.*sobre.*(?:o|a).*(?:top|primeiro|melhor)",
            r"quem.*[eé].*(?:o|a).*melhor.*(?:e|,).*(?:detalhe|mostre)",
        ],
        "pipeline": [
            {"agent": "search", "action": "top", "params": {
                "limit": 1}, "output": "best_candidate"},
            {"agent": "detail", "action": "show", "input": "best_candidate"}
        ]
    },
    "analyze_skill_holders": {
        "patterns": [
            r"an[aá]lise.*(?:dos|de).*(?:que|quem).*sabe",
            r"estat[ií]sticas.*(?:candidatos|de).*(?:python|java|skill)",
        ],
        "pipeline": [
            {"agent": "search", "action": "filter_skill",
                "output": "skill_candidates"},
            {"agent": "analytics", "action": "summarize", "input": "skill_candidates"}
        ]
    }
}

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/report.py

```python
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from src.domains.base import DomainContext
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse
from src.domains.sourced_profile_sourcing.fairness import FairnessGuard, anonymize_for_llm

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "report"

    @property
    def agent_name(self) -> str:
        return "Report Agent"

    @property
    def description(self) -> str:
        return "Especialista em gerar relatórios executivos e análises para gestores"

    @property
    def capabilities(self) -> List[str]:
        return [
            "Relatório executivo completo",
            "Relatório de top candidatos",
            "Métricas para apresentação",
            "Insights e recomendações"
        ]

    def get_system_prompt(self, context: DomainContext) -> str:
        return f"""Você é um consultor de RH sênior especializado em relatórios executivos.

**CONTEXTO:**
- Sourcing ID: {context.sourcing_id}

**SUAS CAPACIDADES:**
- executive_report: Relatório executivo completo
- top_candidates_report: Relatório focado nos melhores candidatos

**RESPOSTA (JSON):**
{{
    "action": "executive_report",
    "params": {{"limit": 10}},
    "reasoning": "motivo"
}}"""

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        params = params or {}

        success, validated_params, warnings = self._validate_and_correct_params(
            params, context)

        action = self._identify_action(query)

        pre_filtered = validated_params.get("_candidates")

        if action == "top_candidates_report":
            return self._generate_top_candidates_report(context, validated_params, pre_filtered, warnings)

        return self._generate_executive_report(context, aggregated_stats, validated_params, pre_filtered, warnings)

    def _identify_action(self, query: str) -> str:
        query_lower = query.lower()

        if "top" in query_lower or "melhores candidatos" in query_lower:
            return "top_candidates_report"

        return "executive_report"

    def _generate_executive_report(
        self,
        context: DomainContext,
        stats: Optional[Dict],
        params: Dict,
        pre_filtered: Optional[List[Dict]] = None,
        warnings: Optional[List[str]] = None
    ) -> AgentResponse:
        candidates = pre_filtered or self._fetch_candidates(
            context, limit=100, order={"sourcing_score": "desc"})

        filter_label = ""
        if pre_filtered:
            filter_label = f" (filtrados: {len(candidates)} candidatos)"

        metrics = self._calculate_metrics(candidates)
        distributions = self._calculate_distributions(candidates)

        analysis = self._generate_executive_analysis(
            metrics, distributions, candidates[:5])

        fact_check_result = self.fact_checker.check_analysis_integrity(
            {
                "total_count": len(candidates),
                "average_score": metrics.get("avg_score"),
                "top_candidates": candidates[:5]
            },
            candidates
        )

        report_warnings = warnings or []
        if not fact_check_result["valid"]:
            logger.warning(
                f"Report failed fact check: {fact_check_result['issues']}")
            report_warnings.extend(fact_check_result["issues"])

        if fact_check_result["warnings"]:
            report_warnings.extend(fact_check_result["warnings"])

        report = self._format_executive_report(
            metrics, distributions, candidates[:10], analysis)

        chart_data = self._prepare_chart_data(
            metrics, distributions, candidates)

        return AgentResponse(
            success=True,
            message=report,
            data={
                "report_type": "executive",
                "metrics": metrics,
                "distributions": distributions,
                "chart_data": chart_data,
                "confidence": fact_check_result.get("confidence", 1.0)
            },
            suggestions=["Top 10 candidatos", "Comparar melhores"],
            confidence=fact_check_result.get("confidence", 1.0),
            warnings=report_warnings if report_warnings else None
        )

    def _generate_top_candidates_report(
        self,
        context: DomainContext,
        params: Dict,
        pre_filtered: Optional[List[Dict]] = None
    ) -> AgentResponse:
        limit = params.get("limit", 5)

        if pre_filtered:
            candidates = pre_filtered[:limit]
        else:
            candidates = self._fetch_candidates(
                context, limit=limit, order={"sourcing_score": "desc"})

        if not candidates:
            return AgentResponse(
                success=False,
                message="❌ Nenhum candidato encontrado",
                error="no_candidates"
            )

        analysis = self._analyze_top_candidates(candidates)
        report = self._format_top_candidates_report(candidates, analysis)

        return AgentResponse(
            success=True,
            message=report,
            data={
                "report_type": "top_candidates",
                "generated_at": datetime.now().isoformat(),
                "sourcing_id": context.sourcing_id,
                "candidates": [self._candidate_dict(c) for c in candidates],
                "analysis": analysis
            },
            suggestions=[
                "Relatório executivo completo",
                f"Detalhes do candidato {candidates[0].get('id', '')}" if candidates else ""
            ]
        )

    def _calculate_metrics(self, candidates: List[Dict]) -> Dict:
        if not candidates:
            return {}

        scores = [c.get("score") or c.get("sourcing_score")
                  or 0 for c in candidates]
        valid_scores = [s for s in scores if s > 0]

        exp = [c.get("total_experience_years") or 0 for c in candidates]
        valid_exp = [e for e in exp if e > 0]

        return {
            "total_candidates": len(candidates),
            "with_score": len(valid_scores),
            "avg_score": round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0,
            "max_score": max(valid_scores) if valid_scores else 0,
            "min_score": min(valid_scores) if valid_scores else 0,
            "score_above_90": len([s for s in valid_scores if s >= 90]),
            "score_above_80": len([s for s in valid_scores if s >= 80]),
            "score_above_70": len([s for s in valid_scores if s >= 70]),
            "avg_experience": round(sum(valid_exp) / len(valid_exp), 1) if valid_exp else 0,
            "max_experience": max(valid_exp) if valid_exp else 0
        }

    def _calculate_distributions(self, candidates: List[Dict]) -> Dict:
        locations = {}
        skills = {}

        for c in candidates:
            city = c.get("city", "N/A")
            if city and city != "N/A":
                locations[city] = locations.get(city, 0) + 1

            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            for skill in analysis.get("skills_assessment", {}).get("strong", []):
                skill_lower = skill.lower()
                skills[skill_lower] = skills.get(skill_lower, 0) + 1

        return {
            "by_location": dict(sorted(locations.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_skills": dict(sorted(skills.items(), key=lambda x: x[1], reverse=True)[:15])
        }

    def _generate_executive_analysis(
        self,
        metrics: Dict,
        distributions: Dict,
        top_candidates: List[Dict]
    ) -> Dict:
        try:
            anonymized_top, _ = anonymize_for_llm(
                top_candidates[:3],
                fields_to_keep=["score", "sourcing_score",
                                "total_experience_years", "city"]
            )

            prompt = f"""Analise esta pipeline de talentos e forneça um parecer executivo em JSON:

MÉTRICAS:
- Total: {metrics.get('total_candidates', 0)}
- Score médio: {metrics.get('avg_score', 0)}
- Score >= 90: {metrics.get('score_above_90', 0)}
- Score >= 80: {metrics.get('score_above_80', 0)}
- Experiência média: {metrics.get('avg_experience', 0)} anos

TOP SKILLS: {list(distributions.get('top_skills', {}).items())[:8]}
DISTRIBUIÇÃO POR REGIÃO: {list(distributions.get('by_location', {}).items())[:5]}

TOP 3 CANDIDATOS (anonimizado):
{anonymized_top}

Retorne JSON:
{{
    "executive_summary": "resumo em 2 frases",
    "insights": ["insight 1", "insight 2", "insight 3"],
    "recommendations": ["recomendação 1", "recomendação 2"],
    "pipeline_health": "excellent/good/moderate/needs_attention",
    "hiring_probability": "high/medium/low"
}}"""

            response = self.llm.invoke([
                SystemMessage(
                    content="Retorne apenas JSON válido, sem markdown. Não mencione nomes de pessoas."),
                HumanMessage(content=prompt)
            ])

            result = self._parse_json_response(response.content)
            return FairnessGuard.add_hiring_probability_disclaimer(result)
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {
                "executive_summary": f"Pipeline com {metrics.get('total_candidates', 0)} candidatos.",
                "insights": [],
                "recommendations": [],
                "pipeline_health": "moderate",
                "hiring_probability": "medium"
            }

    def _analyze_top_candidates(self, candidates: List[Dict]) -> Dict:
        try:
            anonymized, _ = anonymize_for_llm(
                candidates[:5],
                fields_to_keep=["score", "sourcing_score",
                                "total_experience_years", "city", "skills"]
            )

            prompt = f"""Analise estes candidatos (anonimizados) e retorne JSON:

{anonymized}

{{
    "best_pick": "Código do candidato e justificativa baseada em dados técnicos",
    "runner_up": "Código do candidato e justificativa",
    "common_strengths": ["força 1", "força 2"],
    "hiring_advice": "conselho de 1 frase"
}}"""

            response = self.llm.invoke([
                SystemMessage(
                    content="Retorne apenas JSON válido. Use códigos de candidato (C001, C002) em vez de nomes."),
                HumanMessage(content=prompt)
            ])

            return self._parse_json_response(response.content)
        except Exception as e:
            logger.error(f"Error analyzing candidates: {e}")
            return {
                "best_pick": f"Candidato {candidates[0].get('id', 'N/A')}" if candidates else "N/A",
                "common_strengths": [],
                "hiring_advice": "Entrevistar os candidatos com maior score."
            }

    def _format_executive_report(
        self,
        metrics: Dict,
        distributions: Dict,
        top_candidates: List[Dict],
        analysis: Dict
    ) -> str:
        health_emoji = {
            "excellent": "🟢",
            "good": "🟡",
            "moderate": "🟠",
            "needs_attention": "🔴"
        }.get(analysis.get("pipeline_health", "moderate"), "⚪")

        lines = [
            "# 📊 Relatório Executivo de Sourcing",
            "",
            f"*Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}*",
            "",
            "---",
            "",
            "## 📝 Resumo Executivo",
            "",
            f"> {analysis.get('executive_summary', 'N/A')}",
            "",
            f"**Status da Pipeline:** {health_emoji} {analysis.get('pipeline_health', 'N/A').title()}",
            f"**Probabilidade de Contratação:** {analysis.get('hiring_probability', 'N/A').title()}",
            "",
            "---",
            "",
            "## 📈 Métricas Principais",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| 👥 Total de Candidatos | **{metrics.get('total_candidates', 0)}** |",
            f"| 📊 Score Médio | **{metrics.get('avg_score', 0)}** |",
            f"| ⭐ Score Máximo | **{metrics.get('max_score', 0)}** |",
            f"| 🎯 Score >= 90 | **{metrics.get('score_above_90', 0)}** |",
            f"| ✅ Score >= 80 | **{metrics.get('score_above_80', 0)}** |",
            f"| 📅 Exp. Média | **{metrics.get('avg_experience', 0)} anos** |",
            "",
            "---",
            "",
            "## 🏆 Top Candidatos",
            ""
        ]

        if top_candidates:
            lines.append("| # | Candidato | Score | Empresa | Exp. |")
            lines.append("|:-:|-----------|:-----:|---------|:----:|")

            for i, c in enumerate(top_candidates[:5], 1):
                name = c.get("name", "N/A")
                score = c.get("score") or c.get("sourcing_score") or "-"
                company = self._sanitize(c.get("current_company", "-"), 20)
                exp = c.get("total_experience_years") or "-"
                lines.append(
                    f"| {i} | {name} | **{score}** | {company} | {exp} |")

        lines.extend(["", "---", "", "## 💡 Insights", ""])
        for insight in analysis.get("insights", []):
            lines.append(f"- {insight}")

        lines.extend(["", "---", "", "## 🛠️ Skills Mais Encontradas", ""])
        top_skills = list(distributions.get("top_skills", {}).items())[:8]
        if top_skills:
            max_count = top_skills[0][1] if top_skills else 1
            for skill, count in top_skills:
                bar_len = int((count / max_count) * 10)
                bar = "█" * bar_len + "░" * (10 - bar_len)
                lines.append(f"- `{skill}` {bar} ({count})")

        lines.extend(["", "---", "", "## 📍 Distribuição Geográfica", ""])
        for city, count in list(distributions.get("by_location", {}).items())[:5]:
            lines.append(f"- **{city}**: {count} candidatos")

        lines.extend(["", "---", "", "## ✅ Recomendações", ""])
        for i, rec in enumerate(analysis.get("recommendations", []), 1):
            lines.append(f"{i}. {rec}")

        if analysis.get("_disclaimer"):
            lines.extend(["", "---", "", analysis["_disclaimer"]])

        return "\n".join(lines)

    def _format_top_candidates_report(self, candidates: List[Dict], analysis: Dict) -> str:
        lines = [
            "# 🏆 Relatório de Top Candidatos",
            "",
            f"*{len(candidates)} candidatos selecionados*",
            "",
            "---",
            "",
            "## 🎯 Parecer Rápido",
            "",
            f"**Melhor Escolha:** {analysis.get('best_pick', 'N/A')}",
            ""
        ]

        if analysis.get("runner_up"):
            lines.append(f"**Segunda Opção:** {analysis.get('runner_up')}")
            lines.append("")

        lines.extend([
            f"💡 **Conselho:** {analysis.get('hiring_advice', '')}",
            "",
            "---",
            "",
            "## 📋 Candidatos",
            ""
        ])

        for i, c in enumerate(candidates, 1):
            name = c.get("name", "N/A")
            score = c.get("score") or c.get("sourcing_score") or 0
            company = c.get("current_company", "N/A")
            exp = c.get("total_experience_years") or "N/A"

            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."

            lines.append(f"### {medal} {name}")
            lines.append(
                f"**Score:** {score} | **Empresa:** {company} | **Exp:** {exp} anos")

            analysis_data = c.get("analysis") or c.get("ai_analysis") or {}
            one_liner = analysis_data.get("one_liner")
            if one_liner:
                lines.append(f"> {one_liner}")
            lines.append("")

        if analysis.get("common_strengths"):
            lines.extend(["---", "", "## ✨ Pontos Fortes em Comum", ""])
            for strength in analysis.get("common_strengths", []):
                lines.append(f"- {strength}")

        return "\n".join(lines)

    def _prepare_chart_data(self, metrics: Dict, distributions: Dict, candidates: List[Dict]) -> Dict:
        score_ranges = {"90-100": 0, "80-89": 0,
                        "70-79": 0, "60-69": 0, "<60": 0}
        for c in candidates:
            score = c.get("score") or c.get("sourcing_score") or 0
            if score >= 90:
                score_ranges["90-100"] += 1
            elif score >= 80:
                score_ranges["80-89"] += 1
            elif score >= 70:
                score_ranges["70-79"] += 1
            elif score >= 60:
                score_ranges["60-69"] += 1
            else:
                score_ranges["<60"] += 1

        return {
            "score_distribution": {
                "type": "bar",
                "title": "Distribuição de Scores",
                "labels": list(score_ranges.keys()),
                "values": list(score_ranges.values()),
                "colors": ["#22c55e", "#84cc16", "#eab308", "#f97316", "#ef4444"]
            },
            "top_skills": {
                "type": "horizontal_bar",
                "title": "Skills Mais Encontradas",
                "labels": list(distributions.get("top_skills", {}).keys())[:10],
                "values": list(distributions.get("top_skills", {}).values())[:10]
            },
            "location_pie": {
                "type": "pie",
                "title": "Distribuição por Localização",
                "labels": list(distributions.get("by_location", {}).keys())[:6],
                "values": list(distributions.get("by_location", {}).values())[:6]
            },
            "pipeline_funnel": {
                "type": "funnel",
                "title": "Funil de Candidatos",
                "stages": [
                    {"label": "Total", "value": metrics.get(
                        "total_candidates", 0)},
                    {"label": "Score >= 70", "value": metrics.get(
                        "score_above_70", 0)},
                    {"label": "Score >= 80", "value": metrics.get(
                        "score_above_80", 0)},
                    {"label": "Score >= 90", "value": metrics.get(
                        "score_above_90", 0)}
                ]
            },
            "summary_kpis": {
                "type": "kpi_cards",
                "items": [
                    {"label": "Total", "value": metrics.get(
                        "total_candidates", 0), "icon": "users"},
                    {"label": "Score Médio", "value": metrics.get(
                        "avg_score", 0), "icon": "chart"},
                    {"label": "Top Performers", "value": metrics.get(
                        "score_above_90", 0), "icon": "star"},
                    {"label": "Exp. Média",
                        "value": f"{metrics.get('avg_experience', 0)} anos", "icon": "briefcase"}
                ]
            }
        }

    def _candidate_dict(self, c: Dict) -> Dict:
        analysis = c.get("analysis") or c.get("ai_analysis") or {}
        return {
            "id": c.get("id"),
            "name": c.get("name"),
            "score": c.get("score") or c.get("sourcing_score"),
            "experience_years": c.get("total_experience_years"),
            "current_company": c.get("current_company"),
            "city": c.get("city"),
            "skills": analysis.get("skills_assessment", {}).get("strong", []),
            "highlights": analysis.get("highlights", [])
        }

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/router.py

```python
from typing import Dict, Any, Optional, List, Tuple
import logging
import re

from src.domains.base import DomainContext
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse
from src.domains.sourced_profile_sourcing.memory import ConversationMemory
from src.domains.sourced_profile_sourcing.param_extractor import param_extractor

logger = logging.getLogger(__name__)


AGENT_ROUTING = {
    "action": {
        "keywords": [
            "converter", "importar", "adicionar", "incluir", "colocar", "salvar",
            "candidatura", "apply", "aplicar", "inscrever", "vaga", "processo",
            "lista", "favoritar", "favoritos",
            "atualizar", "alterar", "mudar", "score",
            "remover", "excluir", "deletar", "tirar", "descartar"
        ],
        "patterns": [
            r"(?:converter?|importar?).*(?:base|candidato)",
            r"(?:adicionar?|incluir?|colocar?).*(?:lista|vaga|processo)",
            r"(?:criar?|fazer?).*(?:candidatura|apply|inscrição)",
            r"(?:enviar?|mandar?).*(?:para|pra).*vaga",
            r"(?:atualizar?|mudar?).*score",
            r"(?:remover?|excluir?|deletar?).*(?:perfil|candidato)",
            r"(?:salvar?|favoritar?)",
        ],
        "priority": 0
    },
    "analytics": {
        "keywords": [
            "quantos", "total", "média", "media", "distribuição", "distribuicao",
            "percentual", "estatística", "estatistica",
            "híbrido", "hibrido", "remoto", "presencial", "home office",
            "experiência média", "experiencia media", "nível de inglês", "nivel de ingles",
            "formação", "formacao", "pontos fortes", "gaps", "lacunas",
            "descartar", "triagem", "prioridade"
        ],
        "patterns": [
            r"quantos candidatos",
            r"qual a média",
            r"qual o total",
            r"distribuição de",
            r"por cidade",
            r"por gênero",
            r"quantos.*(?:híbrido|hibrido|remoto|presencial)",
            r"(?:aceita|aceitam).*(?:híbrido|hibrido|remoto|presencial)",
            r"(?:experiência|experiencia).*(?:média|media).*(?:top|melhor)",
            r"(?:top|melhor)\s*\d+.*(?:experiência|experiencia|inglês|ingles|formação|formacao)",
            r"(?:nível|nivel).*(?:inglês|ingles).*(?:top|melhor)",
            r"(?:formação|formacao).*(?:top|melhor)",
            r"pontos?\s*fortes?.*comum",
            r"(?:gaps?|lacunas?).*competência",
            r"(?:quais|quem).*descartar",
            r"(?:precisa|precisam).*triagem",
            r"organiz.*prioridade",
            r"(?:como|sugira).*(?:melhorar|refinar|filtros)",
        ],
        "priority": 1,
        "negative_patterns": [
            r"^(?:liste|mostre|busque).*top\s*\d+$",
        ]
    },
    "search": {
        "keywords": ["buscar", "procurar", "filtrar", "listar", "quem sabe", "quem tem", "candidatos com", "top", "melhores"],
        "patterns": [
            r"quem sabe",
            r"buscar por",
            r"filtrar por",
            r"candidatos com",
            r"quais candidatos",
            r"top\s*\d+",
            r"(?:mostr[ae]|list[ae]|traz|tra[gz]).*(?:top|melhor)",
            r"(?:top|melhor)\s*\d+\s*(?:candidato|perfil)",
            r"(?:os|as)\s*\d+\s*melhor",
        ],
        "priority": 2,
        "negative_patterns": [
            r"compar[ae]",
            r"versus|vs\b",
            r"lado a lado",
            r"diferenças?\s+entre",
        ]
    },
    "detail": {
        "keywords": ["detalhes", "detalhe", "mais sobre", "informações", "perfil", "mostrar candidato"],
        "patterns": [r"detalhes do", r"me fale sobre", r"mais sobre o", r"informações do candidato", r"perfil do"],
        "priority": 3
    },
    "comparison": {
        "keywords": ["comparar", "compare", "diferença", "lado a lado", "versus", "vs"],
        "patterns": [
            r"compar[ae]\s*(?:os|as|esses|essas)?",
            r"compar[ae].*(?:candidato|perfil|melhor|top)",
            r"diferenças?\s+entre",
            r"lado a lado",
            r"(?:candidato|perfil).*versus|vs",
        ],
        "priority": 2
    },
    "report": {
        "keywords": ["relatório", "relatorio", "report", "resumo executivo", "apresentar", "gestor"],
        "patterns": [r"relatório executivo", r"gere um report", r"resumo para", r"apresentar ao gestor"],
        "priority": 1
    }
}

MEMORY_PATTERNS = {
    "pronoun_reference": {
        "patterns": [
            r"(?:me )?(?:fale|conta|mostre|explique).*(?:dele|dela|desse|dessa)",
            r"(?:e |qual |quem ).*(?:ele|ela|esse|essa)",
            r"(?:detalhes?|mais|sobre).*(?:dele|dela|desse|dessa)",
            r"^(?:e )?(?:esse|essa|ele|ela)\??$",
        ],
        "action": "resolve_pronoun",
        "target_agent": "detail"
    },
    "position_reference": {
        "patterns": [
            r"(?:o |a )?(?:primeir|segund|terceir|quart|quint|\d+[ºª°])",
            r"^e o (?:primeir|segund|terceir|quart|quint)",
            r"(?:me fale|detalhes) d[oa] (?:primeir|segund|terceir)",
        ],
        "action": "resolve_position",
        "target_agent": "detail"
    },
    "previous_reference": {
        "patterns": [
            r"(?:o |a )?anterior",
            r"(?:volte?|volta) (?:pro|para o|pra) anterior",
            r"o último (?:candidato|que (?:vi|mostrou))",
        ],
        "action": "resolve_previous",
        "target_agent": "detail"
    },
    "shortlist_add": {
        "patterns": [
            r"(?:adicione|coloque|salve|favorite).*(?:shortlist|lista|favoritos?)",
            r"^(?:salve?|favorite)(?:\s+(?:esse|ela|ele))?$",
        ],
        "action": "add_to_shortlist",
        "target_agent": "shortlist"
    },
    "shortlist_show": {
        "patterns": [
            r"(?:mostre|veja|qual|quem).*(?:shortlist|minha lista|favoritos|salvos)",
            r"^(?:shortlist|lista de favoritos)$",
        ],
        "action": "show_shortlist",
        "target_agent": "shortlist"
    },
    "filter_continuation": {
        "patterns": [
            r"^(?:e )?(?:desse|dessa|desses|dessas|deles|delas)",
            r"dentre (?:eles|elas|esses|essas)",
            r"(?:desse|dessa) (?:grupo|lista)",
        ],
        "action": "continue_filter",
        "target_agent": "search"
    },
}


class RouterAgent(BaseAgent):

    def __init__(self):
        super().__init__()
        self._agents: Dict[str, BaseAgent] = {}

    @property
    def agent_id(self) -> str:
        return "router"

    @property
    def agent_name(self) -> str:
        return "Router Agent"

    @property
    def description(self) -> str:
        return "Analisa a pergunta e direciona para o agente especializado correto"

    @property
    def capabilities(self) -> List[str]:
        return ["Roteamento inteligente", "Resolução de referências", "Memória conversacional"]

    def register_agent(self, agent: BaseAgent):
        self._agents[agent.agent_id] = agent
        logger.debug(f"Registered agent: {agent.agent_id}")

    def get_system_prompt(self, context: DomainContext) -> str:
        agents_desc = "\n".join([
            f"- **{agent.agent_id}**: {agent.description}"
            for agent in self._agents.values()
        ])

        memory = context.get_memory()
        memory_context = memory.get_context_for_prompt()

        return f"""Você é um roteador que analisa perguntas e decide qual agente deve responder.

**AGENTES:**
{agents_desc}

**CONTEXTO:**
- Sourcing: {context.sourcing_id}
- Última lista: {memory_context.get('last_shown_count', 0)} candidatos
- Último detalhado: {memory_context.get('last_detailed')}
- Shortlist: {memory_context.get('shortlist_count', 0)}

**RESPOSTA (JSON):**
{{"agent_id": "string", "params": {{}}, "reasoning": "string"}}"""

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        memory = context.get_memory()

        memory_result = self._handle_memory_patterns(query, memory)
        if memory_result:
            agent_id, params = memory_result
            return self._delegate_to_agent(agent_id, query, context, aggregated_stats, params, memory)

        agent_id = self._fast_route(query)

        if agent_id:
            params = self._build_params(query, agent_id, memory)
        else:
            agent_id, params = self._llm_route(query, context)

        return self._delegate_to_agent(agent_id, query, context, aggregated_stats, params, memory)

    def _handle_memory_patterns(
        self,
        query: str,
        memory: ConversationMemory
    ) -> Optional[Tuple[str, Dict[str, Any]]]:
        query_lower = query.lower().strip()

        for pattern_name, config in MEMORY_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, query_lower):
                    action = config["action"]
                    target_agent = config["target_agent"]

                    params = self._resolve_memory_action(action, query, memory)
                    if params is not None:
                        return target_agent, params

        return None

    def _resolve_memory_action(
        self,
        action: str,
        query: str,
        memory: ConversationMemory
    ) -> Optional[Dict[str, Any]]:

        if action == "resolve_pronoun":
            candidate_id = memory.last_candidate_detailed
            if candidate_id:
                return {"candidate_id": candidate_id, "_resolved_from": "pronoun"}
            return None

        if action == "resolve_position":
            candidate_id = memory.resolve_reference(query)
            if candidate_id:
                return {"candidate_id": candidate_id, "_resolved_from": "position"}
            return None

        if action == "resolve_previous":
            if memory.detailed_history:
                return {"candidate_id": memory.detailed_history[-1], "_resolved_from": "previous"}
            if memory.last_candidate_detailed:
                return {"candidate_id": memory.last_candidate_detailed, "_resolved_from": "last"}
            return None

        if action == "add_to_shortlist":
            candidate_id = memory.last_candidate_detailed
            if candidate_id:
                return {"candidate_id": candidate_id, "_action": "add_shortlist"}
            return None

        if action == "show_shortlist":
            return {"_action": "show_shortlist", "candidate_ids": memory.shortlist}

        if action == "continue_filter":
            if memory.active_filters:
                return {"_keep_filters": True, **memory.active_filters}
            return None

        return None

    def _delegate_to_agent(
        self,
        agent_id: str,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]],
        params: Dict[str, Any],
        memory: ConversationMemory
    ) -> AgentResponse:

        if agent_id == "shortlist":
            return self._handle_shortlist_action(params, memory, context)

        if agent_id not in self._agents:
            agent_id = "analytics"

        agent = self._agents[agent_id]

        success, validated_params, warnings = agent._validate_and_correct_params(
            params, context)

        if not success and warnings:
            return AgentResponse(
                success=False,
                message=f"❌ Parâmetros inválidos: {'; '.join(warnings)}",
                error="invalid_params",
                confidence=0.0
            )

        logger.info(
            f"🎯 Routing to: {agent.agent_name} with params: {validated_params}")

        response = agent.process(
            query, context, aggregated_stats, validated_params)

        if warnings and response.success:
            response.warnings = warnings

        self._update_memory_after_response(agent_id, response, memory)

        return response

    def _handle_shortlist_action(
        self,
        params: Dict[str, Any],
        memory: ConversationMemory,
        context: DomainContext
    ) -> AgentResponse:
        action = params.get("_action")

        if action == "add_shortlist":
            candidate_id = params.get("candidate_id")
            if candidate_id:
                if memory.add_to_shortlist(candidate_id):
                    return AgentResponse(
                        success=True,
                        message=f"✅ Candidato #{candidate_id} adicionado à shortlist ({len(memory.shortlist)} total)",
                        data={"shortlist": memory.shortlist}
                    )
                return AgentResponse(
                    success=True,
                    message=f"ℹ️ Candidato #{candidate_id} já está na shortlist",
                    data={"shortlist": memory.shortlist}
                )

        if action == "show_shortlist":
            if not memory.shortlist:
                return AgentResponse(
                    success=True,
                    message="📋 Sua shortlist está vazia",
                    data={"shortlist": []},
                    suggestions=["Top 5 candidatos", "Listar candidatos"]
                )

            candidates = self._fetch_shortlist_candidates(
                memory.shortlist, context)
            return self._format_shortlist_response(candidates, memory)

        return AgentResponse(success=False, message="❌ Ação de shortlist não reconhecida")

    def _fetch_shortlist_candidates(
        self,
        candidate_ids: List[int],
        context: DomainContext
    ) -> List[Dict]:
        api = self.get_api_operations(context)
        result = api.get_candidates_by_ids(candidate_ids)
        return result.data if result.success else []

    def _format_shortlist_response(
        self,
        candidates: List[Dict],
        memory: ConversationMemory
    ) -> AgentResponse:
        if not candidates:
            return AgentResponse(
                success=True,
                message="📋 Não encontrei os candidatos da shortlist",
                data={"shortlist": memory.shortlist}
            )

        lines = [
            f"## 📋 Sua Shortlist ({len(candidates)} candidatos)",
            "",
            "| # | Nome | Score | Empresa |",
            "|:-:|------|:-----:|---------|"
        ]

        for i, c in enumerate(candidates, 1):
            name = c.get("name", "-")
            score = c.get("sourcing_score") or c.get("score") or "-"
            company = c.get("current_company") or "-"
            lines.append(f"| {i} | {name} | {score} | {company} |")

        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={
                "shortlist": memory.shortlist,
                "candidates": [{"id": c.get("id"), "name": c.get("name")} for c in candidates]
            },
            suggestions=["Compare esses candidatos",
                         "Remover da shortlist", "Limpar shortlist"]
        )

    def _update_memory_after_response(
        self,
        agent_id: str,
        response: AgentResponse,
        memory: ConversationMemory
    ):
        if not response.success or not response.data:
            return

        if agent_id in ("search", "analytics", "report"):
            candidates = response.data.get("candidates", [])
            if candidates:
                ids = [c.get("id") for c in candidates if c.get("id")]
                memory.update_after_list(ids)

                for c in candidates[:10]:
                    if c.get("name"):
                        memory._add_mentioned(c["name"], c["id"])

        if agent_id == "detail":
            candidate = response.data.get("candidate", {})
            if candidate.get("id"):
                memory.update_after_detail(
                    candidate["id"], candidate.get("name"))

        if agent_id == "comparison":
            candidates = response.data.get("candidates", [])
            for c in candidates:
                if c.get("name") and c.get("id"):
                    memory._add_mentioned(c["name"], c["id"])

    def _fast_route(self, query: str) -> Optional[str]:
        query_lower = query.lower()

        analytic_indicators = [
            "média", "media", "experiência", "experiencia",
            "nível", "nivel", "inglês", "ingles",
            "formação", "formacao", "pontos fortes", "gaps",
            "híbrido", "hibrido", "remoto", "presencial",
            "descartar", "triagem", "prioridade", "comum"
        ]
        has_top = bool(re.search(r"top\s*\d+", query_lower))
        has_analytic = any(ind in query_lower for ind in analytic_indicators)

        if has_top and has_analytic:
            return "analytics"

        scores = {}
        for agent_id, config in AGENT_ROUTING.items():
            score = 0

            negative_patterns = config.get("negative_patterns", [])
            has_negative = any(re.search(p, query_lower)
                               for p in negative_patterns)
            if has_negative:
                continue

            for keyword in config["keywords"]:
                if keyword in query_lower:
                    score += 1

            for pattern in config["patterns"]:
                if re.search(pattern, query_lower):
                    score += 2

            if score > 0:
                scores[agent_id] = score

        if not scores:
            return None

        max_score = max(scores.values())
        if max_score < 2:
            return None

        top_agents = [agent for agent,
                      score in scores.items() if score == max_score]

        if len(top_agents) > 1:
            logger.info(
                f"Routing tie detected: {top_agents} with score {max_score}")
            priority_order = ["action", "detail",
                              "comparison", "search", "report", "analytics"]
            for preferred in priority_order:
                if preferred in top_agents:
                    return preferred

        return top_agents[0]

    def _build_params(
        self,
        query: str,
        agent_id: str,
        memory: ConversationMemory
    ) -> Dict[str, Any]:
        extracted = param_extractor.extract(query)
        params = extracted.to_dict()

        if memory.should_keep_filters(query):
            for key, value in memory.active_filters.items():
                if key not in params:
                    params[key] = value
            params["_kept_filters"] = True

        if agent_id == "detail":
            if not params.get("candidate_id"):
                resolved = memory.resolve_reference(query)
                if resolved:
                    params["candidate_id"] = resolved

        if agent_id == "comparison":
            has_compare_intent = any(
                w in query.lower() for w in ["compar", "versus", "vs", "diferença", "lado a lado"]
            )
            if has_compare_intent and "top" in query.lower() and not params.get("limit"):
                params["top_n"] = extracted.limit or 3

        if extracted.has_filters() and agent_id == "search":
            params["_is_advanced_search"] = True

        return params

    def _llm_route(self, query: str, context: DomainContext) -> Tuple[str, Dict[str, Any]]:
        system_prompt = self.get_system_prompt(context)

        try:
            response = self._call_llm(system_prompt, f"PERGUNTA: {query}")
            result = self._parse_json_response(response)
            return result.get("agent_id", "analytics"), result.get("params", {})
        except Exception as e:
            logger.error(f"Error in LLM routing: {e}")
            return "analytics", {}

```

---

## 📄 src/domains/sourced_profile_sourcing/agents/search.py

```python
from typing import Dict, Any, Optional, List
import logging

from src.domains.base import DomainContext
from src.domains.sourced_profile_sourcing.agents.base import BaseAgent, AgentResponse
from src.domains.sourced_profile_sourcing.fairness import FairnessGuard

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "search"

    @property
    def agent_name(self) -> str:
        return "Search Agent"

    @property
    def description(self) -> str:
        return "Especialista em buscar e filtrar candidatos por critérios específicos"

    @property
    def capabilities(self) -> List[str]:
        return [
            "Buscar por skill (quem sabe Python?)",
            "Buscar por termo livre",
            "Filtrar por score mínimo",
            "Listar top N candidatos",
            "Filtrar por localização",
            "Buscar perfis similares a um candidato"
        ]

    def get_system_prompt(self, context: DomainContext) -> str:
        return f"""Você é um especialista em buscar candidatos.

**CONTEXTO:**
- Sourcing ID: {context.sourcing_id}

**SUAS CAPACIDADES:**
- search: Busca por termo livre
- filter_skill: Filtrar por skill específica
- filter_score: Filtrar por score mínimo
- top_candidates: Listar top N por score
- filter_location: Filtrar por cidade/estado
- find_similar: Buscar perfis similares a um candidato (usa embeddings)

**RESPOSTA (JSON):**
{{
    "action": "nome_da_acao",
    "params": {{"search": "termo", "min_score": 80, "limit": 10, "reference_id": 123}},
    "reasoning": "motivo"
}}"""

    def process(
        self,
        query: str,
        context: DomainContext,
        aggregated_stats: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        params = params or {}

        # Verificar se é busca de perfis similares
        if self._is_similar_profiles_query(query, params):
            return self._find_similar_profiles(query, context, params)

        action, extracted = self._identify_action(query)

        for key, value in extracted.items():
            if key not in params:
                params[key] = value

        if params.get("_is_advanced_search") or self._has_multiple_filters(params):
            return self._advanced_search(context, params)

        handlers = {
            "search": self._search_candidates,
            "filter_skill": self._filter_by_skill,
            "filter_score": self._filter_by_score,
            "top_candidates": self._top_candidates,
            "filter_location": self._filter_by_location,
            "filter": self._filter_generic,
            "list": self._list_candidates,
        }

        if params.get("skill") or params.get("skills"):
            action = "filter_skill"
        elif params.get("min_score"):
            action = "filter_score"
        elif params.get("location"):
            action = "filter_location"

        handler = handlers.get(action, self._list_candidates)
        return handler(context, params)

    def _has_multiple_filters(self, params: Dict) -> bool:
        filter_keys = [
            "skill", "skills", "min_score", "location", "min_experience",
            "experience_years", "english_level", "language_level", "company",
            "company_history", "gender", "remote", "position_level"
        ]
        return sum(1 for k in filter_keys if params.get(k) is not None) >= 2

    def _advanced_search(self, context: DomainContext, params: Dict) -> AgentResponse:
        fairness_warnings = FairnessGuard.check_sensitive_filters(params)
        compliance_warning = FairnessGuard.get_filter_warning_message(
            fairness_warnings)

        for key in list(params.keys()):
            should_block = FairnessGuard.should_block_filter(
                key,
                allow_exception=context.allow_sensitive_filters,
                justification=context.sensitive_filter_justification,
                user_id=context.user_id
            )
            if should_block:
                logger.warning(f"🚫 Blocked discriminatory filter: {key}")
                return AgentResponse(
                    success=False,
                    message=f"❌ Filtro por '{key}' bloqueado por políticas de igualdade de oportunidades.\n\n"
                    f"Se este é um caso de vaga afirmativa, configure `allow_sensitive_filters=True` "
                    f"com justificativa documentada.",
                    data={},
                    warnings=[
                        "Filtros por atributos protegidos requerem justificativa legal"]
                )

        where = {
            "sourcing_id": int(context.sourcing_id),
            "is_deleted": False
        }

        if params.get("_keep_filters"):
            memory = context.get_memory()
            where.update(memory.active_filters)

        if params.get("min_score"):
            where["sourcing_score"] = {"gte": params["min_score"]}

        if params.get("max_score"):
            where.setdefault("sourcing_score", {})["lte"] = params["max_score"]

        skills = params.get("skills") or (
            [params["skill"]] if params.get("skill") else [])
        if skills:
            where["skills"] = [s.lower() for s in skills]

        if params.get("location"):
            where["city"] = params["location"].lower()

        if params.get("min_experience") or params.get("experience_years"):
            where["total_experience_years"] = {"gte": params.get(
                "min_experience") or params.get("experience_years")}

        if params.get("company"):
            where["current_company"] = params["company"].lower()

        if params.get("company_history"):
            where["recent_companies"] = [c.lower()
                                         for c in params["company_history"]]

        if params.get("gender"):
            where["gender"] = params["gender"].lower()

        if params.get("remote"):
            where["remote_work"] = params["remote"]

        if params.get("has_emails") is not None:
            where["has_emails"] = params["has_emails"]

        if params.get("has_linkedin") is not None:
            where["has_linkedin"] = params["has_linkedin"]

        if params.get("position_level"):
            where["position_level"] = params["position_level"].lower()

        if params.get("english_level") or params.get("language_level"):
            level = params.get("english_level") or params.get("language_level")
            where["language_levels"] = [level.lower()]

        order_by = params.get("order_by", "sourcing_score")
        order_dir = params.get("order_dir", "desc")
        order = {order_by: order_dir}

        limit = params.get("limit", 50)

        candidates = self._fetch_candidates(
            context, limit=limit, order=order, where=where)

        filters_desc = self._build_filters_description(params)

        memory = context.get_memory()
        active = {k: v for k, v in where.items() if k not in [
            "sourcing_id", "is_deleted"]}
        memory.active_filters = active

        response = self._format_candidates_list(
            candidates, f"Busca: {filters_desc}")

        if compliance_warning:
            response.message = f"{compliance_warning}\n\n---\n\n{response.message}"
            response.warnings = (response.warnings or []) + \
                [w.message for w in fairness_warnings]

        return response

    def _filter_by_skills_list(self, candidates: List[Dict], skills: List[str]) -> List[Dict]:
        skills_lower = [s.lower() for s in skills]
        filtered = []

        for c in candidates:
            expertise = [e.lower() for e in (c.get("expertise") or [])]
            title = (c.get("title") or "").lower()
            summary = (c.get("summary") or "").lower()

            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            strong_skills = [s.lower() for s in analysis.get(
                "skills_assessment", {}).get("strong", [])]

            candidate_skills = set(expertise + strong_skills)
            candidate_text = f"{title} {summary}"

            matches = sum(
                1 for skill in skills_lower if skill in candidate_skills or skill in candidate_text)
            if matches > 0:
                c["_skill_matches"] = matches
                filtered.append(c)

        return sorted(filtered, key=lambda x: (-x.get("_skill_matches", 0), -float(x.get("score") or 0)))

    def _filter_by_english(self, candidates: List[Dict], required_level: str) -> List[Dict]:
        level_order = {"básico": 1, "basico": 1, "intermediário": 2,
                       "intermediario": 2, "avançado": 3, "avancado": 3, "fluente": 4}
        min_level = level_order.get(required_level.lower(), 0)

        if min_level == 0:
            return candidates

        return [c for c in candidates if level_order.get((c.get("english_level") or "").lower(), 0) >= min_level]

    def _build_filters_description(self, params: Dict) -> str:
        parts = []

        if params.get("skills"):
            parts.append(f"skills={','.join(params['skills'])}")
        elif params.get("skill"):
            parts.append(f"skill={params['skill']}")

        if params.get("min_score"):
            parts.append(f"score≥{params['min_score']}")

        if params.get("location"):
            parts.append(f"local={params['location']}")

        if params.get("min_experience") or params.get("experience_years"):
            exp = params.get("min_experience") or params.get(
                "experience_years")
            parts.append(f"exp≥{exp}a")

        if params.get("english_level") or params.get("language_level"):
            level = params.get("english_level") or params.get("language_level")
            parts.append(f"inglês={level}")

        if params.get("company"):
            parts.append(f"empresa={params['company']}")

        if params.get("company_history"):
            parts.append(f"ex={','.join(params['company_history'])}")

        if params.get("gender"):
            parts.append(f"gênero={params['gender']}")

        if params.get("remote"):
            parts.append("remoto")

        if params.get("position_level"):
            parts.append(f"nível={params['position_level']}")

        return ", ".join(parts) if parts else "todos"

    def _filter_generic(self, context: DomainContext, params: Dict) -> AgentResponse:
        if params.get("skill"):
            return self._filter_by_skill(context, params)
        if params.get("min_score"):
            return self._filter_by_score(context, params)
        if params.get("location"):
            return self._filter_by_location(context, params)
        return self._list_candidates(context, params)

    def _identify_action(self, query: str) -> tuple[str, Dict]:
        query_lower = query.lower()
        params = {}

        import re
        numbers = re.findall(r'\b(\d+)\b', query)

        if "top" in query_lower:
            if numbers:
                for n in numbers:
                    if int(n) <= 50:
                        params["limit"] = int(n)
                        break
            if "limit" not in params:
                params["limit"] = 10
            return "top_candidates", params

        if "score" in query_lower:
            if "acima" in query_lower or "maior" in query_lower or ">" in query:
                if numbers:
                    params["min_score"] = int(numbers[0])
                else:
                    params["min_score"] = 80
                return "filter_score", params

        skill_patterns = [
            r"quem sabe (\w+)",
            r"candidatos com (\w+)",
            r"filtrar por (\w+)",
            r"buscar (\w+)",
        ]

        for pattern in skill_patterns:
            match = re.search(pattern, query_lower)
            if match:
                skill = match.group(1)
                if skill not in ["score", "candidatos", "os", "de", "do", "da"]:
                    params["skill"] = skill
                    return "filter_skill", params

        location_keywords = ["de são paulo", "de sp",
                             "de rio", "de bh", "de curitiba"]
        for loc in location_keywords:
            if loc in query_lower:
                params["location"] = loc.replace("de ", "")
                return "filter_location", params

        if "listar" in query_lower or "mostrar" in query_lower:
            return "list", params

        return "list", params

    def _search_candidates(self, context: DomainContext, params: Dict) -> AgentResponse:
        search_term = params.get("search", "")

        candidates = self._fetch_candidates(
            context, limit=50, order={"sourcing_score": "desc"})

        if search_term:
            search_lower = search_term.lower()
            candidates = [
                c for c in candidates
                if search_lower in (c.get("name", "").lower()) or
                search_lower in (c.get("title", "").lower()) or
                search_lower in (c.get("summary", "").lower()) or
                search_lower in str(c.get("expertise", [])).lower()
            ]

        return self._format_candidates_list(candidates, f"Busca: '{search_term}'")

    def _filter_by_skill(self, context: DomainContext, params: Dict) -> AgentResponse:
        skill = params.get("skill", "").lower()

        candidates = self._fetch_candidates(
            context, limit=100, order={"sourcing_score": "desc"})

        filtered = []
        for c in candidates:
            expertise = [e.lower() for e in (c.get("expertise") or [])]
            title = (c.get("title") or "").lower()
            summary = (c.get("summary") or "").lower()

            analysis = c.get("analysis") or c.get("ai_analysis") or {}
            strong_skills = [s.lower() for s in analysis.get(
                "skills_assessment", {}).get("strong", [])]

            if (skill in expertise or
                skill in title or
                skill in summary or
                    skill in strong_skills):
                filtered.append(c)

        return self._format_candidates_list(filtered, f"Skill: {skill}")

    def _filter_by_score(self, context: DomainContext, params: Dict) -> AgentResponse:
        min_score = params.get("min_score", 80)

        where = {
            "sourcing_id": int(context.sourcing_id),
            "sourcing_score": {"gte": min_score},
            "is_deleted": False
        }

        candidates = self._fetch_candidates(
            context,
            limit=100,
            order={"sourcing_score": "desc"},
            where=where
        )

        return self._format_candidates_list(candidates, f"Score >= {min_score}")

    def _top_candidates(self, context: DomainContext, params: Dict) -> AgentResponse:
        limit = params.get("limit", 10)

        where = {
            "sourcing_id": int(context.sourcing_id),
            "is_deleted": False
        }

        candidates = self._fetch_candidates(context, limit=limit, order={
                                            "sourcing_score": "desc"}, where=where)

        return self._format_candidates_list(candidates[:limit], f"Top {limit}")

    def _filter_by_location(self, context: DomainContext, params: Dict) -> AgentResponse:
        location = params.get("location", "").lower()

        where = {
            "sourcing_id": int(context.sourcing_id),
            "city": location,
            "is_deleted": False
        }

        candidates = self._fetch_candidates(context, limit=100, order={
                                            "sourcing_score": "desc"}, where=where)

        return self._format_candidates_list(candidates, f"Localização: {location}")

    def _list_candidates(self, context: DomainContext, params: Dict) -> AgentResponse:
        limit = params.get("limit", 20)

        where = {
            "sourcing_id": int(context.sourcing_id),
            "is_deleted": False
        }

        candidates = self._fetch_candidates(context, limit=limit, order={
                                            "sourcing_score": "desc"}, where=where)

        return self._format_candidates_list(candidates, "Todos os candidatos")

    def _format_candidates_list(self, candidates: List[Dict], title: str) -> AgentResponse:
        if not candidates:
            logger.warning(
                f"[OBSERVABILITY] zero_candidates_after_filter: title='{title}'")
            return AgentResponse(
                success=True,
                message=f"## 🔍 {title}\n\n⚠️ Nenhum candidato encontrado com os filtros aplicados.\n\n"
                f"**Sugestões:**\n"
                f"• Tente relaxar os filtros\n"
                f"• Use filtros menos específicos\n"
                f"• Verifique se a busca está correta",
                data={"candidates": [], "count": 0},
                warnings=[
                    "Nenhum resultado encontrado - considere ajustar os filtros"]
            )

        lines = [f"## 🔍 {title}",
                 f"*{len(candidates)} candidatos encontrados*", ""]

        lines.append("| # | Nome | Score | Empresa | Exp. | Cidade |")
        lines.append("|:-:|------|:-----:|---------|:----:|--------|")

        for i, c in enumerate(candidates[:20], 1):
            name = self._sanitize(c.get("name"))
            score = c.get("sourcing_score") or c.get("score") or "-"
            company = self._sanitize(c.get("current_company"))
            exp = c.get("total_experience_years") or "-"
            city = self._sanitize(c.get("city"))

            lines.append(
                f"| {i} | {name} | {score} | {company} | {exp} | {city} |")

        if len(candidates) > 20:
            lines.append(f"\n*... e mais {len(candidates) - 20} candidatos*")

        candidate_data = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "score": c.get("sourcing_score") or c.get("score"),
                "company": c.get("current_company"),
                "experience": c.get("total_experience_years"),
                "city": c.get("city")
            }
            for c in candidates
        ]

        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={"candidates": candidate_data, "count": len(candidates)},
            suggestions=[
                f"Detalhes do candidato {candidates[0].get('id', '')}" if candidates else "",
                "Compare os 3 melhores",
                "Filtrar por score acima de 80"
            ]
        )

    def _is_similar_profiles_query(self, query: str, params: Dict[str, Any]) -> bool:
        """Verifica se a query é sobre buscar perfis similares."""
        query_lower = query.lower()
        
        similar_keywords = [
            "similar", "parecido", "parecidos", "semelhante", "semelhantes",
            "perfis similares", "candidatos similares", "buscar similares",
            "encontrar similares", "outros como", "outros parecidos",
            "mesmo perfil", "perfil parecido"
        ]
        
        # Verificar keywords
        has_similar_keyword = any(kw in query_lower for kw in similar_keywords)
        
        # Verificar se tem reference_id nos params (do frontend)
        has_reference_id = params.get("reference_id") or params.get("candidate_id")
        
        return has_similar_keyword or has_reference_id

    def _find_similar_profiles(
        self,
        query: str,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> AgentResponse:
        """Busca perfis similares a um candidato usando embeddings."""
        memory = context.get_memory()
        
        # 1. Identificar candidato de referência
        reference_candidate_id = self._extract_reference_candidate(query, context, params)
        
        if not reference_candidate_id:
            return AgentResponse(
                success=False,
                message="""❓ **Qual candidato você quer usar como referência?**

💡 Você pode:
- Mencionar o ID: "Buscar similares ao candidato 123"
- Mencionar o nome: "Buscar similares ao João Silva"
- Usar referência: "Buscar similares a ele" (após ver um candidato)
- Selecionar o candidato no frontend""",
                error="missing_reference",
                suggestions=["Top 5 candidatos", "Listar candidatos"]
            )
        
        # 2. Buscar candidato de referência para mostrar na resposta
        api = self.get_api_operations(context)
        reference_result = api.get_candidate_by_id(reference_candidate_id)
        
        if not reference_result.success or not reference_result.data:
            return AgentResponse(
                success=False,
                message=f"❌ Candidato de referência (ID: {reference_candidate_id}) não encontrado.",
                error="reference_not_found"
            )
        
        reference_candidate = reference_result.data
        
        # 3. Extrair parâmetros da busca
        top_k = params.get("top_k") or params.get("limit") or 10
        min_score = params.get("min_score")
        filters = params.get("filters") or {}
        
        # Extrair filtros da query se houver
        if not filters:
            filters = self._extract_filters_from_query(query)
        
        # 4. Buscar candidatos similares
        similar_result = api.find_similar_candidates(
            sourced_profile_id=reference_candidate_id,
            top_k=top_k,
            min_score=min_score,
            filters=filters if filters else None
        )
        
        if not similar_result.success:
            return AgentResponse(
                success=False,
                message=f"❌ Erro ao buscar candidatos similares: {similar_result.error}",
                error=similar_result.error
            )
        
        similar_candidates = similar_result.data
        
        if not similar_candidates:
            return AgentResponse(
                success=True,
                message=f"""## 🔍 Perfis Similares

**Candidato de referência:** {reference_candidate.get('name', 'N/A')} (ID: {reference_candidate_id})

⚠️ Nenhum candidato similar encontrado com os critérios especificados.

💡 Tente:
- Relaxar os filtros
- Reduzir o score mínimo
- Verificar se há candidatos na base""",
                data={"reference": reference_candidate, "similar": []},
                suggestions=["Listar todos os candidatos", "Buscar por skill"]
            )
        
        # 5. Formatar resposta
        return self._format_similar_profiles_response(
            reference_candidate,
            similar_candidates,
            top_k
        )

    def _extract_reference_candidate(
        self,
        query: str,
        context: DomainContext,
        params: Dict[str, Any]
    ) -> Optional[int]:
        """Extrai ID do candidato de referência da query ou params."""
        memory = context.get_memory()
        
        # 1. Verificar params (do frontend)
        if params.get("reference_id"):
            return params["reference_id"]
        if params.get("candidate_id"):
            return params["candidate_id"]
        
        # 2. Tentar extrair da query (ID explícito)
        import re
        numbers = re.findall(r'\b(\d+)\b', query)
        for n in numbers:
            candidate_id = int(n)
            if 10 < candidate_id < 1000000:  # Range razoável
                # Verificar contexto - se tem "candidato" antes do número
                query_lower = query.lower()
                idx = query_lower.find(str(candidate_id))
                if idx > 0:
                    before = query_lower[max(0, idx-30):idx]
                    if any(kw in before for kw in ["candidato", "perfil", "id", "#"]):
                        return candidate_id
        
        # 3. Verificar memória (referências como "ele", "esse", etc.)
        resolved_id = memory.resolve_reference(query)
        if resolved_id:
            return resolved_id
        
        # 4. Usar último candidato detalhado
        if memory.last_candidate_detailed:
            return memory.last_candidate_detailed
        
        # 5. Tentar extrair nome da query
        name_patterns = [
            r"(?:ao|do|da|de)\s+([A-Z][a-záéíóúâêîôûãõç]+(?:\s+[A-Z][a-záéíóúâêîôûãõç]+)*)",
            r"candidato\s+([A-Z][a-záéíóúâêîôûãõç]+(?:\s+[A-Z][a-záéíóúâêîôûãõç]+)*)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Buscar candidato por nome
                api = self.get_api_operations(context)
                result = api.search_candidates(search=name, limit=5)
                if result.success and result.data:
                    name_lower = name.lower()
                    for candidate in result.data:
                        candidate_name = (candidate.get("name") or "").lower()
                        if name_lower in candidate_name or candidate_name.startswith(name_lower):
                            return candidate.get("id")
                    # Se não encontrou match exato, retornar o primeiro
                    if result.data:
                        return result.data[0].get("id")
        
        return None

    def _extract_filters_from_query(self, query: str) -> Dict[str, Any]:
        """Extrai filtros opcionais da query para busca de similares."""
        filters = {}
        query_lower = query.lower()
        
        # Localização
        location_keywords = {
            "são paulo": "São Paulo", "sp": "São Paulo",
            "rio": "Rio de Janeiro", "rj": "Rio de Janeiro",
            "bh": "Belo Horizonte", "curitiba": "Curitiba"
        }
        for key, city in location_keywords.items():
            if key in query_lower:
                filters["city"] = city
                break
        
        # Remote work
        if "remoto" in query_lower or "remote" in query_lower:
            filters["remote_work"] = True
        elif "presencial" in query_lower or "onsite" in query_lower:
            filters["remote_work"] = False
        
        # Position level
        if "senior" in query_lower or "sênior" in query_lower:
            filters["position_level"] = "senior"
        elif "pleno" in query_lower:
            filters["position_level"] = "pleno"
        elif "junior" in query_lower or "júnior" in query_lower:
            filters["position_level"] = "junior"
        
        return filters

    def _format_similar_profiles_response(
        self,
        reference_candidate: Dict[str, Any],
        similar_candidates: List[Dict[str, Any]],
        top_k: int
    ) -> AgentResponse:
        """Formata resposta com perfis similares."""
        reference_name = reference_candidate.get("name", "N/A")
        reference_id = reference_candidate.get("id")
        reference_score = reference_candidate.get("score") or reference_candidate.get("sourcing_score") or "-"
        
        lines = [
            f"# 🔍 Perfis Similares",
            "",
            f"**Candidato de referência:** {reference_name} (ID: {reference_id}, Score: {reference_score})",
            "",
            f"*{len(similar_candidates)} candidatos similares encontrados*",
            "",
            "---",
            "",
            "## 📋 Candidatos Similares",
            "",
            "| # | Nome | Score | Similaridade | Empresa | Exp. | Cidade |",
            "|:-:|------|:-----:|:------------:|---------|:----:|--------|"
        ]
        
        for i, candidate in enumerate(similar_candidates[:top_k], 1):
            name = self._sanitize(candidate.get("name"))
            score = candidate.get("score") or candidate.get("sourcing_score") or "-"
            similarity = candidate.get("similarity_score")
            similarity_str = f"{similarity:.1f}%" if similarity is not None else "-"
            company = self._sanitize(candidate.get("current_company"))
            exp = candidate.get("total_experience_years") or "-"
            city = self._sanitize(candidate.get("city"))
            
            lines.append(
                f"| {i} | {name} | {score} | **{similarity_str}** | {company} | {exp} | {city} |"
            )
        
        if len(similar_candidates) > top_k:
            lines.append(f"\n*... e mais {len(similar_candidates) - top_k} candidatos similares*")
        
        # Adicionar análise de similaridade
        if similar_candidates:
            avg_similarity = sum(
                c.get("similarity_score", 0) for c in similar_candidates 
                if c.get("similarity_score") is not None
            ) / len([c for c in similar_candidates if c.get("similarity_score") is not None])
            
            if avg_similarity > 0:
                lines.extend([
                    "",
                    "---",
                    "",
                    f"**Similaridade média:** {avg_similarity:.1f}%"
                ])
        
        candidate_data = [
            {
                "id": c.get("id"),
                "name": c.get("name"),
                "score": c.get("score") or c.get("sourcing_score"),
                "similarity_score": c.get("similarity_score"),
                "company": c.get("current_company"),
                "experience": c.get("total_experience_years"),
                "city": c.get("city")
            }
            for c in similar_candidates
        ]
        
        suggestions = []
        if similar_candidates:
            suggestions.append(f"Detalhes do candidato {similar_candidates[0].get('id', '')}")
            suggestions.append(f"Compare os top 3 similares")
            suggestions.append(f"Adicionar similares à lista")
        
        return AgentResponse(
            success=True,
            message="\n".join(lines),
            data={
                "reference": {
                    "id": reference_id,
                    "name": reference_name,
                    "score": reference_score
                },
                "similar": candidate_data,
                "count": len(similar_candidates),
                "avg_similarity": round(avg_similarity, 1) if similar_candidates and avg_similarity > 0 else None
            },
            suggestions=suggestions
        )

```

---

## 📄 src/domains/sourced_profile_sourcing/config/__init__.py

```python
from src.domains.sourced_profile_sourcing.config.domain_settings import (
    get_domain_settings,
    DomainSettings,
    OrchestratorSettings,
    MemorySettings,
    CacheSettings,
    ValidationSettings,
    FactCheckerSettings,
    SearchSettings,
    RouterSettings
)
from functools import lru_cache
from pathlib import Path
from typing import Dict, Set, List, Any, Optional
import yaml


CONFIG_PATH = Path(__file__).parent / "extraction_config.yaml"


class ExtractionConfig:
    _instance: Optional["ExtractionConfig"] = None
    _config: Dict[str, Any]

    def __new__(cls) -> "ExtractionConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def reload(self) -> None:
        self._load_config()
        self._get_known_skills.cache_clear()
        self._get_location_aliases.cache_clear()

    @property
    @lru_cache(maxsize=1)
    def _get_known_skills(self) -> Set[str]:
        return set(self._config.get("skills", {}).get("known", []))

    @property
    def known_skills(self) -> Set[str]:
        return self._get_known_skills

    @property
    def skill_patterns(self) -> List[str]:
        return self._config.get("skills", {}).get("patterns", [])

    @property
    def skill_stop_words(self) -> Set[str]:
        return set(self._config.get("skills", {}).get("stop_words", []))

    @property
    def allow_unknown_skills(self) -> bool:
        return self._config.get("skills", {}).get("allow_unknown", True)

    @property
    @lru_cache(maxsize=1)
    def _get_location_aliases(self) -> Dict[str, str]:
        return self._config.get("locations", {}).get("aliases", {})

    @property
    def location_aliases(self) -> Dict[str, str]:
        return self._get_location_aliases

    @property
    def allow_unknown_locations(self) -> bool:
        return self._config.get("locations", {}).get("allow_unknown", True)

    def get_english_level(self, term: str) -> Optional[str]:
        levels = self._config.get("english_levels", {})
        term_lower = term.lower()
        for level_name, aliases in levels.items():
            if term_lower in [a.lower() for a in aliases]:
                return level_name
        return None

    def get_position_level(self, term: str) -> Optional[str]:
        levels = self._config.get("position_levels", {})
        term_lower = term.lower()
        for level_name, aliases in levels.items():
            if term_lower in [a.lower() for a in aliases]:
                return level_name
        return None

    @property
    def big_techs(self) -> Set[str]:
        return set(self._config.get("companies", {}).get("big_techs", []))

    @property
    def consultings(self) -> Set[str]:
        return set(self._config.get("companies", {}).get("consultings", []))

    @property
    def banks(self) -> Set[str]:
        return set(self._config.get("companies", {}).get("banks", []))

    @property
    def startups_br(self) -> Set[str]:
        return set(self._config.get("companies", {}).get("startups_br", []))

    @property
    def company_patterns(self) -> List[str]:
        return self._config.get("companies", {}).get("patterns", [])

    @property
    def company_category_triggers(self) -> Dict[str, List[str]]:
        return self._config.get("companies", {}).get("category_triggers", {})

    def get_companies_by_category(self, category: str) -> Set[str]:
        category_map = {
            "big_techs": self.big_techs,
            "consultings": self.consultings,
            "banks": self.banks,
            "startups_br": self.startups_br,
        }
        return category_map.get(category, set())

    def get_all_known_companies(self) -> Set[str]:
        return self.big_techs | self.consultings | self.banks | self.startups_br


extraction_config = ExtractionConfig()

```

---

## 📄 src/domains/sourced_profile_sourcing/config/domain_settings.py

```python
from dataclasses import dataclass, field
from typing import Optional
from functools import lru_cache


@dataclass(frozen=True)
class OrchestratorSettings:
    max_iterations: int = 5
    fail_fast: bool = False


@dataclass(frozen=True)
class MemorySettings:
    max_history: int = 10
    max_shortlist: int = 50
    max_mentioned: int = 100


@dataclass(frozen=True)
class CacheSettings:
    stats_ttl_seconds: int = 300
    validator_ttl_seconds: int = 600
    max_entries: int = 1000


@dataclass(frozen=True)
class ValidationSettings:
    name_similarity_threshold: float = 0.5
    min_similarity_for_match: float = 0.3
    max_alternatives_shown: int = 5
    name_search_limit: int = 500
    skill_search_limit: int = 100


@dataclass(frozen=True)
class FactCheckerSettings:
    average_tolerance_percent: float = 5.0
    min_confidence: float = 0.7
    auto_correct: bool = True


@dataclass(frozen=True)
class SearchSettings:
    default_limit: int = 50
    max_limit: int = 500
    default_page_size: int = 25


@dataclass(frozen=True)
class RouterSettings:
    min_score_threshold: int = 2
    clarify_on_tie: bool = True


@dataclass(frozen=True)
class DomainSettings:
    orchestrator: OrchestratorSettings = field(
        default_factory=OrchestratorSettings)
    memory: MemorySettings = field(default_factory=MemorySettings)
    cache: CacheSettings = field(default_factory=CacheSettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)
    fact_checker: FactCheckerSettings = field(
        default_factory=FactCheckerSettings)
    search: SearchSettings = field(default_factory=SearchSettings)
    router: RouterSettings = field(default_factory=RouterSettings)


@lru_cache(maxsize=1)
def get_domain_settings() -> DomainSettings:
    return DomainSettings()

```

---

## 📄 src/domains/sourced_profile_sourcing/config/extraction_config.yaml

```python
skills:
  known:
    - python
    - java
    - javascript
    - typescript
    - ruby
    - rails
    - react
    - vue
    - angular
    - node
    - nodejs
    - django
    - flask
    - fastapi
    - spring
    - aws
    - azure
    - gcp
    - docker
    - kubernetes
    - k8s
    - sql
    - postgresql
    - postgres
    - mysql
    - mongodb
    - redis
    - elasticsearch
    - kafka
    - rabbitmq
    - go
    - golang
    - rust
    - c++
    - cpp
    - c#
    - csharp
    - .net
    - dotnet
    - php
    - laravel
    - swift
    - kotlin
    - scala
    - terraform
    - ansible
    - jenkins
    - git
    - linux
    - graphql
    - rest
    - api
    - microservices
    - microsserviços
    - elixir
    - phoenix
    - haskell
    - clojure
    - r
    - matlab
    - julia
    - dart
    - flutter
    - nextjs
    - nuxt
    - svelte
    - remix
    - tailwind
    - sass
    - webpack
    - vite
    - cypress
    - jest
    - pytest
    - selenium
    - pandas
    - numpy
    - tensorflow
    - pytorch
    - scikit-learn
    - spark
    - airflow
    - dbt
    - snowflake
    - bigquery
    - databricks
    - power bi
    - tableau
    - looker
    - figma
    - sketch
    - adobe xd
    - nginx
    - apache
    - tomcat
    - kubernetes
    - helm
    - argocd
    - istio
    - prometheus
    - grafana
    - datadog
    - newrelic
    - splunk
    - vault
    - consul
    - pulumi
    - cloudformation
    - cdk

  patterns:
    - "(?:sabe|conhece|tem|domina|com)\\s+(\\w+)"
    - "(?:skill|habilidade)[s]?\\s*(?:em|de|:)?\\s*(\\w+)"
    - "(?:experiência|experiencia)\\s+(?:em|com)\\s+(\\w+)"

  stop_words:
    - score
    - anos
    - experiência
    - experiencia
    - mais
    - menos
    - inglês
    - ingles
    - fluente
    - avançado
    - avancado
    - intermediário
    - intermediario
    - básico
    - basico
    - candidatos
    - candidato
    - com
    - que
    - tem
    - são
    - sao
    - paulo
    - rio
    - janeiro
    - belo
    - horizonte
    - minas
    - gerais

  allow_unknown: true

locations:
  aliases:
    sp: São Paulo
    são paulo: São Paulo
    sao paulo: São Paulo
    rj: Rio de Janeiro
    rio: Rio de Janeiro
    rio de janeiro: Rio de Janeiro
    bh: Belo Horizonte
    belo horizonte: Belo Horizonte
    curitiba: Curitiba
    cwb: Curitiba
    porto alegre: Porto Alegre
    poa: Porto Alegre
    brasília: Brasília
    brasilia: Brasília
    bsb: Brasília
    salvador: Salvador
    ssa: Salvador
    recife: Recife
    fortaleza: Fortaleza
    florianópolis: Florianópolis
    florianopolis: Florianópolis
    floripa: Florianópolis
    campinas: Campinas
    goiânia: Goiânia
    goiania: Goiânia
    manaus: Manaus
    belém: Belém
    belem: Belém
    vitória: Vitória
    vitoria: Vitória
    natal: Natal
    joão pessoa: João Pessoa
    joao pessoa: João Pessoa
    maceió: Maceió
    maceio: Maceió
    teresina: Teresina
    são luís: São Luís
    sao luis: São Luís
    aracaju: Aracaju
    cuiabá: Cuiabá
    cuiaba: Cuiabá
    campo grande: Campo Grande
    londrina: Londrina
    joinville: Joinville
    ribeirão preto: Ribeirão Preto
    ribeirao preto: Ribeirão Preto
    sorocaba: Sorocaba
    santos: Santos
    são josé dos campos: São José dos Campos
    sao jose dos campos: São José dos Campos
    uberlândia: Uberlândia
    uberlandia: Uberlândia
    
  allow_unknown: true

english_levels:
  basic:
    - básico
    - basico
    - basic
    - iniciante
    - beginner
  intermediate:
    - intermediário
    - intermediario
    - intermediate
    - b1
    - b2
  advanced:
    - avançado
    - avancado
    - advanced
    - c1
  fluent:
    - fluente
    - fluent
    - c2
  native:
    - nativo
    - native
    - bilíngue
    - bilingue
    - bilingual

position_levels:
  junior:
    - junior
    - júnior
    - jr
    - trainee
    - estagiário
    - estagiario
    - entry
    - entry-level
  pleno:
    - pleno
    - mid
    - mid-level
    - intermediário
    - intermediario
  senior:
    - senior
    - sênior
    - sr
    - experiente
  specialist:
    - specialist
    - especialista
    - expert
    - tech lead
  lead:
    - lead
    - líder
    - lider
    - tech lead
    - team lead
  manager:
    - manager
    - gerente
    - gestor
    - head
    - director
    - diretor
  executive:
    - c-level
    - cto
    - cio
    - vp
    - vice-president

companies:
  big_techs:
    - google
    - microsoft
    - amazon
    - meta
    - facebook
    - apple
    - netflix
    - uber
    - airbnb
    - spotify
    - twitter
    - linkedin
    - salesforce
    - oracle
    - ibm
    - adobe
    - stripe
    - shopify
    - dropbox
    - slack
    - zoom
    - databricks
    - snowflake
    - palantir

  consultings:
    - accenture
    - mckinsey
    - bain
    - bcg
    - deloitte
    - pwc
    - kpmg
    - ey
    - capgemini
    - thoughtworks
    - globant
    - ci&t
    - dxc

  banks:
    - itaú
    - itau
    - bradesco
    - santander
    - nubank
    - c6
    - inter
    - btg
    - xp
    - original
    - neon
    - banco do brasil
    - caixa
    - safra
    - modal
    - stone
    - pagseguro
    - mercado pago

  startups_br:
    - ifood
    - rappi
    - loggi
    - loft
    - quinto andar
    - quintoandar
    - creditas
    - gympass
    - wellhub
    - olist
    - vtex
    - hotmart
    - totvs
    - linx
    - locaweb
    - resultados digitais
    - rd station

  patterns:
    - "(?:trabalhou|passou|veio|ex-?|de|da|vindos? de)\\s+(?:na |do |da )?([\\w\\s]+?)(?:\\s|$|,|\\?)"
    - "(?:atualmente|atual)\\s+(?:na|em|do)\\s+([\\w\\s]+?)(?:\\s|$|,|\\?)"
    - "(?:empresa|companhia)\\s+([\\w\\s]+?)(?:\\s|$|,|\\?)"

  category_triggers:
    big_techs:
      - big tech
      - bigtech
      - faang
      - maang
      - tech giant
    consultings:
      - consultoria
      - ex-consultoria
      - consulting
    banks:
      - banco
      - ex-banco
      - bank
      - fintech

```

---

## 📄 src/domains/sourced_profile_sourcing/prompt_builder/__init__.py

```python
from .filter_specs import FilterSpecs
from .action_registry import ActionRegistry, SourceType
from .domain_action import DomainAction, ParamSpec
from .dynamic_builder import DynamicPromptBuilder, PromptConfig
from .actions import register_all_actions

__all__ = [
    "FilterSpecs",
    "ActionRegistry",
    "SourceType",
    "DomainAction",
    "ParamSpec",
    "DynamicPromptBuilder",
    "PromptConfig",
    "register_all_actions",
]

```

---

## 📄 src/domains/sourced_profile_sourcing/prompt_builder/action_registry.py

```python
from typing import Dict, List, Optional

from .domain_action import DomainAction, SourceType


class ActionRegistry:
    _actions: Dict[str, DomainAction] = {}

    @classmethod
    def register(cls, action: DomainAction) -> DomainAction:
        cls._actions[action.id] = action
        return action

    @classmethod
    def get(cls, action_id: str) -> Optional[DomainAction]:
        return cls._actions.get(action_id)

    @classmethod
    def all(cls) -> List[DomainAction]:
        return list(cls._actions.values())

    @classmethod
    def relevant_for(cls, query: str, top_k: int = 6) -> List[DomainAction]:
        scored = [(a, a.matches_query(query)) for a in cls._actions.values()]
        scored.sort(key=lambda x: (-x[1], -x[0].priority))
        return [a for a, score in scored[:top_k] if score > 0 or a.priority >= 8]

    @classmethod
    def clear(cls):
        cls._actions.clear()


__all__ = ["ActionRegistry", "SourceType"]

```

---

## 📄 src/domains/sourced_profile_sourcing/prompt_builder/actions.py

```python
from .action_registry import ActionRegistry
from .domain_action import DomainAction, SourceType
from .filter_specs import FilterSpecs, ParamSpec
from .dynamic_builder import DynamicPromptBuilder


def register_all_actions():
    ActionRegistry.clear()
    try:
        DynamicPromptBuilder._get_relevant_action_ids_cached.cache_clear()
    except (AttributeError, TypeError):
        pass

    ActionRegistry.register(DomainAction(
        id="search_candidates",
        description="Busca candidatos. Use where._cont para filtros parciais em campos específicos (cargo, nome, empresa)",
        source=SourceType.API,
        params=[FilterSpecs.ROLE_NAME_CONT, FilterSpecs.SEARCH, FilterSpecs.SKILLS,
                FilterSpecs.CITY, FilterSpecs.REMOTE, FilterSpecs.SCORE,
                FilterSpecs.EXPERIENCE, FilterSpecs.HAS_EMAIL, FilterSpecs.HAS_LINKEDIN,
                FilterSpecs.POSITION_LEVEL, FilterSpecs.NAME_CONT, FilterSpecs.COMPANY_CONT],
        triggers=["busc", "quem", "candidat", "filtr", "sabe", "conhec",
                  "python", "java", "react", "remoto", "sp", "são paulo", "rio",
                  "senior", "junior", "pleno", "email", "linkedin", "contato",
                  "cargo", "função", "palavra", "desenvolv", "develop", "engineer",
                  "empresa", "companhia", "trabalha"],
        examples=[
            {"input": "Candidatos com cargo de developer",
                "output": '{"action_id": "search_candidates", "params": {"where": {"role_name_cont": "developer"}}, "source": "api"}'},
            {"input": "Pesquise candidatos com cargo full stack",
                "output": '{"action_id": "search_candidates", "params": {"where": {"role_name_cont": "full stack"}}, "source": "api"}'},
            {"input": "Candidatos que trabalham na Google",
                "output": '{"action_id": "search_candidates", "params": {"where": {"current_company_cont": "google"}}, "source": "api"}'},
            {"input": "Busque engineer no cargo",
                "output": '{"action_id": "search_candidates", "params": {"where": {"role_name_cont": "engineer"}}, "source": "api"}'},
            {"input": "Quem sabe Python?",
                "output": '{"action_id": "search_candidates", "params": {"where": {"skills": ["python"]}}, "source": "api"}'},
            {"input": "Senior de SP", "output": '{"action_id": "search_candidates", "params": {"where": {"city": "sao paulo", "position_level": "senior"}}, "source": "api"}'},
        ],
        priority=10
    ))

    ActionRegistry.register(DomainAction(
        id="list_candidates",
        description="Lista candidatos ordenados por score",
        source=SourceType.API,
        params=[FilterSpecs.LIMIT],
        triggers=["top", "melhor", "list", "primeiro", "ranking", "orden"],
        examples=[
            {"input": "Top 10", "output": '{"action_id": "list_candidates", "params": {"limit": 10}, "source": "api"}'},
            {"input": "Melhores candidatos",
                "output": '{"action_id": "list_candidates", "params": {"limit": 10}, "source": "api"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="list_candidates_by_index",
        description="Lista candidatos fazendo GET tradicional para cada um (mais detalhado)",
        source=SourceType.API,
        params=[FilterSpecs.LIMIT],
        triggers=["fazendo favor", "por favor",
                  "favor", "detalhad", "complet"],
        examples=[
            {"input": "Liste os candidatos dessa pesquisa fazendo favor",
                "output": '{"action_id": "list_candidates_by_index", "params": {"limit": 20}, "source": "api"}'},
            {"input": "Mostre os candidatos por favor",
                "output": '{"action_id": "list_candidates_by_index", "params": {"limit": 20}, "source": "api"}'},
        ],
        priority=10
    ))

    ActionRegistry.register(DomainAction(
        id="top_candidates",
        description="Lista os N melhores candidatos por score (sem comparação)",
        source=SourceType.API,
        params=[FilterSpecs.LIMIT],
        triggers=["liste top", "mostre top", "listar melhor", "primeiro"],
        examples=[
            {"input": "Top 5", "output": '{"action_id": "top_candidates", "params": {"limit": 5}, "source": "api"}'},
            {"input": "Mostre os top 10",
                "output": '{"action_id": "top_candidates", "params": {"limit": 10}, "source": "api"}'},
        ],
        priority=7
    ))

    ActionRegistry.register(DomainAction(
        id="show_candidate_details",
        description="Mostra TODOS os detalhes/informações de um candidato específico (por ID ou nome)",
        source=SourceType.API,
        params=[FilterSpecs.CANDIDATE_ID, FilterSpecs.CANDIDATE_NAME],
        triggers=["detalh", "sobre", "quem é", "mais sobre", "fale",
                  "me fale", "informaç", "#", "tudo sobre", "perfil do", "perfil de"],
        examples=[
            {"input": "Detalhes do #123",
                "output": '{"action_id": "show_candidate_details", "params": {"candidate_id": 123}, "source": "api"}'},
            {"input": "Me fale sobre Maria",
                "output": '{"action_id": "show_candidate_details", "params": {"name": "Maria"}, "source": "api"}'},
            {"input": "Quem é o João?",
                "output": '{"action_id": "show_candidate_details", "params": {"name": "João"}, "source": "api"}'},
            {"input": "Mostre todas as informações do Igor Avelar",
                "output": '{"action_id": "show_candidate_details", "params": {"name": "Igor Avelar"}, "source": "api"}'},
            {"input": "Detalhes completos do candidato 404",
                "output": '{"action_id": "show_candidate_details", "params": {"candidate_id": 404}, "source": "api"}'},
        ],
        priority=10
    ))

    ActionRegistry.register(DomainAction(
        id="compare_candidates",
        description="Compara candidatos lado a lado (por nomes, IDs ou top N por score)",
        source=SourceType.API,
        params=[
            ParamSpec("candidate_names",
                      "array[string]", "Nomes para comparar"),
            ParamSpec("candidate_ids", "array[int]", "IDs para comparar"),
            ParamSpec("top_n", "int", "Comparar top N por score"),
        ],
        triggers=["compar", "versus", "vs", "diferenç",
                  "entre", "top 3", "top 5", "top 10"],
        examples=[
            {"input": "Compara João e Maria",
                "output": '{"action_id": "compare_candidates", "params": {"candidate_names": ["João", "Maria"]}, "source": "api"}'},
            {"input": "Compara os top 3",
                "output": '{"action_id": "compare_candidates", "params": {"top_n": 3}, "source": "api"}'},
            {"input": "Compare o top 3 candidatos",
                "output": '{"action_id": "compare_candidates", "params": {"top_n": 3}, "source": "api"}'},
            {"input": "Compare os 5 melhores",
                "output": '{"action_id": "compare_candidates", "params": {"top_n": 5}, "source": "api"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="summarize_search",
        description="Resumo estatístico completo do sourcing com dados demográficos, scores, skills e indicadores",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["resum", "estatíst", "relatório", "overview", "completo",
                  "visão geral", "demográf", "indicador", "principal", "métricas"],
        examples=[
            {"input": "Relatório geral",
                "output": '{"action_id": "summarize_search", "source": "aggregated"}'},
            {"input": "Dados demográficos",
                "output": '{"action_id": "summarize_search", "source": "aggregated"}'},
            {"input": "Relatório completo",
                "output": '{"action_id": "summarize_search", "source": "aggregated"}'},
            {"input": "Principais indicadores",
                "output": '{"action_id": "summarize_search", "source": "aggregated"}'},
            {"input": "Me mostre um relatório completo sobre essa pesquisa",
                "output": '{"action_id": "summarize_search", "source": "aggregated"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="generate_executive_report",
        description="Relatório executivo completo para apresentar ao gestor com métricas, insights e recomendações",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["executiv", "gestor", "apresent",
                  "report", "diretoria", "liderança"],
        examples=[
            {"input": "Relatório executivo",
                "output": '{"action_id": "generate_executive_report", "source": "aggregated"}'},
            {"input": "Mostrar pro gestor",
                "output": '{"action_id": "generate_executive_report", "source": "aggregated"}'},
            {"input": "Gere um report",
                "output": '{"action_id": "generate_executive_report", "source": "aggregated"}'},
            {"input": "Relatório para apresentar",
                "output": '{"action_id": "generate_executive_report", "source": "aggregated"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="generate_top_candidates_report",
        description="Relatório focado nos melhores candidatos com parecer e recomendação",
        source=SourceType.AGGREGATED,
        params=[
            ParamSpec("top_n", "int", "Número de candidatos no relatório")],
        triggers=["melhores candidatos", "destaque",
                  "recomend", "relatório top", "top candidatos"],
        examples=[
            {"input": "Report dos melhores candidatos",
                "output": '{"action_id": "generate_top_candidates_report", "params": {"top_n": 5}, "source": "aggregated"}'},
            {"input": "Relatório dos top 5",
                "output": '{"action_id": "generate_top_candidates_report", "params": {"top_n": 5}, "source": "aggregated"}'},
            {"input": "Quais os candidatos em destaque?",
                "output": '{"action_id": "generate_top_candidates_report", "params": {"top_n": 10}, "source": "aggregated"}'},
        ],
        priority=7
    ))

    ActionRegistry.register(DomainAction(
        id="count_candidates",
        description="Conta total de candidatos nessa pesquisa/sourcing",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["quant", "total", "cont", "essa pesquisa",
                  "nessa pesquisa", "no sourcing", "nesse sourcing"],
        examples=[
            {"input": "Quantos candidatos?",
                "output": '{"action_id": "count_candidates", "source": "aggregated"}'},
            {"input": "Quantos candidatos tem nessa pesquisa?",
                "output": '{"action_id": "count_candidates", "source": "aggregated"}'},
            {"input": "Qual o total dessa pesquisa?",
                "output": '{"action_id": "count_candidates", "source": "aggregated"}'},
        ],
        priority=8
    ))

    ActionRegistry.register(DomainAction(
        id="average_score",
        description="Média de score dos candidatos",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["médi", "media", "score méd", "score med"],
        examples=[
            {"input": "Qual a média de score?",
                "output": '{"action_id": "average_score", "source": "aggregated"}'},
        ],
        priority=5
    ))

    ActionRegistry.register(DomainAction(
        id="score_distribution",
        description="Distribuição de scores",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["distribuiç", "score", "faixa"],
        examples=[
            {"input": "Distribuição de score",
                "output": '{"action_id": "score_distribution", "source": "aggregated"}'},
        ],
        priority=4
    ))

    ActionRegistry.register(DomainAction(
        id="location_distribution",
        description="Distribuição por localização",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["localiza", "cidade", "onde", "geograf"],
        examples=[
            {"input": "De onde são os candidatos?",
                "output": '{"action_id": "location_distribution", "source": "aggregated"}'},
        ],
        priority=4
    ))

    ActionRegistry.register(DomainAction(
        id="analyze_skills",
        description="Análise de skills/habilidades mais comuns entre os candidatos desta busca. Usa dados agregados.",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["skill", "habilidad", "tecnolog", "stack", "competênc", "quais skills",
                  "skills mais comun", "mais comuns", "skills comuns", "habilidades comuns"],
        examples=[
            {"input": "Quais skills são mais comuns nesta busca?",
                "output": '{"action_id": "analyze_skills", "source": "aggregated"}'},
            {"input": "Quais skills são mais comuns?",
                "output": '{"action_id": "analyze_skills", "source": "aggregated"}'},
            {"input": "Skills mais comuns",
                "output": '{"action_id": "analyze_skills", "source": "aggregated"}'},
            {"input": "Quais tecnologias aparecem mais?",
                "output": '{"action_id": "analyze_skills", "source": "aggregated"}'},
            {"input": "Quais habilidades os candidatos têm?",
                "output": '{"action_id": "analyze_skills", "source": "aggregated"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="gender_distribution",
        description="Distribuição por gênero",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["gêner", "gener", "diversidad", "homen", "mulher"],
        examples=[
            {"input": "Distribuição por gênero",
                "output": '{"action_id": "gender_distribution", "source": "aggregated"}'},
        ],
        priority=4
    ))

    ActionRegistry.register(DomainAction(
        id="average_experience",
        description="Média de experiência em anos",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["experiênc", "experienc", "anos de",
                  "média de experiência", "experiência média"],
        examples=[
            {"input": "Qual a experiência média dos candidatos?",
                "output": '{"action_id": "average_experience", "source": "aggregated"}'},
            {"input": "Média de experiência",
                "output": '{"action_id": "average_experience", "source": "aggregated"}'},
            {"input": "Quantos anos de experiência em média?",
                "output": '{"action_id": "average_experience", "source": "aggregated"}'},
        ],
        priority=6
    ))

    ActionRegistry.register(DomainAction(
        id="analyze_search_improvement",
        description="Analisa a busca atual e sugere melhorias baseadas em boas práticas de recrutamento",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["melhorar", "otimizar", "aprimorar", "dica", "sugest",
                  "como posso", "feedback", "avali", "qualidade", "refinar",
                  "encontrar melhores", "mais candidatos", "poucos resultados",
                  "filtros adicionais"],
        examples=[
            {"input": "Como posso melhorar esta busca?",
                "output": '{"action_id": "analyze_search_improvement", "source": "aggregated"}'},
            {"input": "Dicas para melhorar a pesquisa",
                "output": '{"action_id": "analyze_search_improvement", "source": "aggregated"}'},
            {"input": "Avalie minha busca",
                "output": '{"action_id": "analyze_search_improvement", "source": "aggregated"}'},
            {"input": "Sugira filtros adicionais para refinar",
                "output": '{"action_id": "analyze_search_improvement", "source": "aggregated"}'},
        ],
        priority=10
    ))

    ActionRegistry.register(DomainAction(
        id="score_above",
        description="Conta candidatos com score acima de um valor (70, 80, 90)",
        source=SourceType.AGGREGATED,
        params=[ParamSpec("threshold", "int",
                          "Score mínimo (ex: 70, 80, 90)")],
        triggers=["acima de", "maior que", "score", "nota", "lia"],
        examples=[
            {"input": "Quantos candidatos têm nota LIA acima de 70?",
                "output": '{"action_id": "score_above", "params": {"threshold": 70}, "source": "aggregated"}'},
            {"input": "Quantos com score acima de 80?",
                "output": '{"action_id": "score_above", "params": {"threshold": 80}, "source": "aggregated"}'},
            {"input": "Candidatos com nota maior que 90",
                "output": '{"action_id": "score_above", "params": {"threshold": 90}, "source": "aggregated"}'},
        ],
        priority=8
    ))

    ActionRegistry.register(DomainAction(
        id="common_strengths",
        description="Analisa pontos fortes e skills em comum entre os candidatos. Não precisa de parâmetros.",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["pontos fortes", "em comum", "compartilha", "maioria", "força",
                  "têm em comum", "tem em comum", "fortes em comum"],
        examples=[
            {"input": "Quais pontos fortes eles têm em comum?",
                "output": '{"action_id": "common_strengths", "source": "aggregated"}'},
            {"input": "O que os candidatos compartilham?",
                "output": '{"action_id": "common_strengths", "source": "aggregated"}'},
            {"input": "Pontos fortes em comum",
                "output": '{"action_id": "common_strengths", "source": "aggregated"}'},
            {"input": "O que eles têm em comum?",
                "output": '{"action_id": "common_strengths", "source": "aggregated"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="skill_gaps",
        description="Identifica gaps/lacunas de competência nos candidatos. Não precisa de parâmetros.",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["gap", "lacuna", "falta", "competênc", "deficiênc",
                  "gaps de", "posso identificar", "identificar gap"],
        examples=[
            {"input": "Quais gaps de competência posso identificar?",
                "output": '{"action_id": "skill_gaps", "source": "aggregated"}'},
            {"input": "Quais lacunas de skills existem?",
                "output": '{"action_id": "skill_gaps", "source": "aggregated"}'},
            {"input": "Gaps de competência",
                "output": '{"action_id": "skill_gaps", "source": "aggregated"}'},
            {"input": "Quais skills estão faltando?",
                "output": '{"action_id": "skill_gaps", "source": "aggregated"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="top_by_experience",
        description="Lista os candidatos com mais experiência relevante ou os melhores por score",
        source=SourceType.AGGREGATED,
        params=[ParamSpec("limit", "int", "Quantidade de candidatos")],
        triggers=["mais experiência", "experiência relevante",
                  "veterano", "quem tem mais", "mais experient"],
        examples=[
            {"input": "Quem tem mais experiência relevante?",
                "output": '{"action_id": "top_by_experience", "params": {"limit": 5}, "source": "aggregated"}'},
            {"input": "Candidatos mais experientes",
                "output": '{"action_id": "top_by_experience", "params": {"limit": 10}, "source": "aggregated"}'},
            {"input": "Quem tem mais experiência?",
                "output": '{"action_id": "top_by_experience", "params": {"limit": 5}, "source": "aggregated"}'},
        ],
        priority=9
    ))

    ActionRegistry.register(DomainAction(
        id="candidates_to_discard",
        description="Identifica candidatos que podem ser descartados",
        source=SourceType.AGGREGATED,
        params=[ParamSpec("threshold", "int",
                          "Score mínimo para não descartar")],
        triggers=["descartar", "eliminar", "remover", "não qualificado"],
        examples=[
            {"input": "Quais candidatos devo descartar desta busca?",
                "output": '{"action_id": "candidates_to_discard", "params": {"threshold": 50}, "source": "aggregated"}'},
            {"input": "Quem devo eliminar?",
                "output": '{"action_id": "candidates_to_discard", "params": {"threshold": 50}, "source": "aggregated"}'},
        ],
        priority=6
    ))

    ActionRegistry.register(DomainAction(
        id="needs_screening",
        description="Identifica candidatos que precisam de triagem adicional",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["triagem", "avaliar", "revisar", "precisa", "adicional"],
        examples=[
            {"input": "Quem precisa de triagem adicional?",
                "output": '{"action_id": "needs_screening", "source": "aggregated"}'},
            {"input": "Quais candidatos preciso revisar?",
                "output": '{"action_id": "needs_screening", "source": "aggregated"}'},
        ],
        priority=6
    ))

    ActionRegistry.register(DomainAction(
        id="priority_ranking",
        description="Organiza candidatos por prioridade de contato",
        source=SourceType.AGGREGATED,
        params=[],
        triggers=["prioridad", "organiz", "ordem", "ranking", "contactar"],
        examples=[
            {"input": "Organize os candidatos por prioridade",
                "output": '{"action_id": "priority_ranking", "source": "aggregated"}'},
            {"input": "Qual a ordem de prioridade?",
                "output": '{"action_id": "priority_ranking", "source": "aggregated"}'},
        ],
        priority=7
    ))

    ActionRegistry.register(DomainAction(
        id="work_model_specific",
        description="Conta candidatos por modelo de trabalho específico (remoto, híbrido, presencial)",
        source=SourceType.AGGREGATED,
        params=[ParamSpec("model_type", "string",
                          "Tipo: remote, hybrid, onsite")],
        triggers=["híbrido", "hibrido", "remoto",
                  "presencial", "home office", "trabalho"],
        examples=[
            {"input": "Quantos aceitam trabalho híbrido?",
                "output": '{"action_id": "work_model_specific", "params": {"model_type": "hybrid"}, "source": "aggregated"}'},
            {"input": "Quantos aceitam somente remoto?",
                "output": '{"action_id": "work_model_specific", "params": {"model_type": "remote"}, "source": "aggregated"}'},
            {"input": "Quantos aceitam trabalho presencial?",
                "output": '{"action_id": "work_model_specific", "params": {"model_type": "onsite"}, "source": "aggregated"}'},
        ],
        priority=8
    ))

```

---

## 📄 src/domains/sourced_profile_sourcing/prompt_builder/domain_action.py

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum

from .filter_specs import ParamSpec


class SourceType(Enum):
    API = "api"
    AGGREGATED = "aggregated"
    LOCAL = "local"


@dataclass
class DomainAction:
    id: str
    description: str
    source: SourceType
    params: List[ParamSpec] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    priority: int = 0

    def matches_query(self, query: str) -> float:
        query_lower = query.lower()
        matches = sum(1 for t in self.triggers if t in query_lower)
        return min(matches / max(len(self.triggers), 1), 1.0)

    def get_adjusted_priority(self, total_candidates: int) -> int:
        if total_candidates > 500 and self.id == "summarize_search":
            return self.priority + 3
        if total_candidates < 20 and self.id == "list_candidates":
            return self.priority + 2
        if total_candidates > 200 and self.id in ("average_score", "score_distribution"):
            return self.priority + 1
        return self.priority

    def to_compact_doc(self) -> str:
        return f"- **{self.id}**: {self.description}"

    def to_full_doc(self) -> str:
        lines = [f"### {self.id}", self.description]

        if self.params:
            lines.append("Params:")
            for p in self.params[:5]:
                lines.append(f"  - {p.to_doc()}")

        if self.examples:
            lines.append("Exemplos:")
            for ex in self.examples[:4]:
                lines.append(f'  - "{ex["input"]}" -> {ex["output"]}')

        return "\n".join(lines)

```

---

## 📄 src/domains/sourced_profile_sourcing/prompt_builder/dynamic_builder.py

```python
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Any, List, Optional, Tuple

from .domain_action import DomainAction
from .action_registry import ActionRegistry


@dataclass
class PromptConfig:
    max_actions_in_prompt: int = 6
    max_examples_per_action: int = 2
    include_filter_docs: bool = True
    compact_mode: bool = False
    enable_cache: bool = True


class DynamicPromptBuilder:

    CORE_RULES = """## REGRAS
1. source: "api" para dados de candidatos
2. source: "aggregated" para estatísticas pré-calculadas
3. EXECUTE a ação quando houver filtro claro. SÓ peça clarificação se realmente impossível entender.
4. Buscas por texto/palavra no cargo/nome/skill → use search_candidates
5. Ver DETALHES/INFORMAÇÕES de UM candidato específico (por nome ou ID) → use show_candidate_details
6. ANÁLISES AGREGADAS (skills comuns, pontos fortes, gaps, experiência média, score médio) → NÃO peça clarificação, execute direto com source="aggregated"

## FORMATO
Claro: {"action_id": "<id>", "params": {}, "source": "api|aggregated", "confidence": 0.7-1.0}
Ambíguo: {"needs_clarification": true, "clarification_question": "...", "confidence": 0.0-0.6}"""

    FILTER_DOCS = """## FILTROS (where)
### Filtros EXATOS (=):
| Campo | Tipo | Exemplo |
|-------|------|---------|
| city | string | {"city": "sao paulo"} |
| skills | array | {"skills": ["python"]} |
| position_level | string | {"position_level": "senior"} |
| remote_work | bool | {"remote_work": true} |
| has_emails | bool | {"has_emails": true} |

### Filtros de RANGE (gte, lte, gt, lt):
| Campo | Tipo | Exemplo |
|-------|------|---------|
| sourcing_score | range | {"sourcing_score": {"gte": 70}} |
| total_experience_years | range | {"total_experience_years": {"gte": 5}} |

### Filtros PARCIAIS (ilike '%termo%') - use sufixo _cont:
| Campo | Tipo | Exemplo |
|-------|------|---------|
| role_name_cont | string | {"role_name_cont": "developer"} |
| name_cont | string | {"name_cont": "silva"} |
| current_company_cont | string | {"current_company_cont": "google"} |

### Outros operadores:
| Operador | Uso | Exemplo |
|----------|-----|---------|
| exists | campo existe | {"email": {"exists": true}} |
| prefix | comeca com | {"name": {"prefix": "Jo"}} |

Para cargo especifico: use role_name_cont
Ordenacao: sempre sourcing_score"""

    def __init__(self, config: Optional[PromptConfig] = None):
        self.config = config or PromptConfig()

    def build_system_prompt(
        self,
        sourcing_id: str,
        total_candidates: int,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> str:
        stats_lines = []
        if aggregated_stats:
            counts = aggregated_stats.get("counts", {})
            score_stats = aggregated_stats.get("score_stats", {})
            skills_dist = aggregated_stats.get("skills_distribution", {})

            if score_stats.get("average"):
                stats_lines.append(
                    f"Score médio: {score_stats['average']:.1f}")
            if skills_dist.get("unique_count"):
                stats_lines.append(
                    f"Skills únicas: {skills_dist['unique_count']}")
            if counts.get("from_local"):
                stats_lines.append(f"Base local: {counts['from_local']}")

        stats_section = ""
        if stats_lines:
            stats_section = "\n" + " | ".join(stats_lines)

        filter_section = self.FILTER_DOCS if self.config.include_filter_docs else ""

        return f"""Você é **Lia**, assistente de recrutamento.

## CONTEXTO
Sourcing: `{sourcing_id}` | Candidatos: {total_candidates}{stats_section}

{self.CORE_RULES}

{filter_section}"""

    def build_intent_prompt(
        self,
        query: str,
        all_actions: Optional[List[DomainAction]] = None,
        total_candidates: int = 0
    ) -> str:
        actions = all_actions or ActionRegistry.all()
        relevant = self._select_relevant_actions(
            query, actions, total_candidates)

        actions_doc = self._format_actions(relevant)
        examples = self._select_examples(query, relevant)

        return f"""Analise: "{query}"

## AÇÕES
{actions_doc}

## EXEMPLOS
{examples}

Responda JSON puro:"""

    @lru_cache(maxsize=100)
    def _get_relevant_action_ids_cached(self, query_normalized: str) -> Tuple[str, ...]:
        actions = ActionRegistry.all()
        relevant = self._select_relevant_actions(query_normalized, actions, 0)
        return tuple(a.id for a in relevant)

    @classmethod
    def clear_cache(cls):
        cls._get_relevant_action_ids_cached.cache_clear()

    def _select_relevant_actions(
        self,
        query: str,
        actions: List[DomainAction],
        total_candidates: int = 0
    ) -> List[DomainAction]:
        query_lower = query.lower()
        scored = []

        for action in actions:
            score = action.matches_query(query)
            priority = action.get_adjusted_priority(
                total_candidates) if total_candidates else action.priority
            if score > 0 or priority >= 8:
                scored.append((action, score, priority))

        scored.sort(key=lambda x: (-x[1], -x[2]))
        return [a for a, _, _ in scored[:self.config.max_actions_in_prompt]]

    def _format_actions(self, actions: List[DomainAction]) -> str:
        if self.config.compact_mode:
            return "\n".join(a.to_compact_doc() for a in actions)
        return "\n\n".join(a.to_full_doc() for a in actions)

    def _select_examples(self, query: str, actions: List[DomainAction]) -> str:
        examples = []
        for action in actions:
            for ex in action.examples[:self.config.max_examples_per_action]:
                examples.append(f'- "{ex["input"]}" → {ex["output"]}')
        return "\n".join(examples[:8])


class CompactPromptBuilder(DynamicPromptBuilder):

    def __init__(self):
        super().__init__(PromptConfig(
            max_actions_in_prompt=4,
            max_examples_per_action=1,
            include_filter_docs=False,
            compact_mode=True
        ))

    def build_system_prompt(
        self,
        sourcing_id: str,
        total_candidates: int,
        aggregated_stats: Optional[Dict[str, Any]] = None
    ) -> str:
        return f"""Lia - assistente recrutamento.
Sourcing: {sourcing_id} | Candidatos: {total_candidates}
REGRAS: source="api" para candidatos, "aggregated" para stats. Ambíguo? needs_clarification: true
FORMATO: {{"action_id": "...", "params": {{}}, "source": "...", "confidence": 0-1}}"""

```

---

## 📄 src/domains/sourced_profile_sourcing/prompt_builder/filter_specs.py

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ParamSpec:
    name: str
    type: str
    description: str
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def to_doc(self) -> str:
        ex = self.examples[0] if self.examples else {}
        return f"{self.name} ({self.type}): {self.description}. Ex: {ex.get('value', '')}"


class FilterSpecs:

    CITY = ParamSpec(
        name="where.city",
        type="string",
        description="Cidade (lowercase)",
        examples=[{"input": "de SP", "value": {"city": "sao paulo"}}]
    )

    STATE = ParamSpec(
        name="where.state",
        type="string",
        description="Estado (lowercase)",
        examples=[{"input": "de MG", "value": {"state": "mg"}}]
    )

    SKILLS = ParamSpec(
        name="where.skills",
        type="array[string]",
        description="Skills técnicas (lowercase)",
        examples=[{"input": "sabe Python e React",
                   "value": {"skills": ["python", "react"]}}]
    )

    REMOTE = ParamSpec(
        name="where.remote_work",
        type="boolean",
        description="Aceita trabalho remoto",
        examples=[{"input": "aceita remoto", "value": {"remote_work": True}}]
    )

    SCORE = ParamSpec(
        name="where.sourcing_score",
        type="object{gte,lte}",
        description="Range de score",
        examples=[{"input": "score > 70", "value": {
            "sourcing_score": {"gte": 70}}}]
    )

    EXPERIENCE = ParamSpec(
        name="where.total_experience_years",
        type="object{gte,lte}",
        description="Anos de experiência",
        examples=[{"input": "mais de 5 anos", "value": {
            "total_experience_years": {"gte": 5}}}]
    )

    POSITION_LEVEL = ParamSpec(
        name="where.position_level",
        type="string",
        description="Nível (junior/pleno/senior)",
        examples=[{"input": "senior", "value": {"position_level": "senior"}}]
    )

    HAS_EMAIL = ParamSpec(
        name="where.has_emails",
        type="boolean",
        description="Tem email cadastrado",
        examples=[{"input": "tem email", "value": {"has_emails": True}}]
    )

    HAS_LINKEDIN = ParamSpec(
        name="where.has_linkedin",
        type="boolean",
        description="Tem LinkedIn",
        examples=[{"input": "com linkedin", "value": {"has_linkedin": True}}]
    )

    LANGUAGES = ParamSpec(
        name="where.languages",
        type="array[string]",
        description="Idiomas",
        examples=[{"input": "fala inglês", "value": {"languages": ["ingles"]}}]
    )

    GENDER = ParamSpec(
        name="where.gender",
        type="string",
        description="Gênero (male/female)",
        examples=[{"input": "mulheres", "value": {"gender": "female"}}]
    )

    LIMIT = ParamSpec(
        name="limit",
        type="int",
        description="Quantidade máxima",
        examples=[{"input": "top 10", "value": 10}]
    )

    CANDIDATE_ID = ParamSpec(
        name="candidate_id",
        type="int",
        description="ID do candidato",
        examples=[{"input": "#123", "value": 123}]
    )

    CANDIDATE_NAME = ParamSpec(
        name="name",
        type="string",
        description="Nome do candidato",
        examples=[{"input": "detalhes do João", "value": "João"}]
    )

    SEARCH = ParamSpec(
        name="search",
        type="string",
        description="Busca textual geral em todos os campos (nome, cargo, empresa, skills)",
        examples=[{"input": "busque python", "value": "python"}]
    )

    ROLE_NAME_CONT = ParamSpec(
        name="where.role_name_cont",
        type="string",
        description="Busca parcial no cargo (ilike '%termo%'). Converte para where[role_name][ilike]='%termo%'",
        examples=[{"input": "cargo de developer",
                   "value": {"role_name_cont": "developer"}}]
    )

    NAME_CONT = ParamSpec(
        name="where.name_cont",
        type="string",
        description="Busca parcial no nome (ilike '%termo%')",
        examples=[{"input": "nome contenha silva",
                   "value": {"name_cont": "silva"}}]
    )

    COMPANY_CONT = ParamSpec(
        name="where.current_company_cont",
        type="string",
        description="Busca parcial na empresa (ilike '%termo%')",
        examples=[{"input": "empresa google", "value": {
            "current_company_cont": "google"}}]
    )

```

---

## 📄 src/models/__init__.py

```python
"""Data models for the recruiter agent."""

from .state import QueryState
from .intent import Intent, IntentEntity, FilterCondition, Aggregation
from .api_plan import APIStep, APIPlan
from .response import QueryResponse

__all__ = [
    "QueryState",
    "Intent",
    "IntentEntity",
    "FilterCondition",
    "Aggregation",
    "APIStep",
    "APIPlan",
    "QueryResponse",
]

```

---

## 📄 src/models/api_plan.py

```python
"""
API Plan models for representing the execution plan.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class APIEndpoint(str, Enum):
    """Available API endpoints."""
    CANDIDATES_SEARCH = "candidates_search"
    CANDIDATES_SHOW = "candidates_show"
    JOBS_SEARCH = "jobs_search"
    JOBS_SHOW = "jobs_show"
    APPLIES_SEARCH = "applies_search"
    APPLIES_SHOW = "applies_show"


@dataclass
class APIStep:
    """
    Represents a single step in the API execution plan.
    Immutable and focused on single responsibility.
    """
    step: int
    api: APIEndpoint
    params: Dict[str, Any] = field(default_factory=dict)
    save_as: Optional[str] = None
    post_process: Optional[str] = None
    depends_on: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "step": self.step,
            "api": self.api.value,
            "params": self.params
        }
        
        if self.save_as:
            result["save_as"] = self.save_as
        if self.post_process:
            result["post_process"] = self.post_process
        if self.depends_on:
            result["depends_on"] = self.depends_on
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "APIStep":
        """Create APIStep from dictionary."""
        return cls(
            step=data["step"],
            api=APIEndpoint(data["api"]),
            params=data.get("params", {}),
            save_as=data.get("save_as"),
            post_process=data.get("post_process"),
            depends_on=data.get("depends_on")
        )


@dataclass
class APIPlan:
    """
    Represents the complete execution plan.
    Encapsulates multiple API steps.
    """
    steps: List[APIStep] = field(default_factory=list)
    
    def add_step(self, step: APIStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
    
    def get_step(self, step_number: int) -> Optional[APIStep]:
        """Get a specific step by number."""
        for step in self.steps:
            if step.step == step_number:
                return step
        return None
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries."""
        return [step.to_dict() for step in self.steps]
    
    @classmethod
    def from_list(cls, data: List[Dict[str, Any]]) -> "APIPlan":
        """Create APIPlan from list of dictionaries."""
        return cls(steps=[APIStep.from_dict(step) for step in data])
    
    def __len__(self) -> int:
        """Return number of steps."""
        return len(self.steps)
    
    def __iter__(self):
        """Make plan iterable."""
        return iter(self.steps)

```

---

## 📄 src/models/conversation_state.py

```python
"""
Conversation State - Gerencia estado de conversação multi-turno.

Permite que o agente pause execução, faça perguntas, e continue
depois de receber respostas do usuário.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class ActionStatus(Enum):
    """Status de uma ação pendente."""
    PENDING_CLARIFICATION = "pending_clarification"
    PENDING_CONFIRMATION = "pending_confirmation"
    READY_TO_EXECUTE = "ready_to_execute"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ClarificationType(Enum):
    """Tipo de clarificação necessária."""
    AMBIGUOUS_ENTITY = "ambiguous_entity"
    MISSING_PARAMETER = "missing_parameter"
    CONFIRMATION_NEEDED = "confirmation_needed"
    CHOICE_REQUIRED = "choice_required"
    TOO_MANY_RESULTS = "too_many_results"


@dataclass
class ClarificationRequest:
    """
    Representa uma pergunta que o agente precisa fazer ao usuário.
    """
    id: str
    type: ClarificationType
    question: str
    
    context: Dict[str, Any] = field(default_factory=dict)
    options: List[Dict[str, Any]] = field(default_factory=list)
    answer_field: str = ""
    default_answer: Any = None
    optional: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização."""
        return {
            "id": self.id,
            "type": self.type.value,
            "question": self.question,
            "context": self.context,
            "options": self.options,
            "answer_field": self.answer_field,
            "default_answer": self.default_answer,
            "optional": self.optional
        }


@dataclass
class PendingAction:
    """
    Representa uma ação que o agente quer executar mas precisa de clarificação.
    """
    id: str
    description: str
    api_calls: List[Dict[str, Any]]
    
    status: ActionStatus = ActionStatus.PENDING_CLARIFICATION
    clarifications: List[ClarificationRequest] = field(default_factory=list)
    resolved_params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_clarification(self, clarification: ClarificationRequest) -> None:
        """Adiciona uma clarificação necessária."""
        self.clarifications.append(clarification)
        self.status = ActionStatus.PENDING_CLARIFICATION
        self.updated_at = datetime.now()
    
    def resolve_clarification(self, clarification_id: str, answer: Any) -> None:
        """Resolve uma clarificação com a resposta do usuário."""
        for clarif in self.clarifications:
            if clarif.id == clarification_id:
                self.resolved_params[clarif.answer_field] = answer
                self.clarifications.remove(clarif)
                break
        
        if not self.clarifications:
            self.status = ActionStatus.READY_TO_EXECUTE
        
        self.updated_at = datetime.now()
    
    def is_ready(self) -> bool:
        """Verifica se a ação está pronta para executar."""
        return self.status == ActionStatus.READY_TO_EXECUTE and not self.clarifications
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "clarifications": [c.to_dict() for c in self.clarifications],
            "resolved_params": self.resolved_params,
            "api_calls": self.api_calls
        }


@dataclass
class ConversationContext:
    """
    Contexto completo de uma conversação multi-turno.
    """
    session_id: str
    
    messages: List[Dict[str, Any]] = field(default_factory=list)
    pending_actions: List[PendingAction] = field(default_factory=list)
    known_entities: Dict[str, Any] = field(default_factory=dict)
    last_query: str = ""
    awaiting_user_input: bool = False
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_pending_action(self, action: PendingAction) -> None:
        """Adiciona ação pendente."""
        self.pending_actions.append(action)
        self.awaiting_user_input = True
        self.updated_at = datetime.now()
    
    def get_pending_clarifications(self) -> List[ClarificationRequest]:
        """Retorna todas as clarificações pendentes."""
        clarifications = []
        for action in self.pending_actions:
            if action.status == ActionStatus.PENDING_CLARIFICATION:
                clarifications.extend(action.clarifications)
        return clarifications
    
    def resolve_clarification(self, clarification_id: str, answer: Any) -> None:
        """Resolve uma clarificação."""
        for action in self.pending_actions:
            for clarif in action.clarifications:
                if clarif.id == clarification_id:
                    action.resolve_clarification(clarification_id, answer)
                    self.updated_at = datetime.now()
                    return
    
    def has_pending_clarifications(self) -> bool:
        """Verifica se há clarificações pendentes."""
        return len(self.get_pending_clarifications()) > 0
    
    def get_ready_actions(self) -> List[PendingAction]:
        """Retorna ações prontas para executar."""
        return [a for a in self.pending_actions if a.is_ready()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "pending_actions": [a.to_dict() for a in self.pending_actions],
            "known_entities": self.known_entities,
            "awaiting_user_input": self.awaiting_user_input
        }

```

---

## 📄 src/models/exceptions.py

```python
"""
Custom exceptions for the recruiter agent system.
Single Responsibility: Define all custom exception classes.
"""


class APIClientError(Exception):
    """Custom exception for API client errors."""
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        """
        Initialize API client error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Response body from API
        """
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """String representation of the error."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.response_body:
            parts.append(f"Response: {self.response_body[:200]}")
        return " | ".join(parts)


class StepDependencyError(Exception):
    """Raised when a step depends on data from a previous step that failed or returned insufficient data."""
    pass


class ReplanningRequired(Exception):
    """Signals that the current plan failed and replanning is needed."""
    pass


class MaxAttemptsExceeded(Exception):
    """Raised when maximum retry attempts have been exceeded."""
    pass

```

---

## 📄 src/models/intent.py

```python
"""
Intent models for representing analyzed user questions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class IntentEntity(str, Enum):
    """Entities that can be queried in the system."""
    CANDIDATES = "candidates"
    JOBS = "jobs"
    APPLIES = "applies"


class MainAction(str, Enum):
    """Main actions that can be performed."""
    LIST = "list"
    COUNT = "count"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    ANALYZE = "analyze"


class AggregationFunction(str, Enum):
    """Aggregation functions available."""
    COUNT = "count"
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    GROUP_BY = "group_by"


@dataclass
class FilterCondition:
    """Represents a filter condition."""
    field: str
    operator: str  # eq, gt, lt, gte, lte, ilike, in
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {self.field: {self.operator: self.value}}


@dataclass
class Aggregation:
    """Represents an aggregation operation."""
    function: AggregationFunction
    field: Optional[str] = None
    entity: Optional[IntentEntity] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "function": self.function.value,
            "field": self.field,
            "entity": self.entity.value if self.entity else None
        }


@dataclass
class Intent:
    """
    Represents the analyzed intent from a user question.
    Immutable to follow functional programming principles.
    """
    entities: List[IntentEntity]
    main_action: MainAction
    filters: Dict[str, Any] = field(default_factory=dict)
    aggregations: List[Aggregation] = field(default_factory=list)
    fields_needed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert intent to dictionary format."""
        return {
            "entities": [e.value for e in self.entities],
            "main_action": self.main_action.value,
            "filters": self.filters,
            "aggregations": [agg.to_dict() for agg in self.aggregations],
            "fields_needed": self.fields_needed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Intent":
        """Create Intent from dictionary."""
        return cls(
            entities=[IntentEntity(e) for e in data.get("entities", [])],
            main_action=MainAction(data.get("main_action", "list")),
            filters=data.get("filters", {}),
            aggregations=[
                Aggregation(
                    function=AggregationFunction(agg["function"]),
                    field=agg.get("field"),
                    entity=IntentEntity(agg["entity"]) if agg.get("entity") else None
                )
                for agg in data.get("aggregations", [])
            ],
            fields_needed=data.get("fields_needed", [])
        )

```

---

## 📄 src/models/pydantic_models.py

```python
"""
Pydantic models for the Recruiter Agent.
"""

from typing import List, Dict, Any, Optional, Sequence
from enum import Enum

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class APIEndpoint(str, Enum):
    """Available API endpoints."""
    CANDIDATES_SEARCH = "candidates_search"
    CANDIDATES_SHOW = "candidates_show"
    JOBS_SEARCH = "jobs_search"
    JOBS_SHOW = "jobs_show"
    APPLIES_SEARCH = "applies_search"
    APPLIES_SHOW = "applies_show"


class APIStep(BaseModel):
    """
    Represents a single step in the API execution plan.
    """
    step: int
    api: APIEndpoint
    params: Dict[str, Any] = Field(default_factory=dict)
    save_as: Optional[str] = None
    post_process: Optional[str] = None
    depends_on: Optional[str] = None


class APIPlan(BaseModel):
    """
    Represents the complete execution plan.
    """
    steps: List[APIStep] = Field(default_factory=list)


class IntentEntity(str, Enum):
    """Entities that can be queried in the system."""
    CANDIDATES = "candidates"
    JOBS = "jobs"
    APPLIES = "applies"


class MainAction(str, Enum):
    """Main actions that can be performed."""
    LIST = "list"
    COUNT = "count"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    ANALYZE = "analyze"


class AggregationFunction(str, Enum):
    """Aggregation functions available."""
    COUNT = "count"
    AVG = "avg"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    GROUP_BY = "group_by"


class FilterCondition(BaseModel):
    """Represents a filter condition."""
    field: str
    operator: str  # eq, gt, lt, gte, lte, ilike, in
    value: Any


class Aggregation(BaseModel):
    """Represents an aggregation operation."""
    function: AggregationFunction
    field: Optional[str] = None
    entity: Optional[IntentEntity] = None


class Intent(BaseModel):
    """
    Represents the analyzed intent from a user question.
    """
    entities: List[IntentEntity]
    main_action: MainAction
    filters: Dict[str, Any] = Field(default_factory=dict)
    aggregations: List[Aggregation] = Field(default_factory=list)
    fields_needed: List[str] = Field(default_factory=list)


class QueryState(BaseModel):
    """
    State shared across all agents in the workflow.
    """
    question: str
    messages: Sequence[BaseMessage] = Field(default_factory=list)
    intent: Optional[Intent] = None
    api_plan: Optional[APIPlan] = None
    api_results: Dict[str, Any] = Field(default_factory=dict)
    processed_data: Dict[str, Any] = Field(default_factory=dict)
    final_answer: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

```

---

## 📄 src/models/response.py

```python
"""
Response models for query results.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class QueryResponse:
    """
    Represents the final response to a user query.
    Immutable response object following value object pattern.
    """
    question: str
    answer: str
    intent: Dict[str, Any] = field(default_factory=dict)
    api_calls: int = 0
    total_records: int = 0
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "question": self.question,
            "answer": self.answer,
            "intent": self.intent,
            "api_calls": self.api_calls,
            "total_records": self.total_records,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "metadata": self.metadata
        }
    
    @property
    def success(self) -> bool:
        """Check if query was successful."""
        return self.error is None
    
    @property
    def execution_time_seconds(self) -> float:
        """Get execution time in seconds."""
        return self.execution_time_ms / 1000.0

```

---

## 📄 src/models/state.py

```python
"""
Query State definition for LangGraph workflow.
Represents the shared state between all agents.
"""

from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, List
from langchain_core.messages import BaseMessage
import operator


class QueryState(TypedDict):
    """
    State shared across all agents in the workflow.
    Uses Annotated with operator.add to accumulate messages.
    """
    
    # Original user question
    question: str
    
    # Conversation messages (accumulated)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Identified intent from user question
    intent: Optional[Dict[str, Any]]
    
    # Plan of API calls to execute
    api_plan: List[Dict[str, Any]]
    
    # Human-readable explanation of the plan
    plan_explanation: Optional[str]
    
    # Raw results from API calls
    api_results: Dict[str, Any]
    
    # Processed and aggregated data
    processed_data: Dict[str, Any]
    
    # Final answer to user
    final_answer: str
    
    # Error message if something fails
    error: Optional[str]
    
    # Pending confirmation request
    needs_confirmation: bool
    confirmation_request: Optional[Dict[str, Any]]
    user_confirmation: Optional[Dict[str, Any]]
    
    # Replanning control
    attempt_number: int
    max_attempts: int
    failed_strategies: List[Dict[str, Any]]
    execution_feedback: List[str]
    needs_replanning: bool
    critical_failure: bool
    
    # Pagination context
    last_query: Optional[str]
    current_page: int
    total_pages: int
    page_size: int
    
    # Metadata for tracking
    metadata: Dict[str, Any]

```

---

## 📄 src/models/state/__init__.py

```python
"""State models for the multi-agent workflow."""

from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, List
from langchain_core.messages import BaseMessage
import operator


class QueryState(TypedDict):
    """
    State shared across all agents in the workflow.
    Uses Annotated with operator.add to accumulate messages.
    """
    
    # Original user question
    question: str
    
    # Conversation messages (accumulated)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Identified intent from user question
    intent: Optional[Dict[str, Any]]
    
    # Plan of API calls to execute
    api_plan: List[Dict[str, Any]]
    
    # Human-readable explanation of the plan
    plan_explanation: Optional[str]
    
    # Raw results from API calls
    api_results: Dict[str, Any]
    
    # Processed and aggregated data
    processed_data: Dict[str, Any]
    
    # Final answer to user
    final_answer: str
    
    # Error message if something fails
    error: Optional[str]
    
    # Pending confirmation request
    needs_confirmation: bool
    confirmation_request: Optional[Dict[str, Any]]
    user_confirmation: Optional[Dict[str, Any]]
    
    # Metadata for tracking
    metadata: Dict[str, Any]



```

---

## 📄 src/services/__init__.py

```python
"""Services package for external integrations."""

from .api_client import ATSAPIClient
from .memory_service import MemoryService
from .rabbitmq_service import RabbitMQService

__all__ = ["ATSAPIClient", "MemoryService", "RabbitMQService"]

```

---

## 📄 src/services/api_client.py

```python
import json
import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config.settings import ATSAPIConfig
from ..models.exceptions import APIClientError
from .ott_service import get_ott_service
from .endpoint_loader import EndpointLoader
from ..utils.timing import get_timer


logger = logging.getLogger(__name__)


class ATSAPIClient:

    def __init__(self, config: ATSAPIConfig):
        self.config = config
        self.session = self._create_session()
        self.endpoint_loader = EndpointLoader()

    @property
    def auth_service(self):
        return get_ott_service().auth_service

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _build_url(self, endpoint: str) -> str:
        base_url = self.config.base_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base_url}/{endpoint}"

    def _prepare_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        processed = {}

        for key, value in params.items():
            if isinstance(value, (dict, list)):
                processed[key] = json.dumps(value)
            elif value is not None:
                processed[key] = value

        return processed

    def _clean_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            k: v for k, v in params.items()
            if v is not None and v != "" and v != [] and v != {} and not k.startswith("_")
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        timer = get_timer()
        if timer:
            timer.step(f"api_call:{endpoint}")

        url = self._build_url(endpoint)
        processed_params = self._prepare_params(params) if params else None
        headers = self.auth_service.get_auth_header()
        headers["Content-Type"] = "application/json"

        logger.info(f"🌐 API REQUEST: {method} {endpoint}")
        logger.info(
            f"   📋 Params: {json.dumps(params, ensure_ascii=False, default=str) if params else '{}'}")
        if json_data:
            logger.info(
                f"   📦 Body: {json.dumps(json_data, ensure_ascii=False, default=str)}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=processed_params,
                json=json_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 401:
                logger.warning("🔐 Token expired, refreshing...")
                self.auth_service.invalidate()
                headers = self.auth_service.get_auth_header()

                response = self.session.request(
                    method=method,
                    url=url,
                    params=processed_params,
                    json=json_data,
                    headers=headers,
                    timeout=30
                )

            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ API RESPONSE: {response.status_code}")
            if isinstance(result, dict):
                if "data" in result:
                    logger.info(f"   📊 Records: {len(result['data'])}")
                if "meta" in result and "total" in result["meta"]:
                    logger.info(f"   📈 Total: {result['meta']['total']}")

            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error for {method} {url}: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"   Response: {e.response.text[:500]}")
            raise APIClientError(f"API request failed: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error for {method} {url}: {e}")
            raise APIClientError(f"Network error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error for {method} {url}: {e}")
            raise APIClientError(f"Invalid JSON response: {e}") from e

    def call(self, endpoint_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        endpoint_config = self.endpoint_loader.load(endpoint_id)

        method = endpoint_config["endpoint"]["method"]
        path = endpoint_config["endpoint"]["path"]

        single_page_mode = params.get("_single_page", False)
        clean_params = self._clean_params(params)

        logger.debug(f"📞 Calling {endpoint_id}")

        if self.endpoint_loader.is_show_endpoint(endpoint_id):
            result = self._call_show(method, path, clean_params)
            result["_meta"] = {"method": method, "path": path.replace(
                ":id", str(params.get("id", "")))}
            return result

        if method == "GET":
            result = self._make_request("GET", path, params=clean_params)

            if self.endpoint_loader.is_search_endpoint(endpoint_id) and not single_page_mode:
                result = self._auto_paginate(
                    method, path, clean_params, result)

            result["_meta"] = {"method": method, "path": path}
            return result

        if method == "POST":
            body_data = self._wrap_body(endpoint_id, clean_params)
            result = self._make_request("POST", path, json_data=body_data)
            result["_meta"] = {"method": method, "path": path}
            return result

        if method in ["PUT", "PATCH"]:
            body_data = self._wrap_body(endpoint_id, clean_params)
            result = self._make_request(method, path, json_data=body_data)
            result["_meta"] = {"method": method, "path": path}
            return result

        if method == "DELETE":
            result = self._make_request("DELETE", path, params=clean_params)
            result["_meta"] = {"method": method, "path": path}
            return result

        raise ValueError(f"Unsupported HTTP method: {method}")

    def _call_show(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        entity_id = params.pop("id", None)
        if entity_id is None:
            raise ValueError(f"Show endpoint requires 'id' parameter")

        full_path = path.replace(":id", str(entity_id))
        return self._make_request(method, full_path, params=params)

    def _wrap_body(self, endpoint_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        body_contract = self.endpoint_loader.get_body_contract(endpoint_id)

        if not body_contract:
            return params

        wrapper_key = next(iter(body_contract.keys()))
        return {wrapper_key: params}

    def _auto_paginate(
        self,
        method: str,
        path: str,
        params: Dict[str, Any],
        first_result: Dict[str, Any],
        max_records: int = 1000
    ) -> Dict[str, Any]:
        if "data" not in first_result or "meta" not in first_result:
            return first_result

        limit = min(params.get("limit", 100), 100)
        params["limit"] = limit
        params["page"] = params.get("page", 1)

        all_data = first_result["data"]
        total = first_result["meta"].get("total", 0)

        logger.debug(
            f"🔄 Pagination started: page {params['page']}, fetched {len(all_data)}/{total}")

        while len(all_data) < min(total, max_records) and len(first_result["data"]) == limit:
            params["page"] += 1
            logger.debug(
                f"🔄 Fetching page {params['page']} (total so far: {len(all_data)})")

            try:
                next_result = self._make_request(method, path, params=params)
                next_data = next_result.get("data", [])

                if not next_data:
                    break

                all_data.extend(next_data)
                first_result = next_result

                if len(all_data) >= max_records:
                    all_data = all_data[:max_records]
                    logger.info(
                        f"⚠️  Reached max_records limit ({max_records})")
                    break

            except Exception as e:
                logger.warning(
                    f"⚠️  Error fetching page {params['page']}: {e}")
                break

        logger.info(
            f"✅ Pagination complete: {len(all_data)} records ({params['page']} pages)")

        first_result["data"] = all_data
        first_result["meta"]["fetched"] = len(all_data)
        return first_result

    def close(self) -> None:
        self.session.close()
        logger.info("API client session closed")

```

---

## 📄 src/services/api_client_backup.py

```python
import json
import logging
from typing import Dict, Any, Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config.settings import ATSAPIConfig
from ..models.exceptions import APIClientError
from .auth_service import AuthService


logger = logging.getLogger(__name__)


class ATSAPIClient:
    
    def __init__(self, config: ATSAPIConfig):
        self.config = config
        self.session = self._create_session()
        self.auth_service = AuthService(config)
    
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _build_url(self, endpoint: str) -> str:
        base_url = self.config.base_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        return f"{base_url}/{endpoint}"
    
    def _prepare_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        processed = {}
        
        for key, value in params.items():
            if isinstance(value, (dict, list)):
                processed[key] = json.dumps(value)
            elif value is not None:
                processed[key] = value
        
        return processed
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = self._build_url(endpoint)
        processed_params = self._prepare_params(params) if params else None
        headers = self.auth_service.get_auth_header()
        headers["Content-Type"] = "application/json"
        
        logger.info(f"🌐 API REQUEST: {method} {endpoint}")
        logger.info(f"   📋 Params: {json.dumps(params, ensure_ascii=False, default=str) if params else '{}'}")
        if json_data:
            logger.info(f"   📦 Body: {json.dumps(json_data, ensure_ascii=False, default=str)}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=processed_params,
                json=json_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 401:
                logger.warning("🔐 Token expired, refreshing...")
                self.auth_service.invalidate()
                headers = self.auth_service.get_auth_header()
                
                response = self.session.request(
                    method=method,
                    url=url,
                    params=processed_params,
                    json=json_data,
                    headers=headers,
                    timeout=30
                )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"✅ API RESPONSE: {response.status_code}")
            if isinstance(result, dict):
                if "data" in result:
                    logger.info(f"   📊 Records: {len(result['data'])}")
                if "meta" in result and "total" in result["meta"]:
                    logger.info(f"   📈 Total: {result['meta']['total']}")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error for {method} {url}: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"   Response: {e.response.text[:500]}")
            raise APIClientError(f"API request failed: {e}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error for {method} {url}: {e}")
            raise APIClientError(f"Network error: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error for {method} {url}: {e}")
            raise APIClientError(f"Invalid JSON response: {e}") from e
    
    
    def candidates_search(
        self,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        where: Optional[Dict[str, Any]] = None,
        compact: Optional[str] = None,
        includes: Optional[str] = None,
        order: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        params = {
            "search": search,
            "page": page,
            "limit": limit,
            "where": where,
            "compact": compact,
            "includes": includes,
            "order": order
        }
        
        logger.debug(f"Searching candidates with params: {params}")
        return self._make_request("GET", "/v1/users/candidates", params=params)
    
    def candidates_show(
        self,
        candidate_id: int,
        includes: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {"includes": includes} if includes else {}
        
        logger.debug(f"Fetching candidate {candidate_id}")
        return self._make_request(
            "GET",
            f"/v1/users/candidates/{candidate_id}",
            params=params
        )
    
    def jobs_search(
        self,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        where: Optional[Dict[str, Any]] = None,
        compact: Optional[str] = None,
        order: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        params = {
            "search": search,
            "page": page,
            "limit": limit,
            "where": where,
            "compact": compact,
            "order": order
        }
        
        logger.debug(f"Searching jobs with params: {params}")
        return self._make_request("GET", "/v1/users/jobs", params=params)
    
    def jobs_show(self, job_id: int) -> Dict[str, Any]:
        logger.debug(f"Fetching job {job_id}")
        return self._make_request("GET", f"/v1/users/jobs/{job_id}")
    
    def applies_search(
        self,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        where: Optional[Dict[str, Any]] = None,
        compact: Optional[str] = None,
        order: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        params = {
            "search": search,
            "page": page,
            "limit": limit,
            "where": where,
            "compact": compact,
            "order": order
        }
        
        logger.debug(f"Searching applies with params: {params}")
        return self._make_request("GET", "/v1/users/applies", params=params)
    
    def applies_show(self, apply_id: int) -> Dict[str, Any]:
        logger.debug(f"Fetching apply {apply_id}")
        return self._make_request("GET", f"/v1/users/applies/{apply_id}")
    
    def applies_create_collection(
        self,
        job_id: int,
        selective_process_id: int,
        reference_ids: List[int],
        reference_type: str = "Candidate"
    ) -> Dict[str, Any]:
        """
        Create multiple applies (inscribe candidates to job).
        
        Args:
            job_id: ID of the job
            selective_process_id: ID of the selective process (stage)
            reference_ids: List of candidate IDs
            reference_type: Type of reference (default: "Candidate")
            
        Returns:
            API response with created applies
        """
        json_data = {
            "apply": {
                "selective_process_id": selective_process_id,
                "job_id": job_id
            },
            "select_all_params": {
                "reference_ids": reference_ids,
                "reference_type": reference_type
            }
        }
        
        logger.debug(f"Creating {len(reference_ids)} applies for job {job_id}, process {selective_process_id}")
        return self._make_request("POST", "/v1/users/applies/create_collection", json_data=json_data)
    
    def selective_processes_search(
        self,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        where: Optional[Dict[str, Any]] = None,
        compact: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search selective processes (job stages).
        
        Args:
            search: Search query
            page: Page number
            limit: Results per page
            where: Filter conditions
            compact: Compact response (optional, may not be supported by API)
            
        Returns:
            API response with selective processes
        """
        params = {
            "search": search,
            "page": page,
            "limit": limit,
            "where": where,
            "compact": compact
        }
        
        logger.debug(f"Searching selective_processes with params: {params}")
        return self._make_request("GET", "/v1/users/selective_processes", params=params)
    
    def selective_processes_show(self, process_id: int) -> Dict[str, Any]:
        """
        Get selective process by ID.
        
        Args:
            process_id: ID of the selective process
            
        Returns:
            API response with selective process details
        """
        logger.debug(f"Fetching selective_process {process_id}")
        return self._make_request("GET", f"/v1/users/selective_processes/{process_id}")
    
    def experiences_search(
        self,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        where: Optional[Dict[str, Any]] = None,
        order: Optional[Dict[str, str]] = None,
        compact: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search professional experiences.
        
        Args:
            search: Search query (company name, description, etc)
            page: Page number
            limit: Results per page
            where: Filter conditions (user_id, work_here, company_id, etc)
            order: Sort order (e.g., {"start_date": "desc"})
            compact: Compact response fields (optional)
            
        Returns:
            API response with experiences
        """
        params = {
            "search": search,
            "page": page,
            "limit": limit,
            "where": where,
            "order": order,
            "compact": compact
        }
        
        logger.debug(f"Searching experiences with params: {params}")
        return self._make_request("GET", "/v1/users/experiences", params=params)
    
    def experiences_show(self, experience_id: int) -> Dict[str, Any]:
        """
        Get experience by ID.
        
        Args:
            experience_id: ID of the experience
            
        Returns:
            API response with experience details
        """
        logger.debug(f"Fetching experience {experience_id}")
        return self._make_request("GET", f"/v1/users/experiences/{experience_id}")
    
    def extract_ids(self, data: List[Dict[str, Any]], field: str = "id") -> List[int]:
        return [record[field] for record in data if field in record]
    
    def call(self, api_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        api_methods = {
            "candidates_search": self.candidates_search,
            "candidates_show": self.candidates_show,
            "jobs_search": self.jobs_search,
            "jobs_show": self.jobs_show,
            "applies_search": self.applies_search,
            "applies_show": self.applies_show,
            "applies_create_collection": self.applies_create_collection,
            "selective_processes_search": self.selective_processes_search,
            "selective_processes_show": self.selective_processes_show,
            "experiences_search": self.experiences_search,
            "experiences_show": self.experiences_show,
        }
        
        if api_name not in api_methods:
            raise ValueError(f"Unknown API: {api_name}")
        
        method = api_methods[api_name]
        
        if api_name.endswith("_show"):
            entity_id = params.pop("id", None)
            if entity_id is None:
                raise ValueError(f"{api_name} requires 'id' parameter")
            return method(entity_id, **params)
        
        if api_name.endswith("_search"):
            return self._search_with_pagination(method, params, api_name)
        
        return method(**params)
    
    def _search_with_pagination(
        self,
        method: callable,
        params: Dict[str, Any],
        api_name: str,
        max_records: int = 1000
    ) -> Dict[str, Any]:
        limit = min(params.get("limit", 100), 100)
        params["limit"] = limit
        params["page"] = params.get("page", 1)
        
        logger.debug(f"🔄 Pagination: {api_name} page {params['page']} (limit: {limit})")
        response = method(**params)
        
        if "data" not in response or "meta" not in response:
            return response
        
        all_data = response["data"]
        total = response["meta"].get("total", 0)
        
        while len(all_data) < min(total, max_records) and len(response["data"]) == limit:
            params["page"] += 1
            logger.debug(f"🔄 Fetching page {params['page']} (total so far: {len(all_data)})")
            
            try:
                response = method(**params)
                next_data = response.get("data", [])
                
                if not next_data:
                    break
                
                all_data.extend(next_data)
                
                if len(all_data) >= max_records:
                    all_data = all_data[:max_records]
                    logger.info(f"⚠️  Reached max_records limit ({max_records})")
                    break
                    
            except Exception as e:
                logger.warning(f"⚠️  Error fetching page {params['page']}: {e}")
                break
        
        logger.info(f"✅ Pagination complete: {len(all_data)} records ({params['page']} pages)")
        
        response["data"] = all_data
        response["meta"]["fetched"] = len(all_data)
        return response
    
    def close(self) -> None:
        self.session.close()
        logger.info("API client session closed")

```

---

## 📄 src/services/api_executor.py

```python
import logging
from typing import Dict, Any, List, Optional
import httpx
from urllib.parse import urljoin

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class APIExecutor:
    """
    Serviço compartilhado para executar chamadas de API.
    Usado tanto pelo workflow global quanto pelos domains.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ats_api.base_url
        self.timeout = 30.0

    def execute_single(
        self,
        endpoint_id: str,
        payload: Dict[str, Any],
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Executa uma única chamada de API.

        Args:
            endpoint_id: ID do endpoint (ex: "candidates_search")
            payload: Parâmetros da request
            method: Método HTTP (GET, POST, etc)

        Returns:
            Dict com resultado: {"success": bool, "data": Any, "error": str}
        """
        try:
            url = self._build_url(endpoint_id, payload)

            logger.info(f"[APIExecutor] {method} {url}")

            with httpx.Client(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = client.get(
                        url, params=payload.get("params", {}))
                elif method.upper() == "POST":
                    response = client.post(url, json=payload.get("body", {}))
                elif method.upper() == "PUT":
                    response = client.put(url, json=payload.get("body", {}))
                elif method.upper() == "DELETE":
                    response = client.delete(url)
                else:
                    return {
                        "success": False,
                        "error": f"Método HTTP não suportado: {method}"
                    }

                response.raise_for_status()

                return {
                    "success": True,
                    "data": response.json(),
                    "status_code": response.status_code
                }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[APIExecutor] HTTP error: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"Erro HTTP {e.response.status_code}: {e.response.text[:200]}",
                "status_code": e.response.status_code
            }

        except Exception as e:
            logger.error(f"[APIExecutor] Error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def execute_batch(
        self,
        calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Executa múltiplas chamadas de API em sequência.

        Args:
            calls: Lista de dicts com {"endpoint_id", "payload", "method"}

        Returns:
            Lista de resultados
        """
        results = []

        for call in calls:
            result = self.execute_single(
                endpoint_id=call.get("endpoint_id"),
                payload=call.get("payload", {}),
                method=call.get("method", "GET")
            )

            result["endpoint_id"] = call.get("endpoint_id")
            results.append(result)

        return results

    def search_with_filter(
        self,
        endpoint_id: str,
        filters: Dict[str, Any],
        page: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Helper para fazer search com filtros.

        Args:
            endpoint_id: ID do endpoint de search (ex: "sourced_profile_sourcing_search")
            filters: Dict de filtros {"field": {"operator": "value"}}
            page: Página
            limit: Limite por página

        Returns:
            Resultado da busca
        """
        payload = {
            "params": {
                "page": page,
                "limit": limit,
                **self._build_filter_params(filters)
            }
        }

        return self.execute_single(endpoint_id, payload, method="GET")

    def _build_url(self, endpoint_id: str, payload: Dict[str, Any]) -> str:
        """
        Constrói URL baseado no endpoint_id.
        """
        endpoint_map = {
            "candidates_search": "/api/candidates",
            "jobs_search": "/api/jobs",
            "sourced_profile_sourcing_search": "/api/sourced_profile_sourcing",
            "applies_search": "/api/applies",
        }

        path = endpoint_map.get(endpoint_id, f"/api/{endpoint_id}")

        # Se tem ID no path
        if "id" in payload:
            path = f"{path}/{payload['id']}"

        return urljoin(self.base_url, path)

    def _build_filter_params(self, filters: Dict[str, Any]) -> Dict[str, str]:
        """
        Converte filtros para query params.

        Ex: {"score": {"gte": 80}} -> {"filter[score][gte]": 80}
        """
        params = {}

        for field, conditions in filters.items():
            if isinstance(conditions, dict):
                for operator, value in conditions.items():
                    params[f"filter[{field}][{operator}]"] = str(value)
            else:
                params[f"filter[{field}][eq]"] = str(conditions)

        return params

    def get_sourced_profiles_by_sourcing_id(
        self,
        sourcing_id: str,
        additional_filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Busca sourced_profile_sourcing por sourcing_id (caso mais comum para domains).

        Args:
            sourcing_id: ID do sourcing
            additional_filters: Filtros adicionais
            page: Página
            limit: Limite

        Returns:
            Resultado com candidatos do sourcing
        """
        filters = {"sourcing_id": {"eq": sourcing_id}}

        if additional_filters:
            filters.update(additional_filters)

        return self.search_with_filter(
            endpoint_id="sourced_profile_sourcing_search",
            filters=filters,
            page=page,
            limit=limit
        )

```

---

## 📄 src/services/auth_service.py

```python
import logging
from typing import Optional
from datetime import datetime, timedelta
import requests

from ..config.ats_api_config import ATSAPIConfig
from ..models.exceptions import APIClientError
from ..utils.token_utils import validate_jwt_format, mask_token, extract_bearer_token


logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(self):
        self._token: Optional[str] = None
        self._expiration: Optional[datetime] = None
        self._is_ott: bool = False

    def set_token(self, token: str, expires_in_hours: int = 24, is_ott: bool = False) -> None:
        self._token = token
        self._expiration = datetime.now() + timedelta(hours=expires_in_hours)
        self._is_ott = is_ott

    def set_ott(self, token: str) -> None:
        self.set_token(token, expires_in_hours=1, is_ott=True)
        logger.info(f"OTT configured: {mask_token(token)}")

    def get_token(self) -> Optional[str]:
        if not self._token:
            return None

        if not self._expiration:
            return None

        if datetime.now() >= self._expiration:
            self._clear()
            return None

        return self._token

    @property
    def is_ott(self) -> bool:
        return self._is_ott and self.is_valid()

    def _clear(self) -> None:
        self._token = None
        self._expiration = None
        self._is_ott = False

    def is_valid(self) -> bool:
        return self.get_token() is not None


class AuthService:
    def __init__(self, config: ATSAPIConfig):
        self.config = config
        self.token_manager = TokenManager()

    def set_ott(self, token: str) -> bool:
        token = extract_bearer_token(token)

        if not token:
            logger.warning("Empty OTT provided")
            return False

        if not validate_jwt_format(token):
            logger.warning(f"Invalid JWT format: {mask_token(token)}")
            return False

        self.token_manager.set_ott(token)
        return True

    def authenticate(self) -> str:
        if self.token_manager.is_valid():
            return self.token_manager.get_token()

        return self._perform_login()

    def _perform_login(self) -> str:
        url = f"{self.config.base_url}/v1/sessions"
        payload = {
            "email": self.config.username,
            "password": self.config.password
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            token = data.get("token")

            if not token:
                raise APIClientError("No token in authentication response")

            self.token_manager.set_token(token)
            logger.info("Authentication successful")

            return token

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            raise APIClientError(f"Authentication failed: {e}") from e

    def get_auth_header(self) -> dict[str, str]:
        token = self.authenticate()
        return {"Authorization": f"Bearer {token}"}

    def get_current_token(self) -> Optional[str]:
        return self.token_manager.get_token()

    @property
    def using_ott(self) -> bool:
        return self.token_manager.is_ott

    def invalidate(self) -> None:
        self.token_manager._clear()
        logger.info("Token invalidated")

```

---

## 📄 src/services/clarification_service.py

```python
"""
Clarification Service - Detecta ambiguidades e gera perguntas.

Integra-se com o sistema existente de confirmação do executor.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional

from ..models.conversation_state import (
    ClarificationRequest,
    ClarificationType
)

logger = logging.getLogger(__name__)


class ClarificationService:
    """
    Service para gerenciar clarificações e confirmações.
    """
    
    MAX_RESULTS_WITHOUT_CLARIFICATION = 5
    
    def detect_ambiguities_in_results(
        self,
        api_results: Dict[str, Any],
        intent: Dict[str, Any]
    ) -> List[ClarificationRequest]:
        """
        Detecta ambiguidades nos resultados que precisam de clarificação.
        
        Retorna lista de ClarificationRequest para cada ambiguidade encontrada.
        """
        clarifications = []
        
        for step_name, result in api_results.items():
            if not isinstance(result, dict):
                continue
            
            data = result.get("data", [])
            entity_type = result.get("entity_type", "")
            
            # Múltiplas entidades encontradas
            if len(data) > 1:
                clarif = self._create_entity_selection(
                    step_name=step_name,
                    entity_type=entity_type,
                    items=data
                )
                if clarif:
                    clarifications.append(clarif)
            
            # Nenhuma entidade encontrada
            elif len(data) == 0 and entity_type:
                clarif = self._create_not_found_clarification(
                    entity_type=entity_type,
                    context={"step": step_name}
                )
                if clarif:
                    clarifications.append(clarif)
        
        return clarifications
    
    def _create_entity_selection(
        self,
        step_name: str,
        entity_type: str,
        items: List[Dict[str, Any]]
    ) -> Optional[ClarificationRequest]:
        """
        Cria clarificação para selecionar entre múltiplas entidades.
        """
        if not items or len(items) <= 1:
            return None
        
        # Limita opções
        max_options = 10
        items_to_show = items[:max_options]
        has_more = len(items) > max_options
        
        # Formata opções
        options = []
        for i, item in enumerate(items_to_show, 1):
            label = self._format_entity_label(item, entity_type)
            options.append({
                "value": item.get("id"),
                "label": f"{i}. {label}",
                "data": item,
                "index": i
            })
        
        entity_name_pt = self._translate_entity(entity_type)
        
        question_parts = [f"Encontrei {len(items)} {entity_name_pt}."]
        
        if has_more:
            question_parts.append(f"Mostrando os primeiros {max_options}:")
        else:
            question_parts.append("Qual você quer usar?")
        
        question_parts.append("")
        question_parts.extend([opt["label"] for opt in options])
        
        if has_more:
            question_parts.append(f"\n... e mais {len(items) - max_options}")
            question_parts.append("\n💡 Seja mais específico para reduzir resultados")
        
        return ClarificationRequest(
            id=f"select_{entity_type}_{uuid.uuid4().hex[:8]}",
            type=ClarificationType.CHOICE_REQUIRED,
            question="\n".join(question_parts),
            context={
                "step_name": step_name,
                "entity_type": entity_type,
                "total_count": len(items)
            },
            options=options,
            answer_field=f"{step_name}_selected",
            optional=False
        )
    
    def _create_not_found_clarification(
        self,
        entity_type: str,
        context: Dict[str, Any]
    ) -> Optional[ClarificationRequest]:
        """
        Cria clarificação quando nenhuma entidade é encontrada.
        """
        entity_name_pt = self._translate_entity(entity_type)
        
        return ClarificationRequest(
            id=f"not_found_{entity_type}_{uuid.uuid4().hex[:8]}",
            type=ClarificationType.AMBIGUOUS_ENTITY,
            question=(
                f"❌ Não encontrei nenhum(a) {entity_name_pt} com esses critérios.\n\n"
                f"Você pode:\n"
                f"1. Tentar com termos diferentes\n"
                f"2. Cancelar esta operação"
            ),
            context=context,
            answer_field="user_action",
            default_answer="cancel",
            optional=False
        )
    
    def _format_entity_label(self, item: Dict[str, Any], entity_type: str) -> str:
        """
        Formata label legível para uma entidade.
        """
        if entity_type == "candidates":
            name = item.get("name", "Sem nome")
            email = item.get("email", "")
            role = item.get("role_name", "")
            parts = [name]
            if role:
                parts.append(f"({role})")
            if email:
                parts.append(f"- {email}")
            return " ".join(parts)
        
        elif entity_type == "jobs":
            title = item.get("title", "Sem título")
            company = item.get("company_name", "")
            location = item.get("city", "")
            parts = [title]
            if company:
                parts.append(f"@ {company}")
            if location:
                parts.append(f"- {location}")
            return " ".join(parts)
        
        elif entity_type == "selective_processes":
            name = item.get("name", "")
            job = item.get("job_title", "")
            status = item.get("status_name", "")
            parts = [name or "Processo"]
            if job:
                parts.append(f"(Vaga: {job})")
            if status:
                parts.append(f"[{status}]")
            return " ".join(parts)
        
        # Fallback
        name = item.get("name") or item.get("title") or f"Item {item.get('id')}"
        return name
    
    def _translate_entity(self, entity_type: str) -> str:
        """Traduz nome de entidade para português."""
        translations = {
            "candidates": "candidato(s)",
            "jobs": "vaga(s)",
            "applies": "candidatura(s)",
            "selective_processes": "processo(s) seletivo(s)"
        }
        return translations.get(entity_type, entity_type)
    
    def format_for_user(self, clarifications: List[ClarificationRequest]) -> str:
        """
        Formata clarificações para apresentar ao usuário.
        """
        if not clarifications:
            return ""
        
        lines = ["🤔 Preciso de mais informações:\n"]
        
        for i, clarif in enumerate(clarifications, 1):
            lines.append(f"{clarif.question}")
            
            if clarif.type == ClarificationType.CHOICE_REQUIRED:
                lines.append("\n📝 Digite o número da opção escolhida.")
            
            elif clarif.type == ClarificationType.CONFIRMATION_NEEDED:
                lines.append("\n✅ Digite 'sim' para confirmar ou 'não' para cancelar.")
            
            lines.append("")
        
        return "\n".join(lines)

```

---

## 📄 src/services/embedding_service.py

```python
"""
Embedding Service - Gera embeddings usando Google Gemini text-embedding-004.
"""

import logging
from typing import List
import os
import google.generativeai as genai

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service para gerar embeddings de texto usando Google Gemini.
    
    Usa text-embedding-004 (768 dimensions) por ser:
    - Gratuito e sem rate limits agressivos
    - Suficientemente preciso para documentação técnica
    - Integrado com o mesmo Gemini usado no projeto
    - Compatível com índice HNSW
    """
    
    MODEL = "models/text-embedding-004"
    DIMENSIONS = 768
    
    def __init__(self, api_key: str = None):
        """
        Inicializa o serviço de embeddings.
        
        Args:
            api_key: Gemini API key (usa GEMINI_API_KEY env var se None)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada")
        
        genai.configure(api_key=self.api_key)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Gera embedding para um texto.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o vetor de embedding (768 dimensões)
        """
        try:
            result = genai.embed_content(
                model=self.MODEL,
                content=text,
                task_type="retrieval_document"
            )
            
            embedding = result['embedding']
            logger.debug(f"Embedding gerado: {len(embedding)} dimensões")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Gera embeddings para múltiplos textos em lotes.
        
        Args:
            texts: Lista de textos
            batch_size: Tamanho do lote (Gemini suporta até 100)
            
        Returns:
            Lista de embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processando lote {i//batch_size + 1}: {len(batch)} textos")
            
            try:
                # Gemini suporta batch de embeddings
                result = genai.embed_content(
                    model=self.MODEL,
                    content=batch,
                    task_type="retrieval_document"
                )
                
                # Para batch, result['embedding'] é uma lista de embeddings
                if isinstance(result['embedding'][0], list):
                    embeddings = result['embedding']
                else:
                    # Se for single, wrappa em lista
                    embeddings = [result['embedding']]
                
                all_embeddings.extend(embeddings)
                
            except Exception as e:
                logger.error(f"Erro no lote {i//batch_size + 1}: {e}")
                raise
        
        return all_embeddings


```

---

## 📄 src/services/endpoint_loader.py

```python
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class EndpointLoader:

    def __init__(self, docs_path: Optional[Path] = None):
        if docs_path is None:
            docs_path = Path(__file__).parent.parent.parent / "documentation"

        self.docs_path = docs_path
        self._cache = {}

    def load(self, endpoint_id: str) -> Dict[str, Any]:
        if endpoint_id in self._cache:
            return self._cache[endpoint_id]

        yaml_file = self.docs_path / f"{endpoint_id}.yml"

        if not yaml_file.exists():
            raise ValueError(
                f"Documentação não encontrada para endpoint '{endpoint_id}'. "
                f"Esperado: {yaml_file}"
            )

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self._validate_config(config, endpoint_id)
            self._cache[endpoint_id] = config

            logger.debug(f"Loaded endpoint config: {endpoint_id}")
            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Erro ao parsear YAML {endpoint_id}: {e}")

    def _validate_config(self, config: Dict, endpoint_id: str) -> None:
        if "endpoint" not in config:
            raise ValueError(f"Config {endpoint_id} não tem chave 'endpoint'")

        endpoint = config["endpoint"]

        if "method" not in endpoint:
            raise ValueError(f"Config {endpoint_id} não tem 'endpoint.method'")

        if "path" not in endpoint:
            raise ValueError(f"Config {endpoint_id} não tem 'endpoint.path'")

        if endpoint["method"] not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            raise ValueError(
                f"Método inválido em {endpoint_id}: {endpoint['method']}")

    def get_method(self, endpoint_id: str) -> str:
        config = self.load(endpoint_id)
        return config["endpoint"]["method"]

    def get_path(self, endpoint_id: str) -> str:
        config = self.load(endpoint_id)
        return config["endpoint"]["path"]

    def get_query_contract(self, endpoint_id: str) -> Dict[str, Any]:
        config = self.load(endpoint_id)
        return config.get("query_contract", {})

    def get_body_contract(self, endpoint_id: str) -> Dict[str, Any]:
        config = self.load(endpoint_id)
        return config.get("body_contract", {})

    def is_search_endpoint(self, endpoint_id: str) -> bool:
        return endpoint_id.endswith("_search")

    def is_show_endpoint(self, endpoint_id: str) -> bool:
        return endpoint_id.endswith("_show")

    def clear_cache(self) -> None:
        self._cache.clear()

```

---

## 📄 src/services/evaluation_service.py

```python
"""
Evaluation Service - AI-powered candidate evaluation.
Handles prompt building, Gemini API calls, and response normalization.
"""

import json
import re
import time
import random
import logging
from typing import Dict, Any, Optional, List

import google.generativeai as genai

from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for evaluating candidate responses using Gemini AI."""
    
    def __init__(self):
        """Initialize evaluation service with Gemini model."""
        settings = get_settings()
        
        genai.configure(api_key=settings.gemini.api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini.model,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # More deterministic for evaluations
                max_output_tokens=2500,
            )
        )
        
        self.max_retries = 3
        self.initial_backoff = 0.8
        
        logger.info(f"✅ Evaluation Service initialized with model: {settings.gemini.model}")
    
    def evaluate_candidate_response(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluate candidate response and generate AI feedback.
        
        Args:
            payload: Request payload containing:
                - job_description: Job description text
                - question_text: Current question
                - expected_response: Expected answer (optional)
                - candidate_answer: Candidate's response
                - history: Conversation history
                - next_question_hint: Suggestion for next question
                - style: Interview style settings
                - is_introduction: Whether this is the first interaction
                
        Returns:
            Dictionary with evaluation results or None on error.
        """
        try:
            # Build prompt
            prompt = self._build_prompt(payload)
            
            # Call Gemini with retries
            ai_response = self._call_gemini_with_retry(prompt)
            
            # Normalize response
            normalized = self._normalize_ai_response(ai_response, payload)
            
            # Prepare result
            result = {
                "original_payload": payload,
                "ai_response": normalized,
                "chatbot_channel": payload.get("chatbot_channel")
            }
            
            result["is_issue_report"] = bool(result.get("ai_response", {}).get("is_issue_report", False))
            logger.info(f"✅ Evaluation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}", exc_info=True)
            return self._create_fallback_response(payload, str(e))
    
    def _build_prompt(self, payload: Dict[str, Any]) -> str:
        """Build evaluation prompt for Gemini."""
        job_description = payload.get("job_description", "N/A")
        question_text = payload.get("question_text", "N/A")
        expected = payload.get("expected_response")
        candidate_answer = payload.get("candidate_answer", "N/A")
        history = payload.get("history", [])
        hint = payload.get("next_question_hint")
        style = payload.get("style", {"persona": "cordial e técnico", "pt_br": True})
        
        pt = "PT-BR" if style.get("pt_br", True) else "Português"
        persona = style.get("persona", "cordial e técnico")
        
        # Next question handling
        hint_line = ""
        next_question_text = ""
        if isinstance(hint, dict) and hint.get("id") and hint.get("text"):
            hint_line = f'\nSugestão de próxima pergunta: id={hint["id"]} | text="{hint["text"]}"'
            next_question_text = hint["text"]
        
        # Introduction or continuation
        intro_line = ""
        if payload.get("is_introduction"):
            intro_line = f"""
        Esta é a PRIMEIRA interação da entrevista.
        - Se a resposta for sim, faça com que o chat_ack tenha uma mensagem acolhedora e amigável (ex: "Ótimo, então vamos começar!", "Perfeito, seja bem-vindo(a)!").
        - Em seguida, faça um breve resumo sobre a vaga usando a Descrição da Vaga fornecida, mantendo o tom humano e profissional.
        - Ainda em chat_ack, faça uma transição natural para a primeira pergunta, demonstrando empatia. A pergunta deve ser exatamente essa: {next_question_text}.
        - NÃO analise nenhuma resposta anterior.
        - Se o candidato disser que não pode responder agora, responda de forma empática e envie a pergunta mesmo assim para que ele responda quando for possível.
        """
        else:
            intro_line = f"""
        Esta NÃO é a primeira interação.
        - Faça com que o chat_ack comece com uma frase amigável como "Muito bom, agora vamos para a próxima pergunta!".
        - Faça uma transição natural para a próxima pergunta, demonstrando empatia. A próxima pergunta é exatamente essa: {next_question_text}.
        """
        
        # History
        hist_lines = []
        for t in history[-10:]:
            r, c = t.get("role"), t.get("content")
            if r and c:
                hist_lines.append(f"- {r}: {c}")
        
        expected_line = f"\nRespostas esperadas (referência): {expected}" if expected else ""
        
        return f"""
Você é um entrevistador técnico {persona} e fala em {pt}.
Seu objetivo é conduzir uma entrevista de forma natural e empática, mantendo clareza e profissionalismo.
TAREFA: Avalie a resposta do candidato para a PERGUNTA ATUAL. 
Depois decida se precisa de FOLLOW-UP; se não, avance para a PRÓXIMA PERGUNTA (use a sugestão do sistema se existir).

{intro_line}

INSTRUÇÕES DE ESTILO:
- Seja humano, breve e gentil.
- Use expressões leves e naturais como:
  - "Ótimo, então vamos começar..."
  - "Perfeito, entendi seu ponto."
  - "Legal! Agora me conte um pouco mais sobre..."
- Nunca soe como um robô ou formulário.

SE O CANDIDATO FIZER UMA PERGUNTA SOBRE A VAGA:
- Use o texto de "Descrição da Vaga" para responder, se possível.
- Responda de forma útil, em até 2 frases.
- Em seguida, formule uma nova pergunta relacionada à entrevista (para retomar o fluxo).
- Nunca invente informações que não estão na descrição da vaga.

RETORNE EXATAMENTE UM JSON com os seguintes campos:
{{
  "score": <float entre 0 e 1 com 3 casas decimais. Exemplo: 0.775>,
  "feedback_for_recruiter": "<resumo curto e objetivo>",
  "is_answer_satisfactory": <true|false>,
  "chat_ack": "<mensagem humana contendo um comentário breve sobre a resposta do candidato seguido de uma transição para a próxima pergunta: {question_text}>",
  "responded": <true|false>,
  "changed_subject": <true|false>,
  "response_to_candidate": "<resposta curta se ele perguntou algo; senão null>",
  "followup_needed": <true|false>,
  "followup_question": "<mensagem humana contendo um comentário breve sobre a resposta do candidato seguido uma pergunta adicional se followup_needed for true>",
  "next_question": <se followup_needed=false, {{
    "id": <int|str>,
    "text": "<texto>"
  }}; senão null>,
  "end": <true se acabou>,
  "interested_job": <Se a mensagem dá a entender que o candidato não está interessado na vaga retorne False; senão True>,
  "interested_job_msg": "<Se interested_job for false, use exatamente: 'Sem problema. Obrigado pelo retorno. Até mais!'; senão null>",
  "is_issue_report": <INTERPRETE a intenção do candidato: true APENAS se ele estiver solicitando ajuda, reportando problema ou pedindo atendimento humano; senão false. Use o contexto da conversa para decidir.>
}}

CONTEXTOS:
Descrição da Vaga:
{job_description}

Histórico recente:
{chr(10).join(hist_lines) if hist_lines else "(vazio)"}{hint_line}{expected_line}

Pergunta atual:
{question_text}

Resposta do candidato:
\"\"\"{candidate_answer}\"\"\"

Lembre-se:
- Se for a primeira interação, comece com uma saudação humana.
- Se o candidato mudar de assunto, reconheça brevemente e redirecione.
- Sempre responda com JSON válido, sem markdown.
- o chat_ack sempre deve conter uma transição natural para a próxima pergunta({question_text}) se o is_answer_satisfactory for true.

NOTAS:
- Use followup_needed=true **somente** se a resposta for vaga, superficial, incompleta ou se o candidato não respondeu plenamente à pergunta.
- Se a resposta for completa, relevante e direta → followup_needed=false e preencha next_question com a próxima pergunta (ou use a sugestão do sistema).
- Se o candidato fizer uma pergunta, responda-a em response_to_candidate (sem repetir o texto dele).
- Caso não precise follow-up, tente usar a dica de próxima pergunta do sistema (next_question_hint). Se não houver, end=true.
- Se o score for >=0.5 então o is_answer_satisfactory=true.

REPORTE DE PROBLEMAS (is_issue_report) — INTERPRETE A INTENÇÃO:
- Retorne is_issue_report=true APENAS quando o candidato claramente solicitar ajuda, reportar um problema ou pedir atendimento humano.
- Use o CONTEXTO da conversa para decidir. Exemplos que indicam reporte: "AJUDA", "#PROBLEMA", "PARAR", "HUMANO", "HELP", "preciso de ajuda", "quero falar com alguém", "não entendi nada", "estou com problema".
- NÃO retorne true quando a palavra aparecer em outro contexto (ex: "trabalho com recursos humanos", "ajudei no projeto", "separar tarefas"). A intenção deve ser de reportar problema, não de responder à entrevista.
- Se is_issue_report=true, o sistema pausará a LIA e notificará o time de suporte.

RETORNE APENAS O JSON.
""".strip()
    
    def _call_gemini_with_retry(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API with exponential backoff retry."""
        backoff = self.initial_backoff
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.model.generate_content(prompt)
                
                if not response or not response.text:
                    raise ValueError("Empty response from Gemini")
                
                return self._extract_json(response.text)
                
            except Exception as e:
                if attempt >= self.max_retries:
                    raise
                
                logger.warning(
                    f"⚠️ Gemini API call failed (attempt {attempt}/{self.max_retries}): {e}. "
                    f"Retrying in {backoff:.1f}s"
                )
                time.sleep(backoff)
                backoff *= 2.0
        
        return {}  # Never reached
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response."""
        text = (text or "").strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Remove code fences
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try regex extraction
        import re
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError("Failed to extract valid JSON from Gemini response")
    
    def _normalize_ai_response(self, ai: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize AI response to standard format."""
        out: Dict[str, Any] = {}
        
        # Score
        out["score"] = self._clamp_score(ai.get("score", 0.000))
        out["is_answer_satisfactory"] = bool(
            ai.get("is_answer_satisfactory", out["score"] >= 0.500)
        )
        out["feedback_for_recruiter"] = ai.get("feedback_for_recruiter", "")
        
        # Chat acknowledgment
        ack = str(ai.get("chat_ack", "")).strip()
        out["chat_ack"] = ack if ack else self._fallback_ack()
        
        # Response status
        responded = ai.get("responded")
        if responded is None:
            responded = out["score"] >= 0.500
        out["responded"] = bool(responded)
        
        changed = ai.get("changed_subject")
        if changed is None:
            changed = not out["responded"]
        out["changed_subject"] = bool(changed)
        
        rtc = ai.get("response_to_candidate")
        out["response_to_candidate"] = rtc if rtc is None or str(rtc).strip() else None
        
        # Follow-up logic
        follow = bool(ai.get("followup_needed", False))
        
        if ai.get("is_answer_satisfactory") is True or out["score"] >= 0.600:
            follow = False
        
        out["followup_needed"] = follow
        out["followup_question"] = (
            str(ai.get("followup_question")).strip() if follow else None
        )
        
        # Next question / end of interview
        out["next_question"] = None
        out["end"] = False
        
        if not follow:
            next_q = ai.get("next_question")
            if not next_q:
                hint = payload.get("next_question_hint")
                if hint and hint.get("id") and hint.get("text"):
                    next_q = {"id": hint["id"], "text": hint["text"]}
            
            if next_q and isinstance(next_q, dict) and next_q.get("id") and next_q.get("text"):
                out["next_question"] = {"id": next_q["id"], "text": next_q["text"]}
                out["end"] = False
            else:
                out["end"] = True
        
        # Job interest
        out["interested_job"] = ai.get("interested_job", None)
        if out["interested_job"] is False:
            out["interested_job_msg"] = "Sem problema. Obrigado pelo retorno. Até mais!"
        else:
            out["interested_job_msg"] = None

        out["is_issue_report"] = bool(ai.get("is_issue_report", False))
        
        return out
    
    def _create_fallback_response(
        self, 
        payload: Dict[str, Any], 
        error_msg: str
    ) -> Dict[str, Any]:
        """Create fallback response when evaluation fails."""
        hint = payload.get("next_question_hint")
        
        ai_norm = {
            "score": 0.000,
            "is_answer_satisfactory": False,
            "feedback_for_recruiter": f"Falha temporária na avaliação: {error_msg}. Reavaliar manualmente.",
            "chat_ack": self._fallback_ack(),
            "responded": False,
            "changed_subject": True,
            "response_to_candidate": None,
            "followup_needed": False,
            "followup_question": None,
            "next_question": (
                {"id": hint["id"], "text": hint["text"]} 
                if hint and hint.get("id") and hint.get("text") 
                else None
            ),
            "end": False if (hint and hint.get("id") and hint.get("text")) else True,
            "interested_job": True,
            "interested_job_msg": None
        }
        
        return {
            "original_payload": payload,
            "ai_response": ai_norm,
            "chatbot_channel": payload.get("chatbot_channel"),
            "is_issue_report": bool(ai_norm.get("is_issue_report", False))
        }
    
    @staticmethod
    def _clamp_score(x: Any) -> float:
        """Clamp score to [0.0, 1.0] range."""
        try:
            v = float(x)
        except (ValueError, TypeError):
            return 0.000
        return max(0.000, min(1.000, v))
    
    @staticmethod
    def _fallback_ack() -> str:
        """Generate fallback acknowledgment message."""
        return random.choice([
            "Boa!",
            "Entendi.",
            "Show!",
            "Legal.",
            "Hmm, bom ponto."
        ])

```

---

## 📄 src/services/memory_service.py

```python
"""
Memory Service for storing and retrieving conversation history.
Implements hybrid memory with PostgreSQL storage.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from ..config.settings import PostgresConfig


logger = logging.getLogger(__name__)


class MemoryService:
    """
    Service for managing conversation memory in PostgreSQL.
    Follows Repository pattern for data access.
    """
    
    def __init__(self, config: PostgresConfig):
        """
        Initialize memory service with database configuration.
        
        Args:
            config: PostgreSQL configuration.
        """
        self.config = config
        self._ensure_tables()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            Database connection.
        """
        conn = None
        try:
            conn = psycopg2.connect(self.config.connection_string)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _ensure_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS conversation_history (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255),
            question TEXT NOT NULL,
            answer TEXT,
            intent JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS query_metrics (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            execution_time_ms FLOAT,
            api_calls INTEGER,
            total_records INTEGER,
            success BOOLEAN,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_conversation_session_id 
            ON conversation_history (session_id);
        CREATE INDEX IF NOT EXISTS idx_conversation_user_id 
            ON conversation_history (user_id);
        CREATE INDEX IF NOT EXISTS idx_conversation_created_at 
            ON conversation_history (created_at);
            
        CREATE INDEX IF NOT EXISTS idx_metrics_session_id 
            ON query_metrics (session_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_created_at 
            ON query_metrics (created_at);
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create tables
                    cursor.execute(create_tables_sql)
                    # Create indexes
                    cursor.execute(create_indexes_sql)
            logger.info("✓ Database tables and indexes created/verified")
        except Exception as e:
            logger.warning(f"Could not create tables/indexes: {e}")
    
    def save_conversation(
        self,
        session_id: str,
        question: str,
        answer: str,
        intent: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        Save a conversation turn to memory.
        
        Args:
            session_id: Unique session identifier.
            question: User's question.
            answer: System's answer.
            intent: Identified intent (optional).
            metadata: Additional metadata (optional).
            user_id: User identifier (optional).
            
        Returns:
            ID of the saved conversation record.
        """
        insert_sql = """
        INSERT INTO conversation_history 
        (session_id, user_id, question, answer, intent, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        insert_sql,
                        (
                            session_id,
                            user_id,
                            question,
                            answer,
                            psycopg2.extras.Json(intent) if intent else None,
                            psycopg2.extras.Json(metadata) if metadata else None
                        )
                    )
                    conversation_id = cursor.fetchone()[0]
            
            logger.debug(f"Saved conversation {conversation_id} for session {session_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            raise
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier.
            limit: Maximum number of records to retrieve.
            
        Returns:
            List of conversation records.
        """
        select_sql = """
        SELECT id, session_id, user_id, question, answer, intent, metadata, created_at
        FROM conversation_history
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(select_sql, (session_id, limit))
                    records = cursor.fetchall()
            
            logger.debug(f"Retrieved {len(records)} records for session {session_id}")
            return [dict(record) for record in records]
            
        except Exception as e:
            logger.error(f"Failed to retrieve conversation history: {e}")
            return []
    
    def save_metrics(
        self,
        session_id: str,
        execution_time_ms: float,
        api_calls: int,
        total_records: int,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """
        Save query execution metrics.
        
        Args:
            session_id: Session identifier.
            execution_time_ms: Execution time in milliseconds.
            api_calls: Number of API calls made.
            total_records: Total records processed.
            success: Whether query was successful.
            error_message: Error message if failed (optional).
        """
        insert_sql = """
        INSERT INTO query_metrics 
        (session_id, execution_time_ms, api_calls, total_records, success, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        insert_sql,
                        (session_id, execution_time_ms, api_calls, total_records, success, error_message)
                    )
            
            logger.debug(f"Saved metrics for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def get_recent_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent queries across all sessions.
        
        Args:
            limit: Maximum number of queries to retrieve.
            
        Returns:
            List of recent queries.
        """
        select_sql = """
        SELECT ch.question, ch.answer, ch.created_at, qm.execution_time_ms, qm.success
        FROM conversation_history ch
        LEFT JOIN query_metrics qm ON ch.session_id = qm.session_id
        ORDER BY ch.created_at DESC
        LIMIT %s
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(select_sql, (limit,))
                    records = cursor.fetchall()
            
            return [dict(record) for record in records]
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent queries: {e}")
            return []
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier to clear.
        """
        delete_sql = """
        DELETE FROM conversation_history WHERE session_id = %s;
        DELETE FROM query_metrics WHERE session_id = %s;
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(delete_sql, (session_id, session_id))
            
            logger.info(f"Cleared session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

```

---

## 📄 src/services/message_router.py

```python
import logging
from typing import Dict, Any

from src.workflow.graph import create_workflow
from src.domains.orchestrator import DomainOrchestrator
from src.services.ott_service import configure_ott_from_message, get_token_for_callback
from src.utils.timing import RequestTimer, get_timer
import src.domains

logger = logging.getLogger(__name__)


class MessageRouter:

    def __init__(self):
        self.workflow_orchestrator = create_workflow()
        self.domain_orchestrator = DomainOrchestrator()

    def route(self, message: Dict[str, Any]) -> Dict[str, Any]:
        timer = RequestTimer()
        timer.start()
        timer.step("initialization")

        configure_ott_from_message(message)

        question = message.get("question", "")
        domain = message.get("domain")
        context_data = message.get("context_data", {})

        logger.info(
            f"Routing message | Domain: {domain or 'global'} | Question: {question[:100]}")

        if domain:
            result = self._process_domain_query(domain, question, context_data)
        else:
            result = self._process_global_query(question)

        result["auth_token"] = get_token_for_callback()

        timing_report = timer.finish()
        result["timing"] = timing_report.to_dict()

        return result

    def _process_domain_query(
        self,
        domain: str,
        question: str,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        try:
            response = self.domain_orchestrator.process_query(
                domain_id=domain,
                user_query=question,
                context_data=context_data
            )

            return {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "suggestions": response.suggestions,
                "needs_confirmation": response.needs_confirmation,
                "confirmation_message": response.confirmation_message,
                "error": response.error,
                "metadata": {
                    **response.metadata,
                    "mode": "domain",
                    "domain": domain
                }
            }

        except Exception as e:
            logger.error(f"Error in domain query: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"❌ Erro ao processar no domínio {domain}",
                "error": str(e),
                "metadata": {"mode": "domain", "domain": domain}
            }

    def _process_global_query(self, question: str) -> Dict[str, Any]:

        try:
            state = self.workflow_orchestrator.process_query(question)

            processed_data = state.get("processed_data", {})
            summary = processed_data.get("summary", {})

            return {
                "success": state.get("error") is None,
                "message": state.get("final_answer", ""),
                "data": processed_data,
                "needs_confirmation": state.get("needs_confirmation", False),
                "confirmation_request": state.get("confirmation_request"),
                "error": state.get("error"),
                "metadata": {
                    "mode": "global",
                    "api_calls": summary.get("total_api_calls", 0),
                    "total_records": summary.get("total_records", 0)
                }
            }

        except Exception as e:
            logger.error(f"Error in global query: {e}", exc_info=True)
            return {
                "success": False,
                "message": "❌ Erro ao processar sua pergunta",
                "error": str(e),
                "metadata": {"mode": "global"}
            }

```

---

## 📄 src/services/ott_service.py

```python
import logging
from typing import Optional

from src.config.settings import get_settings
from src.services.auth_service import AuthService
from src.utils.token_utils import extract_token_from_dict, validate_jwt_format, mask_token

logger = logging.getLogger(__name__)

_ott_service: Optional["OTTService"] = None


class OTTService:

    def __init__(self):
        settings = get_settings()
        self._auth_service = AuthService(settings.ats_api)
        self._current_ott: Optional[str] = None

    @property
    def auth_service(self) -> AuthService:
        return self._auth_service

    @property
    def current_token(self) -> Optional[str]:
        return self._auth_service.get_current_token()

    @property
    def using_ott(self) -> bool:
        return self._auth_service.using_ott

    def configure_from_message(self, message_data: dict) -> bool:
        token = extract_token_from_dict(message_data)

        if not token:
            logger.debug("No OTT found in message, using credentials auth")
            return False

        if not validate_jwt_format(token):
            logger.warning(
                f"Invalid OTT format in message: {mask_token(token)}")
            return False

        self._current_ott = token
        success = self._auth_service.set_ott(token)

        if success:
            logger.info(f"OTT configured from message: {mask_token(token)}")

        return success

    def configure_token(self, token: str) -> bool:
        if not token:
            return False

        return self._auth_service.set_ott(token)

    def get_auth_header(self) -> dict[str, str]:
        return self._auth_service.get_auth_header()

    def invalidate(self) -> None:
        self._current_ott = None
        self._auth_service.invalidate()

    def get_token_for_callback(self) -> Optional[str]:
        if self._current_ott:
            return self._current_ott
        return self._auth_service.get_current_token()


def get_ott_service() -> OTTService:
    global _ott_service
    if _ott_service is None:
        _ott_service = OTTService()
    return _ott_service


def configure_ott_from_message(message_data: dict) -> bool:
    return get_ott_service().configure_from_message(message_data)


def get_auth_header() -> dict[str, str]:
    return get_ott_service().get_auth_header()


def get_token_for_callback() -> Optional[str]:
    return get_ott_service().get_token_for_callback()

```

---

## 📄 src/services/rabbitmq_service.py

```python
"""
RabbitMQ Service for message queue integration.
Handles async communication with Rails backend.
"""

import json
import logging
from typing import Dict, Any, Callable, Optional
import pika
from pika.adapters.blocking_connection import BlockingChannel

from ..config.settings import RabbitMQConfig


logger = logging.getLogger(__name__)


class RabbitMQService:
    """
    Service for RabbitMQ message queue integration.
    Implements publisher-subscriber pattern.
    """

    def __init__(self, config: RabbitMQConfig):
        """
        Initialize RabbitMQ service with configuration.

        Args:
            config: RabbitMQ configuration.
        """
        self.config = config
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[BlockingChannel] = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            # Parse connection URL
            parameters = pika.URLParameters(self.config.url)

            # Create connection
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.config.exchange,
                exchange_type='direct',
                durable=True
            )

            # Declare queue
            self.channel.queue_declare(
                queue=self.config.request_queue,
                durable=True
            )

            # Bind queue to exchange
            self.channel.queue_bind(
                exchange=self.config.exchange,
                queue=self.config.request_queue,
                routing_key=self.config.request_routing_key
            )

            logger.info("Connected to RabbitMQ successfully")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish_message(
        self,
        message: Dict[str, Any],
        routing_key: Optional[str] = None
    ) -> None:
        """
        Publish a message to the exchange.

        Args:
            message: Message payload as dictionary.
            routing_key: Routing key (uses default if not provided).
        """
        if not self.channel:
            self._connect()

        routing_key = routing_key or self.config.request_routing_key

        try:
            # Serialize message to JSON
            message_body = json.dumps(message, ensure_ascii=False)

            # Publish message
            self.channel.basic_publish(
                exchange=self.config.exchange,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )

            logger.debug(f"Published message with routing key: {routing_key}")

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    def consume_messages(
        self,
        callback: Callable[[Dict[str, Any]], None],
        queue: Optional[str] = None
    ) -> None:
        """
        Start consuming messages from queue.

        Args:
            callback: Function to call for each message.
            queue: Queue name (uses default if not provided).
        """
        if not self.channel:
            self._connect()

        queue = queue or self.config.request_queue

        def on_message(ch, method, properties, body):
            """Internal callback wrapper."""
            try:
                # Decode message
                message = json.loads(body.decode('utf-8'))

                # Call user callback
                callback(message)

                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)

                logger.debug(f"Processed message from queue: {queue}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode message: {e}")
                # Reject and requeue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Reject and requeue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        try:
            # Set QoS (process one message at a time)
            self.channel.basic_qos(prefetch_count=1)

            # Start consuming
            self.channel.basic_consume(
                queue=queue,
                on_message_callback=on_message
            )

            logger.info(f"Started consuming from queue: {queue}")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Stopping consumer")
            self.stop_consuming()

        except Exception as e:
            logger.error(f"Error in message consumer: {e}")
            raise

    def stop_consuming(self) -> None:
        """Stop consuming messages."""
        if self.channel:
            self.channel.stop_consuming()
            logger.info("Stopped consuming messages")

    def close(self) -> None:
        """Close connection to RabbitMQ."""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()

            if self.connection and not self.connection.is_closed:
                self.connection.close()

            logger.info("RabbitMQ connection closed")

        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

```

---

## 📄 src/services/rag_service.py

```python
"""
RAG Service - Retrieval-Augmented Generation para documentação de APIs.

Implementa busca híbrida combinando:
1. Busca semântica usando pgvector (embedding similarity)
2. Full-text search usando pg_trgm (keyword matching)
3. Reranking inteligente para combinar os melhores resultados
"""

import logging
from typing import List, Dict, Any, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import json

from ..config.settings import get_settings
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service para retrieval de documentações usando busca híbrida.
    
    Combina busca semântica (vetores) com busca textual (keywords)
    para máxima precisão e recall.
    """
    
    def __init__(self):
        """Inicializa o serviço RAG."""
        settings = get_settings()
        self.embedding_service = EmbeddingService()
        self.conn = psycopg2.connect(
            host=settings.postgres.host,
            port=settings.postgres.port,
            user=settings.postgres.user,
            password=settings.postgres.password,
            database=settings.postgres.database
        )
    
    def retrieve(
        self,
        query: str,
        entities: List[str] = None,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Recupera documentações mais relevantes para a query.
        
        Args:
            query: Query do usuário
            entities: Filtro opcional de entidades (e.g., ['candidates', 'jobs'])
            top_k: Número de resultados a retornar
            use_hybrid: Se True, combina busca semântica + textual
            
        Returns:
            Lista de documentações ranqueadas por relevância
        """
        logger.info(f"Retrieving docs for query: {query[:100]}")
        
        if use_hybrid:
            return self._hybrid_search(query, entities, top_k)
        else:
            return self._semantic_search(query, entities, top_k)
    
    def _semantic_search(
        self,
        query: str,
        entities: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Busca semântica pura usando embeddings.
        
        Usa cosine similarity entre embedding da query e embeddings das docs.
        """
        # Gera embedding da query
        query_embedding = self.embedding_service.embed_text(query)
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Query SQL com operador de similaridade <=>
        sql = """
            SELECT 
                api_id,
                endpoint_id,
                entity_group,
                category,
                method,
                path,
                summary,
                description,
                query_contract,
                body_contract,
                response_handling,
                requires_context,
                provides_context,
                synonyms,
                examples,
                1 - (embedding <=> %s::vector) AS similarity_score
            FROM api_docs
            WHERE status = 'published'
        """
        
        params = [json.dumps(query_embedding)]
        
        # Filtro por entidades
        if entities:
            sql += " AND entity_group = ANY(%s)"
            params.append(entities)
        
        sql += """
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        params.extend([json.dumps(query_embedding), top_k])
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        
        logger.info(f"Semantic search returned {len(results)} results")
        return [dict(row) for row in results]
    
    def _fulltext_search(
        self,
        query: str,
        entities: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Busca textual usando pg_trgm similarity.
        
        Usa trigram similarity para matching flexível de keywords.
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT 
                api_id,
                endpoint_id,
                entity_group,
                category,
                method,
                path,
                summary,
                description,
                query_contract,
                body_contract,
                response_handling,
                requires_context,
                provides_context,
                synonyms,
                examples,
                similarity(search_text, %s) AS text_score
            FROM api_docs
            WHERE status = 'published'
                AND search_text %% %s  -- % operator para trigram matching
        """
        
        params = [query, query]
        
        if entities:
            sql += " AND entity_group = ANY(%s)"
            params.append(entities)
        
        sql += """
            ORDER BY similarity(search_text, %s) DESC
            LIMIT %s
        """
        params.extend([query, top_k])
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        
        logger.info(f"Fulltext search returned {len(results)} results")
        return [dict(row) for row in results]
    
    def _hybrid_search(
        self,
        query: str,
        entities: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Busca híbrida combinando semântica + textual com reranking.
        
        Estratégia:
        1. Busca semântica (top_k * 2 resultados)
        2. Busca textual (top_k * 2 resultados)
        3. Combina e reranqueia usando RRF (Reciprocal Rank Fusion)
        4. Retorna top_k resultados finais
        """
        # Gera embedding da query
        query_embedding = self.embedding_service.embed_text(query)
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Query híbrida em SQL
        # Usa UNION ALL + window functions para combinar os dois rankings
        sql = """
            WITH semantic_results AS (
                SELECT 
                    api_id,
                    1 - (embedding <=> %s::vector) AS semantic_score,
                    ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS semantic_rank
                FROM api_docs
                WHERE status = 'published'
        """
        
        params = [json.dumps(query_embedding), json.dumps(query_embedding)]
        
        if entities:
            sql += " AND entity_group = ANY(%s)"
            params.append(entities)
        
        sql += """
                LIMIT %s
            ),
            text_results AS (
                SELECT 
                    api_id,
                    similarity(search_text, %s) AS text_score,
                    ROW_NUMBER() OVER (ORDER BY similarity(search_text, %s) DESC) AS text_rank
                FROM api_docs
                WHERE status = 'published'
                    AND search_text %% %s
        """
        
        # top_k * 2 para ter overlap entre os dois métodos
        params.extend([top_k * 2, query, query, query])
        
        if entities:
            sql += " AND entity_group = ANY(%s)"
            params.append(entities)
        
        sql += """
                LIMIT %s
            ),
            combined AS (
                SELECT 
                    COALESCE(s.api_id, t.api_id) AS api_id,
                    COALESCE(s.semantic_score, 0) AS semantic_score,
                    COALESCE(t.text_score, 0) AS text_score,
                    COALESCE(s.semantic_rank, 999999) AS semantic_rank,
                    COALESCE(t.text_rank, 999999) AS text_rank,
                    -- RRF (Reciprocal Rank Fusion) score
                    (1.0 / (60 + COALESCE(s.semantic_rank, 999999))) +
                    (1.0 / (60 + COALESCE(t.text_rank, 999999))) AS rrf_score
                FROM semantic_results s
                FULL OUTER JOIN text_results t ON s.api_id = t.api_id
            )
            SELECT 
                d.api_id,
                d.endpoint_id,
                d.entity_group,
                d.category,
                d.method,
                d.path,
                d.summary,
                d.description,
                d.query_contract,
                d.body_contract,
                d.response_handling,
                d.requires_context,
                d.provides_context,
                d.synonyms,
                d.examples,
                c.semantic_score,
                c.text_score,
                c.rrf_score
            FROM combined c
            JOIN api_docs d ON c.api_id = d.api_id
            ORDER BY c.rrf_score DESC
            LIMIT %s
        """
        
        params.extend([top_k * 2, top_k])
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        
        logger.info(f"Hybrid search returned {len(results)} results")
        if results:
            logger.debug(f"Top result: {results[0]['api_id']} "
                        f"(semantic: {results[0].get('semantic_score', 0):.3f}, "
                        f"text: {results[0].get('text_score', 0):.3f}, "
                        f"rrf: {results[0].get('rrf_score', 0):.3f})")
        
        return [dict(row) for row in results]
    
    def get_by_entity_and_action(
        self,
        entities: List[str],
        action: str
    ) -> List[Dict[str, Any]]:
        """
        Busca determinística por entidade e ação.
        
        Útil quando sabemos exatamente o que queremos (e.g., "search candidates").
        
        Args:
            entities: Lista de entidades (e.g., ['candidates'])
            action: Ação (e.g., 'search', 'create', 'update')
            
        Returns:
            Lista de documentações que correspondem
        """
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        sql = """
            SELECT 
                api_id, endpoint_id, entity_group, category,
                method, path, summary, description,
                query_contract, body_contract, response_handling,
                requires_context, provides_context,
                synonyms, examples
            FROM api_docs
            WHERE status = 'published'
                AND entity_group = ANY(%s)
                AND (
                    category = %s
                    OR api_id ILIKE %s
                    OR summary ILIKE %s
                )
            ORDER BY 
                CASE WHEN category = %s THEN 1 ELSE 2 END,
                api_id
        """
        
        action_pattern = f"%{action}%"
        params = [entities, action, action_pattern, action_pattern, action]
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        cursor.close()
        
        logger.info(f"Entity/action search returned {len(results)} results")
        return [dict(row) for row in results]
    
    def format_for_llm(self, docs: List[Dict[str, Any]]) -> str:
        """
        Formata documentações para consumo do LLM.
        
        Cria um texto estruturado e conciso com as informações essenciais.
        
        Args:
            docs: Lista de documentações
            
        Returns:
            Texto formatado para incluir no prompt
        """
        if not docs:
            return "Nenhuma documentação encontrada."
        
        lines = ["# APIs Disponíveis\n"]
        
        for i, doc in enumerate(docs, 1):
            lines.append(f"## {i}. {doc['api_id']}")
            lines.append(f"**Entidade:** {doc['entity_group']}")
            lines.append(f"**Método:** {doc['method']} {doc['path']}")
            lines.append(f"**Resumo:** {doc['summary']}")
            
            if doc.get('description'):
                desc = doc['description'][:300]  # Limita tamanho
                lines.append(f"**Descrição:** {desc}")
            
            # Parâmetros disponíveis
            if doc.get('query_contract'):
                contract = doc['query_contract']
                if isinstance(contract, dict):
                    params = list(contract.keys())
                    lines.append(f"**Parâmetros:** {', '.join(params)}")
            
            # Context requirements
            if doc.get('requires_context'):
                lines.append(f"**Requer:** {', '.join(doc['requires_context'])}")
            
            lines.append("")  # Linha em branco
        
        return "\n".join(lines)
    
    def __del__(self):
        """Cleanup connection."""
        if hasattr(self, 'conn'):
            self.conn.close()

```

---

## 📄 src/tools/__init__.py

```python
"""
Dynamic Tool System for AI Agent

This module provides a YAML-driven architecture for registering and executing
tools without modifying Python code.
"""

from .contracts import (
    ToolCategory,
    ToolConfig,
    ExecutionContext,
    ExecutionResult,
    FormattedResponse
)
from .registry import ToolRegistry
from .executor import ExecutorFactory, HttpExecutor, WorkflowExecutor
from .formatter import ResponseFormatter
from .hooks import HookRegistry, PreHook, PostHook

__all__ = [
    # Core types
    "ToolCategory",
    "ToolConfig",
    "ExecutionContext",
    "ExecutionResult",
    "FormattedResponse",
    # Registry
    "ToolRegistry",
    # Executors
    "ExecutorFactory",
    "HttpExecutor",
    "WorkflowExecutor",
    # Formatting
    "ResponseFormatter",
    # Hooks
    "HookRegistry",
    "PreHook",
    "PostHook",
]

```

---

## 📄 src/tools/contracts.py

```python
"""
Core contracts and types for the dynamic tool system.

This module defines the fundamental types used across the tool system,
following the Interface Segregation and Dependency Inversion principles.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Protocol
from enum import Enum


class ToolCategory(Enum):
    """Categories of tools based on operation type."""
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    WORKFLOW = "workflow"
    SHOW = "show"


@dataclass(frozen=True)
class ToolConfig:
    """
    Immutable configuration for a tool loaded from YAML.
    
    This is the single source of truth for tool behavior.
    Uses frozen dataclass for immutability and thread-safety.
    """
    # Identity
    id: str
    endpoint_id: str
    entity_group: str
    
    # HTTP config
    method: str
    path: str
    category: ToolCategory
    
    # Documentation
    summary: str = ""
    description: str = ""
    
    # Context management
    requires_context: tuple[str, ...] = field(default_factory=tuple)
    provides_context: Dict[str, str] = field(default_factory=dict)
    
    # Contracts
    query_contract: Dict[str, Any] = field(default_factory=dict)
    body_contract: Dict[str, Any] = field(default_factory=dict)
    response_handling: Dict[str, Any] = field(default_factory=dict)
    
    # Workflow
    flow_config: Optional[Dict[str, Any]] = None
    
    # Extensibility
    pre_hooks: tuple[str, ...] = field(default_factory=tuple)
    post_hooks: tuple[str, ...] = field(default_factory=tuple)
    
    # Raw YAML for debugging
    raw_yaml: str = ""


@dataclass
class ExecutionContext:
    """
    Context for tool execution.
    
    Carries authentication, conversation state, and metadata
    through the execution pipeline.
    """
    auth_token: str
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from conversation context."""
        return self.conversation_context.get(key, default)
    
    def update(self, key: str, value: Any) -> None:
        """Update conversation context."""
        self.conversation_context[key] = value
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value


@dataclass
class ExecutionResult:
    """
    Result of tool execution.
    
    Contains raw API response and metadata about the execution.
    """
    raw: str  # JSON string from API
    tool: ToolConfig
    success: bool = True
    error: Optional[str] = None
    is_workflow: bool = False
    step_results: List[Any] = field(default_factory=list)


@dataclass
class FormattedResponse:
    """
    Formatted response ready for presentation.
    
    Contains user-friendly message, structured data, and metadata
    for context updates and next suggestions.
    """
    message: str
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ExecutionStrategy(Protocol):
    """
    Protocol for execution strategies (Strategy Pattern).
    
    Allows different execution implementations (HTTP, Workflow, etc.)
    without coupling to concrete classes.
    """
    def execute(
        self,
        tool: ToolConfig,
        args: Dict,
        ctx: ExecutionContext
    ) -> ExecutionResult:
        """Execute tool with given arguments and context."""
        ...

```

---

## 📄 src/tools/executor.py

```python
"""
Tool Executors - Strategy Pattern for Different Execution Types.

Implements different execution strategies (HTTP, Workflow) that can be
selected at runtime based on tool configuration.
"""

import json
import re
from typing import Dict, Any, List, Callable, Optional

from .contracts import (
    ToolConfig,
    ExecutionContext,
    ExecutionResult,
    ExecutionStrategy
)


class HttpExecutor:
    """
    Execute HTTP API calls.
    
    Handles path parameter substitution, query parameters,
    and request body formatting.
    """
    
    def __init__(self, client_factory: Optional[Callable] = None):
        """
        Initialize HTTP executor.
        
        Args:
            client_factory: Factory function to create API client
        """
        self._client_factory = client_factory or self._default_client
    
    def _default_client(self, token: str):
        """Default client factory using AtsApiClient."""
        from src.clients.api_client import ATSAPIClient
        from config.settings import get_settings
        
        settings = get_settings()
        return ATSAPIClient(
            base_url=settings.ats_api_base_url,
            username=settings.ats_api_username,
            password=settings.ats_api_password
        )
    
    def execute(
        self,
        tool: ToolConfig,
        args: Dict,
        ctx: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute HTTP request.
        
        Args:
            tool: Tool configuration
            args: Arguments for the request
            ctx: Execution context
            
        Returns:
            ExecutionResult with API response
        """
        client = self._client_factory(ctx.auth_token)
        
        # Substitute path parameters
        path = self._substitute_path_params(tool.path, args)
        
        try:
            # Execute based on method
            if tool.method == "GET":
                result = client.get(path, params=args)
            elif tool.method == "POST":
                result = client.post(path, json=args)
            elif tool.method in ("PUT", "PATCH"):
                result = client.put(path, json=args)
            elif tool.method == "DELETE":
                result = client.delete(path)
            else:
                raise ValueError(f"Unsupported method: {tool.method}")
            
            return ExecutionResult(
                raw=json.dumps(result, ensure_ascii=False),
                tool=tool,
                success=True
            )
        except Exception as e:
            return ExecutionResult(
                raw=json.dumps({"error": str(e)}, ensure_ascii=False),
                tool=tool,
                success=False,
                error=str(e)
            )
    
    def _substitute_path_params(self, path: str, args: Dict) -> str:
        """
        Substitute path parameters from arguments.
        
        Supports both :param and {param} syntax.
        Removes substituted params from args dict.
        
        Args:
            path: URL path template
            args: Arguments dict (modified in-place)
            
        Returns:
            Path with substituted parameters
        """
        result = path
        keys_to_remove = []
        
        for key, value in args.items():
            # Try :param syntax
            colon_pattern = f":{key}"
            if colon_pattern in result:
                result = result.replace(colon_pattern, str(value))
                keys_to_remove.append(key)
                continue
            
            # Try {param} syntax
            brace_pattern = f"{{{key}}}"
            if brace_pattern in result:
                result = result.replace(brace_pattern, str(value))
                keys_to_remove.append(key)
        
        # Remove path params from args
        for key in keys_to_remove:
            del args[key]
        
        return result


class WorkflowExecutor:
    """
    Execute multi-step workflows.
    
    Orchestrates multiple tool calls in sequence,
    managing context between steps.
    """
    
    def __init__(self, registry: 'ToolRegistry', http_executor: HttpExecutor):
        """
        Initialize workflow executor.
        
        Args:
            registry: Tool registry for looking up step tools
            http_executor: HTTP executor for individual steps
        """
        from .registry import ToolRegistry
        self._registry = registry
        self._http = http_executor
    
    def execute(
        self,
        tool: ToolConfig,
        args: Dict,
        ctx: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute workflow.
        
        Args:
            tool: Workflow tool configuration
            args: Initial arguments
            ctx: Execution context
            
        Returns:
            ExecutionResult with aggregated results
        """
        if not tool.flow_config:
            raise ValueError(f"Tool {tool.id} has no flow_config")
        
        steps = tool.flow_config.get("steps", [])
        results: List[ExecutionResult] = []
        step_data: Dict[str, Any] = {}
        
        for i, step in enumerate(steps):
            # Evaluate condition
            if not self._evaluate_condition(step.get("condition"), ctx, step_data):
                continue
            
            # Get step tool
            step_tool = self._registry.get(step["tool"])
            if not step_tool:
                print(f"⚠️ Step tool not found: {step['tool']}")
                continue
            
            # Resolve step arguments
            step_args = self._resolve_args(
                step.get("args", {}),
                ctx,
                step_data,
                args
            )
            
            # Execute step
            step_result = self._http.execute(step_tool, step_args, ctx)
            results.append(step_result)
            
            # Store result if configured
            if step.get("store_result"):
                result_name = step["store_result"]
                try:
                    step_data[result_name] = json.loads(step_result.raw)
                except json.JSONDecodeError:
                    step_data[result_name] = {"error": "Invalid JSON"}
            
            # Stop on error if configured
            on_error = step.get("on_error", "stop")
            if not step_result.success and on_error == "stop":
                break
        
        # Aggregate results
        all_success = all(r.success for r in results)
        aggregated_raw = self._aggregate_results(results, tool.flow_config)
        
        return ExecutionResult(
            raw=aggregated_raw,
            tool=tool,
            success=all_success,
            is_workflow=True,
            step_results=results
        )
    
    def _evaluate_condition(
        self,
        condition: Optional[str],
        ctx: ExecutionContext,
        step_data: Dict
    ) -> bool:
        """
        Evaluate step condition.
        
        Args:
            condition: Condition string or None
            ctx: Execution context
            step_data: Data from previous steps
            
        Returns:
            True if condition passes or is None
        """
        if not condition:
            return True
        
        # Simple implementation - in production use safe eval
        # For now, check if referenced data exists
        if "." in condition:
            path = condition.split(".")[0]
            return path in step_data or path in ctx.conversation_context
        
        return True
    
    def _resolve_args(
        self,
        args: Dict,
        ctx: ExecutionContext,
        step_data: Dict,
        initial_args: Dict
    ) -> Dict:
        """
        Resolve argument placeholders.
        
        Supports:
        - {context.field} - from conversation context
        - {step_result.field} - from previous step
        - {args.field} - from initial arguments
        
        Args:
            args: Template arguments
            ctx: Execution context
            step_data: Data from previous steps
            initial_args: Initial workflow arguments
            
        Returns:
            Resolved arguments
        """
        resolved = {}
        
        for key, value in args.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                path = value[1:-1]
                resolved_value = self._resolve_path(path, ctx, step_data, initial_args)
                if resolved_value is not None:
                    resolved[key] = resolved_value
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_path(
        self,
        path: str,
        ctx: ExecutionContext,
        step_data: Dict,
        initial_args: Dict
    ) -> Any:
        """
        Resolve a dotted path to a value.
        
        Args:
            path: Dotted path (e.g., "context.job_id")
            ctx: Execution context
            step_data: Previous step results
            initial_args: Initial arguments
            
        Returns:
            Resolved value or None
        """
        parts = path.split(".")
        
        # Determine source
        if parts[0] == "context":
            source = ctx.conversation_context
            parts = parts[1:]
        elif parts[0] == "args":
            source = initial_args
            parts = parts[1:]
        else:
            # Assume it's a step result name
            source = step_data.get(parts[0], {})
            parts = parts[1:]
        
        # Navigate path
        current = source
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part == "*":
                # Special case: extract field from all items
                return current
            else:
                return None
        
        return current
    
    def _aggregate_results(
        self,
        results: List[ExecutionResult],
        flow_config: Dict
    ) -> str:
        """
        Aggregate step results.
        
        Args:
            results: List of step results
            flow_config: Workflow configuration
            
        Returns:
            JSON string with aggregated results
        """
        strategy = flow_config.get("result_aggregation", {}).get("strategy", "all")
        
        if strategy == "last":
            return results[-1].raw if results else "{}"
        
        elif strategy == "merge":
            # Merge all results into one object
            merged = {}
            for i, result in enumerate(results):
                try:
                    data = json.loads(result.raw)
                    merged[f"step_{i}"] = data
                except json.JSONDecodeError:
                    merged[f"step_{i}"] = {"error": "Invalid JSON"}
            return json.dumps(merged, ensure_ascii=False)
        
        else:  # "all"
            return json.dumps(
                [result.raw for result in results],
                ensure_ascii=False
            )


class ExecutorFactory:
    """
    Factory for creating appropriate executor for a tool.
    
    Implements Factory Pattern to decouple tool execution
    from specific executor implementations.
    """
    
    _http: Optional[HttpExecutor] = None
    _workflow: Optional[WorkflowExecutor] = None
    
    @classmethod
    def initialize(cls, registry: 'ToolRegistry') -> None:
        """
        Initialize factory with registry.
        
        Args:
            registry: Tool registry
        """
        cls._http = HttpExecutor()
        cls._workflow = WorkflowExecutor(registry, cls._http)
    
    @classmethod
    def get(cls, tool: ToolConfig) -> ExecutionStrategy:
        """
        Get appropriate executor for tool.
        
        Args:
            tool: Tool configuration
            
        Returns:
            Executor instance
            
        Raises:
            RuntimeError: If factory not initialized
        """
        if cls._http is None or cls._workflow is None:
            raise RuntimeError("ExecutorFactory not initialized. Call initialize() first.")
        
        if tool.flow_config:
            return cls._workflow
        return cls._http

```

---

## 📄 src/tools/formatter.py

```python
"""
Response Formatter - Template Method Pattern for Response Formatting.

Dynamically formats tool execution results based on YAML configuration,
following DRY principle by centralizing all formatting logic.
"""

import json
from typing import Dict, List, Any, Optional

from .contracts import ExecutionResult, FormattedResponse, ToolConfig


class ResponseFormatter:
    """
    Format execution results for presentation.
    
    Uses configuration from tool's response_handling section
    to build user-friendly messages.
    """
    
    def format(self, result: ExecutionResult) -> FormattedResponse:
        """
        Format execution result.
        
        Args:
            result: Raw execution result
            
        Returns:
            Formatted response ready for user
        """
        tool = result.tool
        handling = tool.response_handling
        
        # Handle errors
        if not result.success:
            return self._format_error(result)
        
        # Parse raw response
        try:
            data = json.loads(result.raw) if isinstance(result.raw, str) else result.raw
        except json.JSONDecodeError:
            return FormattedResponse(
                message=f"❌ Erro ao processar resposta",
                data=[],
                metadata={"error": True, "raw": result.raw[:200]}
            )
        
        # Extract items from response
        items = self._extract_items(data, handling.get("list_path", "data"))
        
        # Format each item
        formatted_items = [
            self._format_item(item, handling)
            for item in items[:handling.get("max_records", 30)]
        ]
        
        # Build user message
        message = self._build_message(formatted_items, handling, result, len(items))
        
        # Build metadata with context updates
        metadata = self._build_metadata(data, tool, handling, len(items))
        
        return FormattedResponse(
            message=message,
            data=formatted_items,
            metadata=metadata
        )
    
    def _format_error(self, result: ExecutionResult) -> FormattedResponse:
        """
        Format error response.
        
        Args:
            result: Failed execution result
            
        Returns:
            Error formatted response
        """
        error_msg = result.error or "Erro desconhecido"
        return FormattedResponse(
            message=f"❌ Erro ao executar {result.tool.id}: {error_msg}",
            data=[],
            metadata={"error": True, "error_message": error_msg}
        )
    
    def _extract_items(self, data: Dict, path: str) -> List[Dict]:
        """
        Extract list of items from response using JSON path.
        
        Args:
            data: Response data
            path: Dot-separated path to items (e.g., "data", "results.items")
            
        Returns:
            List of items
        """
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, [])
            else:
                return []
        
        # Ensure we return a list
        if isinstance(current, list):
            return current
        elif current:
            return [current]
        else:
            return []
    
    def _format_item(self, item: Dict, handling: Dict) -> Dict:
        """
        Format a single item.
        
        Extracts configured label fields from item.
        
        Args:
            item: Raw item data
            handling: Response handling configuration
            
        Returns:
            Formatted item with only relevant fields
        """
        label_fields = handling.get("item_label_fields", ["id", "name"])
        formatted = {}
        
        for field in label_fields:
            # Try direct access
            if field in item:
                formatted[field] = item[field]
            # Try attributes (common in JSON:API format)
            elif "attributes" in item and field in item["attributes"]:
                formatted[field] = item["attributes"][field]
            # Try nested access
            elif "." in field:
                value = self._get_nested(item, field)
                if value is not None:
                    formatted[field] = value
        
        return formatted
    
    def _get_nested(self, data: Dict, path: str) -> Any:
        """
        Get nested value from dict.
        
        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., "user.name")
            
        Returns:
            Value or None
        """
        current = data
        for part in path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
    
    def _build_message(
        self,
        items: List[Dict],
        handling: Dict,
        result: ExecutionResult,
        total_count: int
    ) -> str:
        """
        Build user-friendly message.
        
        Args:
            items: Formatted items
            handling: Response handling configuration
            result: Execution result
            total_count: Total number of items (before truncation)
            
        Returns:
            Formatted message
        """
        count = len(items)
        
        # No results
        if count == 0:
            return "ℹ️ Nenhum resultado encontrado."
        
        # Build header
        entity = result.tool.entity_group
        entity_pt = self._translate_entity(entity)
        lines = [f"✅ Encontrado(s) {total_count} {entity_pt}:"]
        
        # Add items
        max_display = handling.get("max_records", 30)
        for item in items[:max_display]:
            label = self._build_item_label(item, handling)
            lines.append(f"  • {label}")
        
        # Add truncation notice
        if total_count > max_display:
            remaining = total_count - max_display
            lines.append(f"  ... e mais {remaining} resultado(s)")
        
        return "\n".join(lines)
    
    def _build_item_label(self, item: Dict, handling: Dict) -> str:
        """
        Build label for a single item.
        
        Args:
            item: Formatted item
            handling: Response handling configuration
            
        Returns:
            Item label string
        """
        label_fields = handling.get("item_label_fields", ["id", "name"])
        
        # Get ID
        item_id = None
        for id_field in handling.get("id_fields", ["id"]):
            if id_field in item:
                item_id = item[id_field]
                break
        
        # Get name/title
        name = None
        for field in label_fields:
            if field in item and field not in handling.get("id_fields", ["id"]):
                name = item[field]
                break
        
        # Build label
        if name and item_id:
            return f"{name} (ID: {item_id})"
        elif name:
            return str(name)
        elif item_id:
            return f"ID: {item_id}"
        else:
            return "Item sem identificação"
    
    def _build_metadata(
        self,
        data: Dict,
        tool: ToolConfig,
        handling: Dict,
        total_count: int
    ) -> Dict:
        """
        Build metadata with context updates.
        
        Args:
            data: Response data
            tool: Tool configuration
            handling: Response handling configuration
            total_count: Total number of items
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "tool_id": tool.id,
            "entity_group": tool.entity_group,
            "total_count": total_count
        }
        
        # Extract fields for context storage
        for field, path in tool.provides_context.items():
            value = self._extract_value(data, path)
            if value is not None:
                metadata[field] = value
        
        # Generate next suggestions
        if handling.get("generate_next_suggestions"):
            metadata["next_suggestions"] = self._generate_suggestions(
                data,
                tool,
                handling,
                total_count
            )
        
        return metadata
    
    def _extract_value(self, data: Dict, path: str) -> Any:
        """
        Extract value using JSON path.
        
        Supports:
        - Simple paths: "data.id"
        - Array extraction: "data[].id"
        - First element: "data[0].id"
        
        Args:
            data: Source data
            path: JSON path
            
        Returns:
            Extracted value or None
        """
        parts = path.split(".")
        current = data
        
        for part in parts:
            # Handle array extraction
            if part.endswith("[]"):
                field = part[:-2]
                if isinstance(current, dict):
                    current = current.get(field, [])
                if isinstance(current, list):
                    # Extract field from all items
                    next_parts = parts[parts.index(part) + 1:]
                    if next_parts:
                        next_field = next_parts[0]
                        return [
                            item.get(next_field)
                            for item in current
                            if isinstance(item, dict)
                        ]
                    return current
            
            # Handle indexed access
            elif "[" in part and part.endswith("]"):
                field, idx_str = part[:-1].split("[")
                idx = int(idx_str)
                if isinstance(current, dict):
                    current = current.get(field, [])
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            
            # Regular access
            else:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
        
        return current
    
    def _generate_suggestions(
        self,
        data: Dict,
        tool: ToolConfig,
        handling: Dict,
        total_count: int
    ) -> List[Dict]:
        """
        Generate next action suggestions.
        
        Args:
            data: Response data
            tool: Tool configuration
            handling: Response handling configuration
            total_count: Total items
            
        Returns:
            List of suggestion objects
        """
        suggestions = []
        max_records = handling.get("max_records", 30)
        
        # Pagination suggestion
        if total_count > max_records:
            suggestions.append({
                "suggestion": "Ver mais resultados",
                "content": "Mostre a próxima página de resultados",
                "metadata": {
                    "action": "next_page"
                }
            })
        
        # Single item detail suggestion
        if total_count == 1:
            items = self._extract_items(data, handling.get("list_path", "data"))
            if items:
                item = items[0]
                item_id = item.get("id")
                if item_id:
                    suggestions.append({
                        "suggestion": "Ver detalhes",
                        "content": f"Mostre detalhes completos deste item",
                        "metadata": {
                            "action": "show_details",
                            "entity_id": item_id
                        }
                    })
        
        return suggestions
    
    def _translate_entity(self, entity: str) -> str:
        """
        Translate entity name to Portuguese.
        
        Args:
            entity: Entity name in English
            
        Returns:
            Entity name in Portuguese
        """
        translations = {
            "candidates": "candidato(s)",
            "jobs": "vaga(s)",
            "applies": "candidatura(s)",
            "selective_processes": "processo(s) seletivo(s)",
            "evaluations": "avaliação(ões)",
        }
        return translations.get(entity, entity)

```

---

## 📄 src/tools/hooks.py

```python
"""
Hook System - Cross-Cutting Concerns for Tool Execution.

Implements pre-hooks and post-hooks for extensibility without
modifying core execution logic (Open/Closed Principle).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from .contracts import ToolConfig, ExecutionContext, ExecutionResult


class Hook(ABC):
    """Base class for all hooks."""
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute hook logic."""
        pass


class PreHook(Hook):
    """
    Hook that runs before tool execution.
    
    Can modify state, validate context, enrich requests, etc.
    """
    
    @abstractmethod
    def run(
        self,
        state: Dict,
        tool: ToolConfig,
        ctx: ExecutionContext
    ) -> Dict:
        """
        Execute pre-hook logic.
        
        Args:
            state: Current agent state
            tool: Tool being executed
            ctx: Execution context
            
        Returns:
            Modified state
        """
        pass


class PostHook(Hook):
    """
    Hook that runs after tool execution.
    
    Can modify results, track analytics, update caches, etc.
    """
    
    @abstractmethod
    def run(
        self,
        result: ExecutionResult,
        state: Dict,
        tool: ToolConfig
    ) -> ExecutionResult:
        """
        Execute post-hook logic.
        
        Args:
            result: Execution result
            state: Current agent state
            tool: Tool that was executed
            
        Returns:
            Modified result
        """
        pass


class HookRegistry:
    """
    Registry for managing hooks.
    
    Allows dynamic registration and execution of hooks
    without modifying core code.
    """
    
    _hooks: Dict[str, Hook] = {}
    
    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a hook.
        
        Usage:
            @HookRegistry.register("my_hook")
            class MyHook(PreHook):
                def run(self, state, tool, ctx):
                    return state
        """
        def decorator(hook_class):
            cls._hooks[name] = hook_class()
            return hook_class
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Optional[Hook]:
        """
        Get hook by name.
        
        Args:
            name: Hook name
            
        Returns:
            Hook instance or None
        """
        return cls._hooks.get(name)
    
    @classmethod
    def run_pre_hooks(
        cls,
        hooks: tuple,
        state: Dict,
        tool: ToolConfig,
        ctx: ExecutionContext
    ) -> Dict:
        """
        Run all pre-hooks in sequence.
        
        Args:
            hooks: Tuple of hook names
            state: Current state
            tool: Tool configuration
            ctx: Execution context
            
        Returns:
            Modified state
        """
        for name in hooks:
            hook = cls.get(name)
            if hook and isinstance(hook, PreHook):
                state = hook.run(state, tool, ctx)
        return state
    
    @classmethod
    def run_post_hooks(
        cls,
        hooks: tuple,
        result: ExecutionResult,
        state: Dict,
        tool: ToolConfig
    ) -> ExecutionResult:
        """
        Run all post-hooks in sequence.
        
        Args:
            hooks: Tuple of hook names
            result: Execution result
            state: Current state
            tool: Tool configuration
            
        Returns:
            Modified result
        """
        for name in hooks:
            hook = cls.get(name)
            if hook and isinstance(hook, PostHook):
                result = hook.run(result, state, tool)
        return result
    
    @classmethod
    def list_hooks(cls) -> list[str]:
        """Get list of registered hook names."""
        return list(cls._hooks.keys())


# ============================================================================
# Built-in Hooks
# ============================================================================

@HookRegistry.register("validate_context")
class ValidateContextHook(PreHook):
    """
    Validate that required context fields are present.
    
    Adds 'missing_context' to state if any required fields are missing.
    """
    
    def run(
        self,
        state: Dict,
        tool: ToolConfig,
        ctx: ExecutionContext
    ) -> Dict:
        """Check for missing required context fields."""
        missing = [
            field
            for field in tool.requires_context
            if not ctx.get(field)
        ]
        
        if missing:
            state["missing_context"] = missing
            state["error_message"] = (
                f"Faltam informações necessárias: {', '.join(missing)}"
            )
        
        return state


@HookRegistry.register("enrich_metadata")
class EnrichMetadataHook(PostHook):
    """
    Add execution metadata to result.
    
    Tracks tool usage, execution time, etc.
    """
    
    def run(
        self,
        result: ExecutionResult,
        state: Dict,
        tool: ToolConfig
    ) -> ExecutionResult:
        """Add metadata about tool execution."""
        # Could add timestamps, user info, etc.
        # For now, just pass through
        return result


@HookRegistry.register("log_execution")
class LogExecutionHook(PostHook):
    """
    Log tool execution for debugging.
    
    Useful for monitoring and troubleshooting.
    """
    
    def run(
        self,
        result: ExecutionResult,
        state: Dict,
        tool: ToolConfig
    ) -> ExecutionResult:
        """Log execution details."""
        status = "✅" if result.success else "❌"
        print(f"{status} Tool executed: {tool.id} ({tool.method} {tool.path})")
        
        if not result.success and result.error:
            print(f"   Error: {result.error}")
        
        return result


@HookRegistry.register("track_analytics")
class TrackAnalyticsHook(PostHook):
    """
    Track tool usage for analytics.
    
    In production, would send to analytics service.
    """
    
    def run(
        self,
        result: ExecutionResult,
        state: Dict,
        tool: ToolConfig
    ) -> ExecutionResult:
        """Track tool usage."""
        # In production: send to analytics service
        # analytics.track("tool_executed", {
        #     "tool_id": tool.id,
        #     "success": result.success,
        #     "entity_group": tool.entity_group
        # })
        return result

```

---

## 📄 src/tools/registry.py

```python
"""
Tool Registry - Single Source of Truth for Tools.

Singleton pattern ensures all parts of the system access the same registry.
Loads YAML configurations and indexes them for fast lookup.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock

from .contracts import ToolConfig, ToolCategory


class ToolRegistry:
    """
    Singleton registry of all available tools.
    
    Thread-safe singleton implementation using double-checked locking.
    Tools are indexed by ID, entity group, and category for efficient lookup.
    """
    
    _instance: Optional['ToolRegistry'] = None
    _lock: Lock = Lock()
    
    def __new__(cls) -> 'ToolRegistry':
        """Ensure only one instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize internal data structures."""
        self._tools: Dict[str, ToolConfig] = {}
        self._by_entity: Dict[str, List[str]] = {}
        self._by_category: Dict[ToolCategory, List[str]] = {}
    
    def register(self, yaml_content: str) -> ToolConfig:
        """
        Register a tool from YAML content.
        
        Args:
            yaml_content: YAML string defining the tool
            
        Returns:
            Parsed and registered ToolConfig
            
        Raises:
            ValueError: If YAML is invalid or missing required fields
        """
        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        
        tool = self._parse_config(config, yaml_content)
        self._tools[tool.id] = tool
        self._index_tool(tool)
        return tool
    
    def register_from_file(self, path: Path) -> ToolConfig:
        """
        Register a tool from YAML file.
        
        Args:
            path: Path to YAML file
            
        Returns:
            Parsed and registered ToolConfig
        """
        with open(path, 'r', encoding='utf-8') as f:
            return self.register(f.read())
    
    def load_all(self, directory: Path) -> int:
        """
        Load all YAML files from a directory.
        
        Args:
            directory: Path to directory containing YAML files
            
        Returns:
            Number of tools loaded
        """
        count = 0
        for yaml_file in directory.glob("*.yml"):
            try:
                self.register_from_file(yaml_file)
                count += 1
            except Exception as e:
                print(f"⚠️ Failed to load {yaml_file.name}: {e}")
        return count
    
    def get(self, tool_id: str) -> Optional[ToolConfig]:
        """
        Get tool by ID.
        
        Args:
            tool_id: Unique tool identifier
            
        Returns:
            ToolConfig if found, None otherwise
        """
        return self._tools.get(tool_id)
    
    def get_by_entity(self, entity: str) -> List[ToolConfig]:
        """
        Get all tools for an entity group.
        
        Args:
            entity: Entity group name (e.g., 'candidates', 'jobs')
            
        Returns:
            List of ToolConfigs for that entity
        """
        tool_ids = self._by_entity.get(entity, [])
        return [self._tools[tid] for tid in tool_ids]
    
    def get_by_category(self, category: ToolCategory) -> List[ToolConfig]:
        """
        Get all tools in a category.
        
        Args:
            category: Tool category
            
        Returns:
            List of ToolConfigs in that category
        """
        tool_ids = self._by_category.get(category, [])
        return [self._tools[tid] for tid in tool_ids]
    
    def all_tools(self) -> List[ToolConfig]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def count(self) -> int:
        """Get total number of registered tools."""
        return len(self._tools)
    
    def _parse_config(self, config: Dict, raw: str) -> ToolConfig:
        """
        Parse YAML config dict into ToolConfig.
        
        Args:
            config: Parsed YAML dictionary
            raw: Original YAML string
            
        Returns:
            ToolConfig instance
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required = ['id', 'entity_group', 'endpoint']
        missing = [f for f in required if f not in config]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        endpoint = config.get("endpoint", {})
        method = endpoint.get("method", "GET").upper()
        context_handling = config.get("context_handling", {})
        
        return ToolConfig(
            id=config["id"],
            endpoint_id=config.get("endpoint_id", config["id"]),
            entity_group=config.get("entity_group", "general"),
            method=method,
            path=endpoint.get("path", "/"),
            category=self._infer_category(method, config),
            summary=config.get("summary", ""),
            description=config.get("description", ""),
            requires_context=tuple(context_handling.get("requires_context", [])),
            provides_context=context_handling.get("fields_to_store", {}),
            query_contract=config.get("query_contract", {}),
            body_contract=config.get("body_contract", {}),
            response_handling=config.get("response_handling", {}),
            flow_config=config.get("flow_config"),
            pre_hooks=tuple(config.get("pre_hooks", [])),
            post_hooks=tuple(config.get("post_hooks", [])),
            raw_yaml=raw
        )
    
    def _infer_category(self, method: str, config: Dict) -> ToolCategory:
        """
        Infer tool category from method and config.
        
        Args:
            method: HTTP method
            config: Full YAML config
            
        Returns:
            Inferred ToolCategory
        """
        # Workflow takes precedence
        if config.get("flow_config"):
            return ToolCategory.WORKFLOW
        
        # Check tool ID for hints
        tool_id = config.get("id", "")
        if "_show" in tool_id or tool_id.endswith("_get"):
            return ToolCategory.SHOW
        
        # Map HTTP method to category
        mapping = {
            "GET": ToolCategory.SEARCH,
            "POST": ToolCategory.CREATE,
            "PUT": ToolCategory.UPDATE,
            "PATCH": ToolCategory.UPDATE,
            "DELETE": ToolCategory.DELETE,
        }
        return mapping.get(method, ToolCategory.SEARCH)
    
    def _index_tool(self, tool: ToolConfig) -> None:
        """
        Index tool for fast lookup.
        
        Args:
            tool: ToolConfig to index
        """
        # Index by entity
        if tool.entity_group not in self._by_entity:
            self._by_entity[tool.entity_group] = []
        self._by_entity[tool.entity_group].append(tool.id)
        
        # Index by category
        if tool.category not in self._by_category:
            self._by_category[tool.category] = []
        self._by_category[tool.category].append(tool.id)

```

---

## 📄 src/workflow/__init__.py

```python
"""Workflow package for LangGraph orchestration."""

from .graph import create_workflow, WorkflowOrchestrator

__all__ = ["create_workflow", "WorkflowOrchestrator"]

```

---

## 📄 src/workflow/graph.py

```python
"""
LangGraph Workflow for orchestrating multi-agent query system.
Implements the complete agent pipeline.
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from ..models.state import QueryState
from ..agents import (
    IntentAnalyzerAgent,
    APIExecutorAgent,
    DataProcessorAgent,
    AnswerFormatterAgent,
    PlanValidatorAgent,
)
from ..agents.api_planner import APIPlannerAgent


logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph.
    Implements the complete query processing pipeline.
    """

    def __init__(self):
        """Initialize the workflow orchestrator with all agents."""
        self.intent_analyzer = IntentAnalyzerAgent()
        self.api_planner = APIPlannerAgent()
        self.api_executor = APIExecutorAgent()
        self.plan_validator = PlanValidatorAgent()
        self.data_processor = DataProcessorAgent()
        self.answer_formatter = AnswerFormatterAgent()

        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """
        Create the LangGraph workflow.

        Returns:
            Compiled workflow graph.
        """
        # Create graph
        workflow = StateGraph(QueryState)

        # Add nodes (agents)
        workflow.add_node("intent_analyzer", self.intent_analyzer)
        workflow.add_node("api_planner", self.api_planner)
        workflow.add_node("api_executor", self.api_executor)
        workflow.add_node("plan_validator", self.plan_validator)
        workflow.add_node("data_processor", self.data_processor)
        workflow.add_node("answer_formatter", self.answer_formatter)

        # Set entry point
        workflow.set_entry_point("intent_analyzer")

        # Define edges with conditional error handling
        workflow.add_conditional_edges(
            "intent_analyzer",
            self._should_continue,
            {
                "continue": "api_planner",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "api_planner",
            self._should_continue,
            {
                "continue": "api_executor",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "api_executor",
            self._should_continue_or_confirm,
            {
                "continue": "plan_validator",
                "confirm": END,
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "plan_validator",
            self._should_replan_or_continue,
            {
                "continue": "data_processor",
                "replan": "api_planner",
                "abort": "answer_formatter"
            }
        )

        workflow.add_conditional_edges(
            "data_processor",
            self._should_continue,
            {
                "continue": "answer_formatter",
                "end": END
            }
        )

        # Answer formatter always ends
        workflow.add_edge("answer_formatter", END)
        workflow.add_edge("answer_formatter", END)

        # Compile workflow
        return workflow.compile()

    def _should_continue(self, state: QueryState) -> Literal["continue", "end"]:
        """
        Determine if workflow should continue or end.

        Args:
            state: Current query state.

        Returns:
            "continue" to proceed to next agent, "end" to stop.
        """
        # If there's an error, proceed to formatter to format error message
        if state.get("error"):
            # Check if we're at answer_formatter already
            if state.get("final_answer"):
                return "end"
            # Otherwise, skip to formatter
            return "end"

        return "continue"

    def _should_continue_or_confirm(self, state: QueryState) -> Literal["continue", "confirm", "end"]:
        """
        Determine if workflow should continue, request confirmation, or end.

        Args:
            state: Current query state.

        Returns:
            "continue" to proceed, "confirm" if needs user confirmation, "end" to stop.
        """
        # Check if needs confirmation
        if state.get("needs_confirmation"):
            return "confirm"

        # If there's an error, end
        if state.get("error"):
            return "end"

        return "continue"

    def _should_replan_or_continue(self, state: QueryState) -> Literal["continue", "replan", "abort"]:
        """
        Determine if workflow should continue, replan, or abort.

        Args:
            state: Current query state.

        Returns:
            "continue" to proceed to data processor
            "replan" to go back to planner with feedback
            "abort" to format error message and end
        """
        if state.get("needs_replanning") and state.get("attempt_number", 1) < state.get("max_attempts", 3):
            return "replan"
        elif state.get("critical_failure") or state.get("error"):
            return "abort"
        return "continue"

    def process_query(self, question: str, context_state: QueryState = None) -> QueryState:
        """
        Process a user query through the workflow.

        Args:
            question: User question.
            context_state: Optional previous state for context (pagination, follow-up questions)

        Returns:
            Final state with answer and metadata.
        """
        logger.info(f"Processing query: {question}")

        # Initialize state
        initial_state: QueryState = {
            "question": question,
            "messages": [HumanMessage(content=question)],
            "intent": None,
            "api_plan": [],
            "plan_explanation": None,
            "api_results": {},
            "processed_data": {},
            "final_answer": "",
            "error": None,
            "needs_confirmation": False,
            "confirmation_request": None,
            "user_confirmation": None,
            "attempt_number": 1,
            "max_attempts": 3,
            "failed_strategies": [],
            "execution_feedback": [],
            "needs_replanning": False,
            "critical_failure": False,
            "last_query": None,
            "current_page": 1,
            "total_pages": 1,
            "page_size": 30,
            "metadata": {}
        }

        # Se houver contexto anterior, adicionar informações relevantes
        if context_state:
            initial_state["last_query"] = context_state.get("question")
            initial_state["current_page"] = context_state.get(
                "current_page", 1)
            initial_state["total_pages"] = context_state.get("total_pages", 1)
            initial_state["page_size"] = context_state.get("page_size", 30)

            # Adicionar contexto completo da query anterior nas mensagens
            if context_state.get("question"):
                context_msg = f"\n\n[CONTEXTO DA QUERY ANTERIOR]\n"
                context_msg += f"Query anterior: {context_state['question']}\n"
                context_msg += f"Página atual: {context_state.get('current_page', 1)}/{context_state.get('total_pages', 1)}\n"

                # Incluir intent anterior (entidades e ação)
                if context_state.get("intent"):
                    intent = context_state["intent"]
                    context_msg += f"\nAção anterior: {intent.get('main_action', 'N/A')}\n"
                    context_msg += f"Entidades anteriores: {', '.join(intent.get('entities', []))}\n"
                    if intent.get("filters"):
                        context_msg += f"Filtros anteriores: {intent.get('filters')}\n"

                # Se houver plano anterior, incluir detalhes
                if context_state.get("api_plan"):
                    context_msg += f"\nAPIs chamadas anteriormente:\n"
                    # Limitar a 3 steps
                    for i, step in enumerate(context_state["api_plan"][:3], 1):
                        api = step.get("api", "")
                        params = step.get("params", {})
                        context_msg += f"  {i}. {api}\n"
                        if params.get("where"):
                            context_msg += f"     Filtros: {params.get('where')}\n"

                # Incluir resultado anterior se houver
                if context_state.get("api_results"):
                    results_summary = []
                    # Limitar a 2 resultados
                    for key, result in list(context_state["api_results"].items())[:2]:
                        if isinstance(result, dict):
                            count = result.get("count", 0)
                            entity = result.get("entity_type", key)
                            results_summary.append(
                                f"{entity}: {count} registros")
                    if results_summary:
                        context_msg += f"\nResultados anteriores: {', '.join(results_summary)}\n"

                context_msg += "\n⚠️ IMPORTANTE: Se a pergunta atual faz referência à query anterior (ex: 'e do itau?', 'e da google?'), mantenha a mesma ação e entidades, apenas atualize os filtros.\n"

                initial_state["messages"][0] = HumanMessage(
                    content=question + context_msg)

        try:
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)

            logger.info("Query processed successfully")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Return error state
            initial_state["error"] = f"Erro interno: {str(e)}"
            initial_state[
                "final_answer"] = f"❌ Desculpe, ocorreu um erro ao processar sua pergunta: {str(e)}"

            return initial_state

    def process_query_with_state(self, initial_state: QueryState) -> QueryState:
        """
        Process a query with an existing state (for continuing after confirmation).

        Args:
            initial_state: Pre-configured state with user confirmation.

        Returns:
            Final state with answer and metadata.
        """
        logger.info("Continuing query processing with confirmation")

        try:
            # Execute workflow from the beginning but with confirmation data
            final_state = self.workflow.invoke(initial_state)

            logger.info("Query processed successfully with confirmation")
            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)

            # Return error state
            initial_state["error"] = f"Erro interno: {str(e)}"
            initial_state[
                "final_answer"] = f"❌ Desculpe, ocorreu um erro ao processar sua escolha: {str(e)}"

            return initial_state

    def continue_after_confirmation(self, state: QueryState) -> QueryState:
        """
        Continue processing after user confirmation.
        Skips intent analysis and planning since we already have the plan.

        Args:
            state: State with user confirmation/choice.

        Returns:
            Final state with answer.
        """
        logger.info("Continuing after user confirmation")

        try:
            # Clear the confirmation flag
            state["needs_confirmation"] = False

            # Re-execute from executor onwards
            # The executor will use the user_confirmation to inject the selected item
            state = self.api_executor(state)

            # If still needs confirmation (multi-step), return
            if state.get("needs_confirmation"):
                return state

            # Validate results
            state = self.plan_validator(state)

            # If needs replanning, handle it
            if state.get("needs_replanning"):
                logger.warning("Replanning needed after confirmation")
                state = self.api_planner(state)
                state = self.api_executor(state)
                state = self.plan_validator(state)

            # Process data
            state = self.data_processor(state)

            # Format answer
            state = self.answer_formatter(state)

            logger.info("Query processed successfully after confirmation")
            return state

        except Exception as e:
            logger.error(
                f"Error continuing after confirmation: {e}", exc_info=True)
            state["error"] = f"Erro interno: {str(e)}"
            state["final_answer"] = f"❌ Desculpe, ocorreu um erro: {str(e)}"
            return state


def create_workflow() -> WorkflowOrchestrator:
    """
    Factory function to create workflow orchestrator.

    Returns:
        Configured WorkflowOrchestrator instance.
    """
    return WorkflowOrchestrator()

```

---



