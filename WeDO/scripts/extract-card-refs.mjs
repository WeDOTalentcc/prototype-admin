import { readFileSync } from 'fs';

function extractCardReferences(filepath) {
  const content = readFileSync(filepath, 'utf-8');
  const lines = content.split('\n');
  const cardPattern = /^### CARD ([A-Z]+-(?:[A-Z]+-)?[0-9]+):\s*(.+)/;
  
  const cards = {};
  let currentCard = null;
  let inRefSection = false;
  let refs = [];
  
  for (const line of lines) {
    const match = line.match(cardPattern);
    if (match) {
      if (currentCard && refs.length > 0) {
        cards[currentCard.id] = { title: currentCard.title, refs: [...refs] };
      }
      currentCard = { id: match[1], title: match[2].trim() };
      inRefSection = false;
      refs = [];
      continue;
    }
    
    if (line.includes('Arquivos de Referencia (Prototipo Replit):')) {
      inRefSection = true;
      continue;
    }
    
    if (inRefSection) {
      const refMatch = line.match(/^\s+-\s+(.+?):\s+(https:\/\/.+)$/);
      if (refMatch) {
        refs.push({ filename: refMatch[1], url: refMatch[2] });
      } else if (line.trim() === '' || line.startsWith('###') || line.startsWith('```')) {
        inRefSection = false;
      }
    }
  }
  
  if (currentCard && refs.length > 0) {
    cards[currentCard.id] = { title: currentCard.title, refs: [...refs] };
  }
  
  return cards;
}

const mvpCards = extractCardReferences('docs/lia-mvp-cards-jira.md');
const wdtCards = extractCardReferences('docs/epic-wdt-talent-funnel.md');
const allCards = { ...mvpCards, ...wdtCards };

console.log(`MVP cards with refs: ${Object.keys(mvpCards).length}`);
console.log(`WDT cards with refs: ${Object.keys(wdtCards).length}`);
console.log(`Total: ${Object.keys(allCards).length}`);
console.log('\nSample cards:');
Object.entries(allCards).slice(0, 3).forEach(([id, data]) => {
  console.log(`\n${id}: ${data.title}`);
  console.log(`  ${data.refs.length} refs:`);
  data.refs.forEach(r => console.log(`    - ${r.filename}: ${r.url.substring(0, 60)}...`));
});

// Write as JSON for the updater script
import { writeFileSync } from 'fs';
writeFileSync('scripts/card-refs-data.json', JSON.stringify(allCards, null, 2));
console.log('\nSaved to scripts/card-refs-data.json');
