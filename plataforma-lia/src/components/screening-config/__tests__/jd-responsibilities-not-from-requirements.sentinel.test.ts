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

  it('SCMSectionContent ainda lê o campo canônico `job.responsibilities` (com ou sem mescla via enrichedJd)', () => {
    const src = readFileSync(join(ROOT, 'SCMSectionContent.tsx'), 'utf-8')
    // T-1166 + T-1167 — aceita tanto `responsibilities={job.responsibilities ...}` (forma antiga)
    // quanto a mescla `enrichedJd?.responsibilities ?? job.responsibilities` (forma nova T-1167,
    // que fixa D2/D9=0 quando job.responsibilities é null mas enrichedJd já tem os itens).
    const hasJobRespRef = /job\.responsibilities/.test(src)
    expect(
      hasJobRespRef,
      'T-1166: SCMSectionContent deve referenciar `job.responsibilities` ao montar a prop do ' +
        'JDEvaluationPanel (direto ou via fallback após enrichedJd). Sem isso o painel renderiza ' +
        'vazio (regressão silenciosa).',
    ).toBe(true)
  })

  it('T-1167: SCMSectionContent prefere `enrichedJd.responsibilities` antes do fallback persistido', () => {
    const src = readFileSync(join(ROOT, 'SCMSectionContent.tsx'), 'utf-8')
    // Padrão obrigatório: a mescla `enrichedJd?.responsibilities ?? job.responsibilities` (com `??`).
    // Garante que vagas legacy (job.responsibilities=null) com JD enriquecido salvo continuam
    // pontuando D2/D9 corretamente no painel de avaliação de qualidade.
    // Regex tolerante a TS type annotations (que contêm `}`) entre `enrichedJd` e `.responsibilities`.
    const hasMescla = /enrichedJd[\s\S]{0,200}\.responsibilities[\s\S]{0,200}\?\?[\s\S]{0,200}job\.responsibilities/.test(src)
    expect(
      hasMescla,
      'T-1167 REGRESSÃO: SCMSectionContent deve preferir `enrichedJd?.responsibilities` antes de ' +
        'cair em `job.responsibilities`. Sem essa mescla, vagas com responsabilidades só em ' +
        '`enrichedJd` (criação manual + save inline) pontuam D2=0/15 e D9=0/5 no painel.',
    ).toBe(true)
  })

  it('T-1168: SCMSectionContent prefere `enrichedJd.technical_skills` antes do fallback `job.technicalRequirements`', () => {
    const src = readFileSync(join(ROOT, 'SCMSectionContent.tsx'), 'utf-8')
    // Sem essa mescla, o painel "Perguntas de Triagem" mostra a contagem do
    // form original ("Apenas 5 competências técnicas — recomendado 9") mesmo
    // quando a LIA enriqueceu o JD para 9 skills. Mesmo padrão T-1167.
    const hasTechMerge = /enrichedJd[\s\S]{0,200}\.technical_skills[\s\S]{0,200}\?\?[\s\S]{0,200}job\.technicalRequirements/.test(src)
    expect(
      hasTechMerge,
      'T-1168 REGRESSÃO: SCMSectionContent deve preferir `enrichedJd?.technical_skills` antes de ' +
        '`job.technicalRequirements`. Sem essa mescla, a contagem mostrada e o feed do gerador WSI ' +
        'usam a fonte stale do form original.',
    ).toBe(true)
  })

  it('T-1168: SCMSectionContent prefere `enrichedJd.behavioral_competencies` antes do fallback `job.behavioralCompetencies`', () => {
    const src = readFileSync(join(ROOT, 'SCMSectionContent.tsx'), 'utf-8')
    const hasBehavMerge = /enrichedJd[\s\S]{0,300}\.behavioral_competencies[\s\S]{0,300}\?\?[\s\S]{0,300}job\.behavioralCompetencies/.test(src)
    expect(
      hasBehavMerge,
      'T-1168 REGRESSÃO: SCMSectionContent deve preferir `enrichedJd?.behavioral_competencies` antes ' +
        'de `job.behavioralCompetencies`. Sem isso, painel mostra "4 (recomendado 5)" mesmo quando ' +
        'o JD enriquecido tem 5+.',
    ).toBe(true)
  })

  it('T-1168: useScreeningConfigManagerCore prefere `enrichedJd.technical_skills`/`.behavioral_competencies`', () => {
    const src = readFileSync(join(ROOT, 'hooks', 'useScreeningConfigManagerCore.tsx'), 'utf-8')
    const hasTech = /enrichedJd[\s\S]{0,200}\.technical_skills[\s\S]{0,300}\?\?[\s\S]{0,300}job\.technicalRequirements/.test(src)
    const hasBehav = /enrichedJd[\s\S]{0,200}\.behavioral_competencies[\s\S]{0,300}\?\?[\s\S]{0,300}job\.behavioralCompetencies/.test(src)
    expect(
      hasTech && hasBehav,
      'T-1168 REGRESSÃO: o hook `handleGenerateWSI` deve montar `techSkills`/`behavComp` priorizando ' +
        '`enrichedJd.technical_skills`/`enrichedJd.behavioral_competencies` antes de cair em ' +
        '`job.technicalRequirements`/`job.behavioralCompetencies`. Sem isso o backend recebe a lista ' +
        'stale do form original e o roteiro WSI sai magro.',
    ).toBe(true)
  })

  it('T-1168: hook envia payload alinhado com WSIScreeningPipelineRequest (format/job_description + seniority lowercase)', () => {
    const src = readFileSync(join(ROOT, 'hooks', 'useScreeningConfigManagerCore.tsx'), 'utf-8')
    // Schema canônico (lia-agent-system/app/schemas/screening.py::WSIScreeningPipelineRequest):
    //   • `format: Literal["compact","full"]` (NÃO `mode`)
    //   • `job_description: str | None` (NÃO `description`)
    //   • `seniority: Literal["junior","pleno","senior","lead","executive"]` (lowercase obrigatório)
    // Antes mandávamos `mode`, `description` (ignorados) e `seniority="Pleno"` capitalizado —
    // este último era o ÚNICO erro do 422 "Request validation failed: 1 errors".
    expect(/format:\s*mode/.test(src), 'T-1168: payload deve usar `format: mode` (não `mode`).').toBe(true)
    expect(/job_description:/.test(src), 'T-1168: payload deve usar `job_description` (não `description`).').toBe(true)
    expect(
      /\.toLowerCase\(\)[\s\S]{0,400}(junior|pleno|senior|lead|executive)/.test(src),
      'T-1168: hook deve normalizar seniority para LOWERCASE antes de enviar (schema usa Literal lowercase).',
    ).toBe(true)
  })
})
