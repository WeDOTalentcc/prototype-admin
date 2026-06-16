export const CLEAR_CHAT_COMMANDS = [
  'limpar',
  'limpar chat',
  'limpar conversa',
  'nova conversa',
  'resetar',
  'resetar chat',
  'clear',
  'clear chat',
]

export function isClearChatCommand(text: string): boolean {
  return CLEAR_CHAT_COMMANDS.includes(text.trim().toLowerCase())
}
