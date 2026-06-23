import type { NextRequest } from 'next/server'
import { proxy } from './proxy'

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}

export function middleware(request: NextRequest) {
  return proxy(request)
}
