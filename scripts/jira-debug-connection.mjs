async function main() {
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  console.log("Hostname:", hostname);
  console.log("Token type:", xReplitToken?.split(' ')[0]);

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
  const conn = data.items?.[0];
  
  if (!conn) {
    console.log("No Jira connection found!");
    console.log("Full response:", JSON.stringify(data, null, 2));
    return;
  }

  console.log("\n=== CONNECTION SETTINGS (keys) ===");
  console.log("Top-level keys:", Object.keys(conn));
  console.log("Settings keys:", Object.keys(conn.settings || {}));
  
  const s = conn.settings;
  console.log("\nsite_url:", s.site_url);
  console.log("cloud_id:", s.cloud_id);
  console.log("expires_at:", s.expires_at);
  console.log("Has access_token:", !!s.access_token);
  console.log("Has oauth:", !!s.oauth);
  if (s.oauth) {
    console.log("OAuth keys:", Object.keys(s.oauth));
    if (s.oauth.credentials) {
      console.log("OAuth credentials keys:", Object.keys(s.oauth.credentials));
      console.log("Has oauth access_token:", !!s.oauth.credentials.access_token);
    }
  }
  
  const accessToken = s.access_token || s.oauth?.credentials?.access_token;
  const cloudId = s.cloud_id;
  
  if (cloudId && accessToken) {
    console.log("\n=== TRYING CLOUD ID URL ===");
    const cloudUrl = `https://api.atlassian.com/ex/jira/${cloudId}/rest/api/3/project/search?maxResults=5`;
    console.log("URL:", cloudUrl);
    
    const res = await fetch(cloudUrl, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json'
      }
    });
    
    console.log("Status:", res.status);
    if (res.ok) {
      const projects = await res.json();
      console.log("Projects:", projects.values?.map(p => `${p.key}: ${p.name}`));
    } else {
      const text = await res.text();
      console.log("Error:", text.substring(0, 200));
    }
  }
  
  if (!cloudId && accessToken) {
    console.log("\n=== TRYING ACCESSIBLE RESOURCES ===");
    const res = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json'
      }
    });
    console.log("Status:", res.status);
    if (res.ok) {
      const resources = await res.json();
      console.log("Resources:", JSON.stringify(resources, null, 2));
    } else {
      console.log("Error:", await res.text());
    }
  }
}

main().catch(console.error);
