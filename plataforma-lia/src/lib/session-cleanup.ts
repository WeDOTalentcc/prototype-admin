/**
 * Limpa todos os dados de sessão do localStorage ao fazer logout
 * Garante que dados do usuário anterior não persistam
 */

// Chaves que devem ser preservadas após logout (ex: preferências de UI)
const PRESERVED_KEYS = [
  'theme',                  // preferência de tema
]

export function clearSessionStorage(): void {
  const preserved: Record<string, string> = {}

  // Salvar chaves preservadas
  PRESERVED_KEYS.forEach(key => {
    const value = localStorage.getItem(key)
    if (value !== null) preserved[key] = value
  })

  // Limpar tudo
  localStorage.clear()

  // Restaurar chaves preservadas
  Object.entries(preserved).forEach(([key, value]) => {
    localStorage.setItem(key, value)
  })
}
