import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { fn } from 'storybook/test';
import { Button } from './button';
import { Mail, Plus, Download, Loader2 } from 'lucide-react';

const meta = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Button component following the WeDo Talent design system.

## Design Standards
- **Primary accent**: \`#60BED1\` (wedo-light-blue)
- **Typography**: Open Sans, 11px font size
- **Border radius**: 8px (rounded-md)
- **Gray palette**: gray-100 to gray-900 for various states
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'primary', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
      description: 'Visual style variant of the button',
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
      description: 'Size of the button',
    },
    disabled: {
      control: 'boolean',
      description: 'Disable the button',
    },
    asChild: {
      control: 'boolean',
      description: 'Render as child component using Radix Slot',
    },
  },
  args: { onClick: fn() },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Button',
    variant: 'default',
  },
};

export const Primary: Story = {
  args: {
    children: 'Primary Action',
    variant: 'primary',
  },
  parameters: {
    docs: {
      description: {
        story: 'Primary button using the cyan accent color (#60BED1). Use for main call-to-action buttons.',
      },
    },
  },
};

export const Destructive: Story = {
  args: {
    children: 'Delete',
    variant: 'destructive',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary',
    variant: 'secondary',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Ghost',
    variant: 'ghost',
  },
};

export const Link: Story = {
  args: {
    children: 'Link',
    variant: 'link',
  },
};

export const Small: Story = {
  args: {
    children: 'Small',
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    children: 'Large',
    size: 'lg',
  },
};

export const Icon: Story = {
  args: {
    children: <Plus className="h-4 w-4" />,
    size: 'icon',
    'aria-label': 'Add',
  },
};

export const WithIcon: Story = {
  args: {
    children: (
      <>
        <Mail className="h-4 w-4" />
        Send Email
      </>
    ),
  },
};

export const WithIconRight: Story = {
  args: {
    children: (
      <>
        Download
        <Download className="h-4 w-4" />
      </>
    ),
    variant: 'outline',
  },
};

export const Loading: Story = {
  args: {
    children: (
      <>
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading...
      </>
    ),
    disabled: true,
  },
};

export const Disabled: Story = {
  args: {
    children: 'Disabled',
    disabled: true,
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4 items-center">
      <Button variant="default">Default</Button>
      <Button variant="primary">Primary</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link">Link</Button>
    </div>
  ),
};

export const AllSizes: Story = {
  render: () => (
    <div className="flex flex-wrap gap-4 items-center">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
      <Button size="icon"><Plus className="h-4 w-4" /></Button>
    </div>
  ),
};

export const AccentColorExample: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
        Primary accent color: <code className="bg-gray-100 px-2 py-1 rounded">#374151</code> (gray-700)
      </p>
      <div className="flex gap-4">
        <Button variant="primary">
          Primary Button
        </Button>
        <Button 
          variant="outline" 
          className="border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:bg-gray-800"
        >
          Accent Outline
        </Button>
        <Button variant="link">
          Link with Cyan
        </Button>
      </div>
    </div>
  ),
};
