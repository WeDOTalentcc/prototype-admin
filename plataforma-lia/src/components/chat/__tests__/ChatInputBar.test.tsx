import { render, screen, fireEvent } from '@testing-library/react'
import { ChatInputBar } from '../chat-input-bar'

vi.mock('@/lib/utils', () => ({
  cn: (...args: (string | boolean | undefined | null)[]) => args.filter(Boolean).join(' '),
}))

vi.mock('lucide-react', () => ({
  Send: () => <span data-testid="icon-send" />,
  Mic: () => <span data-testid="icon-mic" />,
  Loader2: () => <span data-testid="icon-loader" />,
}))

describe('ChatInputBar', () => {
  const onSend = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders textarea with correct placeholder', () => {
    render(<ChatInputBar onSend={onSend} />)
    expect(screen.getByLabelText('Mensagem para a LIA')).toBeTruthy()
  })

  it('renders custom placeholder', () => {
    render(<ChatInputBar onSend={onSend} placeholder="Custom..." />)
    const textarea = screen.getByLabelText('Mensagem para a LIA')
    expect(textarea.getAttribute('placeholder')).toBe('Custom...')
  })

  it('send button is disabled when input is empty', () => {
    render(<ChatInputBar onSend={onSend} />)
    const sendBtn = screen.getByLabelText('Enviar mensagem')
    expect(sendBtn).toBeDisabled()
  })

  it('send button becomes enabled when text is entered', () => {
    render(<ChatInputBar onSend={onSend} />)
    const textarea = screen.getByLabelText('Mensagem para a LIA')
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    const sendBtn = screen.getByLabelText('Enviar mensagem')
    expect(sendBtn).not.toBeDisabled()
  })

  it('calls onSend with trimmed message on click', () => {
    render(<ChatInputBar onSend={onSend} />)
    const textarea = screen.getByLabelText('Mensagem para a LIA')
    fireEvent.change(textarea, { target: { value: '  Hello LIA  ' } })
    const sendBtn = screen.getByLabelText('Enviar mensagem')
    fireEvent.click(sendBtn)
    expect(onSend).toHaveBeenCalledWith('Hello LIA')
  })

  it('clears input after sending', () => {
    render(<ChatInputBar onSend={onSend} />)
    const textarea = screen.getByLabelText('Mensagem para a LIA') as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: 'Test' } })
    fireEvent.click(screen.getByLabelText('Enviar mensagem'))
    expect(textarea.value).toBe('')
  })

  it('does not send empty/whitespace messages', () => {
    render(<ChatInputBar onSend={onSend} />)
    const textarea = screen.getByLabelText('Mensagem para a LIA')
    fireEvent.change(textarea, { target: { value: '   ' } })
    fireEvent.click(screen.getByLabelText('Enviar mensagem'))
    expect(onSend).not.toHaveBeenCalled()
  })

  it('sends on Enter key press', () => {
    render(<ChatInputBar onSend={onSend} />)
    const textarea = screen.getByLabelText('Mensagem para a LIA')
    fireEvent.change(textarea, { target: { value: 'Enter test' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).toHaveBeenCalledWith('Enter test')
  })

  it('does not send on Shift+Enter', () => {
    render(<ChatInputBar onSend={onSend} />)
    const textarea = screen.getByLabelText('Mensagem para a LIA')
    fireEvent.change(textarea, { target: { value: 'Multiline' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables textarea when loading', () => {
    render(<ChatInputBar onSend={onSend} isLoading />)
    const textarea = screen.getByLabelText('Mensagem para a LIA')
    expect(textarea).toBeDisabled()
  })

  it('shows loader icon when loading', () => {
    render(<ChatInputBar onSend={onSend} isLoading />)
    expect(screen.getByTestId('icon-loader')).toBeTruthy()
  })

  it('shows mic button by default', () => {
    render(<ChatInputBar onSend={onSend} />)
    expect(screen.getByLabelText('Gravar áudio')).toBeTruthy()
  })

  it('hides mic button when showMic is false', () => {
    render(<ChatInputBar onSend={onSend} showMic={false} />)
    expect(screen.queryByLabelText('Gravar áudio')).toBeNull()
  })

  it('respects maxLength', () => {
    render(<ChatInputBar onSend={onSend} maxLength={5} />)
    const textarea = screen.getByLabelText('Mensagem para a LIA') as HTMLTextAreaElement
    fireEvent.change(textarea, { target: { value: 'TooLongText' } })
    expect(textarea.value).toBe('')
  })
})
