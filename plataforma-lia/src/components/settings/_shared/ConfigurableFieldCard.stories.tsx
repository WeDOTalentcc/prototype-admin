import type { Meta, StoryObj } from "@storybook/nextjs-vite"
import { ConfigurableFieldCard } from "./ConfigurableFieldCard"

const meta = {
  title: "Settings/ConfigurableFieldCard",
  component: ConfigurableFieldCard,
  parameters: {
    layout: "padded",
    chromatic: { modes: { light: { theme: "light" }, dark: { theme: "dark" } } },
  },
  args: {
    label: "Diretrizes de diversidade e inclusão",
    hint: "Políticas afirmativas e grupos prioritários que a LIA deve considerar.",
    instruction: "",
    placeholder: "Ex: Priorizar PcD, mulheres em tech e pessoas negras...",
    onInstructionSave: () => {},
    onToggleChange: () => {},
  },
} satisfies Meta<typeof ConfigurableFieldCard>

export default meta
type Story = StoryObj<typeof meta>

// Instruction-only (policy instructions surface)
export const InstructionOnly: Story = {}

export const Filled: Story = {
  args: { instruction: "Priorizar candidaturas de PcD e mulheres em tech; sinalizar se o funil não reflete diversidade." },
}

// Company field with toggle (LIA fields surface)
export const WithToggleOn: Story = {
  args: { label: "Tech Stack", hint: "Usado em: criação de vaga, triagem", showToggle: true, isActive: true, instruction: "React obrigatório; TypeScript desejável." },
}

export const WithToggleOff: Story = {
  args: { label: "Faixas Salariais", hint: "Usado em: oferta, negociação", showToggle: true, isActive: false, instruction: "" },
}

export const Saving: Story = { args: { instruction: "Texto em salvamento", isSaving: true } }
export const ReadOnly: Story = { args: { instruction: "Somente leitura por permissão.", isReadOnly: true } }

// Approximate the 34-field panel density (2-col grid of cards)
export const GridDensity: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-4xl">
      {[
        { label: "Missão", hint: "Usado em: descrição de vaga", on: true },
        { label: "Valores", hint: "Usado em: triagem comportamental", on: true },
        { label: "Tech Stack", hint: "Usado em: criação de vaga", on: true },
        { label: "Benefícios", hint: "Usado em: EVP / oferta", on: false },
        { label: "Modelo de Trabalho", hint: "Usado em: descrição", on: true },
        { label: "Faixas Salariais", hint: "Usado em: oferta", on: false },
      ].map((f) => (
        <ConfigurableFieldCard
          key={f.label}
          label={f.label}
          hint={f.hint}
          showToggle
          isActive={f.on}
          instruction={f.on ? "Instrução exemplo para a LIA sobre este campo." : ""}
          onInstructionSave={() => {}}
          onToggleChange={() => {}}
          placeholder="Instrução opcional..."
        />
      ))}
    </div>
  ),
}
