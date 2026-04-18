import type { Meta, StoryObj } from "@storybook/nextjs-vite"

import { Chip, type ChipDensity, type ChipVariant } from "./chip"

const VARIANTS: ChipVariant[] = ["neutral", "success", "warning", "danger", "info"]
const DENSITIES: ChipDensity[] = ["comfortable", "compact"]
const MUTED_STATES: boolean[] = [false, true]

const meta = {
  title: "UI/Chip",
  component: Chip,
  parameters: {
    layout: "centered",
    chromatic: {
      // Capture both light and dark color schemes for every story so the
      // visual regression suite covers theme parity automatically.
      modes: {
        light: { theme: "light" },
        dark: { theme: "dark" },
      },
    },
  },
  tags: ["autodocs"],
  argTypes: {
    variant: { control: "select", options: VARIANTS },
    density: { control: "radio", options: DENSITIES },
    muted: { control: "boolean" },
  },
  args: {
    children: "Chip",
    variant: "neutral",
    density: "comfortable",
    muted: false,
  },
} satisfies Meta<typeof Chip>

export default meta
type Story = StoryObj<typeof meta>

export const Neutral: Story = { args: { variant: "neutral", children: "Neutral" } }
export const Success: Story = { args: { variant: "success", children: "Success" } }
export const Warning: Story = { args: { variant: "warning", children: "Warning" } }
export const Danger: Story = { args: { variant: "danger", children: "Danger" } }
export const Info: Story = { args: { variant: "info", children: "Info" } }

export const Compact: Story = {
  args: { density: "compact", children: "Compact" },
}

export const Muted: Story = {
  args: { muted: true, children: "Muted" },
}

/**
 * Exhaustive matrix: every variant × density × muted combination rendered in
 * a single canvas. Chromatic snapshots this story in both `light` and `dark`
 * modes (configured at the meta level) for full visual regression coverage.
 */
export const AllCombinations: Story = {
  parameters: { layout: "padded" },
  render: () => (
    <div data-testid="chip-matrix" className="flex flex-col gap-6">
      {DENSITIES.map((density) => (
        <section key={density} className="flex flex-col gap-3">
          <h3 className="text-sm font-medium text-lia-text-primary">
            Density: {density}
          </h3>
          {MUTED_STATES.map((muted) => (
            <div
              key={`${density}-${String(muted)}`}
              className="flex flex-wrap items-center gap-3"
              data-density={density}
              data-muted={String(muted)}
            >
              <span className="w-20 text-xs text-lia-text-tertiary">
                {muted ? "muted" : "default"}
              </span>
              {VARIANTS.map((variant) => (
                <Chip
                  key={`${density}-${variant}-${String(muted)}`}
                  variant={variant}
                  density={density}
                  muted={muted}
                  data-variant={variant}
                >
                  {variant}
                </Chip>
              ))}
            </div>
          ))}
        </section>
      ))}
    </div>
  ),
}

/**
 * Same matrix wrapped in a `.dark` container. Provides an explicit dark-mode
 * snapshot for environments where Chromatic mode switching is unavailable
 * (e.g. local Storybook test runs without the addon).
 */
export const AllCombinationsDark: Story = {
  parameters: { layout: "padded", backgrounds: { default: "dark" } },
  render: () => (
    <div className="dark bg-lia-bg-primary p-6">
      <div data-testid="chip-matrix-dark" className="flex flex-col gap-6">
        {DENSITIES.map((density) => (
          <section key={density} className="flex flex-col gap-3">
            <h3 className="text-sm font-medium text-lia-text-primary">
              Density: {density}
            </h3>
            {MUTED_STATES.map((muted) => (
              <div
                key={`${density}-${String(muted)}`}
                className="flex flex-wrap items-center gap-3"
              >
                <span className="w-20 text-xs text-lia-text-tertiary">
                  {muted ? "muted" : "default"}
                </span>
                {VARIANTS.map((variant) => (
                  <Chip
                    key={`${density}-${variant}-${String(muted)}`}
                    variant={variant}
                    density={density}
                    muted={muted}
                  >
                    {variant}
                  </Chip>
                ))}
              </div>
            ))}
          </section>
        ))}
      </div>
    </div>
  ),
}
