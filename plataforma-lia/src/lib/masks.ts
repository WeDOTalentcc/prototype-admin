/**
 * Utilitários de máscara para campos de formulário brasileiros
 * Implementação própria — sem dependências externas
 */

export function maskCPF(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 11)
  if (digits.length <= 3) return digits
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9)}`
}

export function maskCNPJ(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 14)
  if (digits.length <= 2) return digits
  if (digits.length <= 5) return `${digits.slice(0, 2)}.${digits.slice(2)}`
  if (digits.length <= 8) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5)}`
  if (digits.length <= 12) return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8)}`
  return `${digits.slice(0, 2)}.${digits.slice(2, 5)}.${digits.slice(5, 8)}/${digits.slice(8, 12)}-${digits.slice(12)}`
}

export function maskPhone(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 11)
  if (digits.length <= 2) return `(${digits}`
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`
  if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`
}

export function maskCEP(value: string): string {
  const digits = value.replace(/\D/g, '').slice(0, 8)
  if (digits.length <= 5) return digits
  return `${digits.slice(0, 5)}-${digits.slice(5)}`
}

export function maskCurrency(value: string): string {
  const digits = value.replace(/\D/g, '')
  const number = parseInt(digits || '0', 10) / 100
  return number.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

/** Valida CPF (algoritmo oficial) */
export function isValidCPF(cpf: string): boolean {
  const digits = cpf.replace(/\D/g, '')
  if (digits.length !== 11 || /^(\d)\1+$/.test(digits)) return false
  const calc = (n: number) => {
    let sum = 0
    for (let i = 0; i < n; i++) sum += parseInt(digits[i]) * (n + 1 - i)
    const remainder = (sum * 10) % 11
    return remainder >= 10 ? 0 : remainder
  }
  return calc(9) === parseInt(digits[9]) && calc(10) === parseInt(digits[10])
}

/** Valida CNPJ (algoritmo oficial) */
export function isValidCNPJ(cnpj: string): boolean {
  const digits = cnpj.replace(/\D/g, '')
  if (digits.length !== 14 || /^(\d)\1+$/.test(digits)) return false
  const calc = (size: number) => {
    let sum = 0
    let pos = size - 7
    for (let i = size; i >= 1; i--) {
      sum += parseInt(digits[size - i]) * pos--
      if (pos < 2) pos = 9
    }
    return sum % 11 < 2 ? 0 : 11 - (sum % 11)
  }
  return calc(12) === parseInt(digits[12]) && calc(13) === parseInt(digits[13])
}
