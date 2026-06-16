// Edge-compatible session signing (Task: deploy fix).
//
// Este módulo é importado pelo Edge Middleware (`src/proxy.ts` → `src/middleware.ts`),
// onde os módulos nativos do Node (ex.: `crypto`) NÃO são suportados. Por isso a
// assinatura HMAC-SHA256 é implementada em JS puro (sem `crypto`, sem `Buffer`),
// mantendo a API síncrona usada por `getAuthHeaders`/proxy/rotas WorkOS.

const SESSION_SECRET = process.env.WORKOS_SESSION_SECRET || process.env.WORKOS_API_KEY || ''
if (!SESSION_SECRET && process.env.NODE_ENV === 'production') {
  // SSO (WorkOS) nao configurado neste deploy: sessoes SSO sao tratadas como
  // ausentes (verifyAndDecodeSession retorna null). O login email/senha nao
  // depende deste secret. Para habilitar SSO, definir WORKOS_SESSION_SECRET
  // ou WORKOS_API_KEY nos Secrets.
  console.warn('[session-crypto] WORKOS secret ausente — SSO desabilitado neste ambiente')
}

export interface SessionPayload {
  workosProfile: {
    id: string
    email: string
    firstName: string | null
    lastName: string | null
    organizationId: string | null
    connectionId: string
    connectionType: string
    idpId: string
  }
  accessToken: string
  expiresAt: number
  createdAt: number
}

// --- SHA-256 (JS puro, Edge-safe) ---------------------------------------------

const SHA256_K = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
])

function rotr(x: number, n: number): number {
  return (x >>> n) | (x << (32 - n))
}

function sha256(data: Uint8Array): Uint8Array {
  const h = new Uint32Array([
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
  ])

  const l = data.length
  const bitLen = l * 8
  const withOne = l + 1
  const padZeros = ((56 - (withOne % 64)) + 64) % 64
  const total = withOne + padZeros + 8

  const msg = new Uint8Array(total)
  msg.set(data)
  msg[l] = 0x80

  const dv = new DataView(msg.buffer)
  dv.setUint32(total - 4, bitLen >>> 0, false)
  dv.setUint32(total - 8, Math.floor(bitLen / 0x100000000), false)

  const w = new Uint32Array(64)

  for (let off = 0; off < total; off += 64) {
    for (let i = 0; i < 16; i++) w[i] = dv.getUint32(off + i * 4, false)
    for (let i = 16; i < 64; i++) {
      const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3)
      const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10)
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0
    }

    let a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7]

    for (let i = 0; i < 64; i++) {
      const S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)
      const ch = (e & f) ^ (~e & g)
      const t1 = (hh + S1 + ch + SHA256_K[i] + w[i]) >>> 0
      const S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)
      const maj = (a & b) ^ (a & c) ^ (b & c)
      const t2 = (S0 + maj) >>> 0
      hh = g
      g = f
      f = e
      e = (d + t1) >>> 0
      d = c
      c = b
      b = a
      a = (t1 + t2) >>> 0
    }

    h[0] = (h[0] + a) >>> 0
    h[1] = (h[1] + b) >>> 0
    h[2] = (h[2] + c) >>> 0
    h[3] = (h[3] + d) >>> 0
    h[4] = (h[4] + e) >>> 0
    h[5] = (h[5] + f) >>> 0
    h[6] = (h[6] + g) >>> 0
    h[7] = (h[7] + hh) >>> 0
  }

  const out = new Uint8Array(32)
  const odv = new DataView(out.buffer)
  for (let i = 0; i < 8; i++) odv.setUint32(i * 4, h[i], false)
  return out
}

function hmacSha256(secret: string, message: string): Uint8Array {
  const enc = new TextEncoder()
  const encoded = enc.encode(secret)
  const key = encoded.length > 64 ? sha256(encoded) : encoded

  const ipad = new Uint8Array(64)
  const opad = new Uint8Array(64)
  for (let i = 0; i < 64; i++) {
    const kb = i < key.length ? key[i] : 0
    ipad[i] = kb ^ 0x36
    opad[i] = kb ^ 0x5c
  }

  const msgBytes = enc.encode(message)
  const inner = new Uint8Array(64 + msgBytes.length)
  inner.set(ipad)
  inner.set(msgBytes, 64)
  const innerHash = sha256(inner)

  const outer = new Uint8Array(64 + 32)
  outer.set(opad)
  outer.set(innerHash, 64)
  return sha256(outer)
}

// --- helpers de encoding (Edge-safe, sem Buffer) ------------------------------

function toHex(bytes: Uint8Array): string {
  let hex = ''
  for (let i = 0; i < bytes.length; i++) hex += bytes[i].toString(16).padStart(2, '0')
  return hex
}

function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) throw new Error('invalid hex length')
  if (!/^[0-9a-fA-F]*$/.test(hex)) throw new Error('invalid hex char')
  const out = new Uint8Array(hex.length / 2)
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.substr(i * 2, 2), 16)
  }
  return out
}

function utf8ToBase64(str: string): string {
  const bytes = new TextEncoder().encode(str)
  let binary = ''
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

function base64ToUtf8(b64: string): string {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return new TextDecoder().decode(bytes)
}

function constantTimeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false
  let diff = 0
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i]
  return diff === 0
}

// --- API pública (inalterada) -------------------------------------------------

function createSignature(payload: string): string {
  return toHex(hmacSha256(SESSION_SECRET, payload))
}

function verifySignature(payload: string, signature: string): boolean {
  try {
    return constantTimeEqual(hexToBytes(signature), hexToBytes(createSignature(payload)))
  } catch {
    return false
  }
}

export function signSession(data: SessionPayload): string {
  if (!SESSION_SECRET) {
    throw new Error('signSession: WORKOS secret ausente — SSO nao configurado neste ambiente')
  }
  const payload = utf8ToBase64(JSON.stringify(data))
  const signature = createSignature(payload)
  return `${payload}.${signature}`
}

export function verifyAndDecodeSession(token: string): SessionPayload | null {
  if (!SESSION_SECRET) return null
  try {
    const [payload, signature] = token.split('.')

    if (!payload || !signature) {
      return null
    }

    if (!verifySignature(payload, signature)) {
      return null
    }

    const data = JSON.parse(base64ToUtf8(payload)) as SessionPayload

    if (data.expiresAt < Date.now()) {
      return null
    }

    if (!data.workosProfile?.id || !data.workosProfile?.email) {
      return null
    }

    return data
  } catch {
    return null
  }
}
