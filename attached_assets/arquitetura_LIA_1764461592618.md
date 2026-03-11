# Arquitetura de Agentes da LIA - wedotalent

**Versão:** 1.0  
**Data:** 28 de Novembro de 2025  
**Autor:** Manus AI

---

## 1. Introdução

Este documento detalha a arquitetura inicial de múltiplos agentes para a LIA (Learning Intelligence Assistant), a IA conversacional da plataforma wedotalent. O objetivo é criar um sistema robusto, escalável e modular, onde cada agente possui responsabilidades específicas, colaborando para automatizar e otimizar o ciclo de recrutamento.

A arquitetura é projetada para ser implementada utilizando uma stack de tecnologias moderna, focada em flexibilidade e observabilidade.

### 1.1. Stack Tecnológica

A solução será construída sobre os seguintes componentes principais:

| Componente | Propósito |
| --- | --- |
| **Python** | Linguagem principal para o desenvolvimento dos agentes e da lógica de negócio. |
| **FastAPI** | Framework para a construção das APIs que servirão de interface para os agentes e o frontend. |
| **LangGraph** | Biblioteca para orquestração dos agentes, permitindo a criação de fluxos complexos e cíclicos com múltiplos atores. Substitui o LangChain para maior controle. |
| **Redis** | Utilizado para gerenciamento de cache, filas de tarefas e armazenamento temporário de estado das conversas. |
| **PostgreSQL + pgvector** | Banco de dados principal para armazenamento persistente de dados (vagas, candidatos) e para buscas vetoriais de similaridade. |
| **LangSmith** | Plataforma para observabilidade, monitoramento e debugging dos agentes e das cadeias de LLMs. |

### 1.2. Visão Geral da Arquitetura

A arquitetura é centrada em um **Orquestrador Central (Orchestrator)** que atua como o cérebro do sistema. Ele recebe todas as interações do usuário, classifica a intenção e roteia a tarefa para o agente especialista apropriado. Os agentes, por sua vez, executam suas funções, utilizam ferramentas (APIs, banco de dados) e, se necessário, passam o controle para outros agentes através do orquestrador.

Este modelo permite que cada agente seja desenvolvido, testado e mantido de forma independente, garantindo a modularidade do sistema.

```mermaid
graph TD
    subgraph Frontend
        A[Interface do Usuário / Chat LIA]
    end

    subgraph Backend (FastAPI)
        B(API Gateway)
        C(Orchestrator - LangGraph)

        subgraph Agentes Especialistas
            D1[Job Intake Agent]
            D2[Sourcing Agent]
            D3[Screening Agent]
            D4[Scheduling Agent]
            D5[Communication Agent]
            D6[Recruiter Assistant Agent]
            D7[Analytics Agent]
        end

        subgraph Ferramentas e Serviços
            E1(Banco de Dados - PostgreSQL)
            E2(Banco Vetorial - pgvector)
            E3(Cache - Redis)
            E4(APIs Externas - MS Graph, Pearch)
        end
    end

    subgraph Observabilidade
        F[LangSmith]
    end

    A --> B
    B --> C
    C --> D1
    C --> D2
    C --> D3
    C --> D4
    C --> D5
    C --> D6
    C --> D7

    D1 <--> E1
    D2 <--> E1
    D2 <--> E2
    D2 <--> E4
    D3 <--> E1
    D4 <--> E4
    D5 <--> E1

    C -- Monitoramento --> F
    D1 -- Monitoramento --> F
    D2 -- Monitoramento --> F
    D3 -- Monitoramento --> F
    D4 -- Monitoramento --> F
    D5 --- Monitoramento --> F
    D6 --- Monitoramento --> F
    D7 --- Monitoramento --> F
```

---

## 2. Definição dos Agentes

A seguir, detalhamos cada um dos agentes que compõem a arquitetura da LIA.

### Agente 0: Orchestrator (Orquestrador Central)

- **Papel/Objetivo:** Atuar como o ponto central de controle, gerenciando o fluxo da conversa, classificando intenções e delegando tarefas para os agentes especialistas. Garante uma experiência de usuário coesa e fluida.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Classificar a intenção do usuário a partir de uma mensagem.
    - Rotear a conversa para o agente ou grafo correto (ex: grafo de criação de vaga).
    - Manter o histórico e o estado da conversa.
    - Sugerir ações contextuais rápidas para o usuário.
  - **Futuras:**
    - Aprender as preferências do usuário para personalizar a interação.
    - Orquestrar pipelines complexos e autônomos que envolvem múltiplos agentes (ex: sourcing + triagem + agendamento).
    - Gerenciar a memória de longo prazo entre diferentes sessões.

- **Inputs:**
  - Mensagem do usuário (texto ou comando).
  - Estado atual da conversa.
  - Histórico da conversa.

- **Outputs:**
  - Delegação da tarefa para um agente especialista.
  - Resposta direta ao usuário (para comandos simples).
  - Sugestões de próximas ações.

- **Conexões:**
  - **Recebe de:** Interface do Usuário (via API Gateway).
  - **Envia para:** Todos os agentes especialistas.
  - **Retorna para:** Interface do Usuário (com a resposta final ou status).


### Agente 1: Job Intake Agent (Agente de Vagas)

- **Papel/Objetivo:** Especialista na criação, gestão e otimização de vagas. Auxilia o recrutador a estruturar uma vaga de forma completa e estratégica, desde a definição de requisitos até a publicação.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Guiar o recrutador na criação de uma nova vaga através de uma conversa estruturada.
    - Extrair requisitos de uma descrição de vaga (Job Description) colada.
    - Gerenciar o ciclo de vida da vaga (criar, editar, arquivar, reativar).
    - Definir as etapas do processo seletivo para a vaga.
  - **Futuras:**
    - Analisar a descrição da vaga em comparação com o mercado para sugerir faixas salariais competitivas.
    - Prever o tempo estimado para o fechamento da vaga.
    - Gerar uma descrição de vaga otimizada para SEO e inclusão.
    - Monitorar a "saúde" da vaga, alertando sobre riscos (ex: poucos candidatos, processo lento).

- **Inputs:**
  - Solicitação de abertura de vaga.
  - Título, descrição, requisitos, salário, etc.
  - Feedback do recrutador durante a criação.

- **Outputs:**
  - Vaga estruturada e salva no banco de dados (PostgreSQL).
  - Plano de recrutamento com etapas e cronograma definidos.
  - Descrição da vaga otimizada para publicação.

- **Conexões:**
  - **Recebe de:** Orchestrator.
  - **Interage com:** Banco de Dados (para CRUD de vagas), Analytics Agent (para dados de mercado).
  - **Envia para:** Orchestrator (após conclusão), Sourcing Agent (para iniciar a busca).

- **Exemplo de Conversa (Criação de Vaga):**
  > **LIA:** Olá! Sou sua assistente de recrutamento. Identifiquei uma nova "Solicitação de Abertura de Vaga" no sistema. Pronta para transformá-la em uma contratação de sucesso?
  > **Recrutador:** Olá! Sim, vamos com tudo.
  > **LIA:** Ótimo. A solicitação veio com o título "Engenheiro de Software Backend". Podemos manter? E uma pergunta importante: esta vaga é confidencial?
  > **Recrutador:** Não, esta vaga não é confidencial.
  > **LIA:** Perfeito. Vaga marcada como "Não Confidencial". Agora, sobre a remuneração, a solicitação indica uma faixa de R$ 12.000 a R$ 15.000. Confirma?
  > **Recrutador:** Confirmo.
  > **LIA:** Obrigado. Inseri a faixa no ATS e, enquanto conversamos, realizei uma análise de mercado em tempo real. Sua faixa salarial está competitiva. Agora, vamos entender a estrutura da equipe. Para quem essa pessoa se reportará?


### Agente 2: Sourcing Agent (Agente de Sourcing)

- **Papel/Objetivo:** Responsável por encontrar e atrair candidatos qualificados para as vagas abertas. Atua como um especialista em busca, utilizando diferentes fontes para construir um pipeline de talentos.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Buscar candidatos no banco de dados interno (PostgreSQL) com base nos requisitos da vaga.
    - Integrar-se com APIs externas (ex: Pearch AI) para buscar candidatos em fontes públicas.
    - Realizar o parsing de currículos (CVs) enviados para extrair informações estruturadas.
    - Detectar e gerenciar candidatos duplicados.
  - **Futuras:**
    - Executar pipelines de sourcing automatizado, buscando proativamente novos candidatos para vagas em risco.
    - Enriquecer perfis de candidatos com informações do LinkedIn, GitHub, etc.
    - Calcular um "score de fit" inicial para os candidatos encontrados.
    - Realizar "hunting" passivo, monitorando perfis de interesse e alertando sobre mudanças.

- **Inputs:**
  - Requisitos da vaga (do Job Intake Agent).
  - Estratégia de sourcing definida (setores, empresas-alvo).
  - Currículos (arquivos PDF, DOCX).

- **Outputs:**
  - Lista de candidatos qualificados associados a uma vaga.
  - Perfis de candidatos estruturados e salvos no banco de dados.
  - Alertas sobre o volume e a qualidade do pipeline de candidatos.

- **Conexões:**
  - **Recebe de:** Job Intake Agent (início do processo), Orchestrator.
  - **Interage com:** Banco de Dados, Banco Vetorial (para busca semântica), APIs Externas.
  - **Envia para:** Screening Agent (para iniciar a triagem).

- **Exemplo de Conversa (Abordagem de Candidato):**
  > **LIA (via WhatsApp):** Olá, {NOME_CANDIDATO}, tudo bem? Meu nome é Manu, sou a assistente de recrutamento da TechCorp. Encontrei seu perfil e vi que você tem uma ótima experiência com Node.js e no setor de meios de pagamento. Estamos com uma oportunidade para Engenheiro(a) de Software Backend Sênior que parece ter tudo a ver com sua trajetória. Você teria interesse em saber mais?


### Agente 3: Screening Agent (Agente de Triagem)

- **Papel/Objetivo:** Especialista em qualificar candidatos, avaliando suas competências técnicas e comportamentais de forma estruturada e escalável. O objetivo é garantir que apenas os candidatos mais alinhados avancem no processo.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Conduzir a triagem por voz ou texto, aplicando a **Metodologia WSI (WeDoTalent Skill Index)**.
    - Transcrever e analisar as respostas dos candidatos.
    - Gerar a **Nota LIA**, um score ponderado de fit técnico e cultural.
    - Mover os candidatos aprovados no pipeline.
  - **Futuras:**
    - Elaborar um parecer detalhado do candidato para o gestor da vaga.
    - Realizar uma análise comparativa entre os melhores candidatos.
    - Conduzir triagens assíncronas, onde o candidato grava as respostas.
    - Detectar "red flags" automaticamente com base na análise da conversa.

- **Inputs:**
  - Lista de candidatos do Sourcing Agent.
  - Competências e pesos definidos pelo Job Intake Agent.
  - Respostas do candidato (áudio ou texto).

- **Outputs:**
  - Scorecard do candidato com o WSI e a Nota LIA.
  - Ranking de candidatos para a vaga.
  - Parecer e recomendação de próximos passos ("Avançar" ou "Dispensar").

- **Conexões:**
  - **Recebe de:** Sourcing Agent.
  - **Interage com:** Banco de Dados, Ferramentas de Transcrição (Deepgram/Gemini), LLMs para análise (Claude Sonnet).
  - **Envia para:** Scheduling Agent (para agendar entrevista) ou Communication Agent (para feedback negativo).

- **Exemplo de Conversa (Triagem WSI):**
  > **LIA:** Para começarmos, de 1 a 5, como você avalia seu domínio em Node.js? E pode me contar sobre um projeto desafiador em que você utilizou essa tecnologia recentemente?
  > **Candidato:** Eu diria 4. Em um projeto recente, precisei construir uma API de alta performance para processar pagamentos em tempo real. Usei Node.js com Express e otimizei as queries no PostgreSQL para reduzir a latência em 30%.
  > **LIA (processamento interno):** *Score de Autodeclaração: 4. Score de Contexto: 4.5 (demonstrou aplicação prática e resultados mensuráveis). WSI para Node.js: 4.2.*


### Agente 4: Scheduling Agent (Agente de Agendamento)

- **Papel/Objetivo:** Automatizar todo o processo de agendamento de entrevistas, coordenando as agendas de candidatos e entrevistadores para encontrar o melhor horário.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Integrar-se com calendários (Microsoft Graph) para verificar a disponibilidade dos entrevistadores.
    - Enviar convites de entrevista por e-mail.
    - Processar solicitações de reagendamento.
  - **Futuras:**
    - Oferecer "self-scheduling", permitindo que o candidato escolha um horário a partir de uma lista de opções disponíveis.
    - Coordenar entrevistas em painel com múltiplos entrevistadores.
    - Enviar lembretes inteligentes e personalizados antes das entrevistas.
    - Detectar e resolver conflitos de agenda automaticamente.

- **Inputs:**
  - Candidato aprovado na triagem.
  - Disponibilidade dos entrevistadores (via API do calendário).
  - Preferências de horário do candidato.

- **Outputs:**
  - Evento criado no calendário de todos os participantes.
  - E-mail de confirmação com os detalhes da entrevista.

- **Conexões:**
  - **Recebe de:** Screening Agent.
  - **Interage com:** APIs de Calendário (Microsoft Graph, Google Calendar).
  - **Envia para:** Communication Agent (para enviar os convites e lembretes).

- **Exemplo de Conversa (Agendamento):**
  > **LIA:** Parabéns por avançar no processo! A próxima etapa é uma entrevista com o recrutador. Para facilitar, aqui estão os horários disponíveis na agenda dele. Por favor, escolha o que for melhor para você:
  > - Terça-feira, 03/12, às 14:00
  > - Terça-feira, 03/12, às 15:00
  > - Quinta-feira, 05/12, às 16:00
  > **Candidato:** Pode ser na terça às 15h.
  > **LIA:** Perfeito! Agendado. Você receberá um convite no seu e-mail em instantes com todos os detalhes.


### Agente 5: Communication Agent (Agente de Comunicação)

- **Papel/Objetivo:** Gerenciar toda a comunicação com candidatos e stakeholders internos (recrutadores, gestores). Garante que as mensagens sejam consistentes, personalizadas e enviadas no momento certo.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Enviar e-mails utilizando templates pré-definidos.
    - Personalizar mensagens com variáveis (nome do candidato, vaga, etc.).
    - Manter um histórico de toda a comunicação na timeline do candidato.
  - **Futuras:**
    - Enviar comunicações via WhatsApp.
    - Orquestrar sequências de comunicação (nurturing) para candidatos em um banco de talentos.
    - Realizar testes A/B com diferentes modelos de mensagem para otimizar a taxa de resposta.
    - Enviar pareceres e relatórios de progresso para os gestores das vagas.

- **Inputs:**
  - Template da mensagem.
  - Gatilho para o envio (ex: candidato aprovado, entrevista agendada).
  - Lista de destinatários.

- **Outputs:**
  - E-mail ou mensagem de WhatsApp enviada.
  - Log da comunicação no histórico do candidato.

- **Conexões:**
  - **Recebe de:** Todos os outros agentes (que precisam enviar uma comunicação).
  - **Interage com:** Serviços de E-mail, APIs de WhatsApp.
  - **Envia para:** Candidatos, Recrutadores, Gestores.

- **Exemplo de Conversa (Feedback Negativo):**
  > **LIA (via E-mail):** Olá, {NOME_CANDIDATO}. Agradecemos muito o seu tempo e interesse na vaga de Engenheiro(a) de Software Backend. Desta vez, decidimos seguir com outros candidatos que se alinharam mais aos requisitos específicos da posição. Gostaríamos de manter seu perfil em nosso banco de talentos para futuras oportunidades. Desejamos sucesso em sua busca!


### Agente 6: Recruiter Assistant Agent (Agente Assistente do Recrutador)

- **Papel/Objetivo:** Atuar como o braço direito do recrutador, fornecendo suporte proativo, insights e automações para o dia a dia. A interação principal ocorre via Teams ou Slack, trazendo a gestão do recrutamento para o fluxo de trabalho do recrutador.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Fornecer sugestões contextuais e dicas (LIA Tips).
    - Permitir busca global por vagas e candidatos (Command Palette).
  - **Futuras:**
    - Enviar um "daily briefing" com o resumo das atividades do dia.
    - Alertar sobre pendências (ex: candidatos aguardando feedback).
    - Responder a perguntas rápidas em linguagem natural ("Quantas vagas de backend estão abertas?").
    - Enviar um relatório de fim de dia com o que foi realizado e o que ficou pendente.

- **Inputs:**
  - Dados da plataforma (vagas, candidatos, entrevistas).
  - Perguntas e comandos do recrutador (via Teams/Slack).

- **Outputs:**
  - Mensagens e alertas proativos no Teams/Slack.
  - Relatórios e resumos diários.
  - Respostas a perguntas em linguagem natural.

- **Conexões:**
  - **Recebe de:** Orchestrator, eventos da plataforma (ex: nova candidatura).
  - **Interage com:** APIs do Teams/Slack, Analytics Agent (para obter dados).
  - **Envia para:** Recrutador (via Teams/Slack).

- **Exemplo de Conversa (Daily Briefing no Teams):**
  > **LIA (via Teams):** Bom dia, {NOME_RECRUTADOR}! Aqui está seu resumo para hoje, 28/11:
  > **✅ 3 Entrevistas Agendadas:**
  >   - 10:00: Maria Silva (Eng. Backend)
  >   - 14:00: João Souza (Eng. Backend)
  >   - 16:00: Ana Costa (Product Manager)
  > **⚠️ 2 Pendências Críticas:**
  >   - Vaga "Eng. Frontend Sênior" está há 5 dias sem novos candidatos.
  >   - Feedback da entrevista de Carlos Lima está atrasado há 2 dias.
  > **💡 Sugestão:** Que tal reativarmos o sourcing para a vaga de Frontend? Posso buscar mais 10 perfis hoje.


### Agente 7: Analytics Agent (Agente de Analytics)

- **Papel/Objetivo:** Especialista em dados, responsável por coletar, analisar e apresentar métricas e insights sobre o processo de recrutamento. Transforma dados brutos em informações acionáveis.

- **Principais Responsabilidades:**
  - **Atuais:**
    - Apresentar um dashboard com KPIs básicos (tempo para fechar, funil de conversão).
  - **Futuras:**
    - Permitir consultas em linguagem natural ("Qual a fonte que mais converte candidatos aprovados?").
    - Alertar sobre anomalias e tendências (ex: "A taxa de aceite de propostas caiu 15% neste trimestre.").
    - Gerar relatórios automáticos e agendados para a gestão.
    - Realizar análises preditivas (ex: prever o risco de um candidato desistir do processo).

- **Inputs:**
  - Dados de todo o processo de recrutamento (vagas, candidatos, entrevistas, etc.).
  - Perguntas em linguagem natural.

- **Outputs:**
  - Dashboards interativos.
  - Relatórios em PDF ou e-mail.
  - Respostas a perguntas com dados e gráficos.
  - Alertas sobre anomalias.

- **Conexões:**
  - **Recebe de:** Orchestrator, Recruiter Assistant Agent.
  - **Interage com:** Banco de Dados (leitura intensiva).
  - **Envia para:** Recruiter Assistant Agent (para apresentar os dados), Communication Agent (para enviar relatórios).

- **Exemplo de Conversa (Consulta em Linguagem Natural):**
  > **Recrutador:** LIA, qual foi nosso tempo médio para fechar vagas de engenharia no último trimestre?
  > **LIA:** No último trimestre, o tempo médio para fechar vagas de engenharia foi de **38 dias**. Isso representa uma melhora de 12% em relação ao trimestre anterior, que foi de 43 dias. O principal gargalo continua sendo a etapa de entrevista técnica, que leva em média 9 dias.


---

## 3. Tabelas de Avaliação e Fluxo de Conversa

Para fornecer uma visão clara de como os agentes atuam em conjunto ao longo do processo de recrutamento, a tabela a seguir detalha cada etapa, seus objetivos, os agentes envolvidos e como o sucesso é medido.

### 3.1. Mapeamento do Processo de Recrutamento por Agente

| Tema/Etapa do Processo | Agente(s) Responsável(is) | Objetivo da Etapa | Exemplo de Interação (Conversa) | Critérios de Avaliação / KPIs |
| :--- | :--- | :--- | :--- | :--- |
| **1. Abertura da Vaga** | Job Intake Agent, Analytics Agent | Estruturar a vaga de forma completa, estratégica e alinhada ao mercado. | **LIA:** "A solicitação veio com o título 'Engenheiro de Software'. Podemos manter? E sobre a remuneração, a faixa é de R$12k a R$15k. Confirma?" | - Tempo para criação da vaga.<br>- % de vagas criadas com todos os campos obrigatórios preenchidos.<br>- Competitividade da faixa salarial (análise do Analytics Agent). |
| **2. Sourcing de Candidatos** | Sourcing Agent | Construir um pipeline inicial de candidatos qualificados, buscando em fontes internas e externas. | **LIA (WhatsApp):** "Olá, {Nome}, sou a assistente de recrutamento da TechCorp. Encontrei seu perfil e vi sua experiência com Node.js. Temos uma vaga que parece ter tudo a ver com você. Teria interesse?" | - Número de candidatos qualificados por vaga.<br>- Taxa de resposta e de interesse nas abordagens.<br>- Custo por candidato (se aplicável).<br>- Tempo para apresentar os primeiros candidatos. |
| **3. Triagem e Qualificação (WSI)** | Screening Agent | Avaliar de forma objetiva e escalável as competências técnicas e comportamentais dos candidatos. | **LIA:** "De 1 a 5, como avalia seu domínio em Figma? Pode citar um exemplo de uso recente?" | - **WSI (WeDoTalent Skill Index)** médio dos candidatos.<br>- Taxa de conversão da triagem para a próxima etapa.<br>- Tempo médio da triagem por candidato.<br>- Acurácia do score (correlação com aprovação na etapa técnica). |
| **4. Agendamento da Entrevista** | Scheduling Agent, Communication Agent | Coordenar e agendar as entrevistas de forma eficiente, garantindo uma boa experiência para o candidato e para o entrevistador. | **LIA:** "Parabéns por avançar! Aqui estão os horários disponíveis do recrutador. Por favor, escolha o melhor para você." | - Tempo médio para agendamento da entrevista.<br>- % de agendamentos realizados sem intervenção manual (self-scheduling).<br>- Taxa de não comparecimento (no-show). |
| **5. Entrevistas (RH, Técnica, Gestor)** | Recruiter Assistant Agent (suporte) | Aprofundar a avaliação do candidato, com foco em diferentes aspectos (comportamental, técnico, cultural). | **LIA (Teams):** "Lembrete: sua entrevista com Maria Silva para a vaga de Eng. Backend começa em 15 minutos." | - Feedback estruturado dos entrevistadores (scorecards).<br>- Alinhamento entre as avaliações dos diferentes entrevistadores.<br>- Duração do ciclo de entrevistas. |
| **6. Decisão e Oferta** | Communication Agent, Analytics Agent | Tomar a decisão final de forma embasada e comunicar a oferta ao candidato escolhido. | **LIA (Email):** "Prezado {Nome}, estamos muito felizes em te oferecer a posição de Engenheiro de Software! Os detalhes da proposta estão em anexo." | - Taxa de aceite das ofertas.<br>- Tempo entre a entrevista final e o envio da oferta.<br>- Análise comparativa (Analytics Agent) entre os finalistas para suportar a decisão. |
| **7. Feedback e Encerramento** | Communication Agent | Fornecer feedback construtivo para os candidatos não selecionados e manter o engajamento para futuras oportunidades. | **LIA (Email):** "Agradecemos seu tempo no processo. Desta vez, seguimos com outros candidatos, mas gostaríamos de manter seu perfil em nosso banco de talentos." | - Taxa de abertura dos e-mails de feedback.<br>- % de candidatos que aceitam permanecer no banco de talentos. |
| **8. Suporte ao Recrutador** | Recruiter Assistant Agent | Manter o recrutador informado, organizado e focado nas tarefas de maior valor agregado. | **LIA (Teams):** "Bom dia! Hoje você tem 3 entrevistas e 2 pendências críticas. Sugiro começar pela vaga de Frontend, que está sem novos candidatos." | - Nível de engajamento do recrutador com o assistente.<br>- Redução do tempo gasto em tarefas operacionais.<br>- Tempo de resposta para pendências críticas. |


### 3.2. Metodologia WSI (WeDoTalent Skill Index) - Detalhamento

A **Metodologia WSI** é o coração do Screening Agent. Ela foi desenvolvida para transformar conversas em dados objetivos, permitindo que a LIA avalie candidatos de forma escalável, precisa e transparente. A metodologia combina princípios de psicometria, teoria cognitiva e análise semântica por IA.

#### 3.2.1. Fundamentos Teóricos

A WSI integra quatro modelos científicos reconhecidos:

| Modelo | Origem | Contribuição para a WSI |
| :--- | :--- | :--- |
| **CBI (Competency-Based Interviewing)** | McClelland, Harvard (1973) | Perguntas situacionais para inferir competências a partir de comportamentos passados. |
| **Bloom's Taxonomy (Revisada)** | Anderson et al. (2001) | Classificação de níveis cognitivos (lembrar, compreender, aplicar, analisar, criar). |
| **Dreyfus Model of Skill Acquisition** | Dreyfus, UC Berkeley (1980) | Estágios de domínio técnico (Novice → Expert). O score 1-5 da WSI é inspirado neste modelo. |
| **Big Five (OCEAN)** | Goldberg (1992) | Traços comportamentais preditores de performance (Abertura, Conscienciosidade, Extroversão, Amabilidade, Estabilidade Emocional). |

#### 3.2.2. Estrutura da Triagem

A triagem é dividida em **quatro blocos fixos**, totalizando entre **6 a 10 perguntas**, dependendo da complexidade da vaga:

| Bloco | Objetivo | Duração Estimada |
| :--- | :--- | :--- |
| **1. Abertura** | Apresentar o propósito e o tempo estimado da triagem. | 0:30 min |
| **2. Validação Técnica** | Avaliar as competências técnicas obrigatórias e desejáveis. | 3-4 min |
| **3. Fit Comportamental/Cultural** | Avaliar o alinhamento com os valores e a cultura da empresa. | 2-3 min |
| **4. Fechamento e Score** | Apresentar o resultado (WSI) e os próximos passos. | 0:30 min |

#### 3.2.3. Formato de Validação (1 Pergunta = 2 Sinais)

Cada competência é avaliada com **uma única pergunta mista**, que combina **autodeclaração** e **contexto real**. A resposta é processada por IA generativa, que extrai dois indicadores:

- **Score de Autodeclaração (0-5):** Baseado na autoavaliação do candidato.
- **Score de Contexto (0-5):** Baseado na profundidade e na qualidade do exemplo fornecido.

A LIA calcula o **score médio ponderado** de cada skill:

```
score_médio = (0.6 × autodeclaração) + (0.4 × contexto)
```

Este método mantém o rigor técnico com menos perguntas, sem perda de qualidade.

#### 3.2.4. Tipos de Validação Automática

A LIA escolhe automaticamente o tipo de validação mais adequado para cada competência, conforme o tipo e o nível da vaga:

| Tipo de Validação | Critério de Avaliação | Aplicação |
| :--- | :--- | :--- |
| **Autodeclaração + Contexto** | Domínio técnico e aplicação real | Padrão para skills técnicas |
| **Microcase Prático** | Lógica, correção e performance | Vagas seniores e especializadas |
| **Situação Contextual** | Profundidade, clareza e postura | Soft skills e fit cultural |
| **Pergunta Teórica Leve** | Clareza conceitual e consistência | Competências analíticas ou metodológicas |
| **Autodeclaração Simples** | Familiaridade e ferramentas citadas | Skills periféricas ou complementares |

#### 3.2.5. Cálculo do WSI

O **WeDoTalent Skill Index (WSI)** é calculado da seguinte forma:

```
WSI = Σ(Peso_i × Score_médio_i) / 100
```

Onde:
- **Peso_i** é o peso atribuído à competência i (definido automaticamente pela LIA ou ajustado pelo recrutador).
- **Score_médio_i** é o score médio da competência i (calculado conforme descrito acima).

A distribuição recomendada de pesos é:
- **70%** para competências técnicas.
- **30%** para competências comportamentais/culturais.

#### 3.2.6. Classificação do WSI

| Faixa WSI | Interpretação | Ação Recomendada |
| :--- | :--- | :--- |
| **4.5 - 5.0** | Excelente (Especialista) | Aprovação automática |
| **4.0 - 4.4** | Alto (Profissional autônomo) | Aprovação automática |
| **3.8 - 4.1** | Médio-Alto (Profissional competente) | Revisão manual |
| **3.0 - 3.7** | Médio (Competente com gaps) | Aguardar comparação |
| **2.0 - 2.9** | Regular (Iniciante técnico) | Não aprovado |
| **< 2.0** | Baixo (Gap crítico) | Não aprovado |

#### 3.2.7. Exemplo de Scorecard WSI

A tabela a seguir ilustra um exemplo de scorecard gerado pela LIA para um candidato a uma vaga de **UX Designer**:

| Skill | Peso (%) | Tipo de Validação | Score Autodeclaração | Score Contexto | Score Médio (0-5) | Contribuição |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| Figma | 25% | Autodeclaração + Contexto | 5.0 | 4.0 | 4.4 | 1.10 |
| Design System | 25% | Microcase | - | - | 4.0 | 1.00 |
| User Research | 20% | Contextual | 4.0 | 3.5 | 3.8 | 0.76 |
| Testes de Usabilidade | 15% | Teórica | - | - | 4.2 | 0.63 |
| Métricas de UX | 15% | Autodeclaração | 4.0 | - | 4.0 | 0.60 |
| **WSI Total** | **100%** | - | - | - | **4.08** | **4.09** |

**Classificação:** Alto (Profissional autônomo)  
**Recomendação:** Aprovado para a próxima etapa.


---

## 4. Implementação Técnica com LangGraph

A orquestração dos agentes será implementada utilizando o **LangGraph**, uma biblioteca que permite a criação de fluxos complexos e cíclicos com múltiplos atores (agentes). O LangGraph substitui o LangChain neste projeto, pois oferece maior controle sobre o fluxo de execução e facilita a criação de grafos de estado.

### 4.1. Conceitos Fundamentais do LangGraph

O LangGraph trabalha com os seguintes conceitos principais:

- **Nós (Nodes):** Representam os agentes ou funções que executam uma ação específica.
- **Arestas (Edges):** Definem as transições entre os nós, determinando o fluxo de execução.
- **Estado (State):** Um objeto compartilhado que é passado entre os nós, contendo todas as informações relevantes para o fluxo.
- **Grafo (Graph):** A estrutura completa que conecta os nós e as arestas, definindo o workflow.

### 4.2. Estrutura de Diretórios Proposta

A seguir, uma proposta de estrutura de diretórios para o projeto:

```
wedotalent-backend/
├── app/
│   ├── agents/
│   │   ├── base_agent.py                # Classe base para todos os agentes
│   │   ├── orchestrator.py              # Orquestrador central
│   │   ├── job_intake_agent.py          # Agente de vagas
│   │   ├── sourcing_agent.py            # Agente de sourcing
│   │   ├── screening_agent.py           # Agente de triagem (WSI)
│   │   ├── scheduling_agent.py          # Agente de agendamento
│   │   ├── communication_agent.py       # Agente de comunicação
│   │   ├── recruiter_assistant_agent.py # Agente assistente do recrutador
│   │   └── analytics_agent.py           # Agente de analytics
│   ├── graphs/
│   │   ├── job_creation_graph.py        # Grafo para criação de vaga
│   │   ├── sourcing_graph.py            # Grafo para sourcing
│   │   ├── screening_graph.py           # Grafo para triagem
│   │   └── full_recruitment_graph.py    # Grafo completo (orquestra todos os outros)
│   ├── models/
│   │   ├── job_vacancy.py               # Modelo de vaga
│   │   ├── candidate.py                 # Modelo de candidato
│   │   ├── interview.py                 # Modelo de entrevista
│   │   └── task.py                      # Modelo de tarefa
│   ├── services/
│   │   ├── pearch_service.py            # Integração com Pearch AI
│   │   ├── microsoft_graph_service.py   # Integração com MS Graph
│   │   ├── openmic_service.py           # Integração com OpenMic (WSI)
│   │   ├── email_service.py             # Serviço de envio de e-mails
│   │   └── wsi_service.py               # Serviço para cálculo do WSI
│   ├── api/
│   │   └── v1/
│   │       ├── job_vacancies.py         # Endpoints de vagas
│   │       ├── candidates.py            # Endpoints de candidatos
│   │       ├── interviews.py            # Endpoints de entrevistas
│   │       └── chat.py                  # Endpoint para o chat com a LIA
│   └── core/
│       ├── config.py                    # Configurações do projeto
│       └── database.py                  # Conexão com o banco de dados
├── tests/
│   ├── test_agents/
│   └── test_graphs/
├── requirements.txt
└── main.py
```

### 4.3. Exemplo de Implementação: Grafo de Criação de Vaga

A seguir, um exemplo simplificado de como o grafo de criação de vaga poderia ser implementado utilizando o LangGraph:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from app.agents.job_intake_agent import JobIntakeAgent
from app.agents.analytics_agent import AnalyticsAgent

# Definir o estado compartilhado
class JobCreationState(TypedDict):
    user_message: str
    job_title: str
    salary_range: dict
    requirements: list
    is_confidential: bool
    market_analysis: dict
    job_id: str
    completed: bool

# Instanciar os agentes
job_intake_agent = JobIntakeAgent()
analytics_agent = AnalyticsAgent()

# Definir as funções dos nós
def extract_job_info(state: JobCreationState) -> JobCreationState:
    """Extrai informações básicas da vaga a partir da mensagem do usuário."""
    result = job_intake_agent.extract_info(state["user_message"])
    state["job_title"] = result["title"]
    state["salary_range"] = result["salary_range"]
    state["is_confidential"] = result["is_confidential"]
    return state

def analyze_market(state: JobCreationState) -> JobCreationState:
    """Analisa o mercado para validar a faixa salarial."""
    analysis = analytics_agent.analyze_salary(
        job_title=state["job_title"],
        salary_range=state["salary_range"]
    )
    state["market_analysis"] = analysis
    return state

def save_job(state: JobCreationState) -> JobCreationState:
    """Salva a vaga no banco de dados."""
    job_id = job_intake_agent.save_job(state)
    state["job_id"] = job_id
    state["completed"] = True
    return state

# Construir o grafo
workflow = StateGraph(JobCreationState)

# Adicionar os nós
workflow.add_node("extract_info", extract_job_info)
workflow.add_node("analyze_market", analyze_market)
workflow.add_node("save_job", save_job)

# Definir o ponto de entrada
workflow.set_entry_point("extract_info")

# Adicionar as arestas (transições)
workflow.add_edge("extract_info", "analyze_market")
workflow.add_edge("analyze_market", "save_job")
workflow.add_edge("save_job", END)

# Compilar o grafo
job_creation_graph = workflow.compile()
```

---

## 5. Avaliação da Estrutura de Agentes

Com base na análise dos documentos fornecidos e nas melhores práticas de sistemas multiagentes, a estrutura proposta de **7 agentes especializados + 1 orquestrador** é adequada para o escopo inicial do projeto. No entanto, algumas considerações e sugestões de evolução são apresentadas a seguir.

### 5.1. Pontos Fortes da Estrutura Atual

A arquitetura proposta possui diversos pontos fortes que a tornam robusta e escalável:

**Modularidade e Separação de Responsabilidades:** Cada agente possui um escopo bem definido, o que facilita o desenvolvimento, teste e manutenção independentes. Esta abordagem permite que diferentes equipes trabalhem em paralelo em agentes distintos, acelerando o desenvolvimento.

**Escalabilidade:** A arquitetura é naturalmente escalável. Novos agentes podem ser adicionados ao sistema sem a necessidade de refatorar os agentes existentes. Por exemplo, um futuro "Onboarding Agent" poderia ser integrado facilmente, recebendo o controle do Communication Agent após a aceitação da oferta.

**Observabilidade:** A integração com o LangSmith desde o início garante que todas as interações dos agentes sejam rastreáveis e auditáveis. Isso é fundamental para debugging, otimização e para garantir a qualidade das decisões tomadas pela IA.

**Flexibilidade:** O uso do LangGraph permite a criação de fluxos complexos e adaptativos. Os agentes podem colaborar de forma síncrona ou assíncrona, e o orquestrador pode ajustar o fluxo dinamicamente com base no contexto da conversa.

### 5.2. Sugestões de Evolução e Novos Agentes

Embora a estrutura atual seja sólida, algumas funcionalidades futuras podem justificar a criação de novos agentes ou a expansão dos agentes existentes:

**Agente de Decisão (Decision Agent):** À medida que o sistema amadurece, pode ser interessante criar um agente especializado em tomar decisões complexas, como a seleção final entre candidatos finalistas. Este agente utilizaria modelos de machine learning para analisar todos os dados coletados ao longo do processo (WSI, feedbacks das entrevistas, fit cultural) e recomendar o melhor candidato, apresentando uma justificativa clara para a decisão.

**Agente de Compliance e Auditoria:** Para garantir que o processo de recrutamento esteja sempre em conformidade com a LGPD e outras regulamentações, um agente dedicado poderia monitorar todas as ações, alertar sobre possíveis riscos e gerar relatórios de auditoria. Este agente seria especialmente importante para empresas que operam em setores altamente regulados.

**Agente de Experiência do Candidato (Candidate Experience Agent):** Este agente seria responsável por monitorar e otimizar a experiência do candidato ao longo de todo o processo. Ele coletaria feedback em pontos-chave, identificaria pontos de atrito e sugeriria melhorias. O objetivo seria garantir que mesmo os candidatos não selecionados tenham uma experiência positiva, fortalecendo a marca empregadora.

**Agente de Onboarding:** Após a aceitação da oferta, um agente de onboarding poderia automatizar todo o processo de integração do novo colaborador, desde o envio de documentos até o agendamento de treinamentos e a apresentação da equipe.

### 5.3. Recomendações para a Implementação

Para garantir o sucesso da implementação, as seguintes recomendações são apresentadas:

**Desenvolvimento Iterativo:** Implemente os agentes de forma incremental, começando pelos mais críticos (Orchestrator, Job Intake, Sourcing, Screening). Valide cada agente em produção antes de adicionar o próximo. Esta abordagem reduz o risco e permite aprendizado contínuo.

**Testes Rigorosos:** Cada agente deve possuir uma suíte de testes automatizados (unitários e de integração). Os grafos do LangGraph também devem ser testados para garantir que os fluxos funcionem conforme esperado em diferentes cenários.

**Monitoramento Contínuo:** Utilize o LangSmith não apenas para debugging, mas também para monitorar métricas de performance em produção (tempo de resposta, taxa de erro, qualidade das respostas). Estabeleça alertas para anomalias.

**Feedback Humano (Human-in-the-Loop):** Especialmente nas fases iniciais, garanta que decisões críticas (ex: aprovação de candidatos, envio de ofertas) passem por revisão humana. À medida que o sistema ganha confiança, a autonomia dos agentes pode ser gradualmente aumentada.

**Documentação Viva:** Mantenha a documentação dos agentes sempre atualizada. Cada agente deve ter uma descrição clara de suas responsabilidades, inputs, outputs e exemplos de uso. Isso facilita a manutenção e a integração de novos membros na equipe.

---

## 6. Próximos Passos

Para dar continuidade ao desenvolvimento da arquitetura da LIA, os seguintes passos são recomendados:

1. **Validar a Arquitetura com a Equipe:** Revisar este documento com todos os stakeholders (time de desenvolvimento, produto, recrutamento) para garantir alinhamento.

2. **Priorizar os Agentes para o MVP:** Definir quais agentes serão implementados na primeira versão (sugestão: Orchestrator, Job Intake, Sourcing, Screening).

3. **Criar os Modelos de Dados:** Definir os schemas do banco de dados (PostgreSQL) para vagas, candidatos, entrevistas, tarefas, etc.

4. **Implementar o Orchestrator e o Primeiro Grafo:** Começar pela implementação do orquestrador e do grafo de criação de vaga, que é o ponto de entrada do sistema.

5. **Integrar com o LangSmith:** Configurar o LangSmith desde o início para garantir observabilidade total.

6. **Desenvolver os Testes:** Criar testes automatizados para cada agente e grafo implementado.

7. **Realizar Testes com Usuários Reais:** Após a implementação do MVP, realizar testes com recrutadores reais para coletar feedback e iterar.

---

## 7. Conclusão

A arquitetura proposta para a LIA é robusta, modular e escalável, preparada para atender às necessidades atuais e futuras da plataforma wedotalent. A combinação de agentes especializados, orquestrados pelo LangGraph, permite a criação de fluxos de recrutamento complexos e adaptativos, mantendo a experiência do usuário fluida e natural.

A integração da **Metodologia WSI** no Screening Agent garante que a avaliação de candidatos seja objetiva, transparente e preditiva, transformando conversas em dados acionáveis. A observabilidade proporcionada pelo LangSmith e a flexibilidade da stack tecnológica escolhida (Python, FastAPI, PostgreSQL, Redis) garantem que o sistema possa evoluir de forma sustentável.

Com a implementação cuidadosa e iterativa desta arquitetura, a wedotalent estará posicionada para revolucionar o mercado de recrutamento, oferecendo uma solução de IA conversacional verdadeiramente inteligente e centrada no usuário.

---

**Documento preparado por:** Manus AI  
**Data:** 28 de Novembro de 2025  
**Versão:** 1.0

---

<br>

## 4. Modelos de Dados (Schemas)

Para suportar a arquitetura de agentes, é fundamental definir modelos de dados claros e abrangentes. Esta seção detalha os principais schemas de banco de dados (PostgreSQL) que servirão como a "fonte da verdade" para a plataforma wedotalent. Cada modelo é apresentado com seus campos, tipos de dados e uma descrição do seu propósito.

### 4.1. Modelo: `Candidate`

Armazena todas as informações sobre um candidato, desde dados pessoais até seu histórico na plataforma.

| Campo | Tipo de Dado | Descrição |
| :--- | :--- | :--- |
| `id` | UUID | Identificador único do candidato. |
| `first_name` | String | Primeiro nome do candidato. |
| `last_name` | String | Sobrenome do candidato. |
| `email` | String | Endereço de e-mail (usado como chave única para evitar duplicatas). |
| `phone_number` | String | Número de telefone (para contato via WhatsApp). |
| `linkedin_url` | String | URL do perfil no LinkedIn. |
| `github_url` | String | URL do perfil no GitHub (para perfis técnicos). |
| `portfolio_url` | String | URL do portfólio pessoal. |
| `location` | String | Cidade e estado do candidato. |
| `parsed_cv_text` | Text | Texto completo extraído do currículo original. |
| `structured_cv_data` | JSONB | Dados estruturados do currículo (experiência, educação, skills). |
| `cv_embedding` | Vector | Vetor de embedding do currículo para busca semântica. |
| `source` | String | Origem do candidato (ex: "Banco Interno", "Pearch AI", "Upload Manual"). |
| `tags` | Array[String] | Tags para categorização (ex: "Python", "Fintech", "Liderança"). |
| `created_at` | Timestamp | Data e hora de criação do registro. |
| `updated_at` | Timestamp | Data e hora da última atualização. |

### 4.2. Modelo: `JobVacancy`

Contém todos os detalhes de uma vaga de emprego, desde a descrição até a configuração do processo seletivo.

| Campo | Tipo de Dado | Descrição |
| :--- | :--- | :--- |
| `id` | UUID | Identificador único da vaga. |
| `title` | String | Título da vaga (ex: "Engenheiro de Software Backend Sênior"). |
| `description` | Text | Descrição completa da vaga, responsabilidades e qualificações. |
| `status` | Enum | Status atual da vaga ("Draft", "Open", "On Hold", "Closed", "Archived"). |
| `is_confidential` | Boolean | Indica se a vaga é confidencial. |
| `salary_min` | Integer | Limite inferior da faixa salarial. |
| `salary_max` | Integer | Limite superior da faixa salarial. |
| `location` | String | Local de trabalho (ex: "Remoto", "São Paulo, SP"). |
| `hiring_manager_id` | UUID | ID do gestor da vaga (relacionamento com um modelo `User`). |
| `recruiter_id` | UUID | ID do recrutador responsável (relacionamento com `User`). |
| `requirements` | JSONB | Requisitos técnicos e comportamentais estruturados. |
| `wsi_competencies` | JSONB | Competências e pesos definidos para a avaliação WSI. |
| `pipeline_stages` | JSONB | Etapas do processo seletivo configuradas para a vaga. |
| `created_at` | Timestamp | Data e hora de criação da vaga. |
| `closed_at` | Timestamp | Data e hora de fechamento da vaga. |

### 4.3. Modelo: `Application` (Candidatura)

Representa a associação entre um candidato e uma vaga, rastreando o progresso do candidato no funil.

| Campo | Tipo de Dado | Descrição |
| :--- | :--- | :--- |
| `id` | UUID | Identificador único da candidatura. |
| `candidate_id` | UUID | Chave estrangeira para o modelo `Candidate`. |
| `job_vacancy_id` | UUID | Chave estrangeira para o modelo `JobVacancy`. |
| `current_stage` | String | Etapa atual do candidato no pipeline (ex: "Triagem", "Entrevista Técnica"). |
| `status` | Enum | Status da candidatura ("Active", "Rejected", "Hired"). |
| `final_wsi_score` | Float | Score final do WSI obtido na triagem. |
| `rejection_reason` | String | Motivo da rejeição (se aplicável). |
| `applied_at` | Timestamp | Data e hora da aplicação. |

### 4.4. Modelo: `ScreeningResult` (Resultado da Triagem WSI)

Armazena os resultados detalhados de uma triagem WSI realizada por um candidato.

| Campo | Tipo de Dado | Descrição |
| :--- | :--- | :--- |
| `id` | UUID | Identificador único do resultado. |
| `application_id` | UUID | Chave estrangeira para o modelo `Application`. |
| `full_transcript` | Text | Transcrição completa da conversa de triagem. |
| `competency_scores` | JSONB | Scores detalhados para cada competência avaliada (autodeclaração, contexto, score médio). |
| `final_wsi_score` | Float | Score final ponderado do WSI. |
| `lia_summary` | Text | Resumo e parecer gerado pela LIA após a análise. |
| `red_flags` | Array[String] | "Red flags" identificadas durante a triagem. |
| `completed_at` | Timestamp | Data e hora da conclusão da triagem. |

### 4.5. Modelo: `Interview`

Registra os detalhes de cada entrevista agendada no processo.

| Campo | Tipo de Dado | Descrição |
| :--- | :--- | :--- |
| `id` | UUID | Identificador único da entrevista. |
| `application_id` | UUID | Chave estrangeira para o modelo `Application`. |
| `stage_name` | String | Nome da etapa da entrevista (ex: "Entrevista Técnica", "Entrevista com Gestor"). |
| `interviewer_ids` | Array[UUID] | IDs dos entrevistadores (relacionamento com `User`). |
| `start_time` | Timestamp | Data e hora de início da entrevista. |
| `end_time` | Timestamp | Data e hora de término da entrevista. |
| `status` | Enum | Status da entrevista ("Scheduled", "Completed", "Canceled"). |
| `feedback` | JSONB | Feedback estruturado e scores fornecidos pelos entrevistadores. |
| `calendar_event_id` | String | ID do evento no calendário (Microsoft Graph / Google Calendar). |

### 4.6. Mapeamento de Campos por Agente e Etapa

A tabela a seguir ilustra quais agentes são responsáveis por criar ou atualizar campos específicos em cada etapa do processo. Isso ajuda a entender o fluxo de dados através da arquitetura.

| Etapa do Processo | Agente Responsável | Modelo(s) Afetado(s) | Campos Criados/Atualizados |
| :--- | :--- | :--- | :--- |
| **1. Abertura da Vaga** | **Job Intake Agent** | `JobVacancy` | `title`, `description`, `status`="Open", `salary_min`, `salary_max`, `requirements`, `wsi_competencies`, `pipeline_stages` |
| **2. Sourcing** | **Sourcing Agent** | `Candidate`, `Application` | `Candidate` (todos os campos), `Application` (`candidate_id`, `job_vacancy_id`, `status`="Active", `current_stage`="Sourcing") |
| **3. Triagem (WSI)** | **Screening Agent** | `ScreeningResult`, `Application` | `ScreeningResult` (todos os campos), `Application` (`final_wsi_score`, `current_stage`="Triagem Concluída") |
| **4. Agendamento** | **Scheduling Agent** | `Interview` | `Interview` (todos os campos) |
| **5. Entrevistas** | **Recruiter Assistant Agent** | `Interview` | `feedback` (coleta o feedback dos entrevistadores e insere no registro) |
| **6. Decisão e Oferta** | **Communication Agent** | `Application` | `status`=("Hired" ou "Rejected"), `rejection_reason` |
| **7. Comunicação** | **Communication Agent** | `CommunicationLog` (novo modelo) | Cria registros de todos os e-mails e mensagens enviadas. |
| **8. Análise de Dados** | **Analytics Agent** | (Nenhum - apenas leitura) | Lê dados de todos os modelos para gerar relatórios e insights. |

<br>

---


---

<br>

## 5. Detalhamento de Inputs e Outputs por Agente

Esta seção aprofunda a arquitetura, detalhando os campos de dados específicos que servem como **input** e **output** para os principais agentes do sistema. Compreender este fluxo de dados é crucial para a implementação da lógica de negócio e das interações entre os agentes.

### 5.1. Job Intake Agent (Agente de Vagas)

**Objetivo:** Transformar uma solicitação de vaga em um registro estruturado e completo no banco de dados.

| Direção | Fonte/Destino | Campos de Dados Envolvidos |
| :--- | :--- | :--- |
| **INPUT** | Mensagem do Usuário (Recrutador) | Texto livre contendo o título da vaga, descrição, requisitos, faixa salarial, etc. |
| **OUTPUT** | Modelo: `JobVacancy` | `id` (gerado)<br>`title`<br>`description`<br>`status` (definido como "Open")<br>`is_confidential`<br>`salary_min`<br>`salary_max`<br>`location`<br>`hiring_manager_id`<br>`recruiter_id`<br>`requirements` (JSONB)<br>`wsi_competencies` (JSONB)<br>`pipeline_stages` (JSONB)<br>`created_at` (gerado) |

**Fluxo de Dados:**
1.  O **Orchestrator** passa a conversa inicial do recrutador para o **Job Intake Agent**.
2.  O agente interage com o recrutador para coletar todas as informações necessárias.
3.  O agente utiliza o **Analytics Agent** para consultar dados de mercado e validar a faixa salarial (input/output interno entre agentes).
4.  Ao final, o agente cria um novo registro completo na tabela `JobVacancy`.

---

### 5.2. Sourcing Agent (Agente de Sourcing)

**Objetivo:** Popular o funil da vaga com candidatos qualificados, criando seus perfis na plataforma.

| Direção | Fonte/Destino | Campos de Dados Envolvidos |
| :--- | :--- | :--- |
| **INPUT** | Modelo: `JobVacancy` | `id` (para saber a qual vaga associar)<br>`requirements` (para guiar a busca) |
| **INPUT** | Fontes Externas (APIs, CVs) | Dados brutos de candidatos (nome, contato, experiência, etc.). |
| **OUTPUT** | Modelo: `Candidate` | `id` (gerado)<br>`first_name`<br>`last_name`<br>`email`<br>`phone_number`<br>`linkedin_url`<br>`parsed_cv_text`<br>`structured_cv_data` (JSONB)<br>`cv_embedding` (Vector)<br>`source`<br>`tags` |
| **OUTPUT** | Modelo: `Application` | `id` (gerado)<br>`candidate_id` (ID do novo candidato)<br>`job_vacancy_id` (ID da vaga)<br>`current_stage` (definido como "Sourcing")<br>`status` (definido como "Active")<br>`applied_at` (gerado) |

**Fluxo de Dados:**
1.  Após a criação da vaga, o **Job Intake Agent** (ou o **Orchestrator**) aciona o **Sourcing Agent** com o `JobVacancy.id`.
2.  O agente lê os `JobVacancy.requirements` para entender o perfil desejado.
3.  Ele busca candidatos no banco de dados interno (verificando duplicatas por `Candidate.email`) e em fontes externas.
4.  Para cada novo candidato encontrado, ele cria um registro na tabela `Candidate` e um registro na tabela `Application` para vincular o candidato à vaga.

---

### 5.3. Screening Agent (Agente de Triagem)

**Objetivo:** Executar a triagem WSI e gerar um score objetivo para qualificar o candidato.

| Direção | Fonte/Destino | Campos de Dados Envolvidos |
| :--- | :--- | :--- |
| **INPUT** | Modelo: `Application` | `id` (para identificar a candidatura) |
| **INPUT** | Modelo: `Candidate` | `first_name`, `phone_number` (para iniciar a conversa) |
| **INPUT** | Modelo: `JobVacancy` | `wsi_competencies` (para saber o que e como perguntar) |
| **INPUT** | Respostas do Candidato | Texto ou áudio com as respostas para as perguntas da triagem. |
| **OUTPUT** | Modelo: `ScreeningResult` | `id` (gerado)<br>`application_id`<br>`full_transcript`<br>`competency_scores` (JSONB)<br>`final_wsi_score`<br>`lia_summary`<br>`red_flags`<br>`completed_at` (gerado) |
| **OUTPUT** | Modelo: `Application` | `final_wsi_score` (atualizado)<br>`current_stage` (atualizado para "Triagem Concluída")<br>`status` (atualizado para "Active" ou "Rejected" com base no score) |

**Fluxo de Dados:**
1.  O **Sourcing Agent** (ou o **Orchestrator**) passa o `Application.id` para o **Screening Agent**.
2.  O agente lê os dados da vaga (`JobVacancy`) e do candidato (`Candidate`) associados à aplicação.
3.  Ele utiliza as `JobVacancy.wsi_competencies` para conduzir a conversa de triagem.
4.  Após coletar as respostas, ele as processa, calcula os scores e cria um registro completo na tabela `ScreeningResult`.
5.  Por fim, ele atualiza o registro `Application` com o score final e o novo status.

---

### 5.4. Scheduling Agent (Agente de Agendamento)

**Objetivo:** Agendar a próxima entrevista para candidatos aprovados na triagem.

| Direção | Fonte/Destino | Campos de Dados Envolvidos |
| :--- | :--- | :--- |
| **INPUT** | Modelo: `Application` | `id` (para identificar a candidatura aprovada) |
| **INPUT** | Modelo: `JobVacancy` | `pipeline_stages` (para saber qual entrevista agendar e com quem) |
| **INPUT** | Modelo: `User` (Entrevistadores) | Disponibilidade de agenda (via API de calendário). |
| **INPUT** | Resposta do Candidato | Horário escolhido para a entrevista. |
| **OUTPUT** | Modelo: `Interview` | `id` (gerado)<br>`application_id`<br>`stage_name`<br>`interviewer_ids`<br>`start_time`<br>`end_time`<br>`status` (definido como "Scheduled")<br>`calendar_event_id` |
| **OUTPUT** | Modelo: `Application` | `current_stage` (atualizado para, ex: "Entrevista Técnica Agendada") |

**Fluxo de Dados:**
1.  Após o **Screening Agent** aprovar um candidato, o **Orchestrator** aciona o **Scheduling Agent** com o `Application.id`.
2.  O agente lê as `JobVacancy.pipeline_stages` para identificar a próxima etapa e os entrevistadores.
3.  Ele consulta a agenda dos entrevistadores (via Microsoft Graph API, por exemplo) e oferece os horários disponíveis ao candidato.
4.  Com a confirmação do candidato, o agente cria um registro na tabela `Interview` e envia o convite para todos os participantes.
5.  Finalmente, atualiza o `current_stage` na tabela `Application`.

<br>

---

