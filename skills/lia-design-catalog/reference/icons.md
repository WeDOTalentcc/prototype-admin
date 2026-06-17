# Icons Catalog Reference - Design System LIA v4.1

## Specs
| Propriedade | Valor |
|-------------|-------|
| **Biblioteca** | Lucide Icons (React/Vue) ou Material Design Icons (Vuetify) |
| **Tamanhos** | 16px (small), 20px (default), 24px (large), 32px (xlarge) |
| **Stroke Width** | 2px (padrão), 1.5px (sutis) |
| **Cor** | Inherit from parent ou gray-600 |

## Navigation Icons (24px)
| Ícone | Lucide | Material | Quando Usar |
|-------|--------|----------|-------------|
| Home | `Home` | `mdi-home` | Dashboard, página inicial |
| Analytics | `BarChart` | `mdi-chart-bar` | Analytics, relatórios |
| Team | `Users` | `mdi-account-group` | Candidatos, equipe |
| Jobs | `Briefcase` | `mdi-briefcase` | Vagas, trabalho |
| Settings | `Settings` | `mdi-cog` | Configurações |
| Notifications | `Bell` | `mdi-bell` | Notificações |

## Action Icons (20px)
| Ícone | Lucide | Material | Quando Usar |
|-------|--------|----------|-------------|
| Edit | `Edit` | `mdi-pencil` | Editar registro |
| Delete | `Trash` | `mdi-delete` | Deletar |
| Copy | `Copy` | `mdi-content-copy` | Copiar texto/dados |
| Save | `Save` | `mdi-content-save` | Salvar mudanças |
| Close | `X` | `mdi-close` | Fechar, cancelar |
| Confirm | `Check` | `mdi-check` | Confirmar, concluir |
| Download | `Download` | `mdi-download` | Baixar arquivo |
| Upload | `Upload` | `mdi-upload` | Enviar arquivo |
| Search | `Search` | `mdi-magnify` | Buscar |
| Add | `Plus` | `mdi-plus` | Adicionar novo |

## Status Icons (16px) - with semantic colors
| Ícone | Lucide | Material | Quando Usar | Cor |
|-------|--------|----------|-------------|-----|
| Success | `CheckCircle` | `mdi-check-circle` | Sucesso, aprovado | green-600 |
| Warning | `AlertTriangle` | `mdi-alert` | Aviso, atenção | amber-600 |
| Error | `XCircle` | `mdi-close-circle` | Erro, rejeitado | red-600 |
| Info | `Info` | `mdi-information` | Informação | blue-600 |
| Time | `Clock` | `mdi-clock` | Tempo, prazo | orange-600 |

## Special WeDo Icons
| Ícone | Lucide | Material | Quando Usar | Cor |
|-------|--------|----------|-------------|-----|
| **LIA/AI** | `Brain` | `mdi-brain` | LIA, IA, automação | **cyan #60BED1** |
| Candidate | `User` | `mdi-account` | Perfil, candidato | green #5DA47A |
| Insights | `Lightbulb` | `mdi-lightbulb` | Insights, sugestões | purple #9860D1 |
| Goals | `Target` | `mdi-target` | Metas, objetivos | magenta #D160AB |

**Brain icon ALWAYS cyan #60BED1. NEVER black/gray.**

## Usage
```html
<!-- React -->
<Brain className="w-6 h-6 text-[#60BED1]" />
<CheckCircle className="w-4 h-4 text-green-600" />
<Edit className="w-5 h-5 text-gray-600" />

<!-- Vue -->
<Brain :size="24" color="#60BED1" />
<CheckCircle :size="16" class="text-green-600" />

<!-- Vuetify -->
<v-icon color="accent" size="24">mdi-brain</v-icon>
<v-icon color="green" size="16">mdi-check-circle</v-icon>
```
