import { Client } from '@notionhq/client';
import * as fs from 'fs';
import * as path from 'path';

let connectionSettings: any;

async function getAccessToken() {
  if (connectionSettings && connectionSettings.settings.expires_at && new Date(connectionSettings.settings.expires_at).getTime() > Date.now()) {
    return connectionSettings.settings.access_token;
  }
  
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found for repl/depl');
  }

  connectionSettings = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=notion',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  ).then(res => res.json()).then(data => data.items?.[0]);

  const accessToken = connectionSettings?.settings?.access_token || connectionSettings.settings?.oauth?.credentials?.access_token;

  if (!connectionSettings || !accessToken) {
    throw new Error('Notion not connected');
  }
  return accessToken;
}

async function getUncachableNotionClient() {
  const accessToken = await getAccessToken();
  return new Client({ auth: accessToken });
}

function splitIntoChunks(text: string, maxLength: number = 2000): string[] {
  const chunks: string[] = [];
  let remaining = text;
  
  while (remaining.length > 0) {
    if (remaining.length <= maxLength) {
      chunks.push(remaining);
      break;
    }
    
    let splitIndex = remaining.lastIndexOf('\n', maxLength);
    if (splitIndex === -1 || splitIndex < maxLength / 2) {
      splitIndex = maxLength;
    }
    
    chunks.push(remaining.substring(0, splitIndex));
    remaining = remaining.substring(splitIndex + 1);
  }
  
  return chunks;
}

function markdownToNotionBlocks(markdown: string): any[] {
  const blocks: any[] = [];
  const lines = markdown.split('\n');
  let i = 0;
  let inCodeBlock = false;
  let codeContent = '';
  let codeLanguage = '';
  
  while (i < lines.length) {
    const line = lines[i];
    
    if (line.startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeLanguage = line.replace('```', '').trim() || 'plain text';
        codeContent = '';
      } else {
        inCodeBlock = false;
        const chunks = splitIntoChunks(codeContent.trim(), 2000);
        chunks.forEach((chunk, idx) => {
          blocks.push({
            object: 'block',
            type: 'code',
            code: {
              rich_text: [{ type: 'text', text: { content: chunk } }],
              language: codeLanguage === 'mermaid' ? 'plain text' : (codeLanguage || 'plain text')
            }
          });
        });
      }
      i++;
      continue;
    }
    
    if (inCodeBlock) {
      codeContent += line + '\n';
      i++;
      continue;
    }
    
    if (line.startsWith('# ')) {
      blocks.push({
        object: 'block',
        type: 'heading_1',
        heading_1: {
          rich_text: [{ type: 'text', text: { content: line.replace('# ', '').substring(0, 2000) } }]
        }
      });
    } else if (line.startsWith('## ')) {
      blocks.push({
        object: 'block',
        type: 'heading_2',
        heading_2: {
          rich_text: [{ type: 'text', text: { content: line.replace('## ', '').substring(0, 2000) } }]
        }
      });
    } else if (line.startsWith('### ')) {
      blocks.push({
        object: 'block',
        type: 'heading_3',
        heading_3: {
          rich_text: [{ type: 'text', text: { content: line.replace('### ', '').substring(0, 2000) } }]
        }
      });
    } else if (line.startsWith('---')) {
      blocks.push({
        object: 'block',
        type: 'divider',
        divider: {}
      });
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      blocks.push({
        object: 'block',
        type: 'bulleted_list_item',
        bulleted_list_item: {
          rich_text: [{ type: 'text', text: { content: line.replace(/^[-*] /, '').substring(0, 2000) } }]
        }
      });
    } else if (line.match(/^\d+\. /)) {
      blocks.push({
        object: 'block',
        type: 'numbered_list_item',
        numbered_list_item: {
          rich_text: [{ type: 'text', text: { content: line.replace(/^\d+\. /, '').substring(0, 2000) } }]
        }
      });
    } else if (line.startsWith('| ')) {
      let tableRows: string[][] = [];
      while (i < lines.length && lines[i].startsWith('|')) {
        const row = lines[i]
          .split('|')
          .filter(cell => cell.trim() !== '')
          .map(cell => cell.trim());
        
        if (!lines[i].match(/^\|[\s-:|]+\|$/)) {
          tableRows.push(row);
        }
        i++;
      }
      i--;
      
      if (tableRows.length > 0) {
        const tableWidth = Math.max(...tableRows.map(r => r.length));
        blocks.push({
          object: 'block',
          type: 'table',
          table: {
            table_width: tableWidth,
            has_column_header: true,
            has_row_header: false,
            children: tableRows.map(row => ({
              type: 'table_row',
              table_row: {
                cells: row.map(cell => [{ type: 'text', text: { content: cell.substring(0, 2000) } }])
              }
            }))
          }
        });
      }
    } else if (line.startsWith('> ')) {
      blocks.push({
        object: 'block',
        type: 'quote',
        quote: {
          rich_text: [{ type: 'text', text: { content: line.replace('> ', '').substring(0, 2000) } }]
        }
      });
    } else if (line.trim() !== '') {
      blocks.push({
        object: 'block',
        type: 'paragraph',
        paragraph: {
          rich_text: [{ type: 'text', text: { content: line.substring(0, 2000) } }]
        }
      });
    }
    
    i++;
  }
  
  return blocks;
}

async function findOrCreatePage(notion: Client, title: string): Promise<string | null> {
  try {
    const searchResponse = await notion.search({
      query: title,
      filter: { property: 'object', value: 'page' }
    });
    
    for (const page of searchResponse.results) {
      if ('properties' in page && page.properties.title) {
        const titleProp = page.properties.title as any;
        if (titleProp.title && titleProp.title[0]?.plain_text === title) {
          return page.id;
        }
      }
    }
    
    return null;
  } catch (error) {
    console.error('Error searching for page:', error);
    return null;
  }
}

async function getFirstAvailablePage(notion: Client): Promise<string | null> {
  try {
    const searchResponse = await notion.search({
      filter: { property: 'object', value: 'page' },
      page_size: 1
    });
    
    if (searchResponse.results.length > 0) {
      return searchResponse.results[0].id;
    }
    
    return null;
  } catch (error) {
    console.error('Error finding available page:', error);
    return null;
  }
}

async function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function appendBlocksInBatches(notion: Client, pageId: string, blocks: any[], batchSize: number = 10) {
  for (let i = 0; i < blocks.length; i += batchSize) {
    const batch = blocks.slice(i, i + batchSize);
    console.log(`  Adding blocks ${i + 1} to ${Math.min(i + batchSize, blocks.length)} of ${blocks.length}...`);
    
    let retries = 3;
    while (retries > 0) {
      try {
        await notion.blocks.children.append({
          block_id: pageId,
          children: batch
        });
        await sleep(500);
        break;
      } catch (error: any) {
        retries--;
        if (retries === 0) {
          console.error(`  Error adding batch: ${error.message}`);
          for (const block of batch) {
            try {
              await notion.blocks.children.append({
                block_id: pageId,
                children: [block]
              });
              await sleep(200);
            } catch (blockError: any) {
              console.error(`  Skipping problematic block`);
            }
          }
        } else {
          console.log(`  Retrying... (${retries} attempts left)`);
          await sleep(2000);
        }
      }
    }
  }
}

async function main() {
  console.log('Publishing WEDOTALENT_PRODUCT_OVERVIEW.md to Notion...\n');
  
  const filePath = path.join(__dirname, '../../docs/WEDOTALENT_PRODUCT_OVERVIEW.md');
  
  if (!fs.existsSync(filePath)) {
    console.error('File not found:', filePath);
    process.exit(1);
  }
  
  const markdown = fs.readFileSync(filePath, 'utf-8');
  console.log(`Read ${markdown.length} characters from file`);
  
  const notion = await getUncachableNotionClient();
  console.log('Connected to Notion');
  
  const pageTitle = 'WeDo Talent - Product Overview';
  
  let parentPageId = await getFirstAvailablePage(notion);
  
  if (!parentPageId) {
    console.error('No accessible pages found in Notion workspace. Please share a page with the integration first.');
    process.exit(1);
  }
  
  console.log(`Using parent page: ${parentPageId}`);
  
  const blocks = markdownToNotionBlocks(markdown);
  console.log(`Converted to ${blocks.length} Notion blocks`);
  
  try {
    console.log('Creating new page...');
    const newPage = await notion.pages.create({
      parent: { page_id: parentPageId },
      properties: {
        title: {
          title: [{ text: { content: pageTitle } }]
        }
      }
    });
    
    console.log(`Created page: ${newPage.id}`);
    console.log('Adding content...');
    
    await appendBlocksInBatches(notion, newPage.id, blocks);
    
    console.log('\nSuccess! Page created and content added.');
    console.log(`Page URL: https://notion.so/${newPage.id.replace(/-/g, '')}`);
    
  } catch (error: any) {
    console.error('Error creating page:', error.message);
    if (error.body) {
      console.error('Details:', JSON.stringify(error.body, null, 2));
    }
    process.exit(1);
  }
}

main();
