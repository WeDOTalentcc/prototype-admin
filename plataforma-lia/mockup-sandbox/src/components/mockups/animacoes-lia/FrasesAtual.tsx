/**
 * FrasesAtual — LiaPromptHeader atual (sem typing), para comparação.
 */
import { Brain } from "lucide-react"
import { useEffect, useState } from "react"

const PHRASES = [
  "Bom dia, Ana. Tudo em dia. Vamos adiantar algo?",
  "Vamos encontrar o talento certo?",
  "Descreva o perfil ideal e eu encontro.",
  "3 entrevistas hoje. Quer revisar os perfis?",
]

export function FrasesAtual() {
  const [idx, setIdx] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setIdx(i => (i + 1) % PHRASES.length), 3000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-10 px-8 font-sans">

      {/* Label */}
      <div className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">
        Atual — texto estático simples
      </div>

      {/* Chat empty state */}
      <div className="flex flex-col items-center gap-3 w-full max-w-md">
        <div className="w-14 h-14 rounded-full border border-gray-200 flex items-center justify-center bg-white">
          <Brain className="w-7 h-7 text-[#60BED1]" strokeWidth={1.5} />
        </div>
        <h2 className="text-xl font-semibold text-gray-800 text-center">
          {PHRASES[idx]}
        </h2>
        <p className="text-xs text-gray-400 mt-1">(troca a cada 3s para simular frases diferentes)</p>
      </div>

      {/* Funil de talentos */}
      <div className="flex flex-col items-center gap-3 w-full max-w-md border-t pt-8">
        <div className="text-xs text-gray-400 mb-1">— versão Funil de Talentos —</div>
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6 text-[#60BED1]" strokeWidth={2} />
          <h2 className="text-xl font-semibold text-gray-800">{PHRASES[idx]}</h2>
        </div>
      </div>

    </div>
  )
}
