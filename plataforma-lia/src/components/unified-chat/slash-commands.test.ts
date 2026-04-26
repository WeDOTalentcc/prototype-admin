import { describe, expect, it } from "vitest"
import {
  AJUDA_REGEX,
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
        "/feedback",
        "/agendar",
        "/ajuda",
      ]),
    )
  })

  it("exposes /job and /talent as official aliases (task #292 contract)", () => {
    expect(findSlashCommandByToken("/job")?.id).toBe("criar-vaga")
    expect(findSlashCommandByToken("/JOB")?.id).toBe("criar-vaga")
    expect(findSlashCommandByToken("/talent")?.id).toBe("buscar")
  })

  it("matches by verb for /verb @target form", () => {
    expect(findSlashCommandByVerb("buscar")?.id).toBe("buscar")
    expect(findSlashCommandByVerb("talent")?.id).toBe("buscar")
    expect(findSlashCommandByVerb("job")?.id).toBe("criar-vaga")
    expect(findSlashCommandByVerb("agendar")?.id).toBe("agendar")
    expect(findSlashCommandByVerb("desconhecido")).toBeUndefined()
  })

  it("normalizes whitespace when matching tokens", () => {
    expect(findSlashCommandByToken("  /CRIAR   VAGA  ")?.id).toBe("criar-vaga")
    expect(findSlashCommandByToken("/nova vaga")?.id).toBe("criar-vaga")
  })

  it("dropdown entries are flagged via showInDropdown", () => {
    const inDropdown = SLASH_COMMANDS.filter((c) => c.showInDropdown).map((c) => c.id)
    expect(inDropdown).toEqual([
      "criar-vaga",
      "buscar",
      "pipeline",
      "relatorio",
      "ajuda",
      "definir",
      "nova-conversa",
    ])
  })

  it("bare-message builders return the legacy backend payloads", () => {
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
    // The two ids must collide on the same `now` slot but stay distinct
    // by suffix — guards against accidental React key reuse.
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
})
