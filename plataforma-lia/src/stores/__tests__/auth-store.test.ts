vi.mock('@/services/auth-service', () => {
  const mockService = {
    login: vi.fn(),
    getMe: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    clearTokens: vi.fn(),
    initiateSSO: vi.fn(),
    getAuthMethod: vi.fn(() => null),
    isJWTAuthenticated: vi.fn(() => false),
    checkSSOSession: vi.fn(),
    refreshToken: vi.fn(),
  }
  return { default: mockService }
})

vi.mock('@/lib/session-cleanup', () => ({
  clearSessionStorage: vi.fn(),
}))

import { useAuthStore, registerStoreReset } from '../auth-store'
import authService from '@/services/auth-service'
import { act } from '@testing-library/react'

const { getState, setState } = useAuthStore

beforeEach(() => {
  vi.clearAllMocks()
  act(() =>
    setState({
      user: null,
      authMethod: null,
      isLoading: true,
      isAuthenticated: false,
      isSSO: false,
      permissions: [],
    })
  )
})

describe('auth-store', () => {
  it('starts unauthenticated', () => {
    const s = getState()
    expect(s.isAuthenticated).toBe(false)
    expect(s.user).toBeNull()
    expect(s.isLoading).toBe(true)
  })

  it('setUser marks authenticated when user is set', () => {
    const user = { id: '1', name: 'Demo', email: 'demo@test.com' }
    act(() => getState().setUser(user as never))
    expect(getState().isAuthenticated).toBe(true)
    expect(getState().user).toEqual(user)
  })

  it('setUser marks unauthenticated when null', () => {
    act(() => getState().setUser({ id: '1' } as never))
    act(() => getState().setUser(null))
    expect(getState().isAuthenticated).toBe(false)
  })

  it('setAuthMethod tracks SSO correctly', () => {
    act(() => getState().setAuthMethod('sso'))
    expect(getState().isSSO).toBe(true)
    expect(getState().authMethod).toBe('sso')
  })

  it('setAuthMethod tracks JWT correctly', () => {
    act(() => getState().setAuthMethod('jwt'))
    expect(getState().isSSO).toBe(false)
    expect(getState().authMethod).toBe('jwt')
  })

  it('setPermissions updates permissions array', () => {
    act(() => getState().setPermissions(['admin', 'edit']))
    expect(getState().permissions).toEqual(['admin', 'edit'])
  })

  it('login calls service and sets user', async () => {
    const user = { id: '1', name: 'Test', email: 'test@test.com' }
    vi.mocked(authService.login).mockResolvedValue(undefined)
    vi.mocked(authService.getMe).mockResolvedValue(user as never)

    await act(async () => {
      await getState().login('test@test.com', 'pass')
    })

    expect(authService.login).toHaveBeenCalledWith('test@test.com', 'pass')
    expect(authService.getMe).toHaveBeenCalled()
    expect(getState().isAuthenticated).toBe(true)
    expect(getState().authMethod).toBe('jwt')
  })

  it('logout clears state and calls service', async () => {
    act(() => getState().setUser({ id: '1' } as never))
    vi.mocked(authService.logout).mockResolvedValue(undefined)

    await act(async () => {
      await getState().logout()
    })

    expect(authService.logout).toHaveBeenCalled()
    expect(getState().isAuthenticated).toBe(false)
    expect(getState().user).toBeNull()
    expect(getState().permissions).toEqual([])
  })

  it('registerStoreReset callbacks run on logout', async () => {
    const resetFn = vi.fn()
    registerStoreReset(resetFn)
    vi.mocked(authService.logout).mockResolvedValue(undefined)

    await act(async () => {
      await getState().logout()
    })

    expect(resetFn).toHaveBeenCalled()
  })

  it('initAuth with JWT sets user from refreshed token', async () => {
    const user = { id: '1', name: 'JWT User' }
    vi.mocked(authService.getAuthMethod).mockReturnValue('jwt' as never)
    vi.mocked(authService.isJWTAuthenticated).mockReturnValue(true)
    vi.mocked(authService.refreshToken).mockResolvedValue(undefined)
    vi.mocked(authService.getMe).mockResolvedValue(user as never)

    await act(async () => {
      await getState().initAuth()
    })

    expect(getState().isAuthenticated).toBe(true)
    expect(getState().authMethod).toBe('jwt')
    expect(getState().isLoading).toBe(false)
  })

  it('initAuth without credentials finishes loading', async () => {
    vi.mocked(authService.getAuthMethod).mockReturnValue(null as never)
    vi.mocked(authService.isJWTAuthenticated).mockReturnValue(false)

    await act(async () => {
      await getState().initAuth()
    })

    expect(getState().isLoading).toBe(false)
    expect(getState().isAuthenticated).toBe(false)
  })
  it('login failure does not set authenticated', async () => {
    vi.mocked(authService.login).mockRejectedValue(new Error('Invalid credentials'))

    await expect(
      act(async () => {
        await getState().login('bad@test.com', 'wrong')
      })
    ).rejects.toThrow('Invalid credentials')

    expect(getState().isAuthenticated).toBe(false)
  })

  it('initAuth with failed JWT refresh clears tokens and state', async () => {
    vi.mocked(authService.getAuthMethod).mockReturnValue(null as never)
    vi.mocked(authService.isJWTAuthenticated).mockReturnValue(true)
    vi.mocked(authService.refreshToken).mockRejectedValue(new Error('expired'))

    await act(async () => {
      await getState().initAuth()
    })

    expect(authService.clearTokens).toHaveBeenCalled()
    expect(getState().isAuthenticated).toBe(false)
    expect(getState().isLoading).toBe(false)
  })

  it('refreshUser with SSO failure clears auth state', async () => {
    vi.mocked(authService.getAuthMethod).mockReturnValue('sso' as never)
    vi.mocked(authService.checkSSOSession).mockRejectedValue(new Error('SSO down'))

    await act(async () => {
      await getState().refreshUser()
    })

    expect(getState().isAuthenticated).toBe(false)
    expect(getState().user).toBeNull()
  })

  it('refreshUser with JWT failure clears tokens', async () => {
    vi.mocked(authService.getAuthMethod).mockReturnValue('jwt' as never)
    vi.mocked(authService.isJWTAuthenticated).mockReturnValue(true)
    vi.mocked(authService.getMe).mockRejectedValue(new Error('401'))

    await act(async () => {
      await getState().refreshUser()
    })

    expect(authService.clearTokens).toHaveBeenCalled()
    expect(getState().isAuthenticated).toBe(false)
  })
})
