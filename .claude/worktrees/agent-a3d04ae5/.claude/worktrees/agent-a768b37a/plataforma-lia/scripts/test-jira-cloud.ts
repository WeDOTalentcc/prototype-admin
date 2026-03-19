async function testJiraCloud() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  const response = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken!
      }
    }
  );
  
  const data = await response.json();
  const settings = data.items?.[0]?.settings;
  const token = settings?.access_token || settings?.oauth?.credentials?.access_token;
  
  console.log('🔑 Token encontrado:', !!token);
  
  // Step 1: Get accessible resources (cloud IDs)
  console.log('\n📌 Buscando cloud resources...');
  const resourcesResponse = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: {
      'Authorization': 'Bearer ' + token,
      'Accept': 'application/json'
    }
  });
  
  console.log('Status:', resourcesResponse.status);
  
  if (resourcesResponse.ok) {
    const resources = await resourcesResponse.json();
    console.log('Resources:', JSON.stringify(resources, null, 2));
    
    if (resources.length > 0) {
      const cloudId = resources[0].id;
      const siteName = resources[0].name;
      console.log('\n✅ Cloud ID encontrado:', cloudId);
      console.log('Site:', siteName);
      
      // Step 2: Test API with cloud ID
      console.log('\n🔍 Testando API com Cloud ID...');
      const myselfResponse = await fetch(`https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/myself`, {
        headers: {
          'Authorization': 'Bearer ' + token,
          'Accept': 'application/json'
        }
      });
      
      console.log('Myself API Status:', myselfResponse.status);
      if (myselfResponse.ok) {
        const myself = await myselfResponse.json();
        console.log('✅ Usuário:', myself.displayName, '(' + myself.emailAddress + ')');
      } else {
        const errorText = await myselfResponse.text();
        console.log('Erro:', errorText.substring(0, 200));
      }
      
      // Step 3: List projects
      console.log('\n📋 Listando projetos...');
      const projectsResponse = await fetch(`https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/project`, {
        headers: {
          'Authorization': 'Bearer ' + token,
          'Accept': 'application/json'
        }
      });
      
      console.log('Projects API Status:', projectsResponse.status);
      if (projectsResponse.ok) {
        const projects = await projectsResponse.json();
        console.log('Projetos encontrados:');
        projects.forEach((p: any) => {
          console.log(`  - ${p.key}: ${p.name}`);
        });
      }
    }
  } else {
    const errorText = await resourcesResponse.text();
    console.log('Erro ao buscar resources:', errorText.substring(0, 300));
  }
}

testJiraCloud().catch(console.error);
