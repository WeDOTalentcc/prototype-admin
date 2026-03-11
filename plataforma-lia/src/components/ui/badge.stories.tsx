import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Badge } from './badge';
import { Check, X, AlertCircle, Clock, Star } from 'lucide-react';

const meta = {
  title: 'UI/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Badge component for status indicators and labels.

## Design Standards
- **Typography**: 11px, font-semibold
- **Border radius**: Full (rounded-full)
- **Padding**: 10px horizontal, 2px vertical
- **Variants**:
  - Default: gray-100 bg, gray-800 text
  - Secondary: cyan bg, cyan text (#60BED1)
  - Destructive: red-100 bg, red-800 text
  - Success: mint color scheme
  - Warning: yellow color scheme
  - Info: light-blue color scheme (#60BED1)
  - Danger: coral color scheme
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'secondary', 'destructive', 'outline', 'success', 'warning', 'info', 'danger'],
      description: 'Visual style variant of the badge',
    },
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Badge',
    variant: 'default',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary',
    variant: 'secondary',
  },
};

export const Destructive: Story = {
  args: {
    children: 'Destructive',
    variant: 'destructive',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
};

export const Success: Story = {
  args: {
    children: 'Success',
    variant: 'success',
  },
};

export const Warning: Story = {
  args: {
    children: 'Warning',
    variant: 'warning',
  },
};

export const Info: Story = {
  args: {
    children: 'Info',
    variant: 'info',
  },
};

export const Danger: Story = {
  args: {
    children: 'Danger',
    variant: 'danger',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge variant="default">Default</Badge>
      <Badge variant="secondary">Secondary</Badge>
      <Badge variant="destructive">Destructive</Badge>
      <Badge variant="outline">Outline</Badge>
      <Badge variant="success">Success</Badge>
      <Badge variant="warning">Warning</Badge>
      <Badge variant="info">Info</Badge>
      <Badge variant="danger">Danger</Badge>
    </div>
  ),
};

export const WithIcons: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <Badge variant="success" className="flex items-center gap-1">
        <Check className="h-3 w-3" />
        Approved
      </Badge>
      <Badge variant="destructive" className="flex items-center gap-1">
        <X className="h-3 w-3" />
        Rejected
      </Badge>
      <Badge variant="warning" className="flex items-center gap-1">
        <AlertCircle className="h-3 w-3" />
        Pending
      </Badge>
      <Badge variant="info" className="flex items-center gap-1">
        <Clock className="h-3 w-3" />
        In Progress
      </Badge>
    </div>
  ),
};

export const RecruitmentStages: Story = {
  render: () => (
    <div className="flex flex-col gap-3" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <p className="text-[11px] text-gray-600">Recruitment Pipeline Stages:</p>
      <div className="flex flex-wrap gap-2">
        <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200">New</Badge>
        <Badge className="bg-[rgba(96,190,209,0.15)] text-wedo-cyan-dark">Screening</Badge>
        <Badge className="bg-purple-100 text-purple-700">Interview</Badge>
        <Badge className="bg-amber-100 text-amber-700">Assessment</Badge>
        <Badge className="bg-green-100 text-green-700">Offer</Badge>
        <Badge className="bg-emerald-100 text-emerald-700">Hired</Badge>
      </div>
    </div>
  ),
};

export const SkillBadges: Story = {
  render: () => (
    <div className="flex flex-col gap-3" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <p className="text-[11px] text-gray-600">Candidate Skills:</p>
      <div className="flex flex-wrap gap-2">
        <Badge variant="outline">React</Badge>
        <Badge variant="outline">TypeScript</Badge>
        <Badge variant="outline">Node.js</Badge>
        <Badge variant="outline">PostgreSQL</Badge>
        <Badge variant="outline">AWS</Badge>
        <Badge variant="outline">Docker</Badge>
      </div>
    </div>
  ),
};

export const MatchScore: Story = {
  render: () => (
    <div className="flex flex-col gap-3" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <p className="text-[11px] text-gray-600">LIA Match Scores:</p>
      <div className="flex flex-wrap gap-2">
        <Badge className="bg-green-100 text-green-700">
          <Star className="h-3 w-3 mr-1 fill-green-500" />
          95% Match
        </Badge>
        <Badge className="bg-[rgba(96,190,209,0.15)] text-wedo-cyan-dark">
          <Star className="h-3 w-3 mr-1 fill-gray-700 dark:fill-gray-300" />
          82% Match
        </Badge>
        <Badge className="bg-amber-100 text-amber-700">
          <Star className="h-3 w-3 mr-1 fill-amber-500" />
          67% Match
        </Badge>
        <Badge className="bg-red-100 text-red-700">
          <Star className="h-3 w-3 mr-1 fill-red-500" />
          45% Match
        </Badge>
      </div>
    </div>
  ),
};

export const AccentColorBadge: Story = {
  render: () => (
    <div className="flex flex-col gap-3">
      <p className="text-[11px] text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
        Using WeDo accent color <code className="bg-gray-100 px-1 rounded">#60BED1</code>:
      </p>
      <div className="flex flex-wrap gap-2">
        <Badge 
          className="border-gray-900 dark:border-gray-50 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
        >
          Featured
        </Badge>
        <Badge 
          className="bg-gray-900 dark:bg-gray-50 text-white border-gray-900 dark:border-gray-50"
        >
          LIA Recommended
        </Badge>
        <Badge 
          className="border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400"
          variant="outline"
        >
          Top Candidate
        </Badge>
      </div>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Badge className="text-[9px] px-1.5 py-0">XS</Badge>
      <Badge className="text-[10px] px-2 py-0.5">Small</Badge>
      <Badge>Default</Badge>
      <Badge className="text-xs px-3 py-1">Large</Badge>
    </div>
  ),
};

export const InContext: Story = {
  render: () => (
    <div className="w-[350px] p-4 border rounded-md space-y-3" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-xs font-semibold">João da Silva</h3>
          <p className="text-[11px] text-gray-500">Senior Developer</p>
        </div>
        <Badge variant="info" className="flex items-center gap-1">
          <Star className="h-3 w-3" />
          92%
        </Badge>
      </div>
      <div className="flex flex-wrap gap-1.5">
        <Badge variant="outline" className="text-[10px]">React</Badge>
        <Badge variant="outline" className="text-[10px]">TypeScript</Badge>
        <Badge variant="outline" className="text-[10px]">Node.js</Badge>
      </div>
      <div className="flex gap-2">
        <Badge variant="success" className="text-[10px]">Available</Badge>
        <Badge variant="secondary" className="text-[10px]">5 years exp.</Badge>
      </div>
    </div>
  ),
};
