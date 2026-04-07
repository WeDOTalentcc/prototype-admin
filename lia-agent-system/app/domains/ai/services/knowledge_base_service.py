"""
KnowledgeBaseService - Base de conhecimento para respostas contextuais.

Fornece:
- Respostas para perguntas frequentes sobre o sistema
- Informações sobre processos de recrutamento
- Dicas e melhores práticas
- Fallback inteligente com sugestões
"""
import logging
import re
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class KnowledgeCategory(StrEnum):
    SYSTEM = "system"
    PROCESS = "process"
    WSI = "wsi"
    AFFIRMATIVE = "affirmative"
    SALARY = "salary"
    BENEFITS = "benefits"
    SKILLS = "skills"
    INTERVIEW = "interview"
    LEGAL = "legal"
    GENERAL = "general"


@dataclass
class KnowledgeEntry:
    """Entrada na base de conhecimento."""
    id: str
    category: KnowledgeCategory
    keywords: list[str]
    question_patterns: list[str]
    answer: str
    follow_up_suggestions: list[str] = field(default_factory=list)
    related_entries: list[str] = field(default_factory=list)


@dataclass
class KnowledgeResponse:
    """Resposta da base de conhecimento."""
    found: bool
    answer: str | None = None
    category: KnowledgeCategory | None = None
    confidence: float = 0.0
    suggestions: list[str] = field(default_factory=list)
    related_topics: list[str] = field(default_factory=list)


class KnowledgeBaseService:
    """
    Base de conhecimento para respostas contextuais da LIA.
    """
    
    _knowledge_base: dict[str, KnowledgeEntry] = {}
    
    def __init__(self):
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Inicializa a base de conhecimento com entradas padrão."""
        
        entries = [
            KnowledgeEntry(
                id="wsi_what",
                category=KnowledgeCategory.WSI,
                keywords=["wsi", "skill index", "índice", "avaliação"],
                question_patterns=[
                    r"o que [ée] wsi",
                    r"como funciona.*(wsi|avalia[çc][aã]o)",
                    r"explica.*(wsi|metodologia)",
                ],
                answer="""O **WSI (WeDoTalent Skill Index)** é nossa metodologia proprietária de avaliação que combina:

🎯 **7 Blocos de Avaliação:**
1. Competências Técnicas (hard skills)
2. Competências Comportamentais (soft skills)
3. Fit Cultural
4. Experiência relevante
5. Potencial de desenvolvimento
6. Motivação e engajamento
7. Adequação ao cargo

📊 **Como funciona:**
- Cada candidato recebe uma pontuação de 0-100
- As perguntas de triagem são geradas automaticamente
- A IA analisa respostas usando taxonomia de Bloom e modelo Dreyfus
- O resultado inclui perfil Big Five para análise comportamental

💡 *Dica: Você pode personalizar os pesos de cada bloco por vaga!*""",
                follow_up_suggestions=[
                    "Como personalizar os pesos do WSI?",
                    "Quantas perguntas de triagem são geradas?",
                    "Como interpretar a pontuação WSI?"
                ],
                related_entries=["wsi_questions", "wsi_scoring"]
            ),
            
            KnowledgeEntry(
                id="wsi_questions",
                category=KnowledgeCategory.WSI,
                keywords=["perguntas", "triagem", "screening", "questões"],
                question_patterns=[
                    r"quantas perguntas",
                    r"perguntas de triagem",
                    r"como.*perguntas.*geradas",
                ],
                answer="""📝 **Perguntas de Triagem WSI:**

A LIA gera automaticamente **5 perguntas** de triagem baseadas no perfil da vaga:

**Distribuição típica:**
- 2-3 perguntas técnicas (hard skills)
- 1-2 perguntas comportamentais (soft skills)
- 1 pergunta de fit cultural

**Características:**
- Perguntas situacionais baseadas em CBI (Competency-Based Interview)
- Nível de dificuldade ajustado à senioridade
- Tempo médio de resposta: 2-3 minutos por pergunta

⚠️ *O limite de 5 perguntas é fixo para garantir experiência do candidato!*""",
                follow_up_suggestions=[
                    "Posso editar as perguntas geradas?",
                    "Como a IA avalia as respostas?",
                    "Posso adicionar mais perguntas?"
                ]
            ),
            
            KnowledgeEntry(
                id="affirmative_what",
                category=KnowledgeCategory.AFFIRMATIVE,
                keywords=["afirmativa", "pcd", "diversidade", "inclusão", "lgbtq"],
                question_patterns=[
                    r"(vaga|a[çc][aã]o) afirmativa",
                    r"como.*pcd",
                    r"diversidade.*vaga",
                    r"inclusão",
                ],
                answer="""🌈 **Vagas Afirmativas na LIA:**

Vagas afirmativas são destinadas a grupos sub-representados no mercado de trabalho.

**Critérios suportados:**
- PCD (Pessoas com Deficiência)
- Mulheres
- Pessoas Negras
- LGBTQIA+
- 50+ (Pessoas acima de 50 anos)
- Indígenas
- Pessoas Trans

**Como funciona:**
1. Marque a vaga como "Afirmativa"
2. Selecione o critério primário (e secundário, se aplicável)
3. A LIA adiciona automaticamente os termos corretos na descrição
4. O sistema garante compliance com LGPD

📋 **Documentação:**
- Você pode solicitar comprovação (laudo PCD, autodeclaração)
- Todo o processo segue as normas da Lei de Cotas

⚠️ *Importante: Garantimos trilha de auditoria para compliance!*""",
                follow_up_suggestions=[
                    "Preciso de laudo para vaga PCD?",
                    "Como funciona a autodeclaração?",
                    "A vaga pode ter dois critérios afirmativos?"
                ],
                related_entries=["affirmative_lgpd", "affirmative_docs"]
            ),
            
            KnowledgeEntry(
                id="salary_market",
                category=KnowledgeCategory.SALARY,
                keywords=["salário", "remuneração", "mercado", "faixa salarial"],
                question_patterns=[
                    r"qual sal[aá]rio",
                    r"faixa salarial",
                    r"quanto pagar",
                    r"remunera[çc][aã]o.*mercado",
                ],
                answer="""💰 **Análise de Remuneração:**

A LIA pode ajudar a definir a faixa salarial com base em:

**Fatores considerados:**
- Cargo e senioridade
- Localização (custo de vida)
- Modelo de trabalho (remoto geralmente +10-15%)
- Setor da empresa
- Histórico de vagas similares na empresa

**Dicas:**
- Defina uma faixa (ex: R$ 8.000 - R$ 12.000)
- Considere incluir variável/bônus
- Benefícios impactam a atratividade

📊 *Posso analisar o mercado para sugerir uma faixa adequada. Me diga o cargo e senioridade!*""",
                follow_up_suggestions=[
                    "Analise o mercado para [cargo]",
                    "Qual a média salarial para [cargo]?",
                    "Devo divulgar o salário na vaga?"
                ]
            ),
            
            KnowledgeEntry(
                id="benefits_common",
                category=KnowledgeCategory.BENEFITS,
                keywords=["benefícios", "vr", "va", "plano", "saúde"],
                question_patterns=[
                    r"quais benef[ií]cios",
                    r"benef[ií]cios.*comuns",
                    r"o que oferecer",
                ],
                answer="""🎁 **Benefícios Comuns:**

**Básicos (esperados pelo mercado):**
- Vale Refeição/Alimentação
- Vale Transporte
- Plano de Saúde
- Plano Odontológico

**Diferenciais (atraem talentos):**
- Gympass/TotalPass
- PLR/PPR (Participação nos lucros)
- Auxílio Home Office
- Day-off no aniversário
- Licença parental estendida

**Para Senioridade Alta:**
- Stock Options
- Bônus por performance
- Previdência privada
- Seguro de vida

💡 *Você pode selecionar os benefícios do catálogo da empresa ou adicionar novos!*""",
                follow_up_suggestions=[
                    "Quais benefícios nossa empresa oferece?",
                    "Como adicionar um novo benefício?",
                    "Benefícios para vaga remota"
                ]
            ),
            
            KnowledgeEntry(
                id="interview_stages",
                category=KnowledgeCategory.INTERVIEW,
                keywords=["entrevista", "etapas", "processo", "fases"],
                question_patterns=[
                    r"quantas entrevistas",
                    r"etapas.*processo",
                    r"fases.*sele[çc][aã]o",
                ],
                answer="""📋 **Etapas do Processo Seletivo:**

**Fluxo típico:**
1. **Triagem Inicial** - Análise de CV + WSI automático
2. **Entrevista RH** - Fit cultural e expectativas
3. **Entrevista Técnica** - Avaliação de hard skills
4. **Entrevista Gestor** - Fit com a equipe
5. **Proposta** - Negociação e fechamento

**A LIA automatiza:**
- Triagem inicial com scoring WSI
- Agendamento de entrevistas (integração com Teams/Outlook)
- Transcrição e análise de entrevistas
- Feedback estruturado para candidatos

💡 *Você pode personalizar as etapas para cada vaga!*""",
                follow_up_suggestions=[
                    "Como agendar entrevistas automaticamente?",
                    "A LIA transcreve entrevistas?",
                    "Como enviar feedback aos candidatos?"
                ]
            ),
            
            KnowledgeEntry(
                id="system_wizard",
                category=KnowledgeCategory.SYSTEM,
                keywords=["wizard", "criação", "vaga", "passos"],
                question_patterns=[
                    r"como criar.*vaga",
                    r"passos.*criar",
                    r"wizard.*funciona",
                ],
                answer="""🧙 **Wizard de Criação de Vagas:**

O wizard tem **5 etapas**:

1. **📋 Informações Básicas** - Cargo, área, gestor, modelo de trabalho
2. **💰 Remuneração** - Salário, bônus, benefícios
3. **🎯 Competências** - Skills técnicas e comportamentais
4. **❓ Triagem WSI** - Perguntas de screening (max 5)
5. **✅ Revisão** - Conferência final e publicação

**Atalhos:**
- 🚀 **Fast Track** - Reutilize uma vaga anterior
- 💬 **Chat com LIA** - Descreva a vaga em linguagem natural
- 📝 **Importar JD** - Cole uma descrição existente

💡 *Você pode pular etapas e voltar a qualquer momento!*""",
                follow_up_suggestions=[
                    "Como usar o Fast Track?",
                    "Posso importar uma descrição de vaga?",
                    "Como pular uma etapa?"
                ]
            ),
            
            KnowledgeEntry(
                id="fast_track",
                category=KnowledgeCategory.SYSTEM,
                keywords=["fast track", "reutilizar", "copiar", "anterior"],
                question_patterns=[
                    r"fast track",
                    r"reutilizar.*vaga",
                    r"copiar.*vaga",
                    r"vaga anterior",
                ],
                answer="""🚀 **Fast Track - Reutilização de Vagas:**

O Fast Track permite criar uma nova vaga baseada em uma anterior.

**O que é copiado:**
- Descrição da vaga
- Competências técnicas e comportamentais
- Perguntas de triagem WSI
- Requisitos e qualificações

**O que você pode ajustar:**
- Salário e bônus
- Benefícios
- Localização
- Modelo de trabalho
- Gestor responsável
- Prazos

**Como usar:**
1. Diga "quero reutilizar uma vaga" ou "fast track"
2. Busque a vaga anterior (por cargo, área ou gestor)
3. Selecione e ajuste os campos editáveis
4. Publique!

⚡ *Economize tempo com vagas recorrentes!*""",
                follow_up_suggestions=[
                    "Mostre as últimas vagas",
                    "Buscar vagas de [cargo]",
                    "Quais campos posso editar no Fast Track?"
                ]
            ),
            
            KnowledgeEntry(
                id="module_pipeline",
                category=KnowledgeCategory.SYSTEM,
                keywords=["funil", "pipeline", "módulo", "etapas", "kanban", "triagem", "como funciona"],
                question_patterns=[
                    r"como funciona.*funil",
                    r"como funciona.*pipeline",
                    r"como funciona.*triagem",
                    r"m[oó]dulo.*funil",
                    r"m[oó]dulo.*pipeline",
                    r"o que [eé].*funil",
                    r"como usar.*funil",
                    r"como usar.*pipeline",
                    r"explica.*funil",
                    r"explica.*pipeline",
                ],
                answer="""📋 **Módulo Funil de Talentos:**

O Funil de Talentos centraliza toda a gestão de candidatos em processo seletivo.

**Funcionalidades principais:**
- **Kanban visual** — Arraste candidatos entre etapas (Triagem → Entrevista → Proposta → Contratado)
- **Triagem automática WSI** — A LIA avalia CVs e gera pontuação 0-100
- **Pipeline analytics** — Identifique gargalos e candidatos em risco
- **Ações em lote** — Mova, reprove ou comunique múltiplos candidatos de uma vez
- **Atualização de cadastro** — Edite campos do candidato diretamente pelo chat

**Etapas padrão:**
Novo → Triagem → Entrevista RH → Entrevista Técnica → Proposta → Contratado / Reprovado

💡 *Diga "mover [candidato] para [etapa]" e eu faço direto pelo chat!*""",
                follow_up_suggestions=[
                    "Como mover um candidato de etapa?",
                    "Como iniciar a triagem automática?",
                    "Como ver candidatos em risco?",
                ]
            ),

            KnowledgeEntry(
                id="module_sourcing",
                category=KnowledgeCategory.SYSTEM,
                keywords=["sourcing", "busca", "candidatos", "módulo", "talent pool", "como funciona"],
                question_patterns=[
                    r"como funciona.*sourcing",
                    r"m[oó]dulo.*sourcing",
                    r"o que [eé].*sourcing",
                    r"como usar.*sourcing",
                    r"como buscar candidatos",
                    r"talent pool",
                    r"busca booleana",
                ],
                answer="""🔍 **Módulo Sourcing:**

O Sourcing permite encontrar e atrair candidatos qualificados com inteligência artificial.

**Funcionalidades:**
- **Busca semântica** — Encontre talentos por habilidades, experiência e perfil
- **Boolean Search** — Crie strings avançadas para busca precisa
- **Talent Pool** — Banco de talentos da empresa e candidatos históricos
- **Ranking automático** — A LIA prioriza os candidatos mais aderentes
- **Shortlist** — Salve os melhores perfis para análise posterior
- **Abordagem inteligente** — Gere mensagens personalizadas de contato

**Como usar:**
1. Diga "buscar candidatos para [vaga]"
2. A LIA sugere critérios de busca com base nos requisitos
3. Revise e refine os resultados
4. Adicione os melhores ao shortlist

💡 *Posso buscar candidatos no pool da empresa ou sugerir fontes externas!*""",
                follow_up_suggestions=[
                    "Buscar candidatos para minha vaga",
                    "Como usar o talent pool?",
                    "Gerar string booleana para [cargo]",
                ]
            ),

            KnowledgeEntry(
                id="module_tasks",
                category=KnowledgeCategory.SYSTEM,
                keywords=["tarefas", "lembretes", "painel", "módulo", "to do", "pendências", "como funciona"],
                question_patterns=[
                    r"como funciona.*tarefa",
                    r"como funciona.*lembrete",
                    r"m[oó]dulo.*tarefa",
                    r"m[oó]dulo.*painel",
                    r"o que [eé].*painel de controle",
                    r"como criar tarefa",
                    r"como criar lembrete",
                ],
                answer="""✅ **Módulo Tarefas & Lembretes:**

Gerencie suas atividades de recrutamento diretamente pelo chat da LIA.

**O que você pode fazer:**
- **Criar tarefas** — "cria uma tarefa: ligar para o gestor da vaga de Dev"
- **Criar lembretes** — "me lembra de ligar para Maria amanhã às 10h"
- **Vincular candidatos/vagas** — A tarefa fica ligada ao contexto relevante
- **Prazo (due date)** — Defina quando a tarefa deve ser concluída
- **Resumo do dia** — "qual minha agenda de hoje?" lista tudo consolidado

**Como usar pelo chat:**
- "me lembra de [ação] [quando]"
- "cria uma tarefa: [título]"
- "quais minhas tarefas pendentes?"
- "resumo do meu dia"

💡 *Digo tudo isso direto aqui no chat e salvo automaticamente!*""",
                follow_up_suggestions=[
                    "Criar um lembrete para hoje",
                    "Quais minhas tarefas pendentes?",
                    "Ver minha agenda de hoje",
                ]
            ),

            KnowledgeEntry(
                id="module_calendar",
                category=KnowledgeCategory.SYSTEM,
                keywords=["calendário", "agenda", "compromisso", "reunião", "módulo", "como funciona"],
                question_patterns=[
                    r"como funciona.*calend[aá]rio",
                    r"m[oó]dulo.*calend[aá]rio",
                    r"como criar.*compromisso",
                    r"como agendar.*reuni[aã]o",
                    r"integra[çc][aã]o.*calend[aá]rio",
                    r"como funciona.*agenda",
                ],
                answer="""📅 **Calendário & Compromissos:**

A LIA integra com seu calendário (Microsoft Outlook/Google Calendar) para gestão completa de agenda.

**Funcionalidades:**
- **Agendar entrevistas** — Integração automática com Teams/Meet
- **Compromissos genéricos** — Crie reuniões, alinhamentos e calls sem vincular candidato
- **Verificar disponibilidade** — A LIA consulta slots livres do entrevistador
- **Resumo diário** — Veja entrevistas + compromissos do dia em uma resposta
- **Reagendamento** — Cancele ou mude horários direto pelo chat

**Como usar:**
- "agendar entrevista com [candidato] [data/hora]"
- "cria um compromisso: alinhamento com gestor amanhã 14h"
- "resumo da minha agenda de hoje"

⚙️ *Requer integração com Microsoft 365 ou Google Workspace configurada!*""",
                follow_up_suggestions=[
                    "Como configurar integração com calendário?",
                    "Agendar entrevista para amanhã",
                    "Ver minha agenda de hoje",
                ]
            ),

            KnowledgeEntry(
                id="module_notes",
                category=KnowledgeCategory.SYSTEM,
                keywords=["nota", "anotação", "anotar", "registrar", "módulo", "como funciona"],
                question_patterns=[
                    r"como funciona.*nota",
                    r"como.*anotar",
                    r"como salvar.*nota",
                    r"como registrar.*observa[çc][aã]o",
                    r"criar.*nota",
                ],
                answer="""📝 **Notas & Observações:**

Registre informações importantes sobre candidatos e vagas diretamente pelo chat.

**Como usar:**
- "anota que o gestor quer candidatos com inglês fluente na vaga X"
- "salva uma nota sobre a Maria: excelente comunicação, avançar"
- "registra: candidato pediu salário acima da faixa"

**Vinculação automática:**
- Se mencionar um candidato → nota fica vinculada ao candidato
- Se mencionar uma vaga → nota fica vinculada à vaga
- Sem contexto → nota geral do recrutador

**Acesso às notas:**
- No perfil do candidato (aba Notas)
- Na página da vaga
- Pelo Painel de Controle

💡 *Basta dizer "anota que..." e eu salvo automaticamente!*""",
                follow_up_suggestions=[
                    "Anotar observação sobre candidato",
                    "Ver notas de um candidato",
                    "Anotar preferência do gestor para a vaga",
                ]
            ),

            KnowledgeEntry(
                id="module_upload_cv",
                category=KnowledgeCategory.SYSTEM,
                keywords=["upload", "cv", "currículo", "arquivo", "enviar arquivo", "importar cv", "analisar arquivo"],
                question_patterns=[
                    r"como enviar.*arquivo",
                    r"como.*upload",
                    r"como importar.*cv",
                    r"como analisar.*arquivo",
                    r"enviar cv pelo chat",
                    r"como usar.*upload",
                ],
                answer="""📎 **Upload de Arquivo / CV pelo Chat:**

Você pode enviar arquivos (CV, planilhas) diretamente no chat flutuante da LIA.

**Como funciona:**
1. Clique no ícone de anexo (📎) no chat
2. Selecione o arquivo (PDF, DOCX, XLS, XLSX — até 10MB)
3. A LIA extrai automaticamente os dados do documento
4. Para CVs: a LIA apresenta os campos encontrados (nome, email, cargo, skills, etc.)
5. Confirme para preencher/atualizar o cadastro do candidato automaticamente

**Dados extraídos de CVs:**
- Informações de contato (email, telefone, LinkedIn)
- Cargo atual e empresa
- Histórico profissional e formação
- Skills técnicas e comportamentais
- Idiomas

**Formatos suportados:** PDF, DOC, DOCX, TXT, XLS, XLSX

💡 *Arraste e solte o arquivo no chat ou use o botão de anexo!*""",
                follow_up_suggestions=[
                    "Enviar CV de um candidato",
                    "Atualizar cadastro do candidato",
                    "Extrair dados de planilha",
                ]
            ),

            KnowledgeEntry(
                id="daily_agenda_summary",
                category=KnowledgeCategory.PROCESS,
                keywords=["agenda", "resumo diário", "agenda do dia", "compromissos de hoje", "tarefas de hoje",
                          "o que tenho hoje", "minha agenda", "resumo", "entrevistas de hoje", "dia"],
                question_patterns=[
                    r"(o que|quais?|me mostre?|veja?)\s+(tenho|tem|são|estão).{0,30}(hoje|amanhã|essa semana)",
                    r"(minha|meus?)\s+(agenda|compromissos?|tarefas?|entrevistas?)",
                    r"(resumo|sumário)\s+(do\s+dia|diário|de hoje)",
                    r"(agenda|entrevistas?|compromissos?)\s+(de\s+)?(hoje|amanhã|esta semana|essa semana)",
                    r"(o que|quem)\s+(tenho|tenho que|preciso)\s+(fazer|entrevistar|atender)\s+(hoje|amanhã)",
                ],
                answer="""📅 **Resumo Diário — Como funciona:**

Peça à LIA um resumo consolidado do seu dia diretamente no chat:

**Exemplos de perguntas:**
- "O que tenho hoje?"
- "Quais entrevistas tenho amanhã?"
- "Resumo do dia"
- "Minha agenda desta semana"

**O resumo inclui:**
1. 📋 **Entrevistas agendadas** — candidatos, horários e vagas
2. ✅ **Tarefas pendentes** — prazos e prioridades
3. 📌 **Compromissos e reuniões** — eventos genéricos do calendário
4. 🔔 **Lembretes ativos** — avisos e pendências

**Criar itens de agenda pelo chat:**
- `"Cria uma tarefa para revisar os CVs amanhã"`
- `"Adiciona um lembrete de ligar para o gestor na sexta"`
- `"Agenda um compromisso com o time de produto amanhã"`

💡 *A LIA cruza dados de entrevistas, tarefas e eventos para dar uma visão consolidada do seu dia!*""",
                follow_up_suggestions=[
                    "Quais entrevistas tenho hoje?",
                    "Criar tarefa para amanhã",
                    "Ver minhas tarefas pendentes",
                ]
            ),

            KnowledgeEntry(
                id="lgpd_compliance",
                category=KnowledgeCategory.LEGAL,
                keywords=["lgpd", "privacidade", "dados", "compliance"],
                question_patterns=[
                    r"lgpd",
                    r"prote[çc][aã]o.*dados",
                    r"privacidade",
                    r"compliance",
                ],
                answer="""🔒 **Compliance LGPD na LIA:**

A plataforma segue rigorosamente a LGPD:

**Proteção de Dados:**
- Todos os dados são criptografados
- Consentimento explícito dos candidatos
- Direito ao esquecimento implementado
- Logs de auditoria completos

**Para Vagas Afirmativas:**
- Dados sensíveis com proteção extra
- Trilha de auditoria para decisões
- Justificativa documentada
- Anonimização quando aplicável

**Retenção de Dados:**
- Candidatos não aprovados: 6 meses
- Candidatos contratados: Vigência do contrato + 5 anos
- Dados de processo: Conforme política da empresa

⚠️ *Toda decisão automatizada pode ser explicada e revisada por humano!*""",
                follow_up_suggestions=[
                    "Como funciona o direito ao esquecimento?",
                    "Onde vejo os logs de auditoria?",
                    "Candidato pode solicitar seus dados?"
                ]
            ),
        ]
        
        for entry in entries:
            self._knowledge_base[entry.id] = entry

    def search(self, query: str, category: KnowledgeCategory | None = None) -> KnowledgeResponse:
        """
        Busca na base de conhecimento.
        
        Args:
            query: Pergunta do usuário
            category: Categoria para filtrar (opcional)
            
        Returns:
            KnowledgeResponse com a resposta encontrada
        """
        query_lower = query.lower()
        best_match: KnowledgeEntry | None = None
        best_score = 0.0
        
        for entry in self._knowledge_base.values():
            if category and entry.category != category:
                continue
            
            score = self._calculate_match_score(query_lower, entry)
            
            if score > best_score:
                best_score = score
                best_match = entry
        
        if best_match and best_score >= 0.3:
            related = []
            for related_id in best_match.related_entries:
                if related_id in self._knowledge_base:
                    related.append(self._knowledge_base[related_id].answer[:100] + "...")
            
            return KnowledgeResponse(
                found=True,
                answer=best_match.answer,
                category=best_match.category,
                confidence=best_score,
                suggestions=best_match.follow_up_suggestions,
                related_topics=related
            )
        
        return KnowledgeResponse(
            found=False,
            confidence=0.0,
            suggestions=self._get_fallback_suggestions(query_lower)
        )

    def _calculate_match_score(self, query: str, entry: KnowledgeEntry) -> float:
        """Calcula score de match entre query e entrada."""
        score = 0.0
        
        for pattern in entry.question_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.5
                break
        
        keyword_matches = sum(1 for kw in entry.keywords if kw in query)
        if keyword_matches > 0:
            score += min(0.4, keyword_matches * 0.15)
        
        return min(1.0, score)

    def _get_fallback_suggestions(self, query: str) -> list[str]:
        """Retorna sugestões quando não encontra resposta."""
        suggestions = [
            "Como criar uma nova vaga?",
            "O que é o WSI?",
            "Como funciona vaga afirmativa?",
            "Quais benefícios posso oferecer?",
            "Como usar o Fast Track?",
        ]
        
        if any(word in query for word in ["salário", "remuneração", "pagar"]):
            suggestions.insert(0, "Analise o mercado para sugerir salário")
        
        if any(word in query for word in ["pcd", "afirmativa", "diversidade"]):
            suggestions.insert(0, "Como configurar vaga afirmativa?")
        
        return suggestions[:5]

    def get_contextual_help(self, stage: int, field: str | None = None) -> str:
        """Retorna ajuda contextual baseada no estágio do wizard."""
        stage_help = {
            1: "📋 **Etapa 1 - Informações Básicas**\nDefina o cargo, área, gestor e modelo de trabalho. Você pode descrever tudo em linguagem natural!",
            2: "💰 **Etapa 2 - Remuneração**\nDefina a faixa salarial, bônus e benefícios. Posso analisar o mercado se precisar!",
            3: "🎯 **Etapa 3 - Competências**\nSelecione as skills técnicas e comportamentais. Sugiro automaticamente com base no cargo!",
            4: "❓ **Etapa 4 - Triagem WSI**\nRevise as 5 perguntas de screening. Você pode editar ou regenerar!",
            5: "✅ **Etapa 5 - Revisão**\nConfira tudo antes de publicar. Posso gerar a descrição completa da vaga!",
        }
        
        return stage_help.get(stage, "💡 Como posso ajudar?")

    def get_all_categories(self) -> list[dict[str, Any]]:
        """Retorna todas as categorias disponíveis."""
        return [
            {"id": cat.value, "name": cat.name}
            for cat in KnowledgeCategory
        ]


knowledge_base = KnowledgeBaseService()
