// src/lib/__tests__/surface-config.test.ts
import { SURFACE_CONFIG } from '../surface-config'

describe('SURFACE_CONFIG — harness sensors', () => {
  it('toda tool com hitl:true tem default_surface:inline (invariant de segurança)', () => {
    for (const [name, config] of Object.entries(SURFACE_CONFIG)) {
      if (config.hitl) {
        expect(
          config.default_surface,
          `Tool "${name}" tem hitl:true mas default_surface:"${config.default_surface}". ` +
          'HITL tools DEVEM ter default_surface:"inline" — aprovações humanas nunca ficam escondidas no painel.'
        ).toBe('inline')
      }
    }
  })

  it('toda entrada tem os campos obrigatórios', () => {
    for (const [name, config] of Object.entries(SURFACE_CONFIG)) {
      expect(config.default_surface, `${name}: falta default_surface`).toBeDefined()
      expect(config.fallback_surface, `${name}: falta fallback_surface`).toBeDefined()
      expect(typeof config.can_show_both, `${name}: can_show_both deve ser boolean`).toBe('boolean')
      expect(typeof config.hitl, `${name}: hitl deve ser boolean`).toBe('boolean')
    }
  })

  it('tools de ação instantânea têm fallback inline-notification', () => {
    expect(SURFACE_CONFIG['navigate_page']?.fallback_surface).toBe('inline-notification')
    expect(SURFACE_CONFIG['open_ui']?.fallback_surface).toBe('inline-notification')
  })
})
