import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
  SelectSeparator,
} from './select';

const meta = {
  title: 'UI/Select',
  component: Select,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Select component built on Radix UI Select primitive.

## Design Standards
- **Height**: 40px (h-10)
- **Border**: 1px solid gray-200, rounded-md
- **Typography**: 14px (text-sm) for trigger
- **Focus**: gray-950 ring
- **Animation**: Zoom and fade animations
- **Dark mode**: gray-800 border, gray-950 background
        `,
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select an option" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>
  ),
};

export const WithDefaultValue: Story = {
  render: () => (
    <Select defaultValue="option2">
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select an option" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>
  ),
};

export const WithGroups: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[250px]">
        <SelectValue placeholder="Select a location" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Brazil</SelectLabel>
          <SelectItem value="sao-paulo">São Paulo</SelectItem>
          <SelectItem value="rio-de-janeiro">Rio de Janeiro</SelectItem>
          <SelectItem value="belo-horizonte">Belo Horizonte</SelectItem>
        </SelectGroup>
        <SelectSeparator />
        <SelectGroup>
          <SelectLabel>United States</SelectLabel>
          <SelectItem value="new-york">New York</SelectItem>
          <SelectItem value="san-francisco">San Francisco</SelectItem>
          <SelectItem value="los-angeles">Los Angeles</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  ),
};

export const Disabled: Story = {
  render: () => (
    <Select disabled>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Disabled select" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
      </SelectContent>
    </Select>
  ),
};

export const DisabledItems: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select status" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="active">Active</SelectItem>
        <SelectItem value="pending">Pending</SelectItem>
        <SelectItem value="archived" disabled>Archived (disabled)</SelectItem>
      </SelectContent>
    </Select>
  ),
};

export const RecruitmentStage: Story = {
  render: () => (
    <div className="space-y-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Recruitment Stage</label>
      <Select defaultValue="interview">
        <SelectTrigger className="w-[250px]">
          <SelectValue placeholder="Select stage" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="new">🆕 New Application</SelectItem>
          <SelectItem value="screening">📋 Screening</SelectItem>
          <SelectItem value="interview">🎤 Interview</SelectItem>
          <SelectItem value="assessment">📝 Assessment</SelectItem>
          <SelectItem value="offer">📄 Offer</SelectItem>
          <SelectItem value="hired">✅ Hired</SelectItem>
          <SelectSeparator />
          <SelectItem value="rejected">❌ Rejected</SelectItem>
        </SelectContent>
      </Select>
    </div>
  ),
};

export const JobFilter: Story = {
  render: () => (
    <div className="space-y-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Filter by Job</label>
      <Select>
        <SelectTrigger className="w-[300px] border-gray-900 dark:border-gray-50 focus:ring-gray-900/20 dark:focus:ring-gray-50/20">
          <SelectValue placeholder="All Jobs" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Jobs</SelectItem>
          <SelectSeparator />
          <SelectGroup>
            <SelectLabel>Technology</SelectLabel>
            <SelectItem value="senior-dev">Senior Developer</SelectItem>
            <SelectItem value="tech-lead">Tech Lead</SelectItem>
            <SelectItem value="devops">DevOps Engineer</SelectItem>
          </SelectGroup>
          <SelectSeparator />
          <SelectGroup>
            <SelectLabel>Design</SelectLabel>
            <SelectItem value="ux-designer">UX Designer</SelectItem>
            <SelectItem value="product-designer">Product Designer</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  ),
};

export const ExperienceLevel: Story = {
  render: () => (
    <div className="space-y-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Experience Level</label>
      <Select>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select level" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="intern">Intern</SelectItem>
          <SelectItem value="junior">Junior (0-2 years)</SelectItem>
          <SelectItem value="mid">Mid-level (2-5 years)</SelectItem>
          <SelectItem value="senior">Senior (5-8 years)</SelectItem>
          <SelectItem value="lead">Lead (8+ years)</SelectItem>
          <SelectItem value="executive">Executive</SelectItem>
        </SelectContent>
      </Select>
    </div>
  ),
};

export const ContractType: Story = {
  render: () => (
    <div className="space-y-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Contract Type</label>
      <Select>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="clt">CLT</SelectItem>
          <SelectItem value="pj">PJ</SelectItem>
          <SelectItem value="temporary">Temporary</SelectItem>
          <SelectItem value="internship">Internship</SelectItem>
          <SelectItem value="freelance">Freelance</SelectItem>
        </SelectContent>
      </Select>
    </div>
  ),
};

export const WorkModel: Story = {
  render: () => (
    <div className="space-y-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Work Model</label>
      <Select defaultValue="remote">
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select model" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="remote">🏠 Remote</SelectItem>
          <SelectItem value="hybrid">🔄 Hybrid</SelectItem>
          <SelectItem value="onsite">🏢 On-site</SelectItem>
        </SelectContent>
      </Select>
    </div>
  ),
};

export const FormExample: Story = {
  render: () => (
    <div className="w-[350px] p-4 border rounded-md space-y-4" style={{ fontFamily: 'Open Sans, sans-serif' }}>
      <h3 className="text-xs font-semibold text-gray-700">Candidate Filters</h3>
      
      <div className="space-y-2">
        <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Experience</label>
        <Select>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Any experience" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any experience</SelectItem>
            <SelectItem value="1-3">1-3 years</SelectItem>
            <SelectItem value="3-5">3-5 years</SelectItem>
            <SelectItem value="5+">5+ years</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Location</label>
        <Select>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Any location" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any location</SelectItem>
            <SelectItem value="sao-paulo">São Paulo</SelectItem>
            <SelectItem value="rio">Rio de Janeiro</SelectItem>
            <SelectItem value="remote">Remote only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-[11px] font-medium text-gray-800 dark:text-gray-200">Salary Range</label>
        <Select>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Any salary" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any salary</SelectItem>
            <SelectItem value="0-5k">Up to R$ 5.000</SelectItem>
            <SelectItem value="5k-10k">R$ 5.000 - R$ 10.000</SelectItem>
            <SelectItem value="10k-15k">R$ 10.000 - R$ 15.000</SelectItem>
            <SelectItem value="15k+">R$ 15.000+</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  ),
};
