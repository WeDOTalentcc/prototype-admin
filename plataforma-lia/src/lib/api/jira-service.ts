import { Version3Client } from 'jira.js';

interface JiraConnectionSettings {
  settings?: {
    expires_at?: string;
    access_token?: string;
    site_url?: string;
    oauth?: {
      credentials?: {
        access_token?: string;
      };
    };
  };
}

let connectionSettings: JiraConnectionSettings | null = null;
let cachedCloudId: string | null = null;

interface JiraAuth {
  accessToken: string;
  hostName: string;
  cloudId: string;
  apiBaseUrl: string;
}

async function getAccessToken(): Promise<JiraAuth> {
  const now = Date.now();
  const expiresAt = connectionSettings?.settings?.expires_at 
    ? new Date(connectionSettings.settings.expires_at).getTime() 
    : 0;
  const hasValidToken = connectionSettings && expiresAt > now + 60000 && cachedCloudId;
  
  if (hasValidToken) {
    const accessToken = connectionSettings!.settings!.access_token || connectionSettings!.settings?.oauth?.credentials?.access_token;
    return {
      accessToken: accessToken || '',
      hostName: connectionSettings!.settings!.site_url || '',
      cloudId: cachedCloudId!,
      apiBaseUrl: `https://api.atlassian.com/ex/jira/${cachedCloudId}`,
    };
  }
  
  connectionSettings = null;
  cachedCloudId = null;

  if (process.env.JIRA_ACCESS_TOKEN && process.env.JIRA_SITE_URL) {
    const directToken = process.env.JIRA_ACCESS_TOKEN;
    const directSiteUrl = process.env.JIRA_SITE_URL;

    if (process.env.JIRA_CLOUD_ID) {
      cachedCloudId = process.env.JIRA_CLOUD_ID;
    } else {
      const resourcesResp = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
        headers: {
          'Authorization': `Bearer ${directToken}`,
          'Accept': 'application/json'
        }
      });

      if (!resourcesResp.ok) {
        throw new Error('Failed to fetch Jira accessible resources with JIRA_ACCESS_TOKEN');
      }

      const resources = await resourcesResp.json();
      const targetResource = resources.find((r: Record<string, unknown>) => r.url === directSiteUrl) || resources[0];

      if (!targetResource?.id) {
        throw new Error('No accessible Jira cloud found for JIRA_SITE_URL');
      }

      cachedCloudId = targetResource.id;
    }

    return {
      accessToken: directToken,
      hostName: directSiteUrl,
      cloudId: cachedCloudId!,
      apiBaseUrl: `https://api.atlassian.com/ex/jira/${cachedCloudId}`,
    };
  }

  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME;
  const xReplitToken = process.env.REPL_IDENTITY
    ? 'repl ' + process.env.REPL_IDENTITY
    : process.env.WEB_REPL_RENEWAL
    ? 'depl ' + process.env.WEB_REPL_RENEWAL
    : null;

  if (!xReplitToken || !hostname) {
    throw new Error(
      'Jira authentication not configured. Set JIRA_ACCESS_TOKEN + JIRA_SITE_URL (Cloud Run) or REPL_IDENTITY/WEB_REPL_RENEWAL + REPLIT_CONNECTORS_HOSTNAME (Replit).'
    );
  }

  connectionSettings = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=jira',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  ).then(res => res.json()).then(data => data.items?.[0] as JiraConnectionSettings | undefined) || null;

  if (!connectionSettings) {
    throw new Error('Jira not connected - no connection settings found');
  }

  const accessToken = connectionSettings.settings?.access_token || connectionSettings.settings?.oauth?.credentials?.access_token;
  const hostName = connectionSettings.settings?.site_url;

  if (!accessToken || !hostName) {
    throw new Error('Jira not connected - missing access token or site URL');
  }

  const resourcesResp = await fetch('https://api.atlassian.com/oauth/token/accessible-resources', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json'
    }
  });
  
  if (!resourcesResp.ok) {
    throw new Error('Failed to fetch Jira accessible resources');
  }
  
  const resources = await resourcesResp.json();
  const targetResource = resources.find((r: Record<string, unknown>) => r.url === hostName) || resources[0];
  
  if (!targetResource?.id) {
    throw new Error('No accessible Jira cloud found');
  }
  
  cachedCloudId = targetResource.id;

  return { 
    accessToken, 
    hostName, 
    cloudId: cachedCloudId!,
    apiBaseUrl: `https://api.atlassian.com/ex/jira/${cachedCloudId}`,
  };
}

async function getUncachableJiraClient() {
  const { accessToken, apiBaseUrl } = await getAccessToken();

  return new Version3Client({
    host: apiBaseUrl,
    authentication: {
      oauth2: { accessToken },
    },
  });
}

async function agileApiRequest(path: string): Promise<Record<string, unknown>> {
  const { accessToken, apiBaseUrl } = await getAccessToken();
  
  const response = await fetch(`${apiBaseUrl}/rest/agile/1.0${path}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/json',
    },
  });
  
  if (!response.ok) {
    throw new Error(`Jira Agile API error: ${response.status}`);
  }
  
  return response.json();
}

export interface JiraColumn {
  id: string;
  name: string;
  statusIds: string[];
}

export interface JiraBoard {
  id: number;
  name: string;
  type: string;
  projectKey: string;
}

export interface JiraIssueStatus {
  issueKey: string;
  summary: string;
  status: string;
  statusCategory: 'todo' | 'indeterminate' | 'done';
  columnName?: string;
  sprint?: string;
  assignee?: string;
  updatedAt: string;
}

export interface JiraSyncResult {
  issueKey: string;
  jiraStatus: string;
  docStatus: string;
  synced: boolean;
  divergence?: string;
}

export class JiraService {
  private client: Version3Client | null = null;

  private async getClient(): Promise<Version3Client> {
    this.client = await getUncachableJiraClient();
    return this.client;
  }

  async getBoards(projectKey?: string): Promise<JiraBoard[]> {
    try {
      const params = projectKey ? `?projectKeyOrId=${projectKey}&type=kanban` : '?type=kanban';
      const response = await agileApiRequest(`/board${params}`);

      return ((response.values || []) as Record<string, unknown>[]).map((board: Record<string, unknown>) => ({
        id: board.id as number,
        name: board.name as string,
        type: board.type as string,
        projectKey: ((board.location as Record<string, unknown> | undefined)?.projectKey as string) || '',
      }));
    } catch (error) {
      throw error;
    }
  }

  async getBoardColumns(boardId: number): Promise<JiraColumn[]> {
    try {
      const response = await agileApiRequest(`/board/${boardId}/configuration`);
      
      const columnConfig = response.columnConfig as Record<string, unknown> | undefined
      return ((columnConfig?.columns || []) as Record<string, unknown>[]).map((col: Record<string, unknown>) => ({
        id: col.name as string,
        name: col.name as string,
        statusIds: ((col.statuses as Array<{ id: string }>) || []).map(s => s.id),
      }));
    } catch (error) {
      throw error;
    }
  }

  async getIssueStatus(issueKey: string): Promise<JiraIssueStatus | null> {
    const client = await this.getClient();
    
    try {
      const issue = await client.issues.getIssue({
        issueIdOrKey: issueKey,
        fields: ['summary', 'status', 'assignee', 'updated', 'sprint'],
      });

      const fields = issue.fields as Record<string, unknown> | undefined;
      const statusField = fields?.status as Record<string, unknown> | undefined;
      const assigneeField = fields?.assignee as Record<string, unknown> | undefined;
      const statusCategoryField = statusField?.statusCategory as Record<string, unknown> | undefined;
      const statusCategory = (statusCategoryField?.key as string) as 'todo' | 'indeterminate' | 'done';
      
      return {
        issueKey: issue.key || issueKey,
        summary: (fields?.summary as string) || '',
        status: (statusField?.name as string) || 'Unknown',
        statusCategory: statusCategory || 'todo',
        assignee: assigneeField?.displayName as string | undefined,
        updatedAt: (fields?.updated as string) || new Date().toISOString(),
      };
    } catch (error) {
      if (error instanceof Error && 'status' in error && (error as { status: number }).status === 404) {
        return null;
      }
      throw error;
    }
  }

  async getMultipleIssuesStatus(issueKeys: string[]): Promise<Map<string, JiraIssueStatus>> {
    const results = new Map<string, JiraIssueStatus>();
    
    const promises = issueKeys.map(async (key) => {
      const status = await this.getIssueStatus(key);
      if (status) {
        results.set(key, status);
      }
    });
    
    await Promise.allSettled(promises);
    return results;
  }

  async searchIssuesByProject(projectKey: string, maxResults: number = 100): Promise<JiraIssueStatus[]> {
    const client = await this.getClient();
    
    try {
      const response = await client.issueSearch.searchForIssuesUsingJql({
        jql: `project = ${projectKey} ORDER BY updated DESC`,
        maxResults,
        fields: ['summary', 'status', 'assignee', 'updated'],
      });

      return (response.issues || []).map((issue: any) => {
        const fields = issue.fields as Record<string, unknown> | undefined
        const status = fields?.status as Record<string, unknown> | undefined
        const assignee = fields?.assignee as Record<string, unknown> | undefined
        const statusCategory = status?.statusCategory as Record<string, unknown> | undefined
        return {
          issueKey: (issue.key as string) || '',
          summary: (fields?.summary as string) || '',
          status: (status?.name as string) || 'Unknown',
          statusCategory: ((statusCategory?.key as string) || 'todo') as 'todo' | 'indeterminate' | 'done',
          assignee: assignee?.displayName as string | undefined,
          updatedAt: (fields?.updated as string) || new Date().toISOString(),
        }
      });
    } catch (error) {
      throw error;
    }
  }

  private normalizeText(text: string): string {
    return text.toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  validateSync(jiraStatus: string, docStatus: string): JiraSyncResult['divergence'] {
    const jiraNorm = this.normalizeText(jiraStatus);
    const docNorm = this.normalizeText(docStatus);
    
    const donePatterns = ['done', 'concluido', 'fechado', 'closed', 'resolved', 'released', 'deployed'];
    const inProgressPatterns = ['progress', 'desenvolvimento', 'doing', 'em andamento', 'in review', 'review', 'qa', 'testing', 'code review', 'selected for development'];
    const blockedPatterns = ['blocked', 'bloqueado', 'impedido', 'on hold', 'paused'];
    const todoPatterns = ['todo', 'backlog', 'aberto', 'open', 'to do', 'new', 'ready'];
    
    const jiraIsDone = donePatterns.some(s => jiraNorm.includes(s));
    const jiraInProgress = inProgressPatterns.some(s => jiraNorm.includes(s));
    const jiraBlocked = blockedPatterns.some(s => jiraNorm.includes(s));
    const jiraTodo = todoPatterns.some(s => jiraNorm.includes(s));
    
    const docIsDone = ['implementado', 'concluido', 'done', 'completed', 'finalizado'].some(s => docNorm.includes(s));
    const docInProgress = ['em desenvolvimento', 'in progress', 'em andamento', 'desenvolvendo'].some(s => docNorm.includes(s));
    const docTodo = ['pendente', 'nao iniciado', 'backlog', 'todo', 'a fazer'].some(s => docNorm.includes(s));
    
    if (jiraIsDone && !docIsDone) {
      return 'Jira: Concluido | Doc: Nao marcado como implementado';
    }
    if (!jiraIsDone && docIsDone) {
      return 'Doc: Implementado | Jira: Nao finalizado';
    }
    if (jiraBlocked) {
      return `Jira: Bloqueado (${jiraStatus}) | Requer atencao`;
    }
    if (jiraInProgress && docTodo) {
      return 'Jira: Em desenvolvimento | Doc: Ainda como pendente';
    }
    if (jiraTodo && docInProgress) {
      return 'Doc: Em desenvolvimento | Jira: Ainda no backlog';
    }
    
    return undefined;
  }

  async syncWithDocumentation(
    issueKeys: string[], 
    docStatuses: Map<string, string>
  ): Promise<JiraSyncResult[]> {
    const jiraStatuses = await this.getMultipleIssuesStatus(issueKeys);
    const results: JiraSyncResult[] = [];

    for (const key of issueKeys) {
      const jiraStatus = jiraStatuses.get(key);
      const docStatus = docStatuses.get(key) || 'Não documentado';
      
      if (!jiraStatus) {
        results.push({
          issueKey: key,
          jiraStatus: 'Não encontrado no Jira',
          docStatus,
          synced: false,
          divergence: 'Card não existe no Jira',
        });
        continue;
      }

      const divergence = this.validateSync(jiraStatus.status, docStatus);
      
      results.push({
        issueKey: key,
        jiraStatus: jiraStatus.status,
        docStatus,
        synced: !divergence,
        divergence,
      });
    }

    return results;
  }

  async getProjects(): Promise<Array<{ id: string; key: string; name: string }>> {
    const { accessToken, apiBaseUrl } = await getAccessToken();
    
    try {
      const response = await fetch(`${apiBaseUrl}/rest/api/3/project/search`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.status}`);
      }
      
      const data = await response.json();
      return (data.values || []).map((project: Record<string, unknown>) => ({
        id: project.id as string,
        key: project.key as string,
        name: project.name as string,
      }));
    } catch (error) {
      throw error;
    }
  }

  async updateIssue(params: {
    issueKey: string;
    summary?: string;
    description?: string;
    labels?: string[];
  }): Promise<{ success: boolean }> {
    const { accessToken, apiBaseUrl } = await getAccessToken();
    
    const fields: Record<string, unknown> = {};

    if (params.summary) {
      fields.summary = params.summary;
    }

    if (params.description) {
      fields.description = {
        type: 'doc',
        version: 1,
        content: [
          {
            type: 'paragraph',
            content: [
              {
                type: 'text',
                text: params.description,
              },
            ],
          },
        ],
      };
    }

    if (params.labels) {
      fields.labels = params.labels;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/rest/api/3/issue/${params.issueKey}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fields }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.errorMessages?.join(', ') || `Failed to update issue: ${response.status}`);
      }
      
      return { success: true };
    } catch (error) {
      throw error;
    }
  }

  async searchIssuesByText(projectKey: string, searchText: string): Promise<JiraIssueStatus[]> {
    const client = await this.getClient();
    
    try {
      const response = await client.issueSearch.searchForIssuesUsingJql({
        jql: `project = ${projectKey} AND (summary ~ "${searchText}" OR description ~ "${searchText}")`,
        maxResults: 100,
        fields: ['summary', 'status', 'description', 'updated'],
      });

      return (response.issues || []).map((issue: any) => {
        const fields = issue.fields as Record<string, unknown> | undefined
        const status = fields?.status as Record<string, unknown> | undefined
        const statusCategory = status?.statusCategory as Record<string, unknown> | undefined
        return {
          issueKey: (issue.key as string) || '',
          summary: (fields?.summary as string) || '',
          status: (status?.name as string) || 'Unknown',
          statusCategory: ((statusCategory?.key as string) || 'todo') as 'todo' | 'indeterminate' | 'done',
          updatedAt: (fields?.updated as string) || new Date().toISOString(),
        }
      });
    } catch (error) {
      throw error;
    }
  }

  async createIssue(params: {
    projectKey: string;
    summary: string;
    description: string;
    issueType: string;
    labels?: string[];
    priority?: string;
    storyPoints?: number;
    epicKey?: string;
    customFields?: Record<string, unknown>;
  }): Promise<{ issueKey: string; issueId: string; success: boolean }> {
    const { accessToken, apiBaseUrl } = await getAccessToken();
    
    const fields: Record<string, unknown> = {
      project: { key: params.projectKey },
      summary: params.summary,
      description: {
        type: 'doc',
        version: 1,
        content: [
          {
            type: 'paragraph',
            content: [
              {
                type: 'text',
                text: params.description,
              },
            ],
          },
        ],
      },
      issuetype: { name: params.issueType },
    };

    if (params.labels && params.labels.length > 0) {
      fields.labels = params.labels;
    }

    if (params.priority) {
      fields.priority = { name: params.priority };
    }

    if (params.epicKey) {
      fields.parent = { key: params.epicKey };
    }

    if (params.customFields) {
      Object.assign(fields, params.customFields);
    }

    try {
      const response = await fetch(`${apiBaseUrl}/rest/api/3/issue`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fields }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.errorMessages?.join(', ') || `Failed to create issue: ${response.status}`);
      }
      
      const data = await response.json();
      return {
        issueKey: data.key || '',
        issueId: data.id || '',
        success: true,
      };
    } catch (error) {
      throw error;
    }
  }

  async createBulkIssues(issues: Array<{
    projectKey: string;
    summary: string;
    description: string;
    issueType: string;
    labels?: string[];
    priority?: string;
    epicKey?: string;
  }>): Promise<{
    created: Array<{ issueKey: string; summary: string }>;
    failed: Array<{ summary: string; error: string }>;
  }> {
    const created: Array<{ issueKey: string; summary: string }> = [];
    const failed: Array<{ summary: string; error: string }> = [];

    for (const issue of issues) {
      try {
        const result = await this.createIssue(issue);
        created.push({ issueKey: result.issueKey, summary: issue.summary });
        await new Promise(resolve => setTimeout(resolve, 200));
      } catch (error) {
        failed.push({ 
          summary: issue.summary, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
      }
    }

    return { created, failed };
  }
}

export const jiraService = new JiraService();
