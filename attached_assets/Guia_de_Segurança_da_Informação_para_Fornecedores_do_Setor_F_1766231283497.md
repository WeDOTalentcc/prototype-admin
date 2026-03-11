# Guia de Segurança da Informação para Fornecedores do Setor Financeiro

**Preparado para: Wedotalent**

**Autor: Manus AI**

**Data: 19 de dezembro de 2025**

## 1. Introdução

Este guia tem como objetivo fornecer um roteiro abrangente para a Wedotalent, uma plataforma de HR Tech, sobre os requisitos de segurança da informação necessários para atuar como fornecedor de instituições financeiras no Brasil, com foco especial em bancos digitais como o C6 Bank. A homologação como fornecedor em um setor tão regulado exige a demonstração de maturidade em governança, gestão de riscos e controles técnicos robustos para proteger dados e garantir a continuidade dos serviços.

O documento está estruturado para abordar o arcabouço regulatório, as certificações mandatórias e recomendadas, e as melhores práticas de mercado em domínios críticos de segurança da informação. Seguir estas diretrizes não apenas facilitará o processo de homologação, mas também fortalecerá a postura de segurança da Wedotalent, tornando-a um parceiro de negócios mais resiliente e confiável.

## 2. Arcabouço Regulatório e Legal

Operar como fornecedor de tecnologia para o setor financeiro brasileiro implica aderir a um conjunto estrito de normas e leis. As principais estão detalhadas abaixo.

| Norma/Lei | Entidade Reguladora | Foco Principal |
| :--- | :--- | :--- |
| **Resolução CMN Nº 4.893/2021** | Banco Central do Brasil (BCB) | Dispõe sobre a política de segurança cibernética e sobre os requisitos para a contratação de serviços de processamento e armazenamento de dados e de computação em nuvem. |
| **Resolução BCB Nº 498/2025** | Banco Central do Brasil (BCB) | Estabelece requisitos para o credenciamento de Provedores de Serviços de Tecnologia da Informação (PSTIs), incluindo a obrigatoriedade de seguro cibernético e certificação de segurança. |
| **Lei Geral de Proteção de Dados (LGPD)** | Autoridade Nacional de Proteção de Dados (ANPD) | Regula o tratamento de dados pessoais de pessoas físicas, estabelecendo papéis (controlador, operador) e exigindo medidas técnicas e administrativas para proteção. |
| **Lei do Acesso à Informação (LAI)** | Controladoria-Geral da União (CGU) | Embora focada no setor público, reforça o princípio da transparência, que se contrapõe à necessidade de sigilo de dados sensíveis, exigindo uma gestão de classificação da informação. |
| **Regulamentação do Open Finance** | Banco Central do Brasil (BCB) | Define padrões de segurança para o compartilhamento de dados entre instituições financeiras por meio de APIs, estabelecendo um benchmark para integrações seguras. |

Como fornecedora, a Wedotalent provavelmente se enquadrará como **Operadora de Dados** sob a LGPD, tratando dados em nome do banco (Controlador). Além disso, dependendo da criticidade do serviço, pode ser classificada como um **PSTI**, devendo cumprir os rigorosos requisitos da Resolução BCB Nº 498/2025.

## 3. Certificações de Segurança Mandatórias e Recomendadas

A Resolução BCB Nº 498/2025 torna explícita a necessidade de "*comprovação de obtenção e manutenção de certificação de segurança da informação em norma reconhecida internacionalmente, ou asseguração independente aceita pelo Banco Central do Brasil*". As certificações mais relevantes para este contexto são a ISO/IEC 27001 e a SOC 2.

### 3.1. ISO/IEC 27001

É o padrão internacional para **Sistemas de Gestão de Segurança da Informação (SGSI)**. A certificação demonstra que a empresa possui um processo de gestão de riscos de segurança maduro e implementou um conjunto abrangente de controles (descritos na norma de apoio ISO/IEC 27002).

- **Processo de Obtenção:** Envolve a definição do escopo do SGSI, realização de uma avaliação de riscos, implementação dos controles necessários, auditorias internas e, finalmente, uma auditoria de certificação por um organismo credenciado.
- **Relevância:** É a certificação mais reconhecida globalmente e frequentemente citada em regulamentações do setor financeiro, incluindo as do BCB. É altamente recomendada e pode ser considerada um requisito-base.

### 3.2. SOC 2 (Service Organization Control 2)

Desenvolvido pelo American Institute of CPAs (AICPA), o relatório SOC 2 atesta sobre os controles de uma organização de serviços relevantes para um ou mais dos cinco **Princípios de Serviços de Confiança (Trust Services Criteria)**: Segurança, Disponibilidade, Integridade de Processamento, Confidencialidade e Privacidade.

- **Tipos de Relatório:**
  - **Tipo I:** Avalia o *desenho* dos controles em um ponto específico no tempo.
  - **Tipo II:** Avalia a *eficácia operacional* dos controles ao longo de um período (geralmente de 6 a 12 meses). O relatório Tipo II é significativamente mais valioso para demonstrar conformidade contínua e é o que clientes como bancos esperam.
- **Relevância:** É extremamente relevante para empresas de SaaS e tecnologia, pois foca diretamente na segurança e disponibilidade dos serviços prestados. Para o C6 Bank e outros bancos digitais, um relatório SOC 2 Tipo II é uma prova robusta da eficácia dos controles da Wedotalent.

**Recomendação:** Para atender às exigências do C6 Bank, a Wedotalent deve buscar **ambas as certificações**. A **ISO 27001** estabelecerá a base de governança de segurança, enquanto o **SOC 2 Tipo II** fornecerá a garantia contínua sobre a eficácia operacional dos controles do serviço, algo crucial para um cliente do setor financeiro.

## 4. Domínios de Segurança e Melhores Práticas

A seguir, são detalhados os domínios essenciais que a Wedotalent precisa abordar para construir uma base de segurança sólida e atender aos requisitos de homologação.

### 4.1. Governança, Risco e Conformidade (GRC)
- **Política de Segurança da Informação:** Documento formal, aprovado pela alta gestão, que estabelece as diretrizes e princípios de segurança da empresa.
- **Gestão de Riscos:** Implementar um processo contínuo para identificar, analisar, avaliar e tratar os riscos de segurança da informação.
- **Classificação da Informação:** Criar uma política para classificar os dados (ex: Público, Interno, Confidencial, Restrito) com base em sua sensibilidade e requisitos de proteção.
- **Funções e Responsabilidades:** Designar formalmente um responsável pela segurança da informação (CISO ou função equivalente) e um Encarregado de Proteção de Dados (DPO), conforme exigido pela LGPD.

### 4.2. Segurança de Recursos Humanos
- **Conscientização e Treinamento:** Programas contínuos de treinamento em segurança para todos os colaboradores, abordando temas como phishing, engenharia social e uso seguro de senhas.
- **Controle de Acesso Lógico:** Implementar o **Princípio do Menor Privilégio**, garantindo que os usuários tenham acesso apenas aos recursos estritamente necessários para suas funções.
- **Autenticação Multifator (MFA):** Exigir MFA para acesso a todos os sistemas críticos, tanto internos quanto externos (e-mail, VPN, plataformas de nuvem, etc.).

### 4.3. Segurança de Ativos e Sistemas
- **Gestão de Vulnerabilidades:** Implementar um programa para identificar, avaliar e remediar vulnerabilidades em sistemas e aplicações, incluindo varreduras periódicas e testes de penetração (pentests) anuais ou sempre que houver mudanças significativas.
- **Hardening de Sistemas:** Configurar servidores, bancos de dados e outros componentes de infraestrutura para um estado seguro, desabilitando serviços e portas desnecessários.
- **Criptografia:** Utilizar criptografia forte para proteger dados em trânsito (TLS 1.2+) e em repouso (ex: criptografia de bancos de dados e discos).

### 4.4. Segurança no Desenvolvimento de Software (DevSecOps)
- **Práticas de Codificação Segura:** Adotar diretrizes como o **OWASP Top 10** para prevenir vulnerabilidades comuns em aplicações web.
- **Análise de Código:** Integrar ferramentas de Análise Estática de Segurança de Aplicações (SAST) e Análise Dinâmica (DAST) no ciclo de vida de desenvolvimento.
- **Segurança de APIs:** Proteger as APIs com mecanismos robustos de autenticação (ex: OAuth 2.0), autorização, limitação de taxa (rate limiting) e validação de entrada.

### 4.5. Gestão de Incidentes de Segurança
- **Plano de Resposta a Incidentes (PRI):** Desenvolver e manter um plano formal que detalhe os procedimentos para detectar, responder, conter e se recuperar de um incidente de segurança.
- **Equipe de Resposta a Incidentes (CSIRT):** Designar uma equipe responsável por coordenar as ações durante um incidente.
- **Comunicação:** O plano deve incluir um protocolo de comunicação para notificar as partes interessadas, incluindo o cliente (o banco) e, se necessário, a ANPD, dentro dos prazos regulatórios.

### 4.6. Continuidade de Negócios e Recuperação de Desastres
- **Plano de Continuidade de Negócios (PCN):** Garantir que as operações críticas de negócio possam continuar em caso de uma interrupção grave.
- **Plano de Recuperação de Desastres (PRD):** Focar na restauração da infraestrutura de TI e dos dados após um desastre.
- **RTO e RPO:** Definir e testar os Objetivos de Tempo de Recuperação (RTO - quanto tempo para restaurar o serviço) e Objetivos de Ponto de Recuperação (RPO - qual a perda de dados máxima aceitável).
- **Backups e Testes:** Implementar uma rotina de backups segura e realizar testes periódicos de restauração para garantir sua eficácia.

### 4.7. Requisitos Contratuais e Legais
- **Seguro Cibernético:** Conforme a Resolução BCB Nº 498/2025, é obrigatória a contratação de seguro de responsabilidade civil e de riscos operacionais, com cobertura para incidentes de fraude e segurança cibernética. Os valores de cobertura devem ser compatíveis com o risco do serviço prestado.
- **Cláusulas Contratuais:** O contrato com o banco deve detalhar as responsabilidades de cada parte, níveis de serviço (SLAs) de segurança, direitos de auditoria e procedimentos em caso de incidentes.

## 5. Conclusão e Próximos Passos

Atender às exigências de segurança de um banco digital como o C6 Bank é um processo rigoroso, mas que eleva o padrão de maturidade e a competitividade da Wedotalent. A jornada para a conformidade deve ser vista como um investimento estratégico na confiança do cliente e na resiliência do negócio.

**Recomendações de Ação Imediata:**

1.  **Realizar um Gap Analysis:** Avaliar o estado atual dos controles de segurança da Wedotalent em relação aos requisitos da ISO 27001 e SOC 2.
2.  **Engajar Consultoria Especializada:** Considerar a contratação de uma consultoria para auxiliar no processo de preparação para as certificações.
3.  **Orçar a Implementação:** Levantar os custos associados à implementação de controles, certificações e à contratação do seguro cibernético obrigatório.
4.  **Iniciar a Documentação:** Começar a desenvolver ou aprimorar as políticas e procedimentos de segurança da informação, como a PSI, o PRI e o PCN.

Ao seguir este guia, a Wedotalent estará bem posicionada para navegar com sucesso no processo de homologação e estabelecer uma parceria duradoura e segura com seus clientes no setor financeiro.
