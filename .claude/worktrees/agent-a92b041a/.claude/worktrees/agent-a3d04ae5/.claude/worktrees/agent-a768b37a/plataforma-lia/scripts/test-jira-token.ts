async function testJiraConnection() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  console.log('REPLIT_CONNECTORS_HOSTNAME:', hostname);
  console.log('Token type:', xReplitToken ? xReplitToken.split(' ')[0] : 'none');

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
  console.log('\n📦 Full response structure:');
  console.log(JSON.stringify(data, null, 2));
  
  if (data.items?.[0]) {
    const settings = data.items[0].settings;
    console.log('\n🔑 Token paths:');
    console.log('settings.access_token:', settings?.access_token ? '✅ exists (length: ' + settings.access_token.length + ')' : '❌ missing');
    console.log('settings.oauth.credentials.access_token:', settings?.oauth?.credentials?.access_token ? '✅ exists' : '❌ missing');
    console.log('site_url:', settings?.site_url);
    
    // Test direct API call
    const token = settings?.access_token || settings?.oauth?.credentials?.access_token;
    const siteUrl = settings?.site_url;
    
    if (token && siteUrl) {
      console.log('\n🔍 Testing direct API call to Jira...');
      const testResponse = await fetch(siteUrl + '/rest/api/3/myself', {
        headers: {
          'Authorization': 'Bearer ' + token,
          'Accept': 'application/json'
        }
      });
      console.log('Status:', testResponse.status);
      const testData = await testResponse.json();
      console.log('Response:', JSON.stringify(testData).substring(0, 300));
    }
  }
}

testJiraConnection().catch(console.error);
