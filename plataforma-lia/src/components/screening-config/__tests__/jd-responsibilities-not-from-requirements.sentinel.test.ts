/**
 * T-1166 — Sentinel offline (sem render).
 *
 * Garante que NENHUM caller no painel de configuração de screening mapeia
 * `job.requirements` para a prop `responsibilities` do JDEvaluationPanel
 * ou para o campo `responsibilities` do contexto de geração de WSI.
 *
 * O bug original (vaga 200) era exatamente esse: `responsibilities={(job.requirements) || []}`
 * fazia a aba "RESPONSABILIDADES" do editor de JD listar Python/TypeScript/
 * PostgreSQL — que eram os technical_skills, não as duties.
 *
 * Esse teste lê os arquivos como texto e dispara regex no source: é AST-free,
 * extremamente rápido, e quebra a build se a contaminação reaparecer.
 */

import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const ROOT = join(__dirname, '..')

const TARGETS = [
  'SCMSectionContent.tsx',
  join('hooks', 'useScreeningConfigManagerCore.tsx'),
]

// Padrões que indicariam regressão:
// 1. `responsibilities={... job.requirements ...}` — JSX prop
// 2. `responsibilities: ...job.requirements...` — object literal (contexto WSI)
// 3. `const responsibilities = (... job.requirements ...).map(...)` — alias direto
const REGRESSION_PATTERNS: Array<{ pattern: RegExp; description: string }> = [
  {
    pattern: /responsibilities\s*=\s*\{\s*\(?\s*job\.requirements/,
    description: 'JSX prop `responsibilities={job.requirements ...}` — contamina o painel RESPONSABILIDADES',
  },
  {
    pattern: /responsibilities\s*:\s*[^,;}\n]*job\.requirements/,
    description: 'campo `responsibilities:` em objeto recebendo `job.requirements` — feed do WSI generator',
  },
  {
    pattern: /const\s+responsibilities\s*=\s*\(?\s*job\.requirements/,
    description: 'alias direto `const responsibilities = job.requirements` — re-introduz a contaminação',
  },
]

describe('T-1166 — JD editor: responsibilities NÃO pode vir de job.requirements', () => {
  it.each(TARGETS)('arquivo %s não contém o anti-padrão', (relPath) => {
    const fullPath = join(ROOT, relPath)
    if (!existsSync(fullPath)) {
      throw new Error(
        `T-1166: arquivo alvo da sentinel não existe: ${fullPath}. ` +
          `Se foi renomeado, atualize TARGETS em ${__filename}.`,
      )
    }
    const src = readFileSync(fullPath, 'utf-8')

    for (const { pattern, description } of REGRESSION_PATTERNS) {
      const match = src.match(pattern)
      expect(
        match,
        `T-1166 REGRESSÃO em ${relPath}: ${description}\n` +
          `Match: ${match?.[0] ?? '(nenhum)'}\n` +
          `Use \`job.responsibilities\` (coluna canônica, migration 132). ` +
          `Vagas legadas têm o campo null → fallback explícito \`[]\` é o correto. ` +
          `NUNCA caia de volta para \`job.requirements\`.`,
      ).toBeNull()
    }
  })

  it('SCMSectionContent ainda lê o campo canônico `job.responsibilities`', () => {
    const src = readFileSync(join(ROOT, 'SCMSectionContent.tsx'), 'utf-8')
    expect(
      /responsibilities\s*=\s*\{\s*\(?\s*job\.responsibilities/.test(src),
      'T-1166: SCMSectionContent deve passar `responsibilities={job.responsibilities ...}` ' +
        'para o JDEvaluationPanel. Sem isso o painel renderiza vazio (regressão silenciosa).',
    ).toBe(true)
  })
})
