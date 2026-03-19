import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Input } from './input';
import { Search, Mail, Lock, User, Eye, EyeOff } from 'lucide-react';
import { useState } from 'react';

const meta = {
  title: 'UI/Input',
  component: Input,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Input component for text entry.

## Design Standards
- **Height**: 40px (h-10)
- **Border**: 1px solid gray-300, rounded-md
- **Typography**: 11px font size
- **Focus**: Cyan border (#60BED1) with 20% opacity ring
- **Placeholder**: gray-500 color
- **Dark mode**: gray-600 border, gray-700 background

## Focus State Pattern
All form components use the standardized cyan focus:
\`\`\`
focus:border-gray-400 focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20
\`\`\`
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'search', 'tel', 'url'],
      description: 'HTML input type',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Disable the input',
    },
  },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
  decorators: [
    (Story) => (
      <div className="w-[300px]">
        <Story />
      </div>
    ),
  ],
};

export const WithValue: Story = {
  args: {
    defaultValue: 'Hello World',
  },
  decorators: [
    (Story) => (
      <div className="w-[300px]">
        <Story />
      </div>
    ),
  ],
};

export const Email: Story = {
  args: {
    type: 'email',
    placeholder: 'email@example.com',
  },
  decorators: [
    (Story) => (
      <div className="w-[300px]">
        <Story />
      </div>
    ),
  ],
};

export const Password: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter password',
  },
  decorators: [
    (Story) => (
      <div className="w-[300px]">
        <Story />
      </div>
    ),
  ],
};

export const Number: Story = {
  args: {
    type: 'number',
    placeholder: '0',
  },
  decorators: [
    (Story) => (
      <div className="w-[300px]">
        <Story />
      </div>
    ),
  ],
};

export const Disabled: Story = {
  args: {
    disabled: true,
    placeholder: 'Disabled input',
  },
  decorators: [
    (Story) => (
      <div className="w-[300px]">
        <Story />
      </div>
    ),
  ],
};

export const WithLabel: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <label 
        htmlFor="name" 
        className="text-[11px] font-medium text-gray-800 dark:text-gray-200"
        style={{ fontFamily: 'Open Sans, sans-serif' }}
      >
        Full Name
      </label>
      <Input id="name" placeholder="João da Silva" />
    </div>
  ),
};

export const WithHelperText: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <label 
        htmlFor="email" 
        className="text-[11px] font-medium text-gray-800 dark:text-gray-200"
        style={{ fontFamily: 'Open Sans, sans-serif' }}
      >
        Email
      </label>
      <Input id="email" type="email" placeholder="email@example.com" />
      <p className="text-[10px] text-gray-500">We'll never share your email.</p>
    </div>
  ),
};

export const WithError: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <label 
        htmlFor="email-error" 
        className="text-[11px] font-medium text-gray-800 dark:text-gray-200"
        style={{ fontFamily: 'Open Sans, sans-serif' }}
      >
        Email
      </label>
      <Input 
        id="email-error" 
        type="email" 
        placeholder="email@example.com" 
        className="border-red-500 focus:ring-red-500"
        defaultValue="invalid-email"
      />
      <p className="text-[10px] text-red-500">Please enter a valid email address.</p>
    </div>
  ),
};

export const WithIcon: Story = {
  render: () => (
    <div className="w-[300px] relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      <Input className="pl-10" placeholder="Search candidates..." />
    </div>
  ),
};

export const WithIconRight: Story = {
  render: () => (
    <div className="w-[300px] relative">
      <Input className="pr-10" placeholder="Email" />
      <Mail className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
    </div>
  ),
};

export const SearchInput: Story = {
  render: () => (
    <div className="w-[350px] relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-700" />
      <Input 
        className="pl-10 border-gray-900 dark:border-gray-50 focus:ring-gray-900/20 dark:focus:ring-gray-50/20" 
        placeholder="Search by name, skills, or location..." 
      />
    </div>
  ),
};

export const FormGroup: Story = {
  render: () => (
    <div className="w-[350px] space-y-4">
      <div className="space-y-2">
        <label className="text-[11px] font-medium flex items-center gap-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
          <User className="h-3.5 w-3.5 text-gray-700" />
          Full Name
        </label>
        <Input placeholder="Enter your full name" />
      </div>
      <div className="space-y-2">
        <label className="text-[11px] font-medium flex items-center gap-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
          <Mail className="h-3.5 w-3.5 text-gray-700" />
          Email
        </label>
        <Input type="email" placeholder="email@company.com" />
      </div>
      <div className="space-y-2">
        <label className="text-[11px] font-medium flex items-center gap-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
          <Lock className="h-3.5 w-3.5 text-gray-700" />
          Password
        </label>
        <Input type="password" placeholder="Enter password" />
      </div>
    </div>
  ),
};

export const AllStates: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div>
        <p className="text-[10px] text-gray-500 mb-1">Default</p>
        <Input placeholder="Default input" />
      </div>
      <div>
        <p className="text-[10px] text-gray-500 mb-1">With Value</p>
        <Input defaultValue="Some value" />
      </div>
      <div>
        <p className="text-[10px] text-gray-500 mb-1">Disabled</p>
        <Input placeholder="Disabled" disabled />
      </div>
      <div>
        <p className="text-[10px] text-gray-500 mb-1">Error State</p>
        <Input 
          className="border-red-500 focus:ring-red-500" 
          defaultValue="Invalid input"
        />
      </div>
      <div>
        <p className="text-[10px] text-gray-500 mb-1">Success State</p>
        <Input 
          className="border-green-500 focus:ring-green-500" 
          defaultValue="Valid input"
        />
      </div>
    </div>
  ),
};
