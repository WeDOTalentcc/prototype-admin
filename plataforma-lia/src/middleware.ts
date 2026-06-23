export const runtime = 'nodejs'

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
}

export { proxy as middleware } from './proxy'
