# Roteiro Completo - Onboarding LIA Platform

## 📋 Visão Geral

Sistema de onboarding impactante no estilo Apple/Samsung para novos usuários da plataforma LIA. Apresentação sofisticada em 6 slides com animações elegantes, storytelling envolvente e call-to-actions estratégicos.

---

## 🎯 Objetivos do Onboarding

1. **Causar primeira impressão WOW** - Design premium e animações fluidas
2. **Explicar o valor da LIA** - IA como diferencial competitivo
3. **Apresentar a plataforma** - Visão geral das funcionalidades
4. **Guiar para ação** - Setup em 3 passos simples
5. **Reduzir fricção** - Tutorial visual e intuitivo

---

## 🎨 Princípios de Design

### Visual Identity
- **Paleta**: Gradientes azul/roxo, branco, cores vibrantes para destaques
- **Tipografia**: Sans-serif bold para títulos, regular para textos
- **Animações**: Smooth, 60fps, easing natural
- **Layout**: Centrado, minimalista, foco no conteúdo

### Animation Patterns
- **Entrada**: FadeIn, SlideUp, Zoom suave
- **Ênfase**: Float, Scale, Glow effects
- **Transição**: Dissolve cross-fade entre slides
- **Micro-interações**: Hover states, loading indicators

---

## 📱 Slide-by-Slide Breakdown

### Slide 1: Welcome
**Duração**: 4 segundos | **Auto-advance**: Sim

#### Conteúdo
```
Título: "Bem-vindo à LIA"
Subtítulo: "A Revolução em Recrutamento"
Descrição: "Sua jornada para transformar talentos em sucessos extraordinários começa agora."
```

#### Especificações Técnicas
- **Background**: Gradiente diagonal blue-600 → purple-600 → indigo-800
- **Animation**: FadeIn suave (0.8s duration)
- **Icon**: Sparkles - animação de brilho pulsante
- **Typography**:
  - H1: 6xl mobile, 8xl desktop, font-bold
  - H2: 3xl mobile, 4xl desktop, font-light
  - P: xl mobile, 2xl desktop, opacity-80

#### Elementos Visuais
- Ícone Sparkles centralizado com glow effect
- Partículas flutuantes sutis no background
- Texto com fade-in sequencial (título → subtítulo → descrição)

---

### Slide 2: Revolution
**Duração**: 5 segundos | **Auto-advance**: Sim

#### Conteúdo
```
Título: "O Futuro do"
Subtítulo: "Recrutamento Chegou"
Descrição: "Inteligência Artificial que compreende, analisa e conecta talentos de forma única no mercado."
```

#### Especificações Técnicas
- **Background**: Dark + partículas animadas (50 pontos flutuantes)
- **Animation**: Zoom (scale 0.8 → 1.0) com opacity fade
- **Icon**: Brain com efeito de pulsação
- **Partículas**: 50 pontos brancos, movimento Y senoidal, 3-5s duration

#### Elementos Visuais
- Background escuro com partículas flutuantes
- Cada partícula: 4px círculo, opacity 0.3-1.0, movimento vertical
- Título com efeito de zoom dinâmico
- Brain icon com escala pulsante

---

### Slide 3: LIA Introduction
**Duração**: 6 segundos | **Auto-advance**: Sim

#### Conteúdo
```
Título: "Conheça a LIA"
Subtítulo: "Sua Assistente de IA"
Descrição: "Uma mente artificial treinada por especialistas em recrutamento para acelerar seus processos e decisões."
```

#### Especificações Técnicas
- **Background**: Gradiente emerald-500 → cyan-500 → blue-500 + formas geométricas
- **Animation**: Float (movimento vertical senoidal contínuo)
- **Visual**: Avatar da LIA customizado
- **Geometric Shapes**: 20 elementos, círculos/quadrados, rotação 360°, scale 1.0-1.2

#### Elementos Visuais Únicos
- **LIA Avatar Central**:
  - Círculo 128px, gradiente cyan-400 → blue-600
  - Brain icon 64px centralizado
  - 6 partículas orbitantes (3px cada)
  - Órbita 60px raio, rotação 4s contínua

- **Background Geométrico**:
  - 20 formas aleatórias (50-150px)
  - Rotação contínua 10-20s
  - Opacity 10%, border branco

---

### Slide 4: Capabilities Showcase
**Duração**: 5 segundos | **Auto-advance**: Sim

#### Conteúdo
```
Título: "Poderes da LIA"
Descrição: "Análise automática de CVs, matching inteligente, agendamento, comunicação personalizada e muito mais."
```

#### Grid de Funcionalidades (8 itens)
1. **Busca Inteligente** (Search icon)
2. **Comunicação Automática** (MessageSquare icon)
3. **Agendamento Smart** (Calendar icon)
4. **Analytics Avançado** (BarChart3 icon)
5. **Matching Preciso** (Filter icon)
6. **Alertas Inteligentes** (Bell icon)
7. **Automação Total** (Workflow icon)
8. **Segurança Premium** (Shield icon)

#### Especificações Técnicas
- **Layout**: Grid 2x4 mobile, 4x2 desktop
- **Cards**:
  - Background: white/10 + backdrop-blur
  - Padding: 16px
  - Border-radius: 8px
  - Animation: Scale 0.5 → 1.0, stagger 0.1s
- **Icons**: 32px, cores específicas por categoria
- **Entry Animation**: Cada card aparece com delay incremental

---

### Slide 5: Platform Overview
**Duração**: 6 segundos | **Auto-advance**: Sim

#### Conteúdo
```
Título: "Plataforma Completa"
Descrição: "Tudo que você precisa para revolucionar seu recrutamento em um só lugar."
```

#### Módulos da Plataforma (3 pilares)
1. **Gestão de Talentos**
   - Icon: Users (cyan-300)
   - Descrição: "Pipeline completo de candidatos"

2. **IA Generativa**
   - Icon: Zap (yellow-300)
   - Descrição: "LIA como sua assistente pessoal"

3. **Analytics**
   - Icon: BarChart3 (green-300)
   - Descrição: "Insights e métricas avançadas"

#### Especificações Técnicas
- **Container**: Card centralizado com backdrop-blur
- **Layout**: 3 colunas responsivas
- **Animation**: Scale 0.8 → 1.0 para o container
- **Icons**: 48px com cores específicas
- **Typography**: H4 1xl semibold, P sm opacity-80

---

### Slide 6: Call to Action
**Duração**: Indefinida | **Auto-advance**: Não

#### Conteúdo
```
Título: "Vamos Começar?"
Subtítulo: "Em 3 passos simples"
Descrição: "Configure sua empresa, crie sua primeira vaga e deixe a LIA trabalhar para você."
```

#### Ações Disponíveis
- **Botão Primário**: "Iniciar Setup" (white bg, blue text)
- **Botão Secundário**: "Assistir Demo" (outline white)

#### Especificações Técnicas
- **Animation**: Typewriter effect no título
- **Buttons**:
  - Primary: bg-white, text-blue-600, px-8 py-4, rounded-full
  - Secondary: border-white, text-white, hover:bg-white/10
- **Layout**: Centrado com gap-6 entre botões

---

## 🛠️ Página de Próximos Passos

Após CTA, transição para página com 3 etapas:

### Etapa 1: Configure sua Empresa
- **Icon**: Building
- **Tempo**: 5 min
- **Descrição**: "Dados básicos, cultura e estrutura organizacional"

### Etapa 2: Crie sua Primeira Vaga
- **Icon**: UserPlus
- **Tempo**: 3 min
- **Descrição**: "Defina requisitos e deixe a LIA otimizar a descrição"

### Etapa 3: Ative o Recrutamento
- **Icon**: Rocket
- **Tempo**: 2 min
- **Descrição**: "Publique e comece a receber candidatos qualificados"

---

## 🎬 Especificações de Animação

### Timing Functions
```css
/* Suave entrada */
ease-out: cubic-bezier(0.25, 0.46, 0.45, 0.94)

/* Bounce sutil */
ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55)

/* Material Design */
ease-standard: cubic-bezier(0.4, 0.0, 0.2, 1)
```

### Durations Padrão
- **Micro**: 200ms (hover states)
- **Quick**: 400ms (buttons, small elements)
- **Standard**: 600ms (slide transitions)
- **Slow**: 800ms (complex animations)
- **Deliberate**: 1200ms (storytelling moments)

### Animation States
```javascript
const variants = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  },
  slideUp: {
    initial: { opacity: 0, y: 50 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -50 }
  },
  zoom: {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 1.2 }
  }
}
```

---

## 📱 Responsividade

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Typography Scale
```css
/* Mobile */
.title-mobile { font-size: 3rem; line-height: 1.1; }
.subtitle-mobile { font-size: 1.5rem; line-height: 1.3; }
.description-mobile { font-size: 1.125rem; line-height: 1.5; }

/* Desktop */
.title-desktop { font-size: 5rem; line-height: 1.1; }
.subtitle-desktop { font-size: 2.25rem; line-height: 1.3; }
.description-desktop { font-size: 1.5rem; line-height: 1.5; }
```

### Layout Adaptations
- **Mobile**: Stack vertical, padding reduzido, botões full-width
- **Tablet**: Grid híbrido, espaçamento médio
- **Desktop**: Grid completo, espaçamento generoso

---

## 🔧 Implementação Técnica

### Dependências Essenciais
```json
{
  "framer-motion": "^10.x.x",
  "react": "^18.x.x",
  "tailwindcss": "^3.x.x",
  "lucide-react": "^0.x.x"
}
```

### Estrutura de Arquivos
```
/components/onboarding/
├── onboarding-journey.tsx     # Componente principal
├── slide-backgrounds.tsx      # Backgrounds animados
├── slide-animations.tsx       # Variantes de animação
├── capability-grid.tsx        # Grid de funcionalidades
├── lia-avatar.tsx            # Avatar da LIA
└── step-guide.tsx            # Guia de próximos passos
```

### Configuração de Estado
```typescript
interface OnboardingState {
  currentSlide: number
  isPlaying: boolean
  progress: number
  hasCompletedBefore: boolean
  userRole: string
  companyName: string
}
```

---

## 📊 Métricas e Analytics

### Eventos para Tracking
1. **onboarding_started** - Usuário iniciou o onboarding
2. **slide_completed** - Slide específico foi visualizado completamente
3. **onboarding_skipped** - Usuário pulou o onboarding
4. **onboarding_completed** - Usuário chegou ao final
5. **setup_started** - Usuário clicou "Iniciar Setup"
6. **demo_requested** - Usuário clicou "Assistir Demo"

### KPIs Importantes
- **Completion Rate**: % que chega ao slide final
- **Skip Rate**: % que pula o onboarding
- **Setup Conversion**: % que inicia setup após onboarding
- **Time on Slide**: Tempo médio por slide
- **Drop-off Points**: Slides com maior abandono

---

## 🎨 Assets e Recursos

### Ícones Necessários
- Sparkles, Brain, Rocket (principais)
- Users, Zap, BarChart3, Building, UserPlus (funcionalidades)
- Search, MessageSquare, Calendar, Filter, Bell, Workflow, Shield (capabilities)
- Play, Pause, ChevronLeft, ChevronRight (controles)

### Gradientes Definidos
```css
.gradient-1 { background: linear-gradient(135deg, #2563eb 0%, #9333ea 50%, #3730a3 100%); }
.gradient-2 { background: linear-gradient(45deg, #10b981 0%, #06b6d4 50%, #3b82f6 100%); }
.gradient-3 { background: linear-gradient(135deg, #ef4444 0%, #f97316 50%, #eab308 100%); }
```

### Efeitos Especiais
- **Backdrop Blur**: backdrop-blur-sm, backdrop-blur-lg
- **Glass Effect**: bg-white/10 + backdrop-blur
- **Glow Effect**: box-shadow com cores vibrantes
- **Particle System**: Pontos flutuantes com movimento senoidal

---

## 🚀 Otimizações de Performance

### Lazy Loading
- Carregar apenas slide atual + próximo
- Preload de assets críticos (fontes, ícones)
- Lazy load de animações complexas

### Animação Performance
- Usar `transform` ao invés de propriedades layout
- `will-change` para elementos animados
- `contain: layout style paint` para otimização
- RequestAnimationFrame para animações customizadas

### Bundle Optimization
- Code splitting por slide
- Tree shaking de ícones não utilizados
- Compressão de assets visuais
- Service worker para cache

---

## 🔄 Adaptação para Outras Stacks

### React/Vue/Angular
- Manter estrutura de componentes modular
- Adaptar sistema de estado (Redux/Vuex/NgRx)
- Converter animações para biblioteca específica

### Framework-Agnostic
- Extrair lógica para vanilla JS
- CSS Animations ao invés de JS
- Web Components para reutilização
- JSON config para conteúdo

### Mobile (React Native/Flutter)
- Adaptar animações para mobile APIs
- Gestures para navegação
- Performance otimizada para 60fps
- Tamanhos e layouts responsivos

---

## ✅ Checklist de Implementação

### Funcional
- [ ] Navegação entre slides funcional
- [ ] Auto-advance configurável
- [ ] Controles play/pause
- [ ] Skip functionality
- [ ] Progress tracking
- [ ] Responsive design

### Visual
- [ ] Todas as animações implementadas
- [ ] Backgrounds dinâmicos funcionais
- [ ] Typography consistente
- [ ] Ícones e cores corretas
- [ ] Estados de hover/active

### UX/Performance
- [ ] Loading states
- [ ] Error handling
- [ ] Accessibility (WCAG)
- [ ] Performance 60fps
- [ ] Touch/swipe gestures
- [ ] Keyboard navigation

### Analytics
- [ ] Event tracking implementado
- [ ] Completion metrics
- [ ] A/B testing ready
- [ ] Error monitoring

---

*Documento criado para garantir fidelidade na reprodução do onboarding LIA em qualquer stack tecnológica.*
