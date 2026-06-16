import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import authService, { type AuthenticatedUser, type AuthMethod } from '@/services/auth-service'
import { clearSessionStorage } from '@/lib/session-cleanup'

const storeResetCallbacks: Array<() => void> = []

export function registerStoreReset(callback: () => void) {
  storeResetCallbacks.push(callback)
}

function resetAllStores() {
  for (const cb of storeResetCallbacks) {
    cb()
  }
}

interface AuthState {
  user: AuthenticatedUser | null
  authMethod: AuthMethod | null
  isLoading: boolean
  isAuthenticated: boolean
  isSSO: boolean
  permissions: string[]
}

interface AuthActions {
  setUser: (user: AuthenticatedUser | null) => void
  setAuthMethod: (method: AuthMethod | null) => void
  setIsLoading: (loading: boolean) => void
  setPermissions: (permissions: string[]) => void
  login: (email: string, password: string) => Promise<void>
  loginWithSSO: (options: { organization?: string; connection?: string; email?: string }) => void
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  initAuth: () => Promise<void>
}

export type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  devtools(
    (set, get) => ({
      user: null,
      authMethod: null,
      isLoading: true,
      isAuthenticated: false,
      isSSO: false,
      permissions: [],

      setUser: (user) => set({
        user,
        isAuthenticated: !!user,
      }, false, 'auth/setUser'),

      setAuthMethod: (method) => set({
        authMethod: method,
        isSSO: method === 'sso',
      }, false, 'auth/setAuthMethod'),

      setIsLoading: (loading) => set({ isLoading: loading }, false, 'auth/setIsLoading'),

      setPermissions: (permissions) => set({ permissions }, false, 'auth/setPermissions'),

      login: async (email, password) => {
        await authService.login(email, password)
        const userData = await authService.getMe()
        set({
          user: userData,
          authMethod: 'jwt',
          isAuthenticated: true,
          isSSO: false,
        }, false, 'auth/login')
      },

      loginWithSSO: (options) => {
        authService.initiateSSO(options)
      },

      register: async (email, password, name) => {
        await authService.register(email, password, name)
        await get().login(email, password)
      },

      logout: async () => {
        clearSessionStorage()
        resetAllStores()
        await authService.logout()
        set({
          user: null,
          authMethod: null,
          isAuthenticated: false,
          isSSO: false,
          permissions: [],
        }, false, 'auth/logout')
      },

      refreshUser: async () => {
        const currentAuthMethod = authService.getAuthMethod()

        if (currentAuthMethod === 'sso') {
          try {
            const ssoSession = await authService.checkSSOSession()
            if (ssoSession.authenticated && ssoSession.user) {
              set({
                user: ssoSession.user,
                authMethod: 'sso',
                isAuthenticated: true,
                isSSO: true,
              }, false, 'auth/refreshUser/sso')
            } else {
              set({ user: null, authMethod: null, isAuthenticated: false, isSSO: false }, false, 'auth/refreshUser/sso-fail')
            }
          } catch {
            set({ user: null, authMethod: null, isAuthenticated: false, isSSO: false }, false, 'auth/refreshUser/sso-error')
          }
        } else if (currentAuthMethod === 'jwt' || currentAuthMethod === 'dev-auto-login' || authService.isJWTAuthenticated()) {
          const isDevLogin = currentAuthMethod === 'dev-auto-login'
          try {
            const userData = await authService.getMe()
            set({
              user: userData,
              authMethod: currentAuthMethod as AuthMethod,
              isAuthenticated: true,
              isSSO: false,
            }, false, 'auth/refreshUser/jwt')
          } catch {
            if (isDevLogin) {
              return
            }
            set({ user: null, authMethod: null, isAuthenticated: false, isSSO: false }, false, 'auth/refreshUser/jwt-fail')
            await authService.clearTokens()
          }
        } else if (currentAuthMethod === null && process.env.NODE_ENV !== 'production') {
          return
        } else {
          set({ user: null, authMethod: null, isAuthenticated: false, isSSO: false }, false, 'auth/refreshUser/none')
        }
      },

      initAuth: async () => {
        const safetyTimer = setTimeout(() => {
          if (get().isLoading) {
            set({ isLoading: false }, false, 'auth/init/safety-timeout')
          }
        }, 15000)

        try {
        if (typeof window !== 'undefined' && (window as unknown as Record<string, unknown>).__INITIAL_USER__) {
          const serverData = (window as unknown as Record<string, unknown>).__INITIAL_USER__ as Record<string, unknown>
          const roleStr = String(serverData.role || 'viewer')
          const userData: AuthenticatedUser = {
            id: String(serverData.id || ''),
            email: String(serverData.email || ''),
            name: String(serverData.name || ''),
            role: (roleStr === 'admin' || roleStr === 'recruiter' || roleStr === 'viewer' || roleStr === 'wedotalent_admin') ? roleStr : 'viewer',
            is_active: serverData.is_active !== false,
            created_at: String(serverData.created_at || ''),
            updated_at: String(serverData.updated_at || ''),
            company_id: serverData.company_id ? String(serverData.company_id) : undefined,
          }
          if (userData.email) {
            set({
              user: userData,
              authMethod: 'dev-auto-login' as AuthMethod,
              isAuthenticated: true,
              isSSO: false,
              isLoading: false,
            }, false, 'auth/init/server-injected')
            delete (window as unknown as Record<string, unknown>).__INITIAL_USER__
            return
          }
        }

        if (process.env.NODE_ENV !== 'production') {
          for (let attempt = 0; attempt < 3; attempt++) {
            try {
              const userData = await authService.getMeDirect()
              if (userData && userData.email) {
                set({
                  user: userData,
                  authMethod: 'dev-auto-login' as AuthMethod,
                  isAuthenticated: true,
                  isSSO: false,
                  isLoading: false,
                }, false, 'auth/init/dev')
                return
              }
            } catch {
              if (attempt < 2) {
                await new Promise(r => setTimeout(r, 3000))
              }
            }
          }
        }

        const currentAuthMethod = authService.getAuthMethod()

        if (currentAuthMethod === 'sso') {
          try {
            const ssoSession = await authService.checkSSOSession()
            if (ssoSession.authenticated && ssoSession.user) {
              set({
                user: ssoSession.user,
                authMethod: 'sso',
                isAuthenticated: true,
                isSSO: true,
              }, false, 'auth/init/sso')
            } else {
              await authService.clearTokens()
            }
          } catch {
            await authService.clearTokens()
          }
        } else if (authService.isJWTAuthenticated()) {
          try {
            const userData = await authService.getMe()
            set({
              user: userData,
              authMethod: 'jwt',
              isAuthenticated: true,
              isSSO: false,
            }, false, 'auth/init/jwt')
          } catch {
            try {
              await authService.refreshToken()
              const userData = await authService.getMe()
              set({
                user: userData,
                authMethod: 'jwt',
                isAuthenticated: true,
                isSSO: false,
              }, false, 'auth/init/jwt-refreshed')
            } catch {
              await authService.clearTokens()
              set({ user: null, authMethod: null, isAuthenticated: false, isSSO: false }, false, 'auth/init/jwt-fail')
            }
          }
        }

        set({ isLoading: false }, false, 'auth/init/done')
        } finally {
          clearTimeout(safetyTimer)
        }
      },
    }),
    { name: 'AuthStore' }
  )
)
