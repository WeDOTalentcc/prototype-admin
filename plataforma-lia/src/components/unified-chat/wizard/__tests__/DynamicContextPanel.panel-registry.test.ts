/**
 * Sensor de harness P0.2 — garante que SPLIT_STAGES tem entrada no PANEL_REGISTRY.
 * Falha em CI se stage novo for adicionado a SPLIT_STAGES sem panel correspondente.
 */
import { SPLIT_STAGES } from '../DynamicContextPanel'
import { PANEL_REGISTRY } from '../DynamicContextPanel'

describe('PANEL_REGISTRY cobre todos os SPLIT_STAGES (harness P0.2)', () => {
  it('todo stage em SPLIT_STAGES tem entrada em PANEL_REGISTRY', () => {
    for (const stage of SPLIT_STAGES) {
      expect(
        PANEL_REGISTRY[stage],
        `Stage "${stage}" está em SPLIT_STAGES mas não tem entrada em PANEL_REGISTRY. ` +
        `Adicione: ${stage}: lazy(() => import("./panels/${toPascalCase(stage)}Panel"))` +
        ` no objeto PANEL_REGISTRY em DynamicContextPanel.tsx.`
      ).toBeDefined()
    }
  })
})

function toPascalCase(str: string): string {
  return str.replace(/(^|_)(\w)/g, (_, __, c) => c.toUpperCase())
}
