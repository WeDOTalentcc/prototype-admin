import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } from './card';
import { Button } from './button';
import { cardStyles, textStyles, badgeStyles, buttonStyles } from '@/lib/design-tokens';

const meta = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Card component for grouping related content.

## Design Standards (LIA Platform v2.0)

### Colors
- **Border**: border-gray-100 (light separation)
- **Background**: White (#FFFFFF)
- **Shadow**: (subtle depth)
- **Accent**: #60BED1 for interactive highlights

### Typography (Source Serif 4 + Open Sans)
- **Title**: 13px, font-semibold, gray-800
- **Description**: 11px, font-normal, gray-500
- **Body**: 12px, font-normal, gray-600

### Card Variants
- **CardCompact**: Compact padding (p-2), smaller content areas
- **CardExpanded**: Standard padding (p-4), full content display
- **CardInteractive**: Hover effects with accent border highlight

### Tailwind → Vuetify 3 Mapping
| Tailwind | Vuetify 3 |
|----------|-----------|
| | elevation="1" |
| | elevation="4" |
| border-gray-100 | variant="outlined" class="border-grey-lighten-4" |
| border-gray-200 | variant="outlined" class="border-grey-lighten-3" |
| p-2 | class="pa-2" |
| p-4 | class="pa-4" |
| px-4 | class="px-4" |
| py-2 | class="py-2" |
| gap-2 | class="gap-2" or style="gap: 8px" |
| gap-3 | class="gap-3" or style="gap: 12px" |
| gap-4 | class="gap-4" or style="gap: 16px" |
| flex | class="d-flex" |
| flex items-center | class="d-flex align-center" |
| flex justify-between | class="d-flex justify-space-between" |
| flex flex-col | class="d-flex flex-column" |
| flex-1 | class="flex-grow-1" |
| text-gray-800 | class="text-grey-darken-3" |
| text-gray-600 | class="text-grey-darken-1" |
| text-gray-500 | class="text-grey" |
| text-gray-400 | class="text-grey-lighten-1" |
| | elevation="8" |
| flex justify-center | class="d-flex justify-center" |
| flex-wrap | class="flex-wrap" |

See \`@/lib/design-tokens.ts\` for the complete mapping table.
        `,
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-[11px]">Card content area. You can put any content here.</p>
      </CardContent>
      <CardFooter>
        <Button className="w-full">Action</Button>
      </CardFooter>
    </Card>
  ),
};

export const Simple: Story = {
  render: () => (
    <Card className="w-[350px] p-6">
      <p className="text-[11px] text-gray-800 dark:text-gray-200">Simple card with just content.</p>
    </Card>
  ),
};

export const WithHeaderOnly: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
    </Card>
  ),
};

export const Interactive: Story = {
  render: () => (
    <Card className="w-[350px] hover:transition-shadow cursor-pointer">
      <CardHeader>
        <CardTitle>Clickable Card</CardTitle>
        <CardDescription>This card has hover effects.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-[11px] text-gray-600">
          Hover over this card to see the shadow effect.
        </p>
      </CardContent>
    </Card>
  ),
};

export const WithAccentBorder: Story = {
  render: () => (
    <Card className="w-[350px] border-l-4 border-l-gray-300 dark:border-l-gray-600">
      <CardHeader>
        <CardTitle>Accent Border</CardTitle>
        <CardDescription>Using the WeDo accent color #60BED1</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-[11px]" style={{ fontFamily: 'Open Sans, sans-serif' }}>
          This card uses the primary accent color for the left border.
        </p>
      </CardContent>
    </Card>
  ),
};

export const CandidateCard: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <div 
            className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold bg-gray-900" style={{ fontFamily: 'Open Sans, sans-serif' }}
          >
            JD
          </div>
          <div>
            <CardTitle>João da Silva</CardTitle>
            <CardDescription>Senior Developer • São Paulo</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-2">
        <div className="flex gap-2 flex-wrap">
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-gray-100 text-gray-800 dark:text-gray-200">React</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-gray-100 text-gray-800 dark:text-gray-200">TypeScript</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] bg-gray-100 text-gray-800 dark:text-gray-200">Node.js</span>
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button size="sm" variant="outline" className="flex-1">View</Button>
        <Button size="sm" className="flex-1 bg-gray-900">Contact</Button>
      </CardFooter>
    </Card>
  ),
};

export const StatsCard: Story = {
  render: () => (
    <Card className="w-[200px]">
      <CardHeader className="pb-2">
        <CardDescription>Total Candidates</CardDescription>
        <CardTitle className="text-2xl">1,234</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-[10px] text-green-600">+12% from last month</p>
      </CardContent>
    </Card>
  ),
};

export const MultipleCards: Story = {
  render: () => (
    <div className="grid grid-cols-3 gap-4">
      <Card className="p-4">
        <CardTitle className="text-lg mb-2">New</CardTitle>
        <p className="text-3xl font-bold text-gray-700">45</p>
      </Card>
      <Card className="p-4">
        <CardTitle className="text-lg mb-2">In Progress</CardTitle>
        <p className="text-3xl font-bold text-amber-500">23</p>
      </Card>
      <Card className="p-4">
        <CardTitle className="text-lg mb-2">Completed</CardTitle>
        <p className="text-3xl font-bold text-green-500">89</p>
      </Card>
    </div>
  ),
};

export const CardCompact: Story = {
  name: 'Variant: Compact',
  render: () => (
    <Card className={cardStyles.compact + " w-[300px]"}>
      <div className="flex items-center gap-2">
        <div 
          className="w-8 h-8 rounded-full flex items-center justify-center text-white text-[10px] font-semibold bg-gray-900"
        >
          MS
        </div>
        <div className="flex-1 min-w-0">
          <p className={textStyles.subtitle + " truncate"}>Maria Santos</p>
          <p className={textStyles.caption + " truncate"}>Product Designer • Rio de Janeiro</p>
        </div>
        <span className={badgeStyles.success}>85%</span>
      </div>
    </Card>
  ),
};

export const CardExpanded: Story = {
  name: 'Variant: Expanded',
  render: () => (
    <Card className={cardStyles.expanded + " w-[400px]"}>
      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div 
            className="w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold bg-gray-900"
          >
            PS
          </div>
          <div className="flex-1">
            <h3 className={textStyles.title}>Pedro Silva</h3>
            <p className={textStyles.description}>Senior Software Engineer</p>
            <p className={textStyles.caption + " mt-1"}>São Paulo, SP • 8 anos de experiência</p>
          </div>
        </div>
        
        <div className="border-t border-gray-100 pt-3">
          <p className={textStyles.label + " mb-2"}>Competências</p>
          <div className="flex gap-2 flex-wrap">
            <span className={badgeStyles.primary}>React</span>
            <span className={badgeStyles.primary}>TypeScript</span>
            <span className={badgeStyles.primary}>Node.js</span>
            <span className={badgeStyles.default}>Python</span>
          </div>
        </div>
        
        <div className="border-t border-gray-100 pt-3">
          <p className={textStyles.body}>
            Profissional com ampla experiência em desenvolvimento de aplicações web, 
            liderança técnica de equipes e arquitetura de sistemas distribuídos.
          </p>
        </div>
        
        <div className="flex gap-2 pt-2">
          <Button variant="outline" size="sm" className="flex-1">Ver Perfil</Button>
          <Button size="sm" className="flex-1 bg-gray-900">Contatar</Button>
        </div>
      </div>
    </Card>
  ),
};

export const CardInteractive: Story = {
  name: 'Variant: Interactive',
  render: () => (
    <div className="space-y-4">
      <p className={textStyles.caption + " text-center"}>Hover para ver o efeito de destaque</p>
      <Card className={cardStyles.interactive + " w-[350px] p-4 cursor-pointer"}>
        <div className="flex items-center gap-3">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center"
            style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
          >
            <svg 
              className="w-5 h-5 text-gray-700"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" 
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className={textStyles.title}>Buscar Candidatos</h3>
            <p className={textStyles.description}>Encontre talentos na base local e global</p>
          </div>
          <svg 
            className="w-5 h-5 text-gray-400" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M9 5l7 7-7 7" 
            />
          </svg>
        </div>
      </Card>
      
      <Card className={cardStyles.interactive + " w-[350px] p-4 cursor-pointer"}>
        <div className="flex items-center gap-3">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center"
            style={{ backgroundColor: 'rgba(93, 164, 122, 0.1)' }}
          >
            <svg 
              className="w-5 h-5 text-wedo-green"
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className={textStyles.title}>Triagem WSI</h3>
            <p className={textStyles.description}>Avalie candidatos com entrevistas estruturadas</p>
          </div>
          <svg 
            className="w-5 h-5 text-gray-400" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M9 5l7 7-7 7" 
            />
          </svg>
        </div>
      </Card>
    </div>
  ),
};

export const DesignTokensReference: Story = {
  name: 'Design Tokens Reference',
  render: () => (
    <div className="space-y-6 p-4 max-w-2xl">
      <div>
        <h2 className={textStyles.titleLarge + " mb-4"}>Referência de Design Tokens</h2>
        <p className={textStyles.body + " mb-6"}>
          Utilize os tokens do arquivo <code className="bg-gray-100 px-1 rounded">@/lib/design-tokens</code> 
          para manter consistência visual em toda a plataforma.
        </p>
      </div>
      
      <div className="space-y-4">
        <h3 className={textStyles.title}>Card Styles</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className={cardStyles.default + " p-3"}>
            <p className={textStyles.label}>cardStyles.default</p>
            <p className={textStyles.caption}>flat, border-gray-200</p>
          </div>
          <div className={cardStyles.elevated + " p-3"}>
            <p className={textStyles.label}>cardStyles.elevated</p>
            <p className={textStyles.caption}>flat, border-gray-200</p>
          </div>
          <div className={cardStyles.compact + " p-3"}>
            <p className={textStyles.label}>cardStyles.compact</p>
            <p className={textStyles.caption}>p-2, rounded-md</p>
          </div>
          <div className={cardStyles.flat + " p-3"}>
            <p className={textStyles.label}>cardStyles.flat</p>
            <p className={textStyles.caption}>bg-gray-50, no shadow</p>
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        <h3 className={textStyles.title}>Text Styles</h3>
        <div className={cardStyles.default + " p-4 space-y-2"}>
          <p className={textStyles.titleLarge}>textStyles.titleLarge (16px)</p>
          <p className={textStyles.title}>textStyles.title (13px, semibold)</p>
          <p className={textStyles.subtitle}>textStyles.subtitle (12px, medium)</p>
          <p className={textStyles.body}>textStyles.body (12px, normal)</p>
          <p className={textStyles.bodySmall}>textStyles.bodySmall (11px)</p>
          <p className={textStyles.description}>textStyles.description (11px, gray-500)</p>
          <p className={textStyles.caption}>textStyles.caption (10px)</p>
        </div>
      </div>
      
      <div className="space-y-4">
        <h3 className={textStyles.title}>Badge Styles</h3>
        <div className={cardStyles.default + " p-4"}>
          <div className="flex gap-2 flex-wrap">
            <span className={badgeStyles.default}>badgeStyles.default</span>
            <span className={badgeStyles.primary}>badgeStyles.primary</span>
            <span className={badgeStyles.success}>badgeStyles.success</span>
            <span className={badgeStyles.warning}>badgeStyles.warning</span>
            <span className={badgeStyles.error}>badgeStyles.error</span>
            <span className={badgeStyles.info}>badgeStyles.info</span>
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        <h3 className={textStyles.title}>Button Styles</h3>
        <div className={cardStyles.default + " p-4"}>
          <div className="flex gap-2 flex-wrap">
            <button className={buttonStyles.primary}>Primary</button>
            <button className={buttonStyles.secondary}>Secondary</button>
            <button className={buttonStyles.ghost}>Ghost</button>
            <button className={buttonStyles.success}>Success</button>
            <button className={buttonStyles.danger}>Danger</button>
          </div>
        </div>
      </div>
    </div>
  ),
};
