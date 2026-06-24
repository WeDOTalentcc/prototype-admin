export const dynamic = 'force-dynamic'

const MOCKUP_SANDBOX_URL = 'http://localhost:23636'

async function proxyToMockup(request: Request, params: { path: string[] }) {
  const path = params.path.join('/')
  const url = new URL(request.url)
  const target = `${MOCKUP_SANDBOX_URL}/__mockup/${path}${url.search}`

  const headers = new Headers(request.headers)
  headers.delete('host')

  try {
    const response = await fetch(target, {
      method: request.method,
      headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      // @ts-expect-error Next.js fetch supports duplex
      duplex: 'half',
    })

    const responseHeaders = new Headers(response.headers)
    responseHeaders.delete('x-frame-options')
    responseHeaders.delete('content-security-policy')

    return new Response(response.body, {
      status: response.status,
      headers: responseHeaders,
    })
  } catch {
    return new Response('Mockup sandbox not available', { status: 502 })
  }
}

export async function GET(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  return proxyToMockup(request, await params)
}

export async function POST(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  return proxyToMockup(request, await params)
}
