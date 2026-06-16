const AUTH_SEGMENTS = [
  "login",
  "forgot-password",
  "reset-password",
  "register",
  "accept-invitation",
  "aceitar-convite",
]

export function isAuthRoute(pathname: string): boolean {
  const withoutLocale = pathname.replace(/^\/[a-z]{2}(-[A-Z]{2})?\//i, "/")
  return AUTH_SEGMENTS.some(
    (seg) => withoutLocale === `/${seg}` || withoutLocale.startsWith(`/${seg}/`)
  )
}
