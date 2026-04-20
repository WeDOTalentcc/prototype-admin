import { describe, expect, it } from "vitest"
import {
  SLASH_COMMANDS,
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
