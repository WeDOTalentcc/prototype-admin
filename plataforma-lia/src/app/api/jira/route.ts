export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server';
import { validateBody } from '@/lib/api/validate'
import { jiraService, JiraSyncResult } from '@/lib/api/jira-service';
import { z } from 'zod'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action');
  
  try {
    switch (action) {
      case 'boards': {
        const projectKey = searchParams.get('project') || undefined;
        const boards = await jiraService.getBoards(projectKey);
        return NextResponse.json({ success: true, data: boards });
      }
      
      case 'columns': {
        const boardId = searchParams.get('boardId');
        if (!boardId) {
          return NextResponse.json({ success: false, error: 'boardId required' }, { status: 400 });
        }
        const columns = await jiraService.getBoardColumns(parseInt(boardId));
        return NextResponse.json({ success: true, data: columns });
      }
      
      case 'issue': {
        const issueKey = searchParams.get('key');
        if (!issueKey) {
          return NextResponse.json({ success: false, error: 'key required' }, { status: 400 });
        }
        const issue = await jiraService.getIssueStatus(issueKey);
        if (!issue) {
          return NextResponse.json({ success: false, error: 'Issue not found' }, { status: 404 });
        }
        return NextResponse.json({ success: true, data: issue });
      }
      
      case 'issues': {
        const keys = searchParams.get('keys');
        if (!keys) {
          return NextResponse.json({ success: false, error: 'keys required (comma-separated)' }, { status: 400 });
        }
        const issueKeys = keys.split(',').map(k => k.trim());
        const issues = await jiraService.getMultipleIssuesStatus(issueKeys);
        
        const result: Record<string, unknown> = {};
        const notFound: string[] = [];
        
        for (const key of issueKeys) {
          const issue = issues.get(key);
          if (issue) {
            result[key] = issue;
          } else {
            result[key] = { issueKey: key, status: 'NOT_FOUND', error: 'Issue not found in Jira' };
            notFound.push(key);
          }
        }
        
        return NextResponse.json({ 
          success: true, 
          data: result,
          notFound: notFound.length > 0 ? notFound : undefined,
        });
      }
      
      case 'project': {
        const projectKey = searchParams.get('project');
        if (!projectKey) {
          return NextResponse.json({ success: false, error: 'project required' }, { status: 400 });
        }
        const maxResults = parseInt(searchParams.get('limit') || '100');
        const issues = await jiraService.searchIssuesByProject(projectKey, maxResults);
        return NextResponse.json({ success: true, data: issues });
      }
      
      case 'projects': {
        const projects = await jiraService.getProjects();
        return NextResponse.json({ success: true, data: projects });
      }
      
      default:
        return NextResponse.json({ 
          success: false, 
          error: 'Invalid action. Use: boards, columns, issue, issues, project, projects',
          examples: {
            boards: '/api/jira?action=boards&project=VAG',
            columns: '/api/jira?action=columns&boardId=123',
            issue: '/api/jira?action=issue&key=VAG-077',
            issues: '/api/jira?action=issues&keys=VAG-077,VAG-078,VAG-079',
            project: '/api/jira?action=project&project=VAG&limit=50',
            projects: '/api/jira?action=projects',
          }
        }, { status: 400 });
    }
  } catch (error: unknown) {
    return NextResponse.json({ 
      success: false, 
      error: (error as Error).message || 'Jira API error' 
    }, { status: 500 });
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(request: NextRequest) {
  try {
    const bodyResult = await validateBody(request, _bodySchema)

    if (!bodyResult.success) return bodyResult.response

    const body = bodyResult.data;
    const { action, issueKeys, docStatuses } = body;
    
    if (action === 'sync') {
      if (!issueKeys || !Array.isArray(issueKeys)) {
        return NextResponse.json({ success: false, error: 'issueKeys array required' }, { status: 400 });
      }
      
      const docStatusMap = new Map<string, string>(
        Object.entries(docStatuses || {})
      );
      
      const results = await jiraService.syncWithDocumentation(issueKeys, docStatusMap);
      
      const summary = {
        total: results.length,
        synced: results.filter(r => r.synced).length,
        divergent: results.filter(r => !r.synced).length,
        notFound: results.filter(r => r.jiraStatus === 'Não encontrado no Jira').length,
      };
      
      return NextResponse.json({ 
        success: true, 
        data: results,
        summary,
      });
    }
    
    if (action === 'create') {
      const projectKey = body.projectKey as string;
      const summary = body.summary as string;
      const description = body.description as string | undefined;
      const issueType = body.issueType as string;
      const labels = body.labels as string[] | undefined;
      const priority = body.priority as string | undefined;
      const epicKey = body.epicKey as string | undefined;
      
      if (!projectKey || !summary || !issueType) {
        return NextResponse.json({ 
          success: false, 
          error: 'projectKey, summary, and issueType are required' 
        }, { status: 400 });
      }
      
      const result = await jiraService.createIssue({
        projectKey,
        summary,
        description: description || '',
        issueType,
        labels,
        priority,
        epicKey,
      });
      
      return NextResponse.json({ success: true, data: result });
    }
    
    if (action === 'create-bulk') {
      const { issues } = body;
      
      if (!issues || !Array.isArray(issues) || issues.length === 0) {
        return NextResponse.json({ 
          success: false, 
          error: 'issues array required' 
        }, { status: 400 });
      }
      
      const result = await jiraService.createBulkIssues(issues);
      
      return NextResponse.json({ 
        success: true, 
        data: result,
        summary: {
          total: issues.length,
          created: result.created.length,
          failed: result.failed.length,
        }
      });
    }
    
    return NextResponse.json({ 
      success: false, 
      error: 'Invalid action. Use: sync, create, create-bulk',
      examples: {
        sync: {
          action: 'sync',
          issueKeys: ['VAG-077', 'VAG-078'],
          docStatuses: { 'VAG-077': 'Implementado', 'VAG-078': 'Pendente' }
        },
        create: {
          action: 'create',
          projectKey: 'WT',
          summary: '[FRONT] Header Principal',
          description: 'Implementar header da pagina',
          issueType: 'Task',
          labels: ['VAGAS', 'Frontend']
        },
        createBulk: {
          action: 'create-bulk',
          issues: [
            { projectKey: 'WT', summary: 'Card 1', description: 'Desc', issueType: 'Task', labels: ['VAGAS'] },
            { projectKey: 'WT', summary: 'Card 2', description: 'Desc', issueType: 'Task', labels: ['VAGAS'] }
          ]
        }
      }
    }, { status: 400 });
    
  } catch (error: unknown) {
    return NextResponse.json({ 
      success: false, 
      error: (error as Error).message || 'Jira API error' 
    }, { status: 500 });
  }
}
