# Gaps Identificados - Criação de Vagas (Super Chat)

**Data:** Dec 14, 2025  
**Reportado por:** Usuário durante revisão do fluxo

## Problemas Críticos (Bloqueadores)

### 6. Erro ao Publicar Vaga
- **Status:** ERRO 500 no backend
- **Logs:** `POST /api/backend-proxy/job-vacancies/ 500`
- **Prioridade:** CRÍTICA - Impede publicação de vagas
- **Ação:** Investigar erro no endpoint de criação de vagas

---

## Gaps de Integração com Admin

### 1. Falta Evidência de Uso de Departamentos
- **Problema:** Não há informação no texto nem na tela indicando que a LIA usa dados de departamento para:
  - Definir gestor da vaga automaticamente
  - Associar vaga à área correta (ex: vaga de TI vai para área de TI, não Produto)
- **Sugestão:** Adicionar tooltip ou texto explicativo no campo Área/Departamento
- **Backend:** Verificar se `DepartmentService` está sendo consultado

### 2. Departamentos Incompletos na Lista
- **Problema:** Faltam departamentos na lista dropdown
- **Departamentos atuais:** Engenharia, Produto, Design, Marketing, Vendas, RH, Financeiro, Operações
- **Departamentos faltantes (marcados em vermelho na imagem):** 
  - TI (Tecnologia da Informação)
  - Logística
  - Outros departamentos específicos da empresa
- **Ação:** Puxar departamentos cadastrados em Admin > Empresa & Equipe > Departamentos
- **API:** `/api/v1/company/departments/`

### 3. Benefícios Não Puxam do Admin
- **Problema:** Não há evidência de que benefícios são carregados do cadastro em Admin
- **Benefícios mostrados:** Vale Refeição, Vale Transporte, Plano de Saúde, Plano Odontológico, Seguro de Vida, Stock Options, Auxílio Home Office, Auxílio Educação, Gympass, Day Off Aniversário
- **Marcação do usuário:** "Benefícios precisam estar com os benefícios configurados"
- **Ação:** Integrar com `/api/v1/company/benefits/`
- **Backend:** Verificar se `BenefitService` está sendo usado

### 4. Perguntas de Triagem do Admin Não Aparecem
- **Problema:** Perguntas de triagem padrão da empresa (cadastradas no Admin) não aparecem como opções
- **Diferença:** Perguntas padrão da empresa ≠ Perguntas WSI geradas por IA
- **Ação:** Criar endpoint para perguntas de triagem da empresa
- **Localização no Admin:** Configurações > Recrutamento > Perguntas Screening

### 5. Sem Integração com Workforce Planning
- **Problema:** Não há evidência de que vagas são puxadas do Workforce Planning
- **Funcionalidade esperada:** 
  - Mostrar vagas planejadas no workforce planning
  - Permitir criar vaga a partir de planejamento aprovado
- **Ação:** Integrar com módulo de Workforce Planning

---

## Gaps de Configuração do Processo

### 7. Etapas do Processo de Recrutamento
- **Problema:** Não é possível configurar etapas do processo na criação da vaga
- **Funcionalidade esperada:**
  - Selecionar template de pipeline
  - Personalizar etapas por vaga
- **Localização no Admin:** Configurações > Recrutamento > Pipeline
- **Ação:** Adicionar etapa de configuração de pipeline no wizard de criação de vaga

### 8. Envio Automático de Relatórios
- **Problema:** Não há configuração de envio automático de relatórios de progresso
- **Funcionalidade esperada:**
  - Configurar frequência de envio (diário, semanal, etc.)
  - Selecionar gestores destinatários
  - Definir métricas a incluir
- **Nota:** Existe botão de gerar relatório na vaga, mas falta automação
- **Ação:** Criar configuração de relatórios automatizados por vaga

---

## Melhorias de UX Sugeridas

### Texto Explicativo da LIA
- Adicionar no texto do chat: "Vou aproveitar as informações de **departamentos**, **gestores** e **benefícios** já cadastrados na sua empresa para preencher automaticamente."

### Campo Área/Departamento
- Tooltip: "A área selecionada define o gestor responsável e agrupa esta vaga nos relatórios departamentais"

---

## Próximos Passos Recomendados

1. **URGENTE:** Corrigir erro 500 na API de vagas
2. Integrar departamentos do Admin no dropdown
3. Integrar benefícios do Admin na seleção
4. Adicionar perguntas de triagem da empresa
5. Adicionar configuração de etapas do processo
6. Integrar com Workforce Planning
7. Implementar envio automático de relatórios

---

## Referências Técnicas

- **Frontend:** `plataforma-lia/src/components/pages/jobs-page.tsx`
- **Backend API:** `lia-agent-system/app/api/v1/`
- **Modelos:** `lia-agent-system/app/models/`
- **Admin Empresa:** `/api/v1/company/`
