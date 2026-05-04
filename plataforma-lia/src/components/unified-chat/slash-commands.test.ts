import { describe, expect, it } from "vitest"
import {
  AJUDA_REGEX,
  EXECUTE_ONLY_COMMAND_IDS,
  SLASH_COMMANDS,
  buildAjudaChatMessages,
  buildAjudaHelpMarkdown,
  findSlashCommandByToken,
  findSlashCommandByVerb,
} from "./slash-commands"

describe("SLASH_COMMANDS registry", () => {
  it("has the canonical Portuguese tokens", () => {
    const primaries = SLASH_COMMANDS.map((c) => c.primary)
    expect(primaries).toEqual(
      expect.arrayContaining([
        "/criar vaga",
        "/buscar",
        "/pipeline",
        "/relatorio",
        "/relatorio semanal",
        "/relatorio funil",
        "/relatorio fonte",
        "/relatorio tempo",
        "/feedback",
        "/agendar",
        "/ajuda",
        "/definir",
        "/nova-conversa",
      ]),
    )
  })

  it("exposes /job and /talent as official aliases (task #292 contract)", () => {
    expect(findSlashCommandByToken("/job")?.id).toBe("criar-vaga")
    expect(findSlashCommandByToken("/JOB")?.id).toBe("criar-vaga")
    expect(findSlashCommandByToken("/talent")?.id).toBe("buscar")
  })

  it("matches by verb for /verb @target form, returning the entry that owns buildMentionMessage", () => {
    expect(findSlashCommandByVerb("buscar")?.id).toBe("buscar")
    expect(findSlashCommandByVerb("talent")?.id).toBe("buscar")
    expect(findSlashCommandByVerb("job")?.id).toBe("criar-vaga")
    expect(findSlashCommandByVerb("agendar")?.id).toBe("agendar")
    // Generic /relatorio is listed before its variants on purpose so
    // `/relatorio @vaga` resolves to the entry with buildMentionMessage.
    expect(findSlashCommandByVerb("relatorio")?.id).toBe("relatorio")
    expect(findSlashCommandByVerb("desconhecido")).toBeUndefined()
  })

  it("normalizes whitespace when matching tokens, including multi-word primaries", () => {
    expect(findSlashCommandByToken("  /CRIAR   VAGA  ")?.id).toBe("criar-vaga")
    expect(findSlashCommandByToken("/nova vaga")?.id).toBe("criar-vaga")
    expect(findSlashCommandByToken("  /RELATORIO   SEMANAL ")?.id).toBe(
      "relatorio-semanal",
    )
    expect(findSlashCommandByToken("/relatorio pipeline")?.id).toBe(
      "relatorio-funil",
    )
  })

  it("dropdown surface is the canonical user-discoverable set", () => {
    const inDropdown = SLASH_COMMANDS.filter((c) => c.showInDropdown).map((c) => c.id)
    expect(inDropdown).toEqual([
      "criar-vaga",
      "buscar",
      "pipeline",
      "relatorio-semanal",
      "relatorio-funil",
      "relatorio-fonte",
      "relatorio-tempo",
      "feedback",
      "agendar",
      "ajuda",
      "definir",
      "nova-conversa",
    ])
  })

  it("hides the generic /relatorio from the dropdown but keeps it in the catalog (backcompat)", () => {
    const generic = SLASH_COMMANDS.find((c) => c.id === "relatorio")
    expect(generic).toBeDefined()
    expect(generic?.showInDropdown).toBe(false)
    // Bare submit still works for chat history that contains plain "/relatorio".
    expect(generic?.buildBareMessage?.()).toBe(
      "Gerar relatorio semanal de recrutamento",
    )
    // Cross-mention form `/relatorio @vaga` keeps working.
    expect(generic?.buildMentionMessage?.("VagaX")).toBe("Relatorio da vaga: VagaX")
  })

  it("bare-message builders return canonical backend payloads for every report variant", () => {
    expect(findSlashCommandByToken("/relatorio semanal")?.buildBareMessage?.()).toBe(
      "Gerar relatorio semanal de recrutamento",
    )
    expect(findSlashCommandByToken("/relatorio funil")?.buildBareMessage?.()).toBe(
      "Gerar relatorio do funil de candidatos com conversao por etapa",
    )
    expect(findSlashCommandByToken("/relatorio fonte")?.buildBareMessage?.()).toBe(
      "Gerar relatorio de performance por canal de origem dos candidatos",
    )
    expect(findSlashCommandByToken("/relatorio tempo")?.buildBareMessage?.()).toBe(
      "Gerar relatorio de time-to-hire e SLA por etapa",
    )
  })

  it("legacy bare-message builders are unchanged", () => {
    expect(findSlashCommandByToken("/criar vaga")?.buildBareMessage?.()).toBe("Criar nova vaga")
    expect(findSlashCommandByToken("/job")?.buildBareMessage?.()).toBe("Criar nova vaga")
    expect(findSlashCommandByToken("/pipeline")?.buildBareMessage?.()).toBe(
      "Mostrar funil de vagas abertas",
    )
    expect(findSlashCommandByToken("/relatorio")?.buildBareMessage?.()).toBe(
      "Gerar relatorio semanal de recrutamento",
    )
    expect(findSlashCommandByToken("/ajuda")?.buildBareMessage?.()).toBe("/ajuda")
  })

  it("/feedback and /agendar are visible with @-prefill so users discover the mention pattern", () => {
    const feedback = SLASH_COMMANDS.find((c) => c.id === "feedback")
    const agendar = SLASH_COMMANDS.find((c) => c.id === "agendar")

    expect(feedback?.showInDropdown).toBe(true)
    expect(agendar?.showInDropdown).toBe(true)
    expect(feedback?.dropdownPrefill).toBe("/feedback @")
    expect(agendar?.dropdownPrefill).toBe("/agendar @")
    // Subtitles must mention "@candidato" so the user knows what comes next.
    expect(feedback?.subtitle).toMatch(/@candidato/i)
    expect(agendar?.subtitle).toMatch(/@candidato/i)
  })

  it("AJUDA_REGEX matches `/ajuda` case-insensitively and rejects args", () => {
    expect(AJUDA_REGEX.test("/ajuda")).toBe(true)
    expect(AJUDA_REGEX.test("/AJUDA")).toBe(true)
    expect(AJUDA_REGEX.test("/ajuda  ")).toBe(true)
    expect(AJUDA_REGEX.test("/ajuda termo")).toBe(false)
    expect(AJUDA_REGEX.test("ajuda")).toBe(false)
  })

  it("buildAjudaHelpMarkdown lists every dropdown command", () => {
    const md = buildAjudaHelpMarkdown()
    expect(md).toMatch(/Comandos disponíveis/)
    expect(md).toMatch(/_Dica: digite .*menu rápido/)
    SLASH_COMMANDS
      .filter((c) => c.showInDropdown)
      .forEach((c) => {
        expect(md).toContain(c.primary)
        expect(md).toContain(c.subtitle)
      })
  })

  it("buildAjudaChatMessages produces the user-echo + lia-help pair (Task #836)", () => {
    const fixed = new Date("2026-04-26T13:00:00.000Z")
    const { userMsg, helpMsg } = buildAjudaChatMessages(
      "/ajuda",
      buildAjudaHelpMarkdown(),
      fixed,
    )
    expect(userMsg.sender).toBe("user")
    expect(userMsg.content).toBe("/ajuda")
    expect(userMsg.timestamp).toBe("2026-04-26T13:00:00.000Z")
    expect(userMsg.id).toMatch(/^user-\d+$/)
    expect(helpMsg.sender).toBe("lia")
    expect(helpMsg.content).toMatch(/Comandos disponíveis/)
    expect(helpMsg.id).toMatch(/^lia-\d+-ajuda$/)
    expect(userMsg.id).not.toBe(helpMsg.id)
  })

  it("mention-message builders preserve the legacy backend payloads", () => {
    expect(findSlashCommandByVerb("buscar")?.buildMentionMessage?.("Ana")).toBe(
      "Buscar candidato: Ana",
    )
    expect(findSlashCommandByVerb("talent")?.buildMentionMessage?.("Ana")).toBe(
      "Buscar candidato: Ana",
    )
    expect(findSlashCommandByVerb("feedback")?.buildMentionMessage?.("Ana")).toBe(
      "Enviar feedback para: Ana",
    )
    expect(findSlashCommandByVerb("agendar")?.buildMentionMessage?.("Ana")).toBe(
      "Agendar entrevista com: Ana",
    )
  })

  // ---------------------------------------------------------------------------
  // Harness sensors — guard rails to prevent the class of regression where
  // a command shows in the dropdown but does nothing useful when picked.
  // ---------------------------------------------------------------------------
  describe("harness invariants (visible commands must lead somewhere)", () => {
    const visible = SLASH_COMMANDS.filter((c) => c.showInDropdown)

    it("every visible command has a stable id, primary token, label and subtitle", () => {
      for (const cmd of visible) {
        expect(cmd.id, `id missing for ${cmd.primary}`).toBeTruthy()
        expect(cmd.primary, `primary missing for ${cmd.id}`).toMatch(/^\//)
        expect(cmd.label, `label missing for ${cmd.id}`).toBeTruthy()
        expect(cmd.subtitle, `subtitle missing for ${cmd.id}`).toBeTruthy()
      }
    })

    it("every visible command resolves to action: backend message OR UI execute OR prefill expects user input", () => {
      for (const cmd of visible) {
        const isExecuteOnly = EXECUTE_ONLY_COMMAND_IDS.includes(cmd.id)
        const hasBareMessage = typeof cmd.buildBareMessage === "function"
        const expectsUserInput =
          typeof cmd.dropdownPrefill === "string" &&
          // Prefill ending with whitespace, "@" or another invitation char
          // means the user is expected to keep typing before hitting Enter.
          /[\s@]$/.test(cmd.dropdownPrefill)

        const ok = isExecuteOnly || hasBareMessage || expectsUserInput
        expect(
          ok,
          `${cmd.primary}: visible commands must EITHER execute via UI ` +
            `(EXECUTE_ONLY_COMMAND_IDS), OR define buildBareMessage for ` +
            `bare submission, OR have a dropdownPrefill that ends with ` +
            `space/@ to invite further input.`,
        ).toBe(true)
      }
    })

    it("ids are unique across the catalog (visible + hidden)", () => {
      const ids = SLASH_COMMANDS.map((c) => c.id)
      const unique = new Set(ids)
      expect(unique.size).toBe(ids.length)
    })

    it("primary tokens are unique across the catalog", () => {
      const primaries = SLASH_COMMANDS.map((c) => c.primary.toLowerCase())
      const unique = new Set(primaries)
      expect(unique.size).toBe(primaries.length)
    })
  })
})
