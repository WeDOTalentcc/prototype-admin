import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = 'WeDoTalent'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function Image() {
  return new ImageResponse(
    <div
      style={{
        background: '#111827',
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontFamily: 'sans-serif',
      }}
    >
      <div style={{ fontSize: 72, fontWeight: 'bold', color: '#60BED1' }}>WeDoTalent</div>
      <div style={{ fontSize: 32, marginTop: 16 }}>Plataforma WeDoTalent</div>
      <div style={{ fontSize: 20, marginTop: 8, color: '#5C5C5C' }}>
        Recrutamento inteligente com IA
      </div>
    </div>
  )
}
