"use client"

import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  CheckCircle, AlertTriangle, X, Check, Info, RefreshCw,
  AlertCircle, Clock, Zap, Shield, Search, Eye, EyeOff,
  Settings, Lightbulb, Target, Globe, Mail, Phone
} from "lucide-react"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

interface ValidationRule {
  field: string
  type: 'required' | 'email' | 'cnpj' | 'phone' | 'url' | 'custom' | 'minLength' | 'maxLength' | 'pattern'
  message: string
  pattern?: string
  minLength?: number
  maxLength?: number
  validator?: (value: unknown) => boolean | Promise<boolean>
  severity: 'error' | 'warning' | 'info'
  category: 'required' | 'format' | 'business' | 'security' | 'compliance'
}

interface ValidationResult {
  field: string
  isValid: boolean
  message?: string
  severity: 'error' | 'warning' | 'info' | 'success'
  suggestions?: string[]
  correctedValue?: string
}

interface ValidationSystemProps {
  data: {[key: string]: unknown}
  section: string
  onValidationChange: (results: ValidationResult[]) => void
  onAutoCorrect?: (field: string, correctedValue: string) => void
}

// Regras de validação por seção
const validationRules: {[section: string]: ValidationRule[]} = {
  institutional: [
    {
      field: 'company_name',
      type: 'required',
      message: 'Nome da empresa é obrigatório',
      severity: 'error',
      category: 'required'
    },
    {
      field: 'company_name',
      type: 'minLength',
      minLength: 2,
      message: 'Nome da empresa deve ter pelo menos 2 caracteres',
      severity: 'error',
      category: 'format'
    },
    {
      field: 'cnpj',
      type: 'cnpj',
      pattern: '^\\d{2}\\.\\d{3}\\.\\d{3}/\\d{4}-\\d{2}$',
      message: 'CNPJ deve ter formato XX.XXX.XXX/XXXX-XX',
      severity: 'error',
      category: 'format'
    },
    {
      field: 'website',
      type: 'url',
      pattern: '^https?://[^\\s/$.?#].[^\\s]*$',
      message: 'Website deve ser uma URL válida (começando com http:// ou https://)',
      severity: 'warning',
      category: 'format'
    },
    {
      field: 'email',
      type: 'email',
      pattern: '^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$',
      message: 'Email deve ter formato válido',
      severity: 'error',
      category: 'format'
    },
    {
      field: 'phone',
      type: 'phone',
      pattern: '^\\+?[1-9]\\d{1,14}$',
      message: 'Telefone deve ter formato válido',
      severity: 'warning',
      category: 'format'
    }
  ],
  culture: [
    {
      field: 'mission',
      type: 'required',
      message: 'Missão é obrigatória',
      severity: 'error',
      category: 'required'
    },
    {
      field: 'mission',
      type: 'minLength',
      minLength: 20,
      message: 'Missão deve ter pelo menos 20 caracteres para ser significativa',
      severity: 'warning',
      category: 'business'
    },
    {
      field: 'vision',
      type: 'required',
      message: 'Visão é obrigatória',
      severity: 'error',
      category: 'required'
    },
    {
      field: 'vision',
      type: 'minLength',
      minLength: 20,
      message: 'Visão deve ter pelo menos 20 caracteres para ser significativa',
      severity: 'warning',
      category: 'business'
    },
    {
      field: 'values',
      type: 'required',
      message: 'Pelo menos um valor deve ser definido',
      severity: 'error',
      category: 'required'
    }
  ],
  users: [
    {
      field: 'user_email',
      type: 'email',
      pattern: '^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$',
      message: 'Email do usuário deve ter formato válido',
      severity: 'error',
      category: 'format'
    },
    {
      field: 'user_name',
      type: 'required',
      message: 'Nome do usuário é obrigatório',
      severity: 'error',
      category: 'required'
    },
    {
      field: 'user_role',
      type: 'required',
      message: 'Cargo do usuário é obrigatório',
      severity: 'error',
      category: 'required'
    },
    {
      field: 'permissions',
      type: 'custom',
      validator: (value) => Array.isArray(value) && value.length > 0,
      message: 'Usuário deve ter pelo menos uma permissão',
      severity: 'warning',
      category: 'security'
    }
  ],
  security: [
    {
      field: 'password_policy',
      type: 'required',
      message: 'Política de senhas deve ser definida',
      severity: 'error',
      category: 'security'
    },
    {
      field: 'two_factor_auth',
      type: 'required',
      message: 'Autenticação em dois fatores é recomendada',
      severity: 'warning',
      category: 'security'
    },
    {
      field: 'session_timeout',
      type: 'custom',
      // @ts-ignore TODO: fix type — 'value' is of type 'unknown'.
      // @ts-ignore TODO: fix type — 'value' is of type 'unknown'.
      validator: (value) => value > 0 && value <= 480, // max 8 hours
      message: 'Timeout de sessão deve ser entre 1 e 480 minutos',
      severity: 'warning',
      category: 'security'
    }
  ]
}

// Funções de validação específicas
const validators = {
  cnpj: (value: string): boolean => {
    if (!value) return false
    const cleanCNPJ = value.replace(/[^\d]/g, '')
    if (cleanCNPJ.length !== 14) return false

    // Validação básica de CNPJ (algoritmo simplificado)
    const invalidCNPJs = [
      '00000000000000', '11111111111111', '22222222222222',
      '33333333333333', '44444444444444', '55555555555555',
      '66666666666666', '77777777777777', '88888888888888',
      '99999999999999'
    ]

    return !invalidCNPJs.includes(cleanCNPJ)
  },

  email: (value: string): boolean => {
    if (!value) return false
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(value)
  },

  url: (value: string): boolean => {
    if (!value) return true // URL é opcional geralmente
    try {
      new URL(value)
      return true
    } catch {
      return false
    }
  },

  phone: (value: string): boolean => {
    if (!value) return true // Phone é opcional geralmente
    const phoneRegex = /^\+?[1-9]\d{1,14}$/
    const cleanPhone = value.replace(/[^\d+]/g, '')
    return phoneRegex.test(cleanPhone)
  }
}

// Auto-correções sugeridas
const autoCorrections = {
  cnpj: (value: string): string => {
    const cleanValue = value.replace(/[^\d]/g, '')
    if (cleanValue.length === 14) {
      return cleanValue.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
    }
    return value
  },

  website: (value: string): string => {
    if (value && !value.startsWith('http://') && !value.startsWith('https://')) {
      return `https://${value}`
    }
    return value
  },

  phone: (value: string): string => {
    const cleanValue = value.replace(/[^\d+]/g, '')
    if (cleanValue.length === 11 && !cleanValue.startsWith('+')) {
      return `+55${cleanValue}`
    }
    return value
  }
}

export function ValidationSystem({ data, section, onValidationChange, onAutoCorrect }: ValidationSystemProps) {
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(true)
  const [autoCorrectEnabled, setAutoCorrectEnabled] = useState(true)

  // Executar validação
  const validateData = useCallback(async () => {
    setIsValidating(true)
    const rules = validationRules[section] || []
    const results: ValidationResult[] = []

    for (const rule of rules) {
      const value = data[rule.field]
      let isValid = true
      let message = ''
      const suggestions: string[] = []
      let correctedValue: string | undefined

      try {
        switch (rule.type) {
          case 'required':
            isValid = value !== undefined && value !== null && value.toString().trim() !== ''
            break

          case 'email':
            // @ts-ignore TODO: fix type — Argument of type 'unknown' is not assignable to parameter of type 'string'.
            isValid = validators.email(value)
            if (!isValid && value) {
              suggestions.push('Verifique se o email contém @ e um domínio válido')
            }
            break

          case 'cnpj':
            // @ts-ignore TODO: fix type — Argument of type 'unknown' is not assignable to parameter of type 'string'.
            isValid = validators.cnpj(value)
            if (!isValid && value && autoCorrectEnabled) {
              // @ts-ignore TODO: fix type — Argument of type '{}' is not assignable to parameter of type 'string'.
              correctedValue = autoCorrections.cnpj(value)
              if (validators.cnpj(correctedValue)) {
                isValid = true
                suggestions.push('CNPJ formatado automaticamente')
              }
            }
            break

          case 'url':
            // @ts-ignore TODO: fix type — Argument of type 'unknown' is not assignable to parameter of type 'string'.
            isValid = validators.url(value)
            if (!isValid && value && autoCorrectEnabled) {
              // @ts-ignore TODO: fix type — Argument of type '{}' is not assignable to parameter of type 'string'.
              correctedValue = autoCorrections.website(value)
              if (validators.url(correctedValue)) {
                isValid = true
                suggestions.push('Protocolo https:// adicionado automaticamente')
              }
            }
            break

          case 'phone':
            // @ts-ignore TODO: fix type — Argument of type 'unknown' is not assignable to parameter of type 'string'.
            isValid = validators.phone(value)
            if (!isValid && value && autoCorrectEnabled) {
              // @ts-ignore TODO: fix type — Argument of type '{}' is not assignable to parameter of type 'string'.
              correctedValue = autoCorrections.phone(value)
              if (validators.phone(correctedValue)) {
                isValid = true
                suggestions.push('Código do país (+55) adicionado automaticamente')
              }
            }
            break

          case 'minLength':
            isValid = !value || value.toString().length >= (rule.minLength || 0)
            if (!isValid) {
              suggestions.push(`Adicione pelo menos ${(rule.minLength || 0) - (value?.toString().length || 0)} caracteres`)
            }
            break

          case 'maxLength':
            isValid = !value || value.toString().length <= (rule.maxLength || Infinity)
            if (!isValid) {
              suggestions.push(`Remova ${(value?.toString().length || 0) - (rule.maxLength || 0)} caracteres`)
            }
            break

          case 'pattern':
            if (rule.pattern && value) {
              const regex = new RegExp(rule.pattern)
              // @ts-ignore TODO: fix type — Argument of type '{}' is not assignable to parameter of type 'string'.
              isValid = regex.test(value)
            }
            break

          case 'custom':
            if (rule.validator) {
              const result = rule.validator(value)
              isValid = result instanceof Promise ? await result : result
            }
            break

          default:
            isValid = true
        }

        if (!isValid) {
          message = rule.message
        }

        results.push({
          field: rule.field,
          isValid,
          message: isValid ? undefined : message,
          severity: isValid ? 'success' : rule.severity,
          suggestions: suggestions.length > 0 ? suggestions : undefined,
          correctedValue
        })

        // Auto-aplicar correções se habilitado
        if (correctedValue && onAutoCorrect && autoCorrectEnabled) {
          onAutoCorrect(rule.field, correctedValue)
        }

      } catch (error) {
        results.push({
          field: rule.field,
          isValid: false,
          message: 'Erro na validação deste campo',
          severity: 'error'
        })
      }
    }

    setValidationResults(results)
    onValidationChange(results)
    setIsValidating(false)
  }, [data, section, onValidationChange, onAutoCorrect, autoCorrectEnabled])

  // Executar validação quando os dados mudarem
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      validateData()
    }, 300) // Debounce de 300ms

    return () => clearTimeout(debounceTimer)
  }, [validateData])

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return `${badgeStyles.error} border-status-error/30`
      case 'warning': return `${badgeStyles.warning} border-status-warning/30`
      case 'info': return `${badgeStyles.info} border-wedo-cyan/30`
      case 'success': return `${badgeStyles.success} border-status-success/30`
      default: return `${badgeStyles.default} border-lia-border-subtle`
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error': return AlertCircle
      case 'warning': return AlertTriangle
      case 'info': return Info
      case 'success': return CheckCircle
      default: return Info
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'required': return badgeStyles.error
      case 'format': return badgeStyles.info
      case 'business': return 'bg-gray-100 text-lia-text-primary dark:bg-lia-bg-secondary'
      case 'security': return badgeStyles.warning
      case 'compliance': return badgeStyles.success
      default: return badgeStyles.default
    }
  }

  const errorResults = validationResults.filter(r => !r.isValid && r.severity === 'error')
  const warningResults = validationResults.filter(r => !r.isValid && r.severity === 'warning')
  const successResults = validationResults.filter(r => r.isValid)

  return (
    <Card className="mb-6 dark:bg-lia-bg-primary dark:border-lia-border-subtle">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-xs">
            <Shield className="w-5 h-5 text-lia-text-secondary" />
            Sistema de Validação
            {isValidating && <RefreshCw className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSuggestions(!showSuggestions)}
              className="gap-2"
            >
              {showSuggestions ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              {showSuggestions ? 'Ocultar' : 'Mostrar'} Sugestões
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoCorrectEnabled(!autoCorrectEnabled)}
              className={`gap-2 ${autoCorrectEnabled ? 'bg-status-success/10 text-status-success' : ''}`}
            >
              <Zap className="w-3 h-3" />
              Auto-correção {autoCorrectEnabled ? 'ON' : 'OFF'}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Resumo */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-xl font-bold text-status-error">{errorResults.length}</div>
            <div className={textStyles.description}>Erros</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-status-warning">{warningResults.length}</div>
            <div className={textStyles.description}>Avisos</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-status-success">{successResults.length}</div>
            <div className={textStyles.description}>Válidos</div>
          </div>
        </div>

        {/* Resultados de Validação */}
        <div className="space-y-3">
          {validationResults.filter(r => !r.isValid).map((result, index) => {
            const SeverityIcon = getSeverityIcon(result.severity)
            const rule = validationRules[section]?.find(r => r.field === result.field)

            return (
              <div key={`${result.field}-${index}`} className={`p-4 rounded-md border ${getSeverityColor(result.severity)}`}>
                <div className="flex items-start gap-3">
                  <SeverityIcon className="w-5 h-5 mt-0.5" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium capitalize">
                        {result.field.replace('_', ' ')}
                      </span>
                      {rule && (
                        <Badge className={`text-xs ${getCategoryColor(rule.category)}`}>
                          {rule.category}
                        </Badge>
                      )}
                    </div>

                    {result.message && (
                      <p className="text-xs mb-2">{result.message}</p>
                    )}

                    {showSuggestions && result.suggestions && result.suggestions.length > 0 && (
                      <div className="bg-lia-bg-primary bg-opacity-50 rounded-md p-2 mt-2">
                        <div className="flex items-center gap-1 mb-1">
                          <Lightbulb className="w-3 h-3" />
                          <span className="text-xs font-medium">Sugestões:</span>
                        </div>
                        <ul className="text-xs space-y-1">
                          {result.suggestions.map((suggestion, idx) => (
                            <li key={idx} className="flex items-center gap-1">
                              <span className="w-1 h-1 bg-current rounded-full"></span>
                              {suggestion}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {result.correctedValue && onAutoCorrect && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs">Correção sugerida:</span>
                        <code className="text-xs bg-lia-bg-primary bg-opacity-50 px-2 py-1 rounded-full">
                          {result.correctedValue}
                        </code>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onAutoCorrect(result.field, result.correctedValue!)}
                          className="text-xs h-6"
                        >
                          Aplicar
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          })}

          {validationResults.filter(r => !r.isValid).length === 0 && (
            <div className="text-center py-6">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 text-status-success" />
              <h3 className={`${textStyles.subtitle} mb-1`}>Tudo Validado!</h3>
              <p className={textStyles.description}>Todos os campos estão corretos para esta seção.</p>
            </div>
          )}
        </div>

        {/* Botões de Ação */}
        <div className="flex items-center justify-between pt-4 border-t border-lia-border-subtle mt-6">
          <div className={textStyles.description}>
            Última validação: {new Date().toLocaleTimeString('pt-BR')}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={validateData} disabled={isValidating}>
              <RefreshCw className={`w-3 h-3 mr-1 ${isValidating ? 'animate-spin motion-reduce:animate-none' : ''}`} />
              Revalidar
            </Button>
            <Button size="sm" disabled={errorResults.length > 0}>
              <Target className="w-3 h-3 mr-1" />
              Seção Válida
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
