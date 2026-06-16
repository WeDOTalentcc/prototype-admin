"use client"

import { Brain, BookOpen, Users, Code, FileText, Clock, ChevronLeft, HelpCircle, Lightbulb, Target, CheckCircle, Fingerprint, AlertTriangle, MessageSquare, TrendingUp, Shield, Compass } from"lucide-react"
import { navigationCatalog } from "@/lib/navigation/navigation-commands"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import Link from"next/link"

export default function AjudaPage() {
  const softSkillsList = ["Comunicação","Liderança","Trabalho em equipe","Negociação","Gestão de tempo","Resolução de problemas","Pensamento crítico","Criatividade","Adaptabilidade","Proatividade","Inteligência emocional","Empatia","Colaboração","Organização","Tomada de decisão","Mentoria","Autonomia","Resiliência"
  ]

  const seniorityLevels = [
    { level:"Júnior", description:"0-2 anos de experiência OU títulos com \"Junior/Jr\"", color:"#4CAF50" },
    { level:"Pleno", description:"2-5 anos de experiência OU sem prefixo de senioridade", color:"#2196F3" },
    { level:"Sênior", description:"5-8 anos de experiência OU títulos com \"Senior/Sr\"", color:"#9C27B0" },
    { level:"Tech Lead", description:"Liderança técnica de equipes", color:"#FF9800" },
    { level:"Manager", description:"Gestão de pessoas e processos", color:"#E91E63" },
    { level:"Diretor", description:"Direção de área ou departamento", color:"#673AB7" },
    { level:"C-Level", description:"Posições executivas (CEO, CTO, CFO, etc.)", color:"#F44336" }
  ]

  const bigFiveDimensions = [
    { trait:"O", name:"Abertura", description:"Curiosidade intelectual, criatividade, receptividade a novas ideias", indicators:"Projetos inovadores, diversidade de experiências, formação contínua" },
    { trait:"C", name:"Conscienciosidade", description:"Organização, disciplina, orientação a resultados", indicators:"Entregas consistentes, progressão de carreira, certificações" },
    { trait:"E", name:"Extroversão", description:"Sociabilidade, assertividade, energia social", indicators:"Liderança de equipes, apresentações, networking" },
    { trait:"A", name:"Amabilidade", description:"Cooperação, empatia, orientação ao coletivo", indicators:"Trabalho em equipe, mentoria, resolução de conflitos" },
    { trait:"N", name:"Neuroticismo", description:"Estabilidade emocional (inverso: baixo N = estável)", indicators:"Resiliência, gestão de pressão, adaptabilidade" }
  ]

  const archetypes = [
    { name:"Catalisador Visionário", profile:"Alto O/E", description:"Inovador, inspirador, busca mudanças", roles:"Fundador, Product Manager, Diretor de Inovação", color:"#FF6B6B" },
    { name:"Executor Confiável", profile:"Alto C/A", description:"Metódico, colaborativo, entrega consistente", roles:"Gerente de Projetos, Analista Sênior, Ops Manager", color:"#2E9E94" },
    { name:"Guardião de Clientes", profile:"Alto A/E", description:"Empático, comunicativo, orientado ao cliente", roles:"Customer Success, Account Manager, Suporte Sênior", color:"#2E97B3" },
    { name:"Estrategista Analítico", profile:"Alto O/C", description:"Pensador profundo, orientado a dados", roles:"Data Scientist, Arquiteto, Pesquisador", color:"#5A9E7E" },
    { name:"Mediador Adaptável", profile:"Alto A/O", description:"Flexível, harmonizador, diplomático", roles:"HRBP, Scrum Master, Consultor", color:"#D4A017" },
    { name:"Rainmaker Audacioso", profile:"Alto E/O", description:"Persuasivo, ambicioso, orientado a resultados", roles:"Vendedor, BD, Founder", color:"#B07AB0" },
    { name:"Operador Resiliente", profile:"Alto C", description:"Estável sob pressão, focado, persistente", roles:"SRE, Suporte Crítico, Operações 24/7", color:"#5BA3C9" },
    { name:"Arquiteto Metódico", profile:"Alto C/O", description:"Detalhista, sistemático, qualidade", roles:"Engenheiro Sênior, QA Lead, Arquiteto de Software", color:"#5DAA96" }
  ]

  return (
    <div className="min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <Link href="/">
            <Button variant="ghost" className="mb-4 text-lia-text-secondary hover:text-lia-text-primary">
              <ChevronLeft className="w-4 h-4 mr-1" />
              Voltar
            </Button>
          </Link>
          
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-md bg-wedo-cyan/15">
              <Brain className="w-8 h-8 text-wedo-cyan" />
            </div>
            <div>
              <h1 className="text-3xl font-semibold text-lia-text-primary dark:text-lia-text-primary">Central de Ajuda</h1>
              <p className="text-lia-text-secondary dark:text-lia-text-tertiary">Entenda como a IA analisa candidatos</p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-lia-text-primary" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Navegar com a IA</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-lia-text-secondary space-y-3">
              <p>Peça à IA no chat para te levar a qualquer página — ou digite <span className="font-mono text-lia-text-primary">Ctrl + /</span> para ver os comandos. Exemplos:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {navigationCatalog().map((item) => (
                  <div key={item.page} className="flex items-center gap-2 rounded-md border border-lia-border-subtle px-3 py-2">
                    <Compass className="w-3.5 h-3.5 text-wedo-cyan shrink-0" />
                    <span className="text-sm text-lia-text-primary">&quot;me leve para {item.label}&quot;</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-lia-text-primary" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Como a IA Analisa Candidatos</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-lia-text-secondary space-y-3">
              <p>
                A IA utiliza inteligência artificial avançada para <strong>extrair e inferir informações</strong> a partir de currículos e perfis profissionais. O processo combina técnicas de processamento de linguagem natural (NLP) com análise semântica para compreender o contexto e significado das informações.
              </p>
              <p>
                Cada currículo passa por um pipeline de análise que identifica automaticamente experiências profissionais, formações acadêmicas, habilidades técnicas e comportamentais, além de inferir o nível de senioridade do candidato.
              </p>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-lia-text-primary" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Classificação de Senioridade</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-lia-text-secondary mb-4">
                A senioridade é determinada com base na combinação de anos de experiência e títulos dos cargos ocupados:
              </p>
              <div className="space-y-3">
                {seniorityLevels.map((item) => (
                  <div key={item.level} className="flex items-start gap-3 p-3 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                    <Chip
                      density="relaxed"
                      variant="neutral"
                      muted
                      className="mt-0.5 text-white"
                      style={{backgroundColor: item.color}}
                    >
                      {item.level}
                    </Chip>
                    <span className="text-lia-text-secondary dark:text-lia-text-tertiary">{item.description}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-lia-text-primary" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Classificação de Skills</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold text-lia-text-primary mb-2 flex items-center gap-2">
                  <Code className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  Technical Skills (Habilidades Técnicas)
                </h4>
                <p className="text-lia-text-secondary mb-2">
                  Incluem linguagens de programação, frameworks, ferramentas, bancos de dados e metodologias técnicas. Exemplos:
                </p>
                <div className="flex flex-wrap gap-2">
                  {["Python","JavaScript","React","Node.js","PostgreSQL","Docker","AWS","Git"].map((skill) => (
                    <Chip density="relaxed" key={skill} variant="neutral" className="border-lia-btn-primary-bg dark:border-lia-border-subtle bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary">
                      {skill}
                    </Chip>
                  ))}
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-semibold text-lia-text-primary mb-2 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Soft Skills (Competências Comportamentais)
                </h4>
                <p className="text-lia-text-secondary mb-2">
                  Habilidades identificadas pela IA:
                </p>
                <div className="flex flex-wrap gap-2">
                  {softSkillsList.map((skill) => (
                    <Chip 
                      key={skill} 
                      variant="danger" 
                      className="text-xs bg-status-error-bg"
                    >
                      {skill}
                    </Chip>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-lia-text-primary" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Campos Extraídos vs Inferidos</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold text-lia-text-primary mb-2 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-status-success" />
                  Extraídos Diretamente do Currículo
                </h4>
                <p className="text-lia-text-secondary mb-2">
                  Informações encontradas explicitamente no documento:
                </p>
                <div className="flex flex-wrap gap-2">
                  {["Nome","Email","Telefone","Experiências profissionais","Educação","Certificações","Idiomas"].map((field) => (
                    <Chip density="relaxed" key={field} variant="success" >
                      {field}
                    </Chip>
                  ))}
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-semibold text-lia-text-primary mb-2 flex items-center gap-2">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  Inferidos pela IA
                </h4>
                <p className="text-lia-text-secondary mb-2">
                  Informações calculadas ou deduzidas pela análise inteligente:
                </p>
                <div className="flex flex-wrap gap-2">
                  {["Senioridade (baseada em título + anos)","Classificação de skills","Interesses profissionais","Fit cultural","Potencial de crescimento"].map((field) => (
                    <Chip 
                      key={field} 
                      variant="neutral" 
                      className="text-xs text-lia-text-muted border-wedo-cyan/30"
                    >
                      {field}
                    </Chip>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-lia-text-primary" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Cálculo de Anos de Experiência</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-lia-text-secondary space-y-3">
              <p>
                O cálculo de anos de experiência é realizado a partir das <strong>datas reais de início e término</strong> de cada experiência profissional registrada no currículo.
              </p>
              <div className="p-4 rounded-xl bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30">
                <p className="text-status-warning dark:text-status-warning flex items-start gap-2">
                  <HelpCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Importante:</strong> Períodos sobrepostos (experiências paralelas) não são contabilizados em duplicidade. A IA identifica automaticamente trabalhos simultâneos e calcula o tempo real de experiência profissional.
                  </span>
                </p>
              </div>
              <div className="mt-4">
                <h4 className="font-semibold text-lia-text-primary mb-2">Exemplo de cálculo:</h4>
                <div className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-3 rounded-xl text-sm">
                  <p className="mb-1">Experiência 1: Jan/2018 - Dez/2020 (3 anos)</p>
                  <p className="mb-1">Experiência 2: Jun/2020 - Atual (4.5 anos)</p>
                  <p className="font-semibold mt-2 text-lia-text-primary">
                    Total calculado: 6.5 anos (não 7.5, pois 6 meses são sobrepostos)
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle my-8 pt-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 rounded-md bg-wedo-cyan/15">
                <Fingerprint className="w-6 h-6 text-lia-text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">Análise de Perfil de Personalidade</h2>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Inferência probabilística baseada no modelo Big Five (OCEAN)</p>
              </div>
            </div>
          </div>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-wedo-cyan" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">O Modelo Big Five (OCEAN)</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-lia-text-secondary space-y-4">
              <p>
                O <strong>Big Five</strong> é o modelo científico mais validado para avaliação de personalidade, utilizado em mais de 3.000 estudos acadêmicos. A IA utiliza este framework para inferir tendências comportamentais dos candidatos através de análise probabilística.
              </p>
              <div className="space-y-3">
                {bigFiveDimensions.map((dim) => (
                  <div key={dim.trait} className="p-3 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="flex items-start gap-3">
                      <Chip
                        density="relaxed"
                        variant="info"
                      >
                        {dim.trait}
                      </Chip>
                      <div className="flex-1">
                        <h4 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">{dim.name}</h4>
                        <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary mb-1">{dim.description}</p>
                        <p className="text-xs text-lia-text-secondary dark:text-lia-text-secondary">
                          <span className="font-medium">Indicadores:</span> {dim.indicators}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-lia-text-primary" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Como a IA Infere a Personalidade</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lia-text-secondary">
                A análise é baseada em múltiplas fontes de dados, combinando sinais comportamentais para gerar uma estimativa probabilística do perfil:
              </p>
              
              <div className="grid gap-3">
                <div className="flex items-start gap-3 p-3 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <FileText className="w-5 h-5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
                  <div>
                    <h4 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Texto e Estrutura do CV</h4>
                    <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                      Análise do vocabulário utilizado, tom de comunicação, forma de apresentar conquistas e nível de detalhamento das descrições.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <Target className="w-5 h-5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
                  <div>
                    <h4 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Padrões de Progressão de Carreira</h4>
                    <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                      Velocidade de crescimento, mudanças laterais vs. verticais, estabilidade em posições e transições entre áreas.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <Users className="w-5 h-5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
                  <div>
                    <h4 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Escolhas de Empresas e Cargos</h4>
                    <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                      Tipos de empresas (startup vs. corporação), setores escolhidos, natureza dos cargos (individual contributor vs. gestão).
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary">
                  <MessageSquare className="w-5 h-5 mt-0.5 flex-shrink-0 text-lia-text-primary" />
                  <div>
                    <h4 className="font-semibold text-lia-text-primary dark:text-lia-text-primary">Estilo de Comunicação</h4>
                    <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                      Assertividade na escrita, uso de primeira pessoa vs. coletivo, foco em resultados quantitativos vs. qualitativos.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-wedo-cyan" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Os 8 Arquétipos Profissionais</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lia-text-secondary">
                Com base nas combinações das 5 dimensões, a IA identifica 8 arquétipos profissionais que ajudam a prever o fit para diferentes tipos de posições:
              </p>
              
              <div className="grid gap-3 sm:grid-cols-2">
                {archetypes.map((archetype) => (
                  <div 
                    key={archetype.name} 
                    className="p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle"
                    style={{backgroundColor: `${archetype.color}10`}}
                  >
                    <div className="flex items-start gap-2 mb-2">
                      <Chip variant="neutral" muted 
                        className="text-white font-medium text-xs px-2 py-0.5"
                        style={{backgroundColor: archetype.color}}
                      >
                        {archetype.profile}
                      </Chip>
                    </div>
                    <h4 className="font-semibold text-lia-text-primary dark:text-lia-text-primary text-sm">{archetype.name}</h4>
                    <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary mb-1">{archetype.description}</p>
                    <p className="text-xs text-lia-text-secondary dark:text-lia-text-secondary">
                      <span className="font-medium">Ideal para:</span> {archetype.roles}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle border-status-warning/30 dark:border-status-warning/30">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-status-warning" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Limitações Importantes</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-xl bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30">
                <p className="text-status-warning dark:text-status-warning text-sm">
                  <strong>Esta é uma inferência probabilística, não uma avaliação clínica.</strong> Os perfis gerados pela IA são estimativas baseadas em padrões observáveis, não diagnósticos psicológicos formais.
                </p>
              </div>
              
              <div className="space-y-2 text-lia-text-secondary text-sm">
                <p className="flex items-start gap-2">
                  <Shield className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-tertiary" />
                  <span>Os scores devem ser usados como <strong>indicadores complementares</strong>, não como critérios eliminatórios únicos.</span>
                </p>
                <p className="flex items-start gap-2">
                  <Shield className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-tertiary" />
                  <span>A personalidade é <strong>contextual e dinâmica</strong> — pessoas podem se comportar diferentemente em diferentes ambientes.</span>
                </p>
                <p className="flex items-start gap-2">
                  <Shield className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-tertiary" />
                  <span>CVs refletem <strong>auto-apresentação</strong>, que pode diferir do comportamento real no trabalho.</span>
                </p>
                <p className="flex items-start gap-2">
                  <Shield className="w-4 h-4 mt-0.5 flex-shrink-0 text-lia-text-tertiary" />
                  <span>Recomendamos sempre <strong>validar inferências</strong> com entrevistas estruturadas e referências.</span>
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-lia-border-subtle">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-status-success" />
                <CardTitle className="text-lg font-semibold text-lia-text-primary">Como Melhorar a Precisão com WSI</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-lia-text-secondary">
                O <strong>WSI (Work Sample Interview)</strong> é nossa metodologia de triagem que aumenta significativamente a precisão das inferências de personalidade:
              </p>
              
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="p-3 rounded-xl bg-status-success/10 dark:bg-status-success/20 border border-status-success/30 dark:border-status-success/30">
                  <h4 className="font-semibold text-status-success dark:text-status-success text-sm mb-1">Antes do WSI</h4>
                  <p className="text-xs text-status-success dark:text-status-success">
                    Inferências baseadas apenas em dados estáticos do CV (precisão ~65%)
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-status-success/10 dark:bg-status-success/20 border border-status-success/30 dark:border-status-success/30">
                  <h4 className="font-semibold text-status-success dark:text-status-success text-sm mb-1">Após o WSI</h4>
                  <p className="text-xs text-status-success dark:text-status-success">
                    Validação com comportamento real em situações simuladas (precisão ~85%)
                  </p>
                </div>
              </div>

              <div className="text-lia-text-secondary text-sm space-y-2">
                <p>
                  O WSI combina a <strong>Taxonomia de Bloom</strong> (níveis cognitivos) com o <strong>Modelo Dreyfus</strong> (proficiência) para avaliar como o candidato pensa e resolve problemas reais.
                </p>
                <p>
                  As respostas do candidato durante a triagem fornecem sinais comportamentais adicionais que refinam e validam as inferências iniciais do Big Five.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-8 text-center text-lia-text-secondary text-sm">
          <p>Precisa de mais ajuda? Entre em contato com nossa equipe de suporte.</p>
        </div>
      </div>
    </div>
  )
}
