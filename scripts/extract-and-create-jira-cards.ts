import * as fs from 'fs';
import * as path from 'path';

interface CardData {
  id: string;
  titulo: string;
  tipo: string;
  sprint: string;
  storyPoints: string;
  prioridade: string;
  epic: string;
  status: string;
  descricao: string;
}

function extractCardsFromDocument(filePath: string): CardData[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const cards: CardData[] = [];
  
  const cardRegex = /```yaml\s*\nID:\s*(VAG-\d+(?:-[A-Z]\d+)?)\s*\nTitulo:\s*(.+?)\s*\nTipo:\s*(.+?)\s*\nSprint:\s*(.+?)\s*\nStory Points:\s*(.+?)\s*\nPrioridade:\s*(.+?)\s*\nEpic:\s*(EPIC-VAG-\d+)?\s*\nStatus:\s*(.+?)\s*\n\nDescricao:\s*\|\s*\n([\s\S]*?)(?=\n\nHistoria de Usuario|\n\nRequisitos Tecnicos|\n```)/g;
  
  let match;
  while ((match = cardRegex.exec(content)) !== null) {
    cards.push({
      id: match[1],
      titulo: match[2].trim(),
      tipo: match[3].trim(),
      sprint: match[4].trim(),
      storyPoints: match[5].trim(),
      prioridade: match[6].trim(),
      epic: match[7]?.trim() || '',
      status: match[8].trim(),
      descricao: match[9].trim().replace(/\s+/g, ' '),
    });
  }
  
  return cards;
}

function extractCardsSimplified(filePath: string): CardData[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const cards: CardData[] = [];
  
  const lines = content.split('\n');
  let inCard = false;
  let currentCard: Partial<CardData> = {};
  let inDescricao = false;
  let descricaoLines: string[] = [];
  
  for (const line of lines) {
    if (line.startsWith('ID: VAG-')) {
      if (currentCard.id) {
        currentCard.descricao = descricaoLines.join(' ').trim();
        cards.push(currentCard as CardData);
      }
      inCard = true;
      currentCard = { id: line.replace('ID: ', '').trim() };
      descricaoLines = [];
      inDescricao = false;
    } else if (inCard) {
      if (line.startsWith('Titulo:')) {
        currentCard.titulo = line.replace('Titulo:', '').trim();
      } else if (line.startsWith('Tipo:')) {
        currentCard.tipo = line.replace('Tipo:', '').trim();
      } else if (line.startsWith('Sprint:')) {
        currentCard.sprint = line.replace('Sprint:', '').trim();
      } else if (line.startsWith('Story Points:')) {
        currentCard.storyPoints = line.replace('Story Points:', '').trim();
      } else if (line.startsWith('Prioridade:')) {
        currentCard.prioridade = line.replace('Prioridade:', '').trim();
      } else if (line.startsWith('Epic:')) {
        currentCard.epic = line.replace('Epic:', '').trim();
      } else if (line.startsWith('Status:')) {
        currentCard.status = line.replace('Status:', '').trim();
      } else if (line.startsWith('Descricao:')) {
        inDescricao = true;
      } else if (inDescricao && !line.startsWith('Historia de Usuario') && !line.startsWith('```')) {
        const cleanLine = line.replace(/^\s+/, '');
        if (cleanLine) descricaoLines.push(cleanLine);
      } else if (line.startsWith('Historia de Usuario') || line === '```') {
        inDescricao = false;
      }
    }
  }
  
  if (currentCard.id) {
    currentCard.descricao = descricaoLines.join(' ').trim();
    cards.push(currentCard as CardData);
  }
  
  return cards;
}

function convertToJiraIssues(cards: CardData[], projectKey: string) {
  return cards.map(card => {
    const labels = ['VAGAS'];
    
    if (card.tipo.includes('Frontend')) labels.push('Frontend');
    if (card.tipo.includes('Backend')) labels.push('Backend');
    if (card.tipo.includes('IA') || card.tipo.includes('AI')) labels.push('Backend-IA');
    if (card.tipo.includes('Integracao')) labels.push('Integracao');
    
    const priorityMap: Record<string, string> = {
      'Critica': 'Highest',
      'Alta': 'High',
      'Media': 'Medium',
      'Baixa': 'Low',
    };
    
    return {
      projectKey,
      summary: `[${card.id}] ${card.titulo}`,
      description: `${card.descricao}\n\nTipo: ${card.tipo}\nSprint: ${card.sprint}\nStory Points: ${card.storyPoints}\nEpic: ${card.epic}\nStatus Doc: ${card.status}`,
      issueType: 'Task',
      labels,
      priority: priorityMap[card.prioridade] || 'Medium',
    };
  });
}

async function main() {
  const docPath = path.join(__dirname, '../docs/gestao-vagas-visao-geral-cards-jira.md');
  
  console.log('Extracting cards from document...');
  const cards = extractCardsSimplified(docPath);
  
  console.log(`Found ${cards.length} cards`);
  
  const jiraIssues = convertToJiraIssues(cards, 'WT');
  
  console.log('\nFirst 5 issues to create:');
  jiraIssues.slice(0, 5).forEach(issue => {
    console.log(`- ${issue.summary}`);
  });
  
  const outputPath = path.join(__dirname, 'jira-issues.json');
  fs.writeFileSync(outputPath, JSON.stringify(jiraIssues, null, 2));
  console.log(`\nSaved ${jiraIssues.length} issues to ${outputPath}`);
}

main().catch(console.error);
