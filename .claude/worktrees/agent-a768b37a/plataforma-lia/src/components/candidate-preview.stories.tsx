import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { fn } from 'storybook/test';
import { CandidatePreview } from './candidate-preview';

const mockCandidate = {
  id: 'cand-12345',
  name: 'João da Silva',
  email: 'joao.silva@email.com',
  phone: '+55 11 99999-9999',
  position: 'Senior Software Engineer',
  title: 'Senior Software Engineer',
  company: 'Tech Company',
  location: 'São Paulo, SP',
  linkedin: 'https://linkedin.com/in/joaosilva',
  github: 'https://github.com/joaosilva',
  avatar_url: '',
  skills: ['React', 'TypeScript', 'Node.js', 'Python', 'PostgreSQL', 'AWS', 'Docker'],
  education: [
    {
      institution: 'Universidade de São Paulo',
      degree: 'Bachelor',
      field: 'Computer Science',
      startDate: '2015',
      endDate: '2019',
    },
  ],
  workHistory: [
    {
      company: 'Tech Company',
      position: 'Senior Software Engineer',
      startDate: '2021-01',
      endDate: 'Present',
      description: 'Leading development of microservices architecture.',
    },
    {
      company: 'Startup Inc',
      position: 'Software Engineer',
      startDate: '2019-06',
      endDate: '2020-12',
      description: 'Full-stack development with React and Node.js.',
    },
  ],
  certifications: [
    { name: 'AWS Solutions Architect', issuer: 'Amazon', date: '2023' },
  ],
  languages: [
    { language: 'Portuguese', proficiency: 'Native' },
    { language: 'English', proficiency: 'Fluent' },
    { language: 'Spanish', proficiency: 'Intermediate' },
  ],
  current_salary: 18000,
  desired_salary_min: 20000,
  desired_salary_max: 25000,
  work_model_preference: 'Remote',
  willing_to_relocate: false,
  liaAnalysis: {
    score: 92,
    fitScore: 88,
    strengths: ['Strong technical skills', 'Leadership experience', 'Good communication'],
    areas_of_improvement: ['Cloud certifications'],
    recommendation: 'Highly recommended for senior positions',
  },
};

const mockCandidateMinimal = {
  id: 'cand-67890',
  name: 'Maria Santos',
  email: 'maria@email.com',
  position: 'Product Designer',
  location: 'Rio de Janeiro, RJ',
  skills: ['Figma', 'UI/UX', 'Design Systems'],
  education: [],
  workHistory: [],
};

const meta = {
  title: 'Components/CandidatePreview',
  component: CandidatePreview,
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        component: `
CandidatePreview is a complex panel component that displays detailed candidate information.

## Features
- Full candidate profile with photo, contact info, and social links
- Tabbed interface: Profile, Activities, Files
- Quick action buttons: Email, Schedule Interview, Assign to Job, Favorite, Hide
- LIA AI analysis scores and recommendations
- Work history, education, skills, and certifications
- Responsive design with maximize/minimize options

## Design Standards
- **Accent color**: \`#60BED1\` used for badges, buttons, and highlights
- **Typography**: Open Sans font family
- **Avatar fallback**: Uses candidate initials with accent color background
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    isOpen: {
      control: 'boolean',
      description: 'Controls panel visibility',
    },
    isMaximized: {
      control: 'boolean',
      description: 'Maximizes the panel to full width',
    },
    isFavorite: {
      control: 'boolean',
      description: 'Shows favorite state',
    },
    isHidden: {
      control: 'boolean',
      description: 'Shows hidden state',
    },
  },
  args: {
    onClose: fn(),
    onToggleMaximize: fn(),
    onOpenFullPage: fn(),
    onScheduleInterview: fn(),
    onAddToVacancy: fn(),
    onToggleFavorite: fn(),
    onHideCandidate: fn(),
    onWSIScreening: fn(),
  },
  decorators: [
    (Story) => (
      <div className="h-[700px] w-[450px] border rounded-md overflow-hidden bg-white">
        <Story />
      </div>
    ),
  ],
} satisfies Meta<typeof CandidatePreview>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    candidate: mockCandidate,
    isOpen: true,
    isMaximized: false,
    isFavorite: false,
    isHidden: false,
    candidates: [mockCandidate],
    currentIndex: 0,
  },
};

export const Favorited: Story = {
  args: {
    candidate: mockCandidate,
    isOpen: true,
    isMaximized: false,
    isFavorite: true,
    isHidden: false,
    candidates: [mockCandidate],
    currentIndex: 0,
  },
};

export const Hidden: Story = {
  args: {
    candidate: mockCandidate,
    isOpen: true,
    isMaximized: false,
    isFavorite: false,
    isHidden: true,
    candidates: [mockCandidate],
    currentIndex: 0,
  },
};

export const MinimalData: Story = {
  args: {
    candidate: mockCandidateMinimal,
    isOpen: true,
    isMaximized: false,
    isFavorite: false,
    isHidden: false,
    candidates: [mockCandidateMinimal],
    currentIndex: 0,
  },
};

export const WithHighScore: Story = {
  args: {
    candidate: {
      ...mockCandidate,
      liaAnalysis: {
        score: 98,
        fitScore: 95,
        strengths: ['Perfect technical match', 'Culture fit', 'Leadership'],
        areas_of_improvement: [],
        recommendation: 'Top candidate - immediate hire recommended',
      },
    },
    isOpen: true,
    isMaximized: false,
    isFavorite: true,
    isHidden: false,
    candidates: [mockCandidate],
    currentIndex: 0,
  },
};

export const WithNavigation: Story = {
  args: {
    candidate: mockCandidate,
    isOpen: true,
    isMaximized: false,
    isFavorite: false,
    isHidden: false,
    candidates: [mockCandidate, mockCandidateMinimal, mockCandidate],
    currentIndex: 1,
    onNavigateCandidate: fn(),
  },
};

export const Closed: Story = {
  args: {
    candidate: mockCandidate,
    isOpen: false,
    isMaximized: false,
    isFavorite: false,
    isHidden: false,
    candidates: [mockCandidate],
    currentIndex: 0,
  },
};

export const ExperiencedCandidate: Story = {
  args: {
    candidate: {
      ...mockCandidate,
      name: 'Carlos Mendes',
      position: 'Tech Lead',
      workHistory: [
        {
          company: 'Big Tech Corp',
          position: 'Tech Lead',
          startDate: '2020-01',
          endDate: 'Present',
          description: 'Leading a team of 15 engineers.',
        },
        {
          company: 'Scale Startup',
          position: 'Senior Engineer',
          startDate: '2018-01',
          endDate: '2019-12',
          description: 'Built core platform from scratch.',
        },
        {
          company: 'Consulting Firm',
          position: 'Software Engineer',
          startDate: '2015-06',
          endDate: '2017-12',
          description: 'Enterprise software development.',
        },
      ],
      skills: [
        'React', 'TypeScript', 'Node.js', 'Python', 'Go', 
        'PostgreSQL', 'MongoDB', 'Redis', 'AWS', 'GCP', 
        'Docker', 'Kubernetes', 'Terraform', 'CI/CD'
      ],
      certifications: [
        { name: 'AWS Solutions Architect Pro', issuer: 'Amazon', date: '2023' },
        { name: 'Kubernetes Administrator', issuer: 'CNCF', date: '2022' },
        { name: 'Google Cloud Engineer', issuer: 'Google', date: '2021' },
      ],
      current_salary: 35000,
      desired_salary_min: 40000,
      desired_salary_max: 50000,
    },
    isOpen: true,
    isMaximized: false,
    isFavorite: false,
    isHidden: false,
    candidates: [mockCandidate],
    currentIndex: 0,
  },
};

export const DesignerProfile: Story = {
  args: {
    candidate: {
      id: 'cand-design-1',
      name: 'Ana Oliveira',
      email: 'ana.oliveira@design.com',
      phone: '+55 21 98888-8888',
      position: 'Senior Product Designer',
      title: 'Senior Product Designer',
      company: 'Design Studio',
      location: 'Remote, Brazil',
      linkedin: 'https://linkedin.com/in/anaoliveira',
      avatar_url: '',
      skills: ['Figma', 'Sketch', 'Adobe XD', 'Design Systems', 'User Research', 'Prototyping', 'Motion Design'],
      education: [
        {
          institution: 'ESPM',
          degree: 'Bachelor',
          field: 'Design',
          startDate: '2014',
          endDate: '2018',
        },
      ],
      workHistory: [
        {
          company: 'Design Studio',
          position: 'Senior Product Designer',
          startDate: '2022-01',
          endDate: 'Present',
          description: 'Leading design system initiatives.',
        },
        {
          company: 'Fintech App',
          position: 'Product Designer',
          startDate: '2019-03',
          endDate: '2021-12',
          description: 'Designed mobile banking experience.',
        },
      ],
      certifications: [
        { name: 'Google UX Design', issuer: 'Google', date: '2022' },
      ],
      languages: [
        { language: 'Portuguese', proficiency: 'Native' },
        { language: 'English', proficiency: 'Advanced' },
      ],
      work_model_preference: 'Remote',
      willing_to_relocate: false,
      liaAnalysis: {
        score: 85,
        fitScore: 90,
        strengths: ['Strong portfolio', 'Design system experience', 'User research skills'],
        areas_of_improvement: ['Development collaboration'],
        recommendation: 'Great fit for product design roles',
      },
    },
    isOpen: true,
    isMaximized: false,
    isFavorite: false,
    isHidden: false,
    candidates: [],
    currentIndex: 0,
  },
};
