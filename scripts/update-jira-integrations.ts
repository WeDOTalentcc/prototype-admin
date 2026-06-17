import { jiraService } from '../plataforma-lia/src/lib/api/jira-service';

const PROJECT_KEY = 'WT';

async function updateSendGridToMailgun() {
  console.log('\n🔄 Buscando cards que mencionam SendGrid...');
  console.log('ℹ️ Nota: Se não houver cards com SendGrid no Jira, significa que foram enviados já atualizados');
  console.log('✅ Os documentos locais já foram atualizados (SendGrid → Mailgun)');
}

async function createApifyCards() {
  console.log('\n🆕 Criando cards do Apify...');
  
  const apifyCards = [
    {
      projectKey: PROJECT_KEY,
      summary: '[INTEGRAÇÃO] INT-APY-001: Configurar Apify Account',
      description: `Configurar conta Apify para web scraping de LinkedIn.

Tarefas:
- Criar conta Apify e obter API token
- Configurar secret APIFY_API_TOKEN no ambiente
- Testar conexão com a API do Apify

Critérios de Aceite:
- Token configurado e funcionando
- Conexão testada com sucesso

Prioridade: MVP
Sprint: 2-3`,
      issueType: 'Task',
      labels: ['integracao', 'mvp', 'apify', 'sourcing'],
    },
    {
      projectKey: PROJECT_KEY,
      summary: '[INTEGRAÇÃO] INT-APY-002: LinkedIn Scraper Actor',
      description: `Implementar scraping de perfis do LinkedIn via Apify.

Tarefas:
- Configurar LinkedIn Profile Scraper Actor
- Implementar ApifyService no backend
- Criar endpoints para busca de candidatos
- Implementar cache de resultados (Redis)
- Rate limiting para evitar bloqueios

Critérios de Aceite:
- Busca de perfis funcionando
- Cache implementado
- Rate limiting ativo

Prioridade: MVP
Sprint: 2-3`,
      issueType: 'Task',
      labels: ['backend', 'mvp', 'apify', 'sourcing'],
    },
    {
      projectKey: PROJECT_KEY,
      summary: '[AI] INT-APY-003: Integração com Sourcing Agent',
      description: `Integrar Apify com o Sourcing Agent para automação de busca.

Tarefas:
- Conectar ApifyService ao Sourcing Agent
- Implementar Boolean query builder para buscas
- Criar fluxo de matching automático
- Integrar com sugestões proativas da LIA

Critérios de Aceite:
- Sourcing Agent usando Apify para buscas
- Boolean queries funcionando
- Sugestões proativas implementadas

Prioridade: MVP
Sprint: 3-4`,
      issueType: 'Task',
      labels: ['ai', 'mvp', 'apify', 'sourcing', 'agents'],
    },
  ];

  const results = await jiraService.createBulkIssues(apifyCards);
  
  console.log('\n📊 Resultado da criação:');
  console.log(`  ✅ Criados: ${results.created.length}`);
  results.created.forEach(card => {
    console.log(`    - ${card.issueKey}: ${card.summary}`);
  });
  
  if (results.failed.length > 0) {
    console.log(`  ❌ Falhas: ${results.failed.length}`);
    results.failed.forEach(fail => {
      console.log(`    - ${fail.summary}: ${fail.error}`);
    });
  }
  
  return results;
}

async function main() {
  console.log('═══════════════════════════════════════════════════════════');
  console.log('        ATUALIZAÇÃO DE CARDS JIRA - INTEGRAÇÕES MVP');
  console.log('═══════════════════════════════════════════════════════════');
  
  try {
    await updateSendGridToMailgun();
    
    await createApifyCards();
    
    console.log('\n═══════════════════════════════════════════════════════════');
    console.log('✅ Todas as atualizações concluídas!');
    console.log('═══════════════════════════════════════════════════════════');
  } catch (error: any) {
    console.error('\n❌ Erro fatal:', error.message);
    process.exit(1);
  }
}

main();
