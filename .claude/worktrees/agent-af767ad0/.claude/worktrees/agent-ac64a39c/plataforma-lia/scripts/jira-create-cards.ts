import { Version3Client } from 'jira.js';

const PROJECT_KEY = 'WT';
const CLOUD_ID = '8cf762f8-6a44-47de-8915-6b3dc0cd2715';

interface CardData {
  summary: string;
  description: string;
  priority: string;
  labels: string[];
  storyPoints?: number;
}

const cards: CardData[] = [
  // ============================================
  // CARDS EXISTENTES (VAG-001 a VAG-013) - 13 cards
  // ============================================
  {
    summary: '[FRONT] Header Principal - Gestao de Vagas',
    description: 'Implementar header principal da pagina de Gestao de Vagas com icone, titulo e alinhamento conforme design system.\n\nCriterios de Aceitacao:\n- Icone Building2 24px visivel\n- Titulo Gestao de Vagas visivel\n- Fonte Open Sans 18px semibold',
    priority: 'High',
    labels: ['frontend', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Botao Nova Vaga - CTA Principal',
    description: 'Implementar botao principal de criacao de vaga no header, com estilo cyan (#60BED1), icone plus.\n\nCriterios de Aceitacao:\n- Botao cyan visivel no header\n- Abre ExpandedChatModal corretamente',
    priority: 'Highest',
    labels: ['frontend', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Integracao Busca Global - Header Icon',
    description: 'Integrar icone de busca global no header da pagina de vagas.\n\nCriterios de Aceitacao:\n- Icone de busca visivel\n- Abre GlobalSearchModal ao clicar\n- Atalho Cmd+K funciona',
    priority: 'Medium',
    labels: ['frontend', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Integracao Notificacoes - Bell Icon',
    description: 'Integrar icone de notificacoes no header com badge de contador.\n\nCriterios de Aceitacao:\n- Icone de sino visivel\n- Badge contador quando ha nao lidas',
    priority: 'Medium',
    labels: ['frontend', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Sistema de Tabs de Filtro por Status',
    description: 'Implementar sistema de tabs horizontais para filtrar vagas por status.\n\nCriterios de Aceitacao:\n- Tabs renderizam corretamente\n- Click muda filtro ativo\n- Underline animada na tab ativa',
    priority: 'High',
    labels: ['frontend', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT/BACK] Contadores Dinamicos por Status',
    description: 'Implementar contadores dinamicos ao lado de cada tab.\n\nCriterios de Aceitacao:\n- Contadores exibidos corretamente\n- Atualizacao em tempo real',
    priority: 'High',
    labels: ['frontend', 'backend', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Container LIA Centralizado',
    description: 'Implementar container centralizado para o prompt da LIA.\n\nCriterios de Aceitacao:\n- Container renderiza centralizado\n- Segue specs do design system',
    priority: 'Highest',
    labels: ['frontend', 'lia', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Input de Chat LIA',
    description: 'Implementar input de chat para interacao com LIA.\n\nCriterios de Aceitacao:\n- Input renderiza corretamente\n- Submit funciona (Enter + botao)\n- Focus state com borda cyan',
    priority: 'Highest',
    labels: ['frontend', 'lia', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[BACK] Integracao Backend LIA - Vagas Context',
    description: 'Integrar frontend com backend da LIA para processar comandos de gestao de vagas.\n\nAgentes: Orchestrator, job_intake_agent, analytics_agent\n\nVALIDACAO PENDENTE - Andre Bevilaqua',
    priority: 'Highest',
    labels: ['backend', 'lia', 'ai', 'gestao-vagas', 'validacao-andre'],
    storyPoints: 13
  },
  {
    summary: '[FRONT] Quick Action - Criar Nova Vaga',
    description: 'Implementar botao de quick action que abre o wizard de criacao.\n\nAgente: job_intake_agent\n\nVALIDACAO PENDENTE - Andre Bevilaqua',
    priority: 'Highest',
    labels: ['frontend', 'gestao-vagas', 'validacao-andre'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Quick Action - Resumo das Vagas',
    description: 'Implementar botao que pede para LIA gerar um resumo analytics.\n\nAgente: analytics_agent\n\nVALIDACAO PENDENTE - Andre Bevilaqua',
    priority: 'Medium',
    labels: ['frontend', 'gestao-vagas', 'validacao-andre'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Quick Action - Mais Ideias (AI)',
    description: 'Implementar botao que pede sugestoes proativas da LIA.\n\nAgente: recruiter_assistant_agent\n\nVALIDACAO PENDENTE - Andre Bevilaqua',
    priority: 'Medium',
    labels: ['frontend', 'ai', 'gestao-vagas', 'validacao-andre'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Empty State - Design Pagina Vazia',
    description: 'Implementar design de pagina vazia quando nao ha vagas cadastradas.\n\nCriterios de Aceitacao:\n- Ilustracao ou icone grande\n- Mensagem acolhedora\n- CTA claro para criar vaga',
    priority: 'High',
    labels: ['frontend', 'onboarding', 'gestao-vagas'],
    storyPoints: 5
  },

  // ============================================
  // EPIC-VAG-006: TABELA DE VAGAS (VAG-028 a VAG-036) - 9 cards
  // ============================================
  {
    summary: '[FRONT] Tabela de Vagas - Estrutura Base',
    description: 'Componente principal de tabela para listagem de vagas com suporte a colunas dinamicas, ordenacao, selecao e preview. Implementado nas linhas 3500-4400 do jobs-page.tsx.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver todas as vagas em uma tabela organizada para gerenciar facilmente o pipeline de vagas.\n\nCriterios de Aceitacao:\n- Tabela renderiza lista de vagas\n- Header com nomes das colunas\n- Rows clicaveis abrem preview\n- Responsivo em diferentes tamanhos\n- Performance aceitavel com 100+ vagas',
    priority: 'Highest',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Colunas Configuraveis - Toggle e Reordenacao',
    description: 'Sistema para mostrar/ocultar e reordenar colunas da tabela de vagas usando o hook useJobColumnConfig.\n\nHistoria de Usuario:\nComo recrutador, eu quero escolher quais colunas ver para personalizar minha visualizacao de vagas.\n\nCriterios de Aceitacao:\n- Toggle de visibilidade por coluna\n- Drag-and-drop para reordenar\n- Persistencia no localStorage\n- UI para configurar colunas',
    priority: 'High',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Ordenacao Multi-Coluna - Sort Headers',
    description: 'Ordenacao de vagas clicando nos headers das colunas com indicador visual de direcao (asc/desc).\n\nHistoria de Usuario:\nComo recrutador, eu quero ordenar vagas por diferentes criterios para encontrar rapidamente o que procuro.\n\nCriterios de Aceitacao:\n- Click no header ordena a coluna\n- Toggle entre asc/desc/none\n- Icone visual indica direcao\n- Ordenacao funciona corretamente',
    priority: 'High',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Redimensionamento de Colunas - Column Resize',
    description: 'Permitir redimensionamento de colunas arrastando a borda entre colunas do header da tabela.\n\nHistoria de Usuario:\nComo recrutador, eu quero ajustar a largura das colunas para ver mais ou menos informacao em cada uma.\n\nCriterios de Aceitacao:\n- Resize handle visivel\n- Drag para redimensionar\n- Persistencia no localStorage\n- Cursor de resize correto',
    priority: 'Medium',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Selecao em Lote - Checkbox',
    description: 'Sistema de checkbox para selecionar multiplas vagas e executar acoes em lote.\n\nHistoria de Usuario:\nComo recrutador, eu quero selecionar varias vagas para executar acoes em lote.\n\nCriterios de Aceitacao:\n- Checkbox por linha\n- Checkbox master no header\n- Contador de selecionados\n- Selecao persiste ao filtrar',
    priority: 'High',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Persistencia de Config - localStorage',
    description: 'Salvar configuracoes da tabela (colunas, ordenacao, larguras) no localStorage.\n\nHistoria de Usuario:\nComo recrutador, eu quero que minhas preferencias de tabela sejam lembradas.\n\nCriterios de Aceitacao:\n- Colunas visiveis persistidas\n- Ordem de colunas persistida\n- Larguras persistidas\n- Ordenacao persistida',
    priority: 'Medium',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Coluna Performance LIA - Triagens',
    description: 'Coluna especial mostrando metricas de performance da LIA nas triagens da vaga.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver a performance da LIA em cada vaga.\n\nCriterios de Aceitacao:\n- Score de triagem visivel\n- Indicador visual de qualidade\n- Tooltip com detalhes\n- Link para analytics',
    priority: 'High',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Coluna Roteiro de Triagem',
    description: 'Coluna mostrando status do roteiro de triagem da vaga (configurado, pendente, etc).\n\nHistoria de Usuario:\nComo recrutador, eu quero ver rapidamente se o roteiro de triagem esta configurado.\n\nCriterios de Aceitacao:\n- Status do roteiro visivel\n- Badge colorido por status\n- Click abre configuracao\n- Tooltip com resumo',
    priority: 'Medium',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Acoes por Linha - Menu Dropdown',
    description: 'Menu dropdown com acoes disponiveis para cada vaga na linha da tabela.\n\nHistoria de Usuario:\nComo recrutador, eu quero ter acesso rapido a acoes da vaga direto da tabela.\n\nCriterios de Aceitacao:\n- Botao de menu na linha\n- Dropdown com acoes\n- Acoes: Editar, Duplicar, Pausar, Publicar\n- Icones por acao',
    priority: 'High',
    labels: ['frontend', 'tabela', 'gestao-vagas'],
    storyPoints: 5
  },

  // ============================================
  // EPIC-VAG-007: PAINEL DE PREVIEW DA VAGA (VAG-037 a VAG-047) - 11 cards
  // ============================================
  {
    summary: '[FRONT] Preview Panel - Estrutura Base',
    description: 'Painel lateral que aparece ao selecionar uma vaga na tabela, mostrando detalhes e acoes rapidas.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver detalhes da vaga sem sair da lista.\n\nCriterios de Aceitacao:\n- Painel lateral abre ao clicar\n- Header com titulo e acoes\n- Tabs para diferentes secoes\n- Close button funciona',
    priority: 'Highest',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Tab Visao Geral - Funil Rapido',
    description: 'Tab de visao geral com funil de candidatos resumido e metricas principais.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver o funil da vaga rapidamente.\n\nCriterios de Aceitacao:\n- Funil visual com etapas\n- Contadores por etapa\n- Cores por status\n- Click navega para etapa',
    priority: 'High',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Tab Visao Geral - Metricas LIA',
    description: 'Secao com metricas de performance da LIA na vaga: triagens, tempo medio, qualidade.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver como a LIA esta performando nesta vaga.\n\nCriterios de Aceitacao:\n- Score geral LIA\n- Tempo medio de triagem\n- Taxa de aprovacao\n- Grafico de evolucao',
    priority: 'High',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Tab Visao Geral - Responsaveis',
    description: 'Secao mostrando recrutador, gestor e outros envolvidos na vaga.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver quem sao os responsaveis pela vaga.\n\nCriterios de Aceitacao:\n- Avatar e nome do recrutador\n- Avatar e nome do gestor\n- Role de cada pessoa\n- Link para contato',
    priority: 'Medium',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Tab Visao Geral - Datas Criticas',
    description: 'Secao com datas importantes: criacao, deadline, SLA, etc.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver os prazos da vaga rapidamente.\n\nCriterios de Aceitacao:\n- Data de criacao\n- Deadline de fechamento\n- Dias restantes\n- Alerta visual se urgente',
    priority: 'Medium',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Tab Roteiro de Triagem - WSI Blocks',
    description: 'Tab mostrando o roteiro de triagem configurado com blocos WSI (competencias comportamentais).\n\nHistoria de Usuario:\nComo recrutador, eu quero ver e editar o roteiro de triagem da vaga.\n\nCriterios de Aceitacao:\n- Blocos WSI visiveis\n- Perguntas por bloco\n- Pesos configurados\n- Modo de edicao inline',
    priority: 'Highest',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 13
  },
  {
    summary: '[FRONT] WSI Blocks - Accordion Expansivel',
    description: 'Componente accordion para expandir/colapsar blocos WSI no roteiro.\n\nHistoria de Usuario:\nComo recrutador, eu quero expandir blocos para ver detalhes.\n\nCriterios de Aceitacao:\n- Accordion funcional\n- Header com titulo do bloco\n- Icone de expand/collapse\n- Animacao suave',
    priority: 'High',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] WSI Blocks - Editor de Perguntas',
    description: 'Interface para editar perguntas dentro de cada bloco WSI.\n\nHistoria de Usuario:\nComo recrutador, eu quero editar as perguntas de triagem.\n\nCriterios de Aceitacao:\n- Adicionar pergunta\n- Editar pergunta existente\n- Remover pergunta\n- Reordenar perguntas',
    priority: 'High',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Configuracao de Canais de Triagem',
    description: 'Secao para configurar em quais canais a triagem sera realizada (WhatsApp, Email, etc).\n\nHistoria de Usuario:\nComo recrutador, eu quero definir por onde a LIA vai triar candidatos.\n\nCriterios de Aceitacao:\n- Toggle por canal\n- WhatsApp, Email, Chat\n- Preview de mensagem\n- Salvar configuracao',
    priority: 'High',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Processo Seletivo - Inline Breadcrumb',
    description: 'Breadcrumb mostrando as etapas do processo seletivo configurado para a vaga.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver o processo seletivo configurado.\n\nCriterios de Aceitacao:\n- Etapas em sequencia\n- Icone por etapa\n- Etapa atual destacada\n- Click para editar',
    priority: 'Medium',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Resize do Painel de Preview',
    description: 'Permitir redimensionar a largura do painel de preview arrastando a borda.\n\nHistoria de Usuario:\nComo recrutador, eu quero ajustar o tamanho do preview.\n\nCriterios de Aceitacao:\n- Handle de resize visivel\n- Drag para redimensionar\n- Largura minima e maxima\n- Persistencia da preferencia',
    priority: 'Low',
    labels: ['frontend', 'preview', 'gestao-vagas'],
    storyPoints: 3
  },

  // ============================================
  // EPIC-VAG-008: MODAIS DE ACAO EM LOTE (VAG-048 a VAG-056) - 9 cards
  // ============================================
  {
    summary: '[FRONT] JobActionsBar - Barra de Acoes em Lote',
    description: 'Barra fixa que aparece quando vagas sao selecionadas, com botoes para acoes em lote.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver uma barra de acoes quando seleciono vagas para executar operacoes em lote.\n\nCriterios de Aceitacao:\n- Barra aparece ao selecionar\n- Contador de vagas selecionadas\n- Todos os botoes funcionam\n- Botao X limpa selecao',
    priority: 'High',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] JobPublishModal - Publicar em Canais',
    description: 'Modal para publicar vagas em canais externos: LinkedIn, Website, Indeed, portais de vagas.\n\nHistoria de Usuario:\nComo recrutador, eu quero publicar vagas em varios canais de uma vez para ampliar o alcance.\n\nCriterios de Aceitacao:\n- Modal lista canais disponiveis\n- Checkbox para selecionar canais\n- Botao publicar funciona\n- Feedback de sucesso/erro',
    priority: 'High',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] JobInsightsModal - Metricas Expandidas',
    description: 'Modal com metricas detalhadas das vagas selecionadas: WSI scores, demographics, performance analytics.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver analises detalhadas das vagas para tomar decisoes informadas.\n\nCriterios de Aceitacao:\n- Modal exibe metricas\n- Graficos funcionam\n- Insights LIA gerados\n- Export de dados possivel',
    priority: 'Highest',
    labels: ['frontend', 'backend', 'modais', 'gestao-vagas'],
    storyPoints: 13
  },
  {
    summary: '[FRONT] JobDuplicateModal - Duplicar Vaga',
    description: 'Modal para duplicar vaga selecionada com opcao de alterar recrutador e configuracoes basicas.\n\nHistoria de Usuario:\nComo recrutador, eu quero duplicar uma vaga existente para criar uma similar rapidamente.\n\nCriterios de Aceitacao:\n- Modal exibe dados da vaga original\n- Form para alterar titulo\n- Selector para recrutador\n- Duplicacao cria nova vaga',
    priority: 'Medium',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] JobStatusModal - Pausar/Ativar Vaga',
    description: 'Modal para pausar ou reativar vagas selecionadas com campo para motivo/comentario.\n\nHistoria de Usuario:\nComo recrutador, eu quero pausar ou ativar vagas com registro do motivo.\n\nCriterios de Aceitacao:\n- Modal exibe acao correta (pausar/ativar)\n- Campo para motivo\n- Confirmacao atualiza status\n- Feedback visual adequado',
    priority: 'High',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] JobAssignRecruiterModal - Atribuir Recrutador',
    description: 'Modal para atribuir ou trocar o recrutador responsavel pelas vagas selecionadas.\n\nHistoria de Usuario:\nComo gestor, eu quero atribuir vagas a diferentes recrutadores da minha equipe.\n\nCriterios de Aceitacao:\n- Lista de recrutadores disponiveis\n- Selecao de novo recrutador\n- Confirmacao atualiza vagas\n- Notificacao ao novo recrutador',
    priority: 'Medium',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] JobUnpublishModal - Despublicar Vaga',
    description: 'Modal para remover vaga de canais onde foi publicada (LinkedIn, Indeed, Website).\n\nHistoria de Usuario:\nComo recrutador, eu quero despublicar uma vaga quando nao estiver mais disponivel.\n\nCriterios de Aceitacao:\n- Lista canais publicados\n- Checkbox para selecionar\n- Confirmacao remove de canais\n- Status atualiza na vaga',
    priority: 'Low',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] JobCompareModal - Comparar Vagas',
    description: 'Modal para comparar 2 ou mais vagas lado a lado com metricas e caracteristicas.\n\nHistoria de Usuario:\nComo recrutador, eu quero comparar vagas similares para entender diferencas de performance.\n\nCriterios de Aceitacao:\n- Vagas exibidas lado a lado\n- Metricas comparadas\n- Diferencas destacadas\n- Scroll sincronizado',
    priority: 'Medium',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] EditJobModal - Edicao Completa da Vaga',
    description: 'Modal completo para edicao de todos os campos da vaga com validacao e preview.\n\nHistoria de Usuario:\nComo recrutador, eu quero editar todos os detalhes de uma vaga em um unico lugar.\n\nCriterios de Aceitacao:\n- Todos os campos editaveis\n- Validacao em tempo real\n- Preview das mudancas\n- Salvar atualiza a vaga',
    priority: 'Highest',
    labels: ['frontend', 'modais', 'gestao-vagas'],
    storyPoints: 13
  },

  // ============================================
  // EPIC-VAG-009: SISTEMA DE FILTROS E BUSCA (VAG-057 a VAG-065) - 9 cards
  // ============================================
  {
    summary: '[FRONT] JobFiltersPanel - Painel Lateral de Filtros',
    description: 'Painel lateral com todos os filtros disponiveis para vagas, organizado por categorias.\n\nHistoria de Usuario:\nComo recrutador, eu quero ter um painel de filtros organizado para refinar minha busca de vagas.\n\nCriterios de Aceitacao:\n- Painel lateral funcional\n- Categorias organizadas\n- Badge com contador de filtros ativos\n- Botao limpar todos os filtros',
    priority: 'High',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Filtros Rapidos - Botoes Pre-definidos',
    description: 'Botoes de filtro rapido no topo do painel para os filtros mais usados: Ativas, Urgentes, Remotas, Sem Candidatos.\n\nHistoria de Usuario:\nComo recrutador, eu quero filtrar rapidamente por criterios comuns com um clique.\n\nCriterios de Aceitacao:\n- 4 botoes visiveis\n- Toggle funciona\n- Visual de estado ativo\n- Combina com outros filtros',
    priority: 'High',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Filtro por Status da Vaga',
    description: 'Filtro para selecionar vagas por status: Ativa, Rascunho, Paralisada, Fechada, etc.\n\nHistoria de Usuario:\nComo recrutador, eu quero filtrar vagas pelo status para focar nas que preciso trabalhar.\n\nCriterios de Aceitacao:\n- Lista todos os status\n- Multi-selecao funciona\n- Contador por status\n- Cores por status',
    priority: 'High',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Filtro por Etapa do Processo',
    description: 'Filtro para selecionar vagas pela etapa atual do processo: Triagem, Entrevistas, Finalistas, etc.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver vagas que estao em determinada etapa do processo.\n\nCriterios de Aceitacao:\n- Lista etapas do processo\n- Multi-selecao funciona\n- Icones por etapa\n- Contador de vagas por etapa',
    priority: 'Medium',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Filtro por Modelo de Trabalho',
    description: 'Filtro para selecionar vagas pelo modelo de trabalho: Remoto, Hibrido, Presencial.\n\nHistoria de Usuario:\nComo recrutador, eu quero filtrar vagas pelo modelo de trabalho para agrupar similares.\n\nCriterios de Aceitacao:\n- 3 opcoes visiveis\n- Multi-selecao permitida\n- Icone por modelo\n- Filtro funciona corretamente',
    priority: 'Medium',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Filtro por Recrutador/Gestor',
    description: 'Dropdown para filtrar vagas pelo recrutador responsavel ou gestor da vaga.\n\nHistoria de Usuario:\nComo gestor, eu quero ver vagas de um recrutador especifico da minha equipe.\n\nCriterios de Aceitacao:\n- Dropdown com recrutadores\n- Dropdown com gestores\n- Busca por nome\n- Filtro funciona',
    priority: 'Medium',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Busca Booleana - Operadores AND/OR/NOT',
    description: 'Campo de busca avancada com suporte a operadores booleanos para queries complexas.\n\nHistoria de Usuario:\nComo recrutador avancado, eu quero usar operadores booleanos para buscas mais precisas.\n\nCriterios de Aceitacao:\n- Toggle para modo booleano\n- Parsing de operadores\n- Highlighting de sintaxe\n- Ajuda de sintaxe disponivel',
    priority: 'Low',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Pesquisas Salvas - Templates de Busca',
    description: 'Sistema para salvar combinacoes de filtros como templates reutilizaveis.\n\nHistoria de Usuario:\nComo recrutador, eu quero salvar minhas buscas frequentes para reutilizar depois.\n\nCriterios de Aceitacao:\n- Botao salvar busca atual\n- Lista de buscas salvas\n- Aplicar busca salva\n- Deletar busca salva',
    priority: 'Medium',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Persistencia de Filtros - Custom Hook',
    description: 'Hook customizado para persistir estado dos filtros no localStorage e URL search params.\n\nHistoria de Usuario:\nComo recrutador, eu quero que meus filtros sejam lembrados entre sessoes.\n\nCriterios de Aceitacao:\n- Filtros salvos no localStorage\n- URL reflete filtros ativos\n- Carregar filtros da URL\n- Clear limpa tudo',
    priority: 'High',
    labels: ['frontend', 'filtros', 'gestao-vagas'],
    storyPoints: 3
  },

  // ============================================
  // EPIC-VAG-010: CHAT LIA MULTI-NIVEL (VAG-066 a VAG-074) - 9 cards
  // ============================================
  {
    summary: '[FRONT] Nivel 1 - Mini Prompt Inline',
    description: 'Campo de input compacto no header da tabela para perguntas rapidas a LIA.\n\nHistoria de Usuario:\nComo recrutador, eu quero fazer perguntas rapidas sem abrir um chat completo.\n\nCriterios de Aceitacao:\n- Input visivel no header\n- Icones funcionais\n- Enter envia mensagem\n- Resposta exibida inline',
    priority: 'High',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Nivel 2 - Chat Expandido Lateral',
    description: 'Painel lateral de chat expandido para conversas mais longas com LIA.\n\nHistoria de Usuario:\nComo recrutador, eu quero ter um chat completo para conversas mais detalhadas.\n\nCriterios de Aceitacao:\n- Painel lateral abre\n- Historico de mensagens\n- Resize funciona\n- Close button funciona',
    priority: 'Highest',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Nivel 3 - Super Chat Criacao de Vaga',
    description: 'Modal expandido para criacao de vaga guiada por LIA com wizard de etapas.\n\nHistoria de Usuario:\nComo recrutador, eu quero criar vagas conversando com a LIA de forma guiada.\n\nCriterios de Aceitacao:\n- Modal expande para criacao\n- Wizard de etapas funciona\n- LIA guia o processo\n- Vaga criada ao final',
    priority: 'Highest',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 13
  },
  {
    summary: '[FRONT] Deteccao de Intent de Criacao de Vaga',
    description: 'Funcao que detecta quando usuario quer criar vaga e abre automaticamente o wizard.\n\nHistoria de Usuario:\nComo recrutador, eu quero que a LIA entenda quando quero criar uma vaga e inicie o processo.\n\nCriterios de Aceitacao:\n- Detecta padroes de criacao\n- Abre wizard automaticamente\n- Funciona em todos os niveis\n- Confirmacao antes de abrir',
    priority: 'High',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Auto-Expand LIA ao Selecionar Vagas',
    description: 'Expandir automaticamente o chat LIA quando vagas sao selecionadas para acoes em lote.\n\nHistoria de Usuario:\nComo recrutador, eu quero que a LIA esteja pronta para me ajudar quando seleciono vagas.\n\nCriterios de Aceitacao:\n- Chat expande ao selecionar\n- Contexto das vagas passado\n- Mensagem inicial contextual\n- Nao expande se ja aberto',
    priority: 'Medium',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Historico de Mensagens Inline',
    description: 'Manter historico de mensagens do chat inline durante a sessao.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver o historico das minhas perguntas anteriores.\n\nCriterios de Aceitacao:\n- Mensagens mantidas na sessao\n- Scroll para ver historico\n- Botao limpar funciona\n- Limite de mensagens',
    priority: 'Medium',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] AudioRecordButton - Gravacao de Voz',
    description: 'Botao para gravar audio e transcrever usando Web Speech API ou Deepgram.\n\nHistoria de Usuario:\nComo recrutador, eu quero falar com a LIA ao inves de digitar.\n\nCriterios de Aceitacao:\n- Botao mic visivel\n- Gravacao inicia ao clicar\n- Transcricao automatica\n- Texto inserido no input',
    priority: 'Medium',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] LiaVacancyQueriesGuide - Popover de Sugestoes',
    description: 'Popover com tabs mostrando queries pre-definidas para perguntar a LIA sobre vagas.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver sugestoes de perguntas que posso fazer sobre vagas.\n\nCriterios de Aceitacao:\n- Popover abre ao clicar\n- Tabs organizadas\n- Queries clicaveis\n- Envia para chat ao clicar',
    priority: 'High',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] ExpandedChatModal - Modal Full Screen',
    description: 'Modal de chat expandido em tela cheia para conversas complexas e criacao de vagas.\n\nHistoria de Usuario:\nComo recrutador, eu quero ter espaco total para conversar com a LIA em tarefas complexas.\n\nCriterios de Aceitacao:\n- Modal abre em full screen\n- Chat funcional completo\n- Modo criacao de vaga\n- Close e minimize funcionam',
    priority: 'Highest',
    labels: ['frontend', 'lia', 'chat', 'gestao-vagas'],
    storyPoints: 8
  },

  // ============================================
  // EPIC-VAG-011: JOB CREATION WIZARD (VAG-075 a VAG-093) - 19 cards
  // ============================================
  {
    summary: '[FRONT] Botao Nova Vaga - Header Principal',
    description: 'Botao principal no header para iniciar criacao de nova vaga via wizard LIA.\n\nHistoria de Usuario:\nComo recrutador, eu quero um botao claro para iniciar a criacao de uma nova vaga.\n\nCriterios de Aceitacao:\n- Botao visivel no header\n- Icone Plus correto\n- Abre wizard ao clicar\n- Hover state funciona',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[FRONT] Super Chat Modal - Container Principal',
    description: 'Container principal do wizard de criacao de vaga com layout split (chat + formulario).\n\nHistoria de Usuario:\nComo recrutador, eu quero uma interface clara para criar vagas passo a passo.\n\nCriterios de Aceitacao:\n- Layout split funcional\n- Stepper de progresso\n- Chat side funciona\n- Form side funciona',
    priority: 'Highest',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Wizard Step 1 - Descricao Inicial via Chat',
    description: 'Primeira etapa do wizard onde usuario descreve a vaga conversando com LIA que extrai requisitos.\n\nHistoria de Usuario:\nComo recrutador, eu quero descrever a vaga naturalmente e a LIA extrair os requisitos.\n\nCriterios de Aceitacao:\n- Chat funcional\n- LIA extrai requisitos\n- Criterios exibidos para confirmacao\n- Avancar para proxima etapa',
    priority: 'Highest',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Wizard Step 2 - Informacoes Basicas',
    description: 'Formulario para titulo, departamento, localizacao e gestor responsavel.\n\nHistoria de Usuario:\nComo recrutador, eu quero preencher as informacoes basicas da vaga de forma estruturada.\n\nCriterios de Aceitacao:\n- Todos os campos funcionam\n- Validacao em tempo real\n- AutoComplete departamentos\n- Gestor selecionavel',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Wizard Step 3 - Remuneracao e Beneficios',
    description: 'Formulario para faixa salarial e selecao de beneficios da empresa.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir salario e beneficios usando os cadastrados da empresa.\n\nCriterios de Aceitacao:\n- Range de salario funciona\n- Beneficios da empresa listados\n- Multi-selecao de beneficios\n- Preview de total compensation',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Wizard Step 4 - Competencias Tecnicas',
    description: 'Formulario para skills, tecnologias e tech stack com sugestoes baseadas no titulo.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir os requisitos tecnicos com sugestoes inteligentes.\n\nCriterios de Aceitacao:\n- Tags de skills funcionam\n- Tech stack por categoria\n- Sugestoes automaticas\n- Pesos por skill',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Wizard Step 5 - Competencias WSI Comportamentais',
    description: 'Formulario para definir competencias comportamentais usando metodologia Big Five / WSI.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir o perfil comportamental ideal para a vaga.\n\nCriterios de Aceitacao:\n- 5 dimensoes Big Five\n- Sliders funcionam\n- Peso por competencia\n- Perfil ideal visualizado',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Wizard Step 6 - Requisitos Idiomas e Formacao',
    description: 'Formulario para requisitos de idiomas e nivel de formacao academica.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir requisitos de idiomas e formacao para a vaga.\n\nCriterios de Aceitacao:\n- Multi-idiomas com nivel\n- Selecao de formacao\n- Area de estudo\n- Campos opcionais',
    priority: 'Medium',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Wizard Step 7 - Scorecard de Avaliacao',
    description: 'Formulario para definir criterios de avaliacao e pesos para scoring de candidatos.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir como os candidatos serao avaliados e pontuados.\n\nCriterios de Aceitacao:\n- Builder de criterios\n- Pesos ajustaveis\n- Rubricas por criterio\n- Validacao de total',
    priority: 'Medium',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Wizard Step 8 - Prazos e Cronograma',
    description: 'Formulario para definir prazos das etapas do processo: triagem, shortlist, fechamento.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir prazos para cada etapa do processo seletivo.\n\nCriterios de Aceitacao:\n- DatePickers funcionam\n- Validacao de sequencia\n- SLA calculado\n- Alertas de prazo curto',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Wizard Step 9 - Pipeline do Processo',
    description: 'Configuracao das etapas do processo seletivo usando templates ou customizacao.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir as etapas do processo seletivo para esta vaga.\n\nCriterios de Aceitacao:\n- Templates disponiveis\n- Customizacao de etapas\n- Drag-and-drop funciona\n- Etapas salvas na vaga',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Wizard Step 10 - Solicitacao de Dados',
    description: 'Configuracao dos documentos e dados a solicitar dos candidatos durante triagem.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir quais documentos solicitar dos candidatos.\n\nCriterios de Aceitacao:\n- Lista de campos disponiveis\n- Toggle obrigatorio/opcional\n- Campos customizados\n- Preview da solicitacao',
    priority: 'Medium',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Wizard Step 11 - Revisao Final e Publicacao',
    description: 'Tela final de revisao de todos os dados da vaga com opcao de publicar ou salvar como rascunho.\n\nHistoria de Usuario:\nComo recrutador, eu quero revisar tudo antes de criar a vaga oficialmente.\n\nCriterios de Aceitacao:\n- Preview completo\n- Validacao final\n- Botao criar vaga\n- Feedback de sucesso',
    priority: 'Highest',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[BACK] Endpoint /lia/job-wizard/step',
    description: 'Endpoint backend para processar cada etapa do wizard de criacao de vaga com LIA.\n\nHistoria de Usuario:\nComo sistema, eu preciso processar as interacoes do wizard e manter o estado da conversa.\n\nCriterios de Aceitacao:\n- Endpoint processa todas as etapas\n- Mantem estado da conversa\n- Detecta intents por etapa\n- Retorna dados extraidos',
    priority: 'Highest',
    labels: ['backend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 13
  },
  {
    summary: '[FRONT] Navegacao entre Etapas - Stepper Visual',
    description: 'Componente visual de stepper mostrando progresso e permitindo navegacao entre etapas.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver meu progresso e poder voltar a etapas anteriores.\n\nCriterios de Aceitacao:\n- Stepper visual claro\n- Status por etapa\n- Navegacao funciona\n- Validacao ao avancar',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[FRONT] Calibracao de Candidatos - Sourcing',
    description: 'Funcionalidade de calibracao mostrando candidatos similares da base local e global para feedback.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver candidatos similares para calibrar os requisitos da vaga.\n\nCriterios de Aceitacao:\n- Candidatos locais exibidos\n- Candidatos globais exibidos\n- Feedback influencia requisitos\n- Adicionar a base funciona',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] ScreeningQuestionsPanel - Perguntas de Triagem',
    description: 'Painel para configurar perguntas de triagem que a LIA fara aos candidatos.\n\nHistoria de Usuario:\nComo recrutador, eu quero definir as perguntas que a LIA fara na triagem.\n\nCriterios de Aceitacao:\n- Lista de perguntas editavel\n- Adicionar/remover perguntas\n- Reordenar perguntas\n- Tipos de resposta',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Integracao com Busca Global - Pearch API',
    description: 'Integracao com API Pearch para buscar candidatos globais durante calibracao.\n\nHistoria de Usuario:\nComo recrutador, eu quero ver candidatos de fora da minha base para expandir opcoes.\n\nCriterios de Aceitacao:\n- Busca Pearch funciona\n- Resultados exibidos\n- Reveal com creditos\n- Error handling adequado',
    priority: 'High',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 8
  },
  {
    summary: '[FRONT] Validacao de Dados por Etapa - Zod Schema',
    description: 'Schemas Zod para validacao dos dados em cada etapa do wizard.\n\nHistoria de Usuario:\nComo sistema, eu preciso validar os dados antes de permitir avancar no wizard.\n\nCriterios de Aceitacao:\n- Validacao por etapa\n- Mensagens de erro claras\n- Bloqueio de avanco se invalido\n- Highlight de campos com erro',
    priority: 'Medium',
    labels: ['frontend', 'wizard', 'job-creation', 'gestao-vagas'],
    storyPoints: 3
  },
  
  // ============================================
  // CARDS BACKEND RAILS (VAG-094 a VAG-108) - 15 cards
  // Adicionados em 22/Jan/2026
  // ============================================
  
  // EPIC-VAG-006: Tabela de Vagas
  {
    summary: '[BACK] API Listagem de Vagas - GET /api/v1/jobs',
    description: 'Endpoint para listagem de vagas com paginacao, filtros, ordenacao e busca.\n\nEndpoint: GET /api/v1/jobs\n\nParametros:\n- page, per_page (paginacao)\n- status (ativa, paralisada, concluida, cancelada)\n- search (busca textual)\n- sort_by, sort_order (ordenacao)\n- recruiter_id, work_model, date_from, date_to\n\nCriterios de Aceitacao:\n- Paginacao funciona\n- Filtros aplicados corretamente\n- Ordenacao multi-coluna\n- Performance < 200ms para 1000 vagas',
    priority: 'Highest',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 8
  },
  
  // EPIC-VAG-007: Preview da Vaga
  {
    summary: '[BACK] API Detalhes da Vaga - GET /api/v1/jobs/{id}',
    description: 'Endpoint para obter detalhes completos de uma vaga incluindo responsaveis, datas e configuracoes.\n\nEndpoint: GET /api/v1/jobs/{id}\n\nResponse: job, responsaveis, dates, config\n\nCriterios de Aceitacao:\n- Retorna todos os campos necessarios\n- 404 se vaga nao existe\n- Autorizacao por empresa',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[BACK] API Funil da Vaga - GET /api/v1/jobs/{id}/funnel',
    description: 'Endpoint para obter dados do funil de candidatos de uma vaga especifica.\n\nEndpoint: GET /api/v1/jobs/{id}/funnel\n\nResponse: total, screening, interview, final, hired\n\nCriterios de Aceitacao:\n- Contagens corretas por etapa\n- Atualizado em tempo real\n- Cache de 60s para performance',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[BACK] API Metricas da Vaga - GET /api/v1/jobs/{id}/metrics',
    description: 'Endpoint para obter metricas de performance LIA de uma vaga especifica.\n\nEndpoint: GET /api/v1/jobs/{id}/metrics\n\nResponse: triagens_realizadas, tempo_medio_triagem, taxa_aprovacao, wsi_medio, taxa_resposta\n\nCriterios de Aceitacao:\n- Metricas calculadas corretamente\n- Cache de 5min para performance',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas', 'lia'],
    storyPoints: 5
  },
  {
    summary: '[BACK] API Roteiro Triagem - GET /api/v1/jobs/{id}/screening-script',
    description: 'Endpoint para obter o roteiro de triagem WSI com os 7 blocos de perguntas.\n\nEndpoint: GET /api/v1/jobs/{id}/screening-script\n\nResponse: blocks (7 blocos WSI), questions, config canais\n\nCriterios de Aceitacao:\n- 7 blocos WSI retornados\n- Perguntas ordenadas por bloco\n- Configuracao de canais incluida',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas', 'wsi'],
    storyPoints: 5
  },
  {
    summary: '[BACK] API Editar Perguntas Triagem - PUT /api/v1/jobs/{id}/screening-questions',
    description: 'Endpoint para editar perguntas do roteiro de triagem de uma vaga.\n\nEndpoint: PUT /api/v1/jobs/{id}/screening-questions\n\nBody: questions, block_id\n\nCriterios de Aceitacao:\n- Atualizacao persiste no banco\n- Validacao de estrutura das perguntas\n- Auditoria de alteracoes',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas', 'wsi'],
    storyPoints: 5
  },
  
  // EPIC-VAG-008: Modais de Acao
  {
    summary: '[BACK] API Publicar Vagas Bulk - POST /api/v1/jobs/bulk/publish',
    description: 'Endpoint para publicar multiplas vagas em canais de divulgacao.\n\nEndpoint: POST /api/v1/jobs/bulk/publish\n\nBody: job_ids, channels (linkedin, indeed, site, careers_page)\n\nCriterios de Aceitacao:\n- Suporta multiplas vagas\n- Suporta multiplos canais\n- Retorna status individual por vaga\n- Rollback parcial se algum falhar',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas', 'bulk'],
    storyPoints: 8
  },
  {
    summary: '[BACK] API Pausar/Ativar Vaga - PATCH /api/v1/jobs/{id}/status',
    description: 'Endpoint para alterar status da vaga (ativa, paralisada, cancelada, concluida). Nao inclui fluxo de IA.\n\nEndpoint: PATCH /api/v1/jobs/{id}/status\n\nBody: status, reason (opcional), unpause_date (opcional)\n\nCriterios de Aceitacao:\n- Altera status corretamente\n- Grava motivo da pausa se informado\n- Registra auditoria\n- Nao dispara fluxo de IA (separado)',
    priority: 'Highest',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[BACK] API Duplicar Vaga - POST /api/v1/jobs/{id}/duplicate',
    description: 'Endpoint para duplicar uma vaga existente com novo titulo e datas.\n\nEndpoint: POST /api/v1/jobs/{id}/duplicate\n\nBody: new_title (opcional), copy_pipeline, copy_screening\n\nCriterios de Aceitacao:\n- Copia todos os campos da vaga\n- Gera novo ID e codigo\n- Status inicial: rascunho\n- Pipeline e triagem copiados se solicitado',
    priority: 'Medium',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[BACK] API Atribuir Recrutador - PATCH /api/v1/jobs/{id}/recruiter',
    description: 'Endpoint para atribuir ou alterar o recrutador responsavel por uma vaga.\n\nEndpoint: PATCH /api/v1/jobs/{id}/recruiter\n\nBody: recruiter_id, notify (boolean)\n\nCriterios de Aceitacao:\n- Atribui recrutador corretamente\n- Notifica recrutador se solicitado\n- Valida se recrutador existe',
    priority: 'Medium',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 3
  },
  {
    summary: '[BACK] API Despublicar Vaga - DELETE /api/v1/jobs/{id}/publications',
    description: 'Endpoint para despublicar vaga de todos os canais de divulgacao.\n\nEndpoint: DELETE /api/v1/jobs/{id}/publications\n\nParametros: channels (opcional, todos se vazio)\n\nCriterios de Aceitacao:\n- Remove de todos os canais se nao especificado\n- Remove de canais especificos se informado\n- Retorna status por canal',
    priority: 'Medium',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 5
  },
  {
    summary: '[BACK] API Editar Vaga Completa - PUT /api/v1/jobs/{id}',
    description: 'Endpoint para edicao completa de uma vaga, atualizando todos os campos permitidos.\n\nEndpoint: PUT /api/v1/jobs/{id}\n\nBody: Todos os campos editaveis da vaga\n\nCriterios de Aceitacao:\n- Atualiza todos os campos\n- Validacao de campos obrigatorios\n- Registra alteracoes em auditoria\n- Nao permite alterar campos bloqueados',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas'],
    storyPoints: 8
  },
  
  // EPIC-VAG-009: Filtros
  {
    summary: '[BACK] API Pesquisas Salvas - CRUD /api/v1/saved-searches',
    description: 'Endpoints para salvar, listar e excluir pesquisas/filtros favoritos do usuario.\n\nEndpoints:\n- POST /api/v1/saved-searches (criar)\n- GET /api/v1/saved-searches (listar)\n- DELETE /api/v1/saved-searches/{id} (excluir)\n\nCriterios de Aceitacao:\n- Salva pesquisa com nome\n- Lista pesquisas do usuario\n- Exclui pesquisa existente\n- Limite de 20 pesquisas por usuario',
    priority: 'Medium',
    labels: ['backend', 'rails', 'api', 'gestao-vagas', 'filtros'],
    storyPoints: 5
  },
  
  // EPIC-VAG-011: Job Creation Wizard
  {
    summary: '[BACK] API Criar Vaga - POST /api/v1/jobs',
    description: 'Endpoint para criar nova vaga a partir dos dados coletados pelo wizard de criacao.\n\nEndpoint: POST /api/v1/jobs\n\nBody: Todos os campos das 11 etapas do wizard\n\nCriterios de Aceitacao:\n- Cria vaga com todos os campos\n- Gera codigo unico automaticamente\n- Valida campos obrigatorios\n- Status inicial configuravel (rascunho/ativa)',
    priority: 'Highest',
    labels: ['backend', 'rails', 'api', 'gestao-vagas', 'wizard'],
    storyPoints: 8
  },
  {
    summary: '[BACK] API Recursos do Wizard - GET endpoints auxiliares',
    description: 'Endpoints auxiliares para o wizard de criacao: beneficios, skills, templates de pipeline.\n\nEndpoints:\n- GET /api/v1/benefits (lista de beneficios)\n- GET /api/v1/skills (lista de competencias)\n- GET /api/v1/pipeline-templates (templates de pipeline)\n\nCriterios de Aceitacao:\n- Lista beneficios da empresa\n- Lista competencias por categoria\n- Lista templates de pipeline ativos\n- Cache de 1h para performance',
    priority: 'High',
    labels: ['backend', 'rails', 'api', 'gestao-vagas', 'wizard'],
    storyPoints: 5
  }
];

async function getAccessToken() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found for repl/depl');
  }

  const response = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  );
  
  const data = await response.json();
  const settings = data.items?.[0]?.settings;
  const accessToken = settings?.access_token || settings?.oauth?.credentials?.access_token;

  if (!accessToken) {
    throw new Error('Jira not connected');
  }

  return accessToken;
}

async function getJiraClient() {
  const accessToken = await getAccessToken();
  
  return new Version3Client({
    host: `https://api.atlassian.com/ex/jira/${CLOUD_ID}`,
    authentication: {
      oauth2: { accessToken },
    },
  });
}

async function main() {
  console.log('🚀 Iniciando criacao de cards no Jira...\n');
  console.log('Projeto alvo: ' + PROJECT_KEY);
  console.log('Cloud ID: ' + CLOUD_ID);
  console.log('Total de cards: ' + cards.length);
  console.log('---\n');
  
  try {
    const client = await getJiraClient();
    console.log('✅ Cliente Jira criado!\n');

    // Buscar tipos de issue do projeto
    console.log('📋 Buscando tipos de issue do projeto ' + PROJECT_KEY + '...');
    
    const projectData = await client.projects.getProject({ projectIdOrKey: PROJECT_KEY });
    console.log('✅ Projeto encontrado:', projectData.name);
    
    // Buscar issue types
    const createMeta = await client.issues.getCreateIssueMeta({ 
      projectKeys: [PROJECT_KEY],
      expand: 'projects.issuetypes.fields'
    });
    
    const project = createMeta.projects?.[0];
    if (!project) {
      console.log('❌ Projeto nao encontrado nos metadados');
      return;
    }
    
    const issueTypes = project.issuetypes || [];
    console.log('\nTipos de issue disponiveis:');
    issueTypes.forEach((t: any) => {
      console.log(`  - ${t.id}: ${t.name}`);
    });
    
    // Encontrar tipo Story ou Task
    const storyType = issueTypes.find((t: any) => 
      t.name === 'Story' || t.name === 'História' || t.name === 'Task' || t.name === 'Tarefa'
    );
    
    if (!storyType) {
      console.log('❌ Tipo Story/Task nao encontrado. Usando primeiro tipo disponivel.');
      return;
    }
    
    console.log(`\n📝 Usando tipo: ${storyType.name} (${storyType.id})\n`);
    console.log('--- Iniciando criacao dos cards ---\n');
    
    // Criar cards
    let created = 0;
    let failed = 0;
    
    for (const card of cards) {
      try {
        const issueData: any = {
          fields: {
            project: { key: PROJECT_KEY },
            issuetype: { id: storyType.id },
            summary: card.summary,
            description: {
              type: 'doc',
              version: 1,
              content: [
                {
                  type: 'paragraph',
                  content: [
                    {
                      type: 'text',
                      text: card.description
                    }
                  ]
                }
              ]
            },
            labels: card.labels
          }
        };
        
        const issue = await client.issues.createIssue(issueData);
        console.log(`✅ ${issue.key} - ${card.summary.substring(0, 50)}...`);
        created++;
        
        // Pequeno delay para evitar rate limiting
        await new Promise(resolve => setTimeout(resolve, 300));
        
      } catch (error: any) {
        console.log(`❌ Erro: ${card.summary.substring(0, 40)}... - ${error.message}`);
        if (error.response?.data) {
          console.log('   Detalhes:', JSON.stringify(error.response.data).substring(0, 200));
        }
        failed++;
      }
    }
    
    console.log(`\n📊 Resultado Final:`);
    console.log(`   ✅ Criados: ${created}`);
    console.log(`   ❌ Falhas: ${failed}`);
    console.log(`   📋 Total: ${cards.length}`);
    console.log(`\n🔗 Acesse o board: https://wedotalent.atlassian.net/jira/software/projects/WT/boards/1`);
    
  } catch (error: any) {
    console.error('❌ Erro geral:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', JSON.stringify(error.response.data).substring(0, 500));
    }
  }
}

main();
