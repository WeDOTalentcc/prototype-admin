"""
Seed WSI Demo Data - Creates realistic WSI screening evaluations for demo candidates.
Populates: wsi_sessions, wsi_questions, wsi_response_analyses, wsi_results, wsi_reports, wsi_feedbacks
"""
import os
import sys
import uuid
import json
import asyncio
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VACANCY_ID = "4a6a6be6-4068-4d43-bfe4-0ac9880dadc9"
VACANCY_TITLE = "Desenvolvedor(a) Full Stack Sênior"

CANDIDATES = [
    {
        "id": "dd05cf5f-6761-45ab-90ac-08dcf89725a7",
        "name": "Mariana Costa Oliveira",
        "title": "Senior Software Engineer",
        "screening_type": "voice",
        "overall": 4.60, "technical": 4.70, "behavioral": 4.40,
        "classification": "excelente", "percentile": 92,
        "decision": "aprovado"
    },
    {
        "id": "cc4966df-2ef5-4ffc-be0a-82ec6461de8c",
        "name": "Ana Beatriz Santos",
        "title": "UX Designer Senior",
        "screening_type": "chat",
        "overall": 4.20, "technical": 3.90, "behavioral": 4.70,
        "classification": "alto", "percentile": 85,
        "decision": "aprovado"
    },
    {
        "id": "1bb0811f-4ae4-4d18-9538-704cee192aad",
        "name": "Julia Nascimento Rosa",
        "title": "DevOps Engineer",
        "screening_type": "voice",
        "overall": 4.35, "technical": 4.50, "behavioral": 4.10,
        "classification": "alto", "percentile": 88,
        "decision": "aprovado"
    },
    {
        "id": "aace87ea-b16e-434d-a505-b0ce17e4a4b5",
        "name": "André Luis Pereira",
        "title": "Backend Developer",
        "screening_type": "chat",
        "overall": 3.80, "technical": 4.10, "behavioral": 3.30,
        "classification": "alto", "percentile": 72,
        "decision": "aprovado"
    },
    {
        "id": "8f8e3c93-d8fa-4ab1-aa39-b605348e12cb",
        "name": "Isabela Martins Ramos",
        "title": "Marketing Manager",
        "screening_type": "chat",
        "overall": 3.10, "technical": 2.60, "behavioral": 3.80,
        "classification": "medio", "percentile": 45,
        "decision": "aguardando"
    },
    {
        "id": "94709e7c-883d-4892-ad25-8cc9a36ee208",
        "name": "Gabriel Ferreira Lima",
        "title": "Data Analyst",
        "screening_type": "voice",
        "overall": 3.50, "technical": 3.70, "behavioral": 3.20,
        "classification": "medio", "percentile": 60,
        "decision": "aprovado"
    },
    {
        "id": "a64b75cc-3818-499b-a769-a3a5651a7b31",
        "name": "Thiago Barbosa Souza",
        "title": "Mobile Developer",
        "screening_type": "voice",
        "overall": 3.90, "technical": 4.20, "behavioral": 3.40,
        "classification": "alto", "percentile": 78,
        "decision": "aprovado"
    },
    {
        "id": "9792b94a-e25b-41f3-adea-0ae5e54a2046",
        "name": "Carolina Vieira Nunes",
        "title": "Product Designer",
        "screening_type": "chat",
        "overall": 3.40, "technical": 3.10, "behavioral": 3.80,
        "classification": "medio", "percentile": 55,
        "decision": "aguardando"
    },
    {
        "id": "809d364f-63f5-449e-935e-90e273732acf",
        "name": "Fernanda Lima Castro",
        "title": "HR Business Partner",
        "screening_type": "chat",
        "overall": 2.40, "technical": 1.80, "behavioral": 3.30,
        "classification": "regular", "percentile": 22,
        "decision": "nao_aprovado"
    },
    {
        "id": "95a3658b-44ce-42b0-b89b-efa1876235de",
        "name": "Camila Rodrigues Pinto",
        "title": "Desenvolvedora Backend Jr",
        "screening_type": "voice",
        "overall": 2.80, "technical": 2.90, "behavioral": 2.60,
        "classification": "regular", "percentile": 30,
        "decision": "nao_aprovado"
    },
    {
        "id": "e74b0391-ac32-4ce8-89b8-8a9cdcfff85c",
        "name": "Diego Santos Machado",
        "title": "Data Scientist",
        "screening_type": "voice",
        "overall": 4.45, "technical": 4.60, "behavioral": 4.20,
        "classification": "alto", "percentile": 90,
        "decision": "aprovado"
    },
    {
        "id": "d538fef9-91a7-4fc9-8a49-fb2d2d23f0dd",
        "name": "Lucas Mendes Silva",
        "title": "Desenvolvedor Full Stack",
        "screening_type": "voice",
        "overall": 4.75, "technical": 4.80, "behavioral": 4.65,
        "classification": "excelente", "percentile": 95,
        "decision": "aprovado"
    },
]

QUESTIONS_TEMPLATES = [
    {
        "competency": "Arquitetura de Software",
        "framework": "CBI",
        "question_type": "contextual",
        "question_text": "Descreva um projeto onde você teve que tomar decisões arquiteturais importantes. Qual foi o contexto, quais alternativas você considerou e qual foi o resultado?",
        "weight": 0.20,
        "expected_signals": ["SOLID principles", "trade-off analysis", "scalability", "performance"],
        "scoring_criteria": {"1": "Sem experiência arquitetural", "3": "Decisões básicas", "5": "Arquitetura complexa com trade-offs bem fundamentados"}
    },
    {
        "competency": "Desenvolvimento Full Stack",
        "framework": "Dreyfus",
        "question_type": "microcase",
        "question_text": "Você precisa implementar um sistema de notificações em tempo real que suporte 100k usuários simultâneos. Como você abordaria frontend, backend e infraestrutura?",
        "weight": 0.20,
        "expected_signals": ["WebSocket/SSE", "message queues", "horizontal scaling", "caching"],
        "scoring_criteria": {"1": "Solução simplista", "3": "Abordagem funcional", "5": "Solução escalável e bem fundamentada"}
    },
    {
        "competency": "APIs e Integrações",
        "framework": "Bloom",
        "question_type": "contextual",
        "question_text": "Me conte sobre a API mais complexa que você projetou ou manteve. Quais padrões utilizou? Como lidou com versionamento, autenticação e documentação?",
        "weight": 0.15,
        "expected_signals": ["REST/GraphQL", "OAuth/JWT", "API versioning", "OpenAPI"],
        "scoring_criteria": {"1": "APIs básicas CRUD", "3": "APIs com autenticação e versionamento", "5": "APIs complexas com padrões avançados"}
    },
    {
        "competency": "Resolução de Problemas",
        "framework": "CBI",
        "question_type": "situational",
        "question_text": "Conte-me sobre um bug crítico em produção que você resolveu. Qual era o problema, como diagnosticou e qual foi a solução? O que fez para evitar recorrência?",
        "weight": 0.15,
        "expected_signals": ["systematic debugging", "root cause analysis", "monitoring", "post-mortem"],
        "scoring_criteria": {"1": "Abordagem aleatória", "3": "Debug sistemático", "5": "RCA completo com prevenção"}
    },
    {
        "competency": "Colaboração e Comunicação",
        "framework": "BigFive",
        "question_type": "situational",
        "question_text": "Descreva uma situação onde houve um desacordo técnico significativo com um colega ou líder. Como você conduziu a discussão e qual foi o resultado?",
        "weight": 0.15,
        "expected_signals": ["active listening", "empathy", "compromise", "data-driven argument"],
        "scoring_criteria": {"1": "Conflito sem resolução", "3": "Resolução aceitável", "5": "Resolução construtiva com aprendizado mútuo"}
    },
    {
        "competency": "Liderança Técnica",
        "framework": "CBI",
        "question_type": "contextual",
        "question_text": "Me fale sobre uma iniciativa técnica que você liderou - pode ser uma migração, implementação de novas práticas, mentoria de time. Qual foi seu papel e o impacto gerado?",
        "weight": 0.15,
        "expected_signals": ["initiative", "mentoring", "technical vision", "measurable impact"],
        "scoring_criteria": {"1": "Sem experiência de liderança", "3": "Liderança pontual", "5": "Liderança consistente com impacto mensurável"}
    }
]

TRANSCRIPT_TEMPLATES = {
    "excelente": [
        {"type": "lia", "ts": "14:00", "msg": "Olá, {name}! Sou a LIA, assistente de recrutamento inteligente. Obrigada por aceitar participar da triagem para a vaga de {vacancy}. Vamos conversar sobre sua experiência e competências. Está pronta(o)?"},
        {"type": "candidate", "ts": "14:01", "msg": "Olá LIA! Sim, estou pronta. Pode começar."},
        {"type": "lia", "ts": "14:02", "msg": "Ótimo! Começando pela sua experiência com arquitetura de software. Descreva um projeto onde você teve que tomar decisões arquiteturais importantes."},
        {"type": "candidate", "ts": "14:05", "msg": "No meu projeto mais recente, liderei a migração de uma arquitetura monolítica para microsserviços. Analisei 3 alternativas: decomposição por domínio, por funcionalidade técnica e strangler fig pattern. Optei pelo strangler fig combinado com domain-driven design, o que permitiu migrar gradualmente sem downtime. Implementamos event sourcing para comunicação entre serviços, reduzimos o tempo de deploy de 2h para 15min e melhoramos a resiliência - nosso uptime passou de 99.2% para 99.95%."},
        {"type": "lia", "ts": "14:06", "msg": "Excelente resposta! Agora sobre Full Stack: como você abordaria um sistema de notificações em tempo real para 100k usuários simultâneos?"},
        {"type": "candidate", "ts": "14:10", "msg": "Primeiro, separaria a arquitetura em camadas. No frontend, usaria WebSocket com fallback para SSE e polling longo. No backend, implementaria um serviço dedicado de notificações com Redis Pub/Sub para broadcasting e RabbitMQ para garantia de entrega. Para escalar horizontalmente, usaria sticky sessions no load balancer com health checks. Implementaria também um sistema de priorização - notificações críticas via push nativo, regulares via in-app, e batch diário por email. Com essa arquitetura, já suportei 150k conexões simultâneas no projeto anterior."},
        {"type": "lia", "ts": "14:11", "msg": "Impressionante! Me conte sobre a API mais complexa que você projetou."},
        {"type": "candidate", "ts": "14:15", "msg": "Projetei uma API GraphQL com mais de 200 types para um marketplace financeiro. Implementei federation com Apollo para compor dados de 8 microsserviços. Usamos JWT com refresh tokens e rate limiting por cliente. Para versionamento, usamos schema evolution com deprecation gradual. A documentação era auto-gerada via introspecção e publicada no Notion. O ponto mais desafiador foi otimizar N+1 queries com DataLoader e implementar cursor-based pagination para conjuntos de dados com milhões de registros."},
        {"type": "lia", "ts": "14:16", "msg": "Sobre resolução de problemas: conte sobre um bug crítico em produção que você resolveu."},
        {"type": "candidate", "ts": "14:20", "msg": "Tivemos um memory leak em produção que causava crashes a cada 6 horas. Comecei analisando os dumps de memória com Chrome DevTools e correlacionei com logs do APM. Identifiquei que o problema estava em event listeners não removidos em um componente React que fazia polling. Além do fix imediato, implementei um circuit breaker, adicionei métricas de memória no Grafana, e criei uma policy de cleanup automático. Fiz um post-mortem documentado e implementamos testes de stress automatizados no CI para prevenir recorrência."},
        {"type": "lia", "ts": "14:21", "msg": "Sobre colaboração: descreva um desacordo técnico significativo que você vivenciou."},
        {"type": "candidate", "ts": "14:25", "msg": "Tive um desacordo com o Tech Lead sobre usar TypeScript vs JavaScript puro em um novo projeto. Em vez de insistir, propus um experimento: implementamos o mesmo módulo nas duas abordagens e medimos tempo de desenvolvimento, bugs em code review e facilidade de onboarding. Os dados mostraram que TypeScript reduziu bugs em 40% e o onboarding de novos devs em 2 dias. O Tech Lead reconheceu os dados e adotamos TypeScript. Aprendi que argumentos baseados em dados são mais efetivos que opiniões."},
        {"type": "lia", "ts": "14:26", "msg": "Por fim, fale sobre uma iniciativa técnica que você liderou e seu impacto."},
        {"type": "candidate", "ts": "14:30", "msg": "Liderei a implementação de um Design System compartilhado entre 4 squads. Comecei fazendo um audit de inconsistências no produto, identifiquei 47 variações de botões e 12 paletas de cores diferentes. Criei um RFC, apresentei para stakeholders e liderei uma squad dedicada por 3 meses. Mentoreei 3 devs juniores no processo. O resultado: reduzimos 60% do tempo de desenvolvimento de novas features, cortamos inconsistências visuais de 47 para 5 componentes base, e a satisfação do time de design subiu de 3.2 para 4.7 na pesquisa interna."},
        {"type": "lia", "ts": "14:31", "msg": "Muito obrigada, {name}! Suas respostas foram excepcionais. Vou compilar sua avaliação e a equipe de recrutamento entrará em contato em breve com os próximos passos. Alguma dúvida?"},
        {"type": "candidate", "ts": "14:32", "msg": "Sem dúvidas. Agradeço a oportunidade e aguardo o retorno!"}
    ],
    "alto": [
        {"type": "lia", "ts": "14:00", "msg": "Olá, {name}! Sou a LIA, assistente de recrutamento. Obrigada por participar da triagem para a vaga de {vacancy}. Vamos conversar sobre sua experiência. Podemos começar?"},
        {"type": "candidate", "ts": "14:01", "msg": "Oi LIA! Claro, estou pronto(a). Vamos lá!"},
        {"type": "lia", "ts": "14:02", "msg": "Vamos começar com arquitetura. Descreva um projeto com decisões arquiteturais importantes que você participou."},
        {"type": "candidate", "ts": "14:05", "msg": "Participei da migração do nosso sistema de pagamentos de um monolito para microsserviços. Escolhemos usar Docker e Kubernetes. Minha contribuição principal foi no serviço de processamento de transações, onde implementei filas com SQS e padrão saga para transações distribuídas. O resultado foi positivo - conseguimos escalar independentemente cada serviço e reduzimos o deploy time de 45min para 8min."},
        {"type": "lia", "ts": "14:06", "msg": "Bom! Como você abordaria um sistema de notificações em tempo real para 100k usuários?"},
        {"type": "candidate", "ts": "14:09", "msg": "Usaria WebSocket no frontend com Socket.io pela facilidade de reconexão automática. No backend, um serviço Node.js com Redis para pub/sub. Para escalar, colocaria um load balancer com sticky sessions. Armazenaria notificações não lidas no PostgreSQL com índice no user_id. Para 100k simultâneos, precisaria de pelo menos 3-4 instâncias do serviço de WebSocket."},
        {"type": "lia", "ts": "14:10", "msg": "Me conte sobre a API mais complexa que você trabalhou."},
        {"type": "candidate", "ts": "14:13", "msg": "Trabalhei em uma API REST para um e-commerce com cerca de 80 endpoints. Usamos Express com TypeScript, autenticação JWT, e documentação com Swagger. O mais desafiador foi implementar o sistema de busca com Elasticsearch e o carrinho de compras com sessões. Implementamos rate limiting por IP e por token de API."},
        {"type": "lia", "ts": "14:14", "msg": "Conte sobre um bug crítico em produção que você resolveu."},
        {"type": "candidate", "ts": "14:17", "msg": "Tivemos um problema de race condition no checkout que causava cobranças duplicadas. Descobri usando os logs da aplicação correlacionados com transações no Stripe. A solução foi implementar idempotency keys e um lock otimista no banco. Depois adicionei testes de concorrência no CI para prevenir."},
        {"type": "lia", "ts": "14:18", "msg": "Descreva um desacordo técnico que você vivenciou."},
        {"type": "candidate", "ts": "14:21", "msg": "Tive um desacordo sobre usar ORM vs queries SQL raw. Meu colega preferia SQL puro por performance, eu preferia ORM por produtividade. Chegamos a um meio-termo: usamos o ORM para CRUD básico e queries otimizadas para relatórios pesados. Funcionou bem para ambos."},
        {"type": "lia", "ts": "14:22", "msg": "Fale sobre uma iniciativa técnica que você liderou."},
        {"type": "candidate", "ts": "14:25", "msg": "Liderei a adoção de testes automatizados no time. Começamos com 0% de cobertura e em 4 meses chegamos a 65%. Fiz workshops semanais, criei templates de testes e ajudei cada dev individualmente. O número de bugs em produção caiu 35%."},
        {"type": "lia", "ts": "14:26", "msg": "Obrigada, {name}! Ótimas respostas. A equipe entrará em contato com os próximos passos. Alguma dúvida?"},
        {"type": "candidate", "ts": "14:27", "msg": "Obrigado(a) pela conversa! Aguardo o retorno."}
    ],
    "medio": [
        {"type": "lia", "ts": "14:00", "msg": "Olá, {name}! Sou a LIA. Obrigada por participar da triagem para {vacancy}. Vamos conversar?"},
        {"type": "candidate", "ts": "14:01", "msg": "Oi! Pode começar."},
        {"type": "lia", "ts": "14:02", "msg": "Me conte sobre sua experiência com decisões arquiteturais."},
        {"type": "candidate", "ts": "14:04", "msg": "Trabalho principalmente com aplicações web usando React no frontend e Node no backend. Costumo seguir a estrutura MVC e organizar o código por módulos. Em um projeto recente, escolhi usar MongoDB pela flexibilidade do schema."},
        {"type": "lia", "ts": "14:05", "msg": "Como você faria um sistema de notificações em tempo real?"},
        {"type": "candidate", "ts": "14:07", "msg": "Usaria Socket.io para a comunicação em tempo real. No backend, guardaria as notificações no banco e quando uma nova fosse criada, emitiria um evento via socket. No frontend, escutaria esses eventos e atualizaria a lista."},
        {"type": "lia", "ts": "14:08", "msg": "Fale sobre APIs que você trabalhou."},
        {"type": "candidate", "ts": "14:10", "msg": "Trabalhei com APIs REST usando Express.js. Faço CRUD básico, autenticação com JWT, e uso Postman para testar. Em geral, sigo as convenções de nomenclatura RESTful."},
        {"type": "lia", "ts": "14:11", "msg": "Conte sobre um bug que você resolveu em produção."},
        {"type": "candidate", "ts": "14:13", "msg": "Uma vez o site ficou fora do ar por causa de um import circular. Levei umas 2 horas para encontrar. Depois disso passei a prestar mais atenção na organização dos imports."},
        {"type": "lia", "ts": "14:14", "msg": "E sobre trabalho em equipe, algum desafio?"},
        {"type": "candidate", "ts": "14:16", "msg": "Às vezes tenho divergências sobre estilo de código, mas geralmente sigo o padrão do time. Tento ser flexível."},
        {"type": "lia", "ts": "14:17", "msg": "Obrigada, {name}! A equipe entrará em contato. Alguma dúvida?"},
        {"type": "candidate", "ts": "14:18", "msg": "Não, obrigado(a)."}
    ],
    "regular": [
        {"type": "lia", "ts": "14:00", "msg": "Olá, {name}! Sou a LIA. Vamos conversar sobre a vaga de {vacancy}?"},
        {"type": "candidate", "ts": "14:01", "msg": "Oi, pode falar."},
        {"type": "lia", "ts": "14:02", "msg": "Qual sua experiência com arquitetura de software?"},
        {"type": "candidate", "ts": "14:03", "msg": "Eu trabalho mais na parte de execução mesmo, sigo o que o líder técnico define. Não tenho muita experiência com decisões de arquitetura."},
        {"type": "lia", "ts": "14:04", "msg": "Como faria um sistema de notificações em tempo real?"},
        {"type": "candidate", "ts": "14:06", "msg": "Acho que usaria um setInterval no frontend para verificar novas notificações a cada 5 segundos. Ou talvez WebSocket, mas nunca implementei."},
        {"type": "lia", "ts": "14:07", "msg": "Me fale sobre APIs."},
        {"type": "candidate", "ts": "14:08", "msg": "Já consumi APIs usando fetch e axios. Criei algumas rotas básicas com Express, tipo login e cadastro."},
        {"type": "lia", "ts": "14:09", "msg": "Já resolveu algum bug em produção?"},
        {"type": "candidate", "ts": "14:10", "msg": "Já tive problemas com CORS que levei bastante tempo para resolver. Acabei achando a solução no StackOverflow."},
        {"type": "lia", "ts": "14:11", "msg": "Obrigada, {name}! A equipe analisará seu perfil. Alguma dúvida?"},
        {"type": "candidate", "ts": "14:12", "msg": "Não, valeu."}
    ]
}

RESPONSE_TEMPLATES = {
    "excelente": {
        "Arquitetura de Software": {
            "response": "Liderei a migração de monolito para microsserviços usando DDD e strangler fig pattern. Analisei 3 alternativas, implementei event sourcing. Resultado: deploy de 2h para 15min, uptime 99.2% para 99.95%.",
            "auto_score": 4.8, "ctx_score": 4.9, "bloom": 5, "dreyfus": 5, "final": 4.85,
            "evidences": ["Trade-off analysis entre 3 alternativas", "Metrics-driven decision (uptime, deploy time)", "DDD + Event Sourcing implementation"],
            "justification": "Demonstra domínio completo de arquitetura com decisões fundamentadas em métricas e trade-offs claros."
        },
        "Desenvolvimento Full Stack": {
            "response": "WebSocket com fallback SSE no frontend, Redis Pub/Sub + RabbitMQ no backend, sticky sessions no LB. Sistema de priorização por canal. Já suportei 150k conexões.",
            "auto_score": 4.7, "ctx_score": 4.8, "bloom": 5, "dreyfus": 5, "final": 4.75,
            "evidences": ["Multi-protocol strategy (WS + SSE + polling)", "Message queue architecture", "Load balancing with horizontal scaling"],
            "justification": "Solução completa e escalável com experiência comprovada em volume similar."
        },
        "APIs e Integrações": {
            "response": "API GraphQL com 200+ types, Apollo Federation para 8 microsserviços. JWT com refresh tokens, rate limiting. Cursor-based pagination para milhões de registros.",
            "auto_score": 4.6, "ctx_score": 4.7, "bloom": 5, "dreyfus": 4, "final": 4.60,
            "evidences": ["GraphQL Federation", "Advanced pagination", "Multi-service composition"],
            "justification": "Experiência avançada com APIs complexas e padrões modernos."
        },
        "Resolução de Problemas": {
            "response": "Memory leak em produção com crashes a cada 6h. Diagnosticado via Chrome DevTools + APM. Fix: cleanup de event listeners. Prevenção: circuit breaker + métricas Grafana + stress tests no CI.",
            "auto_score": 4.5, "ctx_score": 4.8, "bloom": 5, "dreyfus": 5, "final": 4.70,
            "evidences": ["Systematic debugging approach", "Root cause analysis", "Post-mortem + prevention measures"],
            "justification": "Abordagem exemplar de troubleshooting com foco em prevenção."
        },
        "Colaboração e Comunicação": {
            "response": "Desacordo sobre TypeScript vs JavaScript. Propus experimento A/B medindo bugs e onboarding. Dados mostraram -40% bugs com TS. Tech Lead adotou TS. Aprendi que dados vencem opiniões.",
            "auto_score": 4.3, "ctx_score": 4.5, "bloom": 4, "dreyfus": 4, "final": 4.40,
            "evidences": ["Data-driven conflict resolution", "Experiment design", "Constructive outcome with mutual learning"],
            "justification": "Resolução madura de conflitos com abordagem científica."
        },
        "Liderança Técnica": {
            "response": "Liderei Design System para 4 squads. Audit identificou 47 variações de botões. RFC, squad dedicada 3 meses, mentoreei 3 juniores. Resultado: -60% tempo dev, satisfação design 3.2→4.7.",
            "auto_score": 4.4, "ctx_score": 4.6, "bloom": 5, "dreyfus": 4, "final": 4.50,
            "evidences": ["Cross-team leadership", "Measurable impact", "Junior mentoring"],
            "justification": "Liderança proativa com impacto organizacional mensurável."
        }
    },
    "alto": {
        "Arquitetura de Software": {
            "response": "Participei da migração para microsserviços com Docker e K8s. Implementei serviço de pagamentos com SQS e saga pattern. Deploy de 45min para 8min.",
            "auto_score": 4.0, "ctx_score": 4.2, "bloom": 4, "dreyfus": 4, "final": 4.10,
            "evidences": ["Microservices experience", "Saga pattern", "Container orchestration"],
            "justification": "Boa experiência prática com arquitetura moderna."
        },
        "Desenvolvimento Full Stack": {
            "response": "Socket.io com reconexão automática no frontend. Node.js com Redis pub/sub no backend. Load balancer com sticky sessions. PostgreSQL para persistência.",
            "auto_score": 3.8, "ctx_score": 4.0, "bloom": 4, "dreyfus": 3, "final": 3.90,
            "evidences": ["Real-time architecture knowledge", "Appropriate technology choices", "Scaling awareness"],
            "justification": "Solução funcional com bom nível de detalhe."
        },
        "APIs e Integrações": {
            "response": "API REST com 80 endpoints, Express + TypeScript. JWT auth, Swagger docs. Elasticsearch para busca. Rate limiting por IP e token.",
            "auto_score": 3.7, "ctx_score": 3.9, "bloom": 4, "dreyfus": 3, "final": 3.80,
            "evidences": ["REST API experience", "Security awareness", "Search integration"],
            "justification": "Experiência sólida com APIs REST e boas práticas."
        },
        "Resolução de Problemas": {
            "response": "Race condition no checkout causando cobranças duplicadas. Diagnostiquei via logs + Stripe dashboard. Fix: idempotency keys + lock otimista. Testes de concorrência no CI.",
            "auto_score": 4.0, "ctx_score": 4.1, "bloom": 4, "dreyfus": 4, "final": 4.05,
            "evidences": ["Concurrency problem solving", "Idempotency implementation", "Prevention via CI"],
            "justification": "Excelente debugging com solução adequada."
        },
        "Colaboração e Comunicação": {
            "response": "Desacordo ORM vs SQL raw. Propus meio-termo: ORM para CRUD, SQL para relatórios pesados. Funcionou bem.",
            "auto_score": 3.5, "ctx_score": 3.6, "bloom": 3, "dreyfus": 3, "final": 3.50,
            "evidences": ["Compromise approach", "Pragmatic solution"],
            "justification": "Boa capacidade de negociação técnica."
        },
        "Liderança Técnica": {
            "response": "Liderei adoção de testes automatizados. De 0% para 65% cobertura em 4 meses. Workshops, templates, mentoria individual. Bugs em produção -35%.",
            "auto_score": 3.8, "ctx_score": 4.0, "bloom": 4, "dreyfus": 3, "final": 3.90,
            "evidences": ["Testing culture initiative", "Measurable improvement", "Team mentoring"],
            "justification": "Liderança efetiva em melhoria de processos."
        }
    },
    "medio": {
        "Arquitetura de Software": {
            "response": "Uso MVC, organizo por módulos. Escolhi MongoDB pela flexibilidade.",
            "auto_score": 3.0, "ctx_score": 2.8, "bloom": 3, "dreyfus": 2, "final": 2.90,
            "evidences": ["Basic MVC knowledge", "Technology choice without deep analysis"],
            "justification": "Conhecimento básico de arquitetura, sem análise de trade-offs."
        },
        "Desenvolvimento Full Stack": {
            "response": "Socket.io para real-time. Backend guarda notificações no banco, emite evento via socket. Frontend escuta eventos.",
            "auto_score": 3.2, "ctx_score": 3.0, "bloom": 3, "dreyfus": 2, "final": 3.10,
            "evidences": ["Basic real-time understanding", "Simple but functional approach"],
            "justification": "Solução funcional mas sem considerar escalabilidade."
        },
        "APIs e Integrações": {
            "response": "CRUD com Express.js, JWT auth, testo com Postman.",
            "auto_score": 2.8, "ctx_score": 2.9, "bloom": 2, "dreyfus": 2, "final": 2.85,
            "evidences": ["Basic REST knowledge", "JWT authentication"],
            "justification": "Experiência limitada a APIs simples."
        },
        "Resolução de Problemas": {
            "response": "Import circular causou site fora do ar. Levei 2h para achar. Depois presto mais atenção nos imports.",
            "auto_score": 2.9, "ctx_score": 2.7, "bloom": 2, "dreyfus": 2, "final": 2.80,
            "evidences": ["Basic debugging", "No systematic approach"],
            "justification": "Resolução reativa sem processo estruturado."
        },
        "Colaboração e Comunicação": {
            "response": "Divergências sobre estilo de código, sigo o padrão do time. Tento ser flexível.",
            "auto_score": 3.5, "ctx_score": 3.3, "bloom": 3, "dreyfus": 3, "final": 3.40,
            "evidences": ["Flexibility", "Team alignment"],
            "justification": "Perfil colaborativo, mas sem iniciativa proativa."
        },
        "Liderança Técnica": {
            "response": "Ajudei um colega a aprender React. Documentei alguns processos no Notion.",
            "auto_score": 2.5, "ctx_score": 2.6, "bloom": 2, "dreyfus": 2, "final": 2.55,
            "evidences": ["Basic mentoring", "Documentation effort"],
            "justification": "Iniciativas pontuais sem impacto amplo."
        }
    },
    "regular": {
        "Arquitetura de Software": {
            "response": "Sigo o que o líder técnico define. Não tenho muita experiência com decisões de arquitetura.",
            "auto_score": 1.8, "ctx_score": 1.5, "bloom": 1, "dreyfus": 1, "final": 1.65,
            "evidences": ["No architectural experience"],
            "justification": "Sem experiência em decisões arquiteturais."
        },
        "Desenvolvimento Full Stack": {
            "response": "setInterval para verificar notificações a cada 5 segundos. Ou WebSocket, mas nunca implementei.",
            "auto_score": 2.0, "ctx_score": 1.8, "bloom": 2, "dreyfus": 1, "final": 1.90,
            "evidences": ["Polling approach only", "No real-time experience"],
            "justification": "Conhecimento teórico limitado sem prática."
        },
        "APIs e Integrações": {
            "response": "Já consumi APIs com fetch e axios. Criei rotas básicas de login e cadastro.",
            "auto_score": 2.2, "ctx_score": 2.0, "bloom": 2, "dreyfus": 1, "final": 2.10,
            "evidences": ["API consumption only", "Basic CRUD routes"],
            "justification": "Experiência limitada ao consumo de APIs."
        },
        "Resolução de Problemas": {
            "response": "Problemas com CORS, achei solução no StackOverflow.",
            "auto_score": 1.8, "ctx_score": 1.6, "bloom": 1, "dreyfus": 1, "final": 1.70,
            "evidences": ["Copy-paste problem solving"],
            "justification": "Abordagem não estruturada de resolução de problemas."
        },
        "Colaboração e Comunicação": {
            "response": "Não tive grandes desafios. Trabalho mais sozinho.",
            "auto_score": 2.0, "ctx_score": 1.9, "bloom": 2, "dreyfus": 1, "final": 1.95,
            "evidences": ["Limited team interaction"],
            "justification": "Pouca experiência colaborativa."
        },
        "Liderança Técnica": {
            "response": "Não tive oportunidade de liderar nada ainda.",
            "auto_score": 1.5, "ctx_score": 1.3, "bloom": 1, "dreyfus": 1, "final": 1.40,
            "evidences": ["No leadership experience"],
            "justification": "Sem experiência de liderança técnica."
        }
    }
}

REPORT_TEMPLATES = {
    "excelente": {
        "executive_summary": "Candidata excepcional com domínio completo de arquitetura, desenvolvimento full stack e liderança técnica. Demonstra capacidade de tomar decisões fundamentadas em métricas, resolver problemas complexos sistematicamente e liderar times com impacto mensurável. Altamente recomendada para posições de liderança técnica sênior.",
        "technical_analysis": {
            "pontos_fortes": [
                "Domínio avançado de arquitetura de microsserviços com DDD e event sourcing",
                "Experiência comprovada com sistemas de alta escala (150k+ conexões)",
                "Proficiência em GraphQL Federation e APIs complexas",
                "Abordagem sistemática de debugging com prevenção via CI/CD"
            ],
            "gaps": [
                "Poderia explorar mais tecnologias de edge computing"
            ],
            "evidencias": [
                "Migração monolito→microsserviços com uptime 99.95%",
                "API GraphQL com 200+ types e federation de 8 serviços",
                "Resolução de memory leak com post-mortem documentado"
            ]
        },
        "behavioral_analysis": {
            "colaboracao": {"score": 4.4, "descricao": "Excelente capacidade de resolução de conflitos com abordagem data-driven"},
            "inovacao": {"score": 4.5, "descricao": "Proativa em propor e liderar iniciativas técnicas transformadoras"},
            "organizacao": {"score": 4.6, "descricao": "Metodologia estruturada com foco em métricas e processos"},
            "resiliencia": {"score": 4.3, "descricao": "Lida bem com pressão e situações críticas em produção"}
        },
        "cultural_fit": {
            "score": 4.5,
            "valores_alinhados": ["Excelência técnica", "Colaboração", "Inovação", "Mentoria"],
            "atencoes": []
        },
        "recommendation": {
            "decisao": "Fortemente Recomendado",
            "justificativa": "Perfil excepcional que combina excelência técnica com habilidades de liderança. Candidata tem potencial para elevar a qualidade técnica de toda a equipe.",
            "proximos_passos": ["Agendar entrevista técnica aprofundada", "Apresentar ao gestor da área", "Preparar proposta competitiva"]
        }
    },
    "alto": {
        "executive_summary": "Candidato(a) sólido(a) com boa experiência em desenvolvimento full stack e capacidade de resolver problemas complexos. Demonstra autonomia técnica e espírito colaborativo. Recomendado(a) para avançar no processo.",
        "technical_analysis": {
            "pontos_fortes": [
                "Experiência prática com microsserviços e containers",
                "Bom domínio de patterns (saga, CQRS)",
                "Conhecimento sólido de APIs REST",
                "Capacidade de implementar soluções de testing"
            ],
            "gaps": [
                "Experiência com GraphQL limitada",
                "Poderia ter mais experiência com sistemas distribuídos em larga escala"
            ],
            "evidencias": [
                "Migração para microsserviços com Docker/K8s",
                "Resolução de race condition em checkout",
                "Implementação de cultura de testes (0% → 65%)"
            ]
        },
        "behavioral_analysis": {
            "colaboracao": {"score": 3.5, "descricao": "Boa capacidade de negociação e busca de consenso"},
            "inovacao": {"score": 3.8, "descricao": "Iniciativa para melhorias incrementais"},
            "organizacao": {"score": 3.9, "descricao": "Organizado com foco em produtividade"},
            "resiliencia": {"score": 3.7, "descricao": "Bom desempenho sob pressão"}
        },
        "cultural_fit": {
            "score": 3.8,
            "valores_alinhados": ["Qualidade de código", "Colaboração", "Melhoria contínua"],
            "atencoes": ["Verificar alinhamento com ritmo de entrega"]
        },
        "recommendation": {
            "decisao": "Recomendado",
            "justificativa": "Perfil sólido com bom equilíbrio entre competências técnicas e comportamentais. Indicado para posição sênior com perspectiva de crescimento.",
            "proximos_passos": ["Agendar entrevista técnica", "Avaliar fit cultural com o time"]
        }
    },
    "medio": {
        "executive_summary": "Candidato(a) com base técnica adequada mas experiência limitada em alguns aspectos-chave da vaga. Demonstra vontade de aprender mas precisa desenvolver visão arquitetural e liderança técnica.",
        "technical_analysis": {
            "pontos_fortes": [
                "Conhecimento funcional de React e Node.js",
                "Familiaridade com JWT e APIs REST básicas",
                "Disposição para aprender"
            ],
            "gaps": [
                "Pouca experiência com arquitetura de sistemas",
                "Sem vivência em sistemas de alta escala",
                "Limitada experiência com APIs complexas",
                "Debugging reativo sem metodologia"
            ],
            "evidencias": [
                "Trabalho com MVC e MongoDB",
                "Socket.io para funcionalidades básicas",
                "CRUD com Express.js"
            ]
        },
        "behavioral_analysis": {
            "colaboracao": {"score": 3.4, "descricao": "Flexível e alinhado com o time"},
            "inovacao": {"score": 2.5, "descricao": "Pouca iniciativa proativa para melhorias"},
            "organizacao": {"score": 2.8, "descricao": "Organização básica"},
            "resiliencia": {"score": 2.9, "descricao": "Performance adequada em situações normais"}
        },
        "cultural_fit": {
            "score": 3.0,
            "valores_alinhados": ["Flexibilidade", "Trabalho em equipe"],
            "atencoes": ["Nível de senioridade pode não atender expectativas da vaga", "Necessita orientação técnica frequente"]
        },
        "recommendation": {
            "decisao": "Aguardando Avaliação",
            "justificativa": "Perfil com potencial mas gap significativo em relação ao nível sênior exigido. Pode ser considerado para posição pleno ou com plano de desenvolvimento.",
            "proximos_passos": ["Avaliar para posição pleno", "Verificar disponibilidade de mentoria no time"]
        }
    },
    "regular": {
        "executive_summary": "Candidato(a) em estágio inicial de desenvolvimento técnico, sem experiência relevante para o nível sênior exigido. Perfil mais adequado para posições júnior com forte acompanhamento.",
        "technical_analysis": {
            "pontos_fortes": [
                "Conhecimento básico de tecnologias web",
                "Interesse em tecnologia"
            ],
            "gaps": [
                "Sem experiência arquitetural",
                "Sem vivência com sistemas em produção de escala",
                "Resolução de problemas dependente de soluções externas",
                "Sem experiência com APIs além de consumo básico",
                "Sem experiência de liderança técnica"
            ],
            "evidencias": [
                "Consumo básico de APIs com fetch/axios",
                "Rotas simples com Express",
                "Resolução via StackOverflow"
            ]
        },
        "behavioral_analysis": {
            "colaboracao": {"score": 1.9, "descricao": "Trabalha mais individualmente"},
            "inovacao": {"score": 1.5, "descricao": "Segue padrões existentes"},
            "organizacao": {"score": 2.0, "descricao": "Organização básica"},
            "resiliencia": {"score": 2.1, "descricao": "Pouca experiência com pressão"}
        },
        "cultural_fit": {
            "score": 2.0,
            "valores_alinhados": ["Interesse em aprender"],
            "atencoes": ["Nível muito abaixo do exigido para posição sênior", "Necessitaria plano de desenvolvimento extenso"]
        },
        "recommendation": {
            "decisao": "Não Recomendado para esta vaga",
            "justificativa": "Perfil significativamente abaixo das exigências da posição sênior. Recomendamos manter no banco de talentos para oportunidades de nível júnior/estagiário.",
            "proximos_passos": ["Adicionar ao banco de talentos para vagas júnior", "Enviar feedback construtivo"]
        }
    }
}

FEEDBACK_TEMPLATES = {
    "aprovado": {
        "main_message": "Parabéns! Sua performance na triagem foi excelente e demonstrou alinhamento com as competências que buscamos para a posição de Desenvolvedor(a) Full Stack Sênior. Você avançou para a próxima etapa do processo seletivo!",
        "technical_strengths": [
            "Forte domínio de arquitetura de software e padrões de design",
            "Experiência sólida com sistemas escaláveis e de alta disponibilidade",
            "Proficiência em APIs modernas e integrações complexas"
        ],
        "behavioral_strengths": [
            "Excelente capacidade de comunicação técnica",
            "Abordagem colaborativa e construtiva para resolução de conflitos",
            "Proatividade em liderança e mentoria"
        ],
        "development_opportunities": [
            "Explorar mais sobre edge computing e arquiteturas serverless",
            "Aprofundar conhecimento em observabilidade e SRE practices"
        ],
        "next_steps": "Nossa equipe de recrutamento entrará em contato em até 48 horas para agendar a próxima etapa do processo. Fique atento(a) ao seu email e telefone.",
        "personalized_tip": "Sua capacidade de fundamentar decisões com dados e métricas foi um destaque. Continue usando essa abordagem nas próximas etapas.",
        "development_plan": {
            "curto_prazo": ["Revisar os conceitos de system design para a entrevista técnica"],
            "medio_prazo": ["Expandir portfólio com projetos open source de infraestrutura"]
        },
        "recommended_resources": [
            {"tipo": "livro", "titulo": "Designing Data-Intensive Applications", "autor": "Martin Kleppmann"},
            {"tipo": "curso", "titulo": "System Design Interview", "plataforma": "Educative.io"}
        ]
    },
    "aguardando": {
        "main_message": "Agradecemos sua participação na triagem para a posição de Desenvolvedor(a) Full Stack Sênior! Identificamos boas competências no seu perfil, porém algumas áreas precisam de avaliação adicional antes de definirmos os próximos passos.",
        "technical_strengths": [
            "Conhecimento funcional de tecnologias web modernas",
            "Familiaridade com padrões básicos de desenvolvimento"
        ],
        "behavioral_strengths": [
            "Postura colaborativa e flexível",
            "Disposição para aprender e se adaptar"
        ],
        "development_opportunities": [
            "Aprofundar conhecimento em arquitetura de sistemas",
            "Desenvolver experiência com sistemas de alta escala",
            "Investir em liderança técnica e mentoria"
        ],
        "next_steps": "Seu perfil está em análise pela equipe técnica. Entraremos em contato em até 5 dias úteis com uma atualização sobre o processo.",
        "personalized_tip": "Investir em projetos pessoais que envolvam design de arquitetura e escalabilidade pode fortalecer muito seu perfil para posições sênior.",
        "development_plan": {
            "curto_prazo": ["Estudar padrões de microsserviços e DDD", "Praticar system design"],
            "medio_prazo": ["Contribuir para projetos open source", "Implementar um projeto pessoal com arquitetura distribuída"]
        },
        "recommended_resources": [
            {"tipo": "curso", "titulo": "Fundamentals of Software Architecture", "plataforma": "O'Reilly"},
            {"tipo": "livro", "titulo": "Clean Architecture", "autor": "Robert C. Martin"}
        ]
    },
    "nao_aprovado": {
        "main_message": "Agradecemos seu interesse e participação no processo seletivo para Desenvolvedor(a) Full Stack Sênior. Após análise cuidadosa, identificamos que seu perfil atual não atende completamente aos requisitos técnicos desta posição específica. Seu perfil permanecerá em nosso banco de talentos para futuras oportunidades mais alinhadas.",
        "technical_strengths": [
            "Interesse demonstrado em tecnologias de desenvolvimento",
            "Conhecimento básico de ferramentas fundamentais"
        ],
        "behavioral_strengths": [
            "Honestidade sobre limitações técnicas",
            "Disposição para crescer profissionalmente"
        ],
        "development_opportunities": [
            "Desenvolver sólida base em estruturas de dados e algoritmos",
            "Construir experiência prática com projetos completos (frontend + backend)",
            "Aprender sobre versionamento, CI/CD e deploy",
            "Estudar padrões de API REST e boas práticas de desenvolvimento"
        ],
        "next_steps": "Manteremos seu perfil em nosso banco de talentos. Quando surgirem oportunidades adequadas ao seu nível de experiência, entraremos em contato.",
        "personalized_tip": "Sugerimos focar em construir 2-3 projetos completos do zero para ganhar experiência prática end-to-end antes de buscar posições sênior.",
        "development_plan": {
            "curto_prazo": ["Completar um curso de estruturas de dados", "Construir um projeto CRUD completo com deploy"],
            "medio_prazo": ["Participar de hackathons", "Contribuir para projetos open source como forma de aprendizado"]
        },
        "recommended_resources": [
            {"tipo": "curso", "titulo": "The Complete Web Developer in 2024", "plataforma": "Udemy"},
            {"tipo": "plataforma", "titulo": "freeCodeCamp", "url": "https://freecodecamp.org"}
        ]
    }
}


def get_classification_level(classification):
    if classification in ("excelente",):
        return "excelente"
    elif classification in ("alto",):
        return "alto"
    elif classification in ("medio",):
        return "medio"
    else:
        return "regular"


async def seed_wsi_data():
    import asyncpg
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return
    
    conn = await asyncpg.connect(database_url)
    
    try:
        existing = await conn.fetchval("SELECT COUNT(*) FROM wsi_sessions")
        if existing > 0:
            logger.info(f"WSI data already exists ({existing} sessions). Clearing...")
            await conn.execute("DELETE FROM wsi_feedbacks")
            await conn.execute("DELETE FROM wsi_reports")
            await conn.execute("DELETE FROM wsi_results")
            await conn.execute("DELETE FROM wsi_response_analyses")
            await conn.execute("DELETE FROM wsi_questions")
            await conn.execute("DELETE FROM wsi_sessions")
            logger.info("Cleared existing WSI data.")
        
        base_date = datetime(2026, 2, 5, 14, 0, 0)
        
        for idx, cand in enumerate(CANDIDATES):
            level = get_classification_level(cand["classification"])
            session_date = base_date - timedelta(days=idx, hours=idx % 3)
            completed_date = session_date + timedelta(minutes=25 + idx * 2)
            
            session_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO wsi_sessions (id, candidate_id, job_vacancy_id, screening_type, mode, status, 
                    question_set_version, question_set_id, started_at, completed_at, created_at, updated_at)
                VALUES ($1, $2::uuid, $3::uuid, $4, 'compact', 'completed', 1, 'qset_fullstack_senior_v1',
                    $5, $6, $5, $6)
            """, session_id, cand["id"], VACANCY_ID, cand["screening_type"], session_date, completed_date)
            
            logger.info(f"Created session for {cand['name']} ({level})")
            
            question_ids = []
            for q_idx, q_template in enumerate(QUESTIONS_TEMPLATES):
                q_id = str(uuid.uuid4())
                question_ids.append(q_id)
                await conn.execute("""
                    INSERT INTO wsi_questions (id, session_id, competency, framework, question_type, 
                        question_text, weight, expected_signals, scoring_criteria, sequence_order, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10, $11)
                """, q_id, session_id, q_template["competency"], q_template["framework"],
                    q_template["question_type"], q_template["question_text"], q_template["weight"],
                    json.dumps(q_template["expected_signals"]), json.dumps(q_template["scoring_criteria"]),
                    q_idx + 1, session_date)
            
            responses = RESPONSE_TEMPLATES.get(level, RESPONSE_TEMPLATES["medio"])
            for q_idx, (q_template, q_id) in enumerate(zip(QUESTIONS_TEMPLATES, question_ids)):
                competency = q_template["competency"]
                resp_data = responses.get(competency, {
                    "response": "Resposta não disponível para esta competência.",
                    "auto_score": 2.5, "ctx_score": 2.5, "bloom": 2, "dreyfus": 2, "final": 2.5,
                    "evidences": [], "justification": "Sem dados suficientes."
                })
                
                ra_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO wsi_response_analyses (id, session_id, question_id, candidate_id, job_vacancy_id,
                        competency, response_text, autodeclaration_score, context_score, bloom_level, dreyfus_level,
                        evidences, red_flags, consistency_penalty, final_score, justification, created_at)
                    VALUES ($1, $2, $3, $4::uuid, $5::uuid, $6, $7, $8, $9, $10, $11, 
                        $12::jsonb, '[]'::jsonb, 0, $13, $14, $15)
                """, ra_id, session_id, q_id, cand["id"], VACANCY_ID,
                    competency, resp_data["response"],
                    resp_data["auto_score"], resp_data["ctx_score"],
                    resp_data["bloom"], resp_data["dreyfus"],
                    json.dumps(resp_data["evidences"]),
                    resp_data["final"], resp_data["justification"],
                    session_date + timedelta(minutes=5 * (q_idx + 1)))
            
            result_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO wsi_results (id, session_id, candidate_id, job_vacancy_id,
                    technical_wsi, behavioral_wsi, overall_wsi, classification, percentile, created_at)
                VALUES ($1, $2, $3::uuid, $4::uuid, $5, $6, $7, $8, $9, $10)
            """, result_id, session_id, cand["id"], VACANCY_ID,
                cand["technical"], cand["behavioral"], cand["overall"],
                cand["classification"], cand["percentile"], completed_date)
            
            report_data = REPORT_TEMPLATES.get(level, REPORT_TEMPLATES["medio"])
            report_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO wsi_reports (id, wsi_result_id, candidate_id, executive_summary,
                    technical_analysis, behavioral_analysis, cultural_fit, recommendation, created_at)
                VALUES ($1, $2, $3::uuid, $4, $5::jsonb, $6::jsonb, $7::jsonb, $8::jsonb, $9)
            """, report_id, result_id, cand["id"],
                report_data["executive_summary"].replace("{name}", cand["name"]),
                json.dumps(report_data["technical_analysis"]),
                json.dumps(report_data["behavioral_analysis"]),
                json.dumps(report_data["cultural_fit"]),
                json.dumps(report_data["recommendation"]),
                completed_date + timedelta(minutes=1))
            
            decision = cand["decision"]
            feedback_data = FEEDBACK_TEMPLATES.get(decision, FEEDBACK_TEMPLATES["aguardando"])
            feedback_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO wsi_feedbacks (id, wsi_result_id, candidate_id, decision, main_message,
                    technical_strengths, development_opportunities, behavioral_strengths,
                    next_steps, personalized_tip, development_plan, recommended_resources, created_at)
                VALUES ($1, $2, $3::uuid, $4, $5, $6::jsonb, $7::jsonb, $8::jsonb, $9, $10, $11::jsonb, $12::jsonb, $13)
            """, feedback_id, result_id, cand["id"], decision,
                feedback_data["main_message"],
                json.dumps(feedback_data["technical_strengths"]),
                json.dumps(feedback_data["development_opportunities"]),
                json.dumps(feedback_data["behavioral_strengths"]),
                feedback_data["next_steps"],
                feedback_data["personalized_tip"],
                json.dumps(feedback_data["development_plan"]),
                json.dumps(feedback_data["recommended_resources"]),
                completed_date + timedelta(minutes=2))
            
            logger.info(f"  -> Result: {cand['overall']}/5.0 ({cand['classification']}) | Decision: {decision}")
        
        logger.info(f"\nSeed complete! Created WSI data for {len(CANDIDATES)} candidates.")
        
        stats = await conn.fetch("""
            SELECT classification, COUNT(*) as cnt, 
                   ROUND(AVG(overall_wsi)::numeric, 2) as avg_score
            FROM wsi_results 
            WHERE job_vacancy_id = $1::uuid
            GROUP BY classification 
            ORDER BY avg_score DESC
        """, VACANCY_ID)
        
        logger.info("\nDistribuição por classificação:")
        for row in stats:
            logger.info(f"  {row['classification']}: {row['cnt']} candidatos (média: {row['avg_score']})")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_wsi_data())
