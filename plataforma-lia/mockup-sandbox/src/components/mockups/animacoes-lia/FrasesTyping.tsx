/**
 * FrasesTyping — LiaPromptHeader com efeito typewriter.
 * Digita a frase char a char, pausa, apaga, troca.
 */
import { Brain } from "lucide-react"
import { useEffect, useRef, useState } from "react"

const PHRASES = [
  "Bom dia, Ana. Tudo em dia. Vamos adiantar algo?",
  "Vamos encontrar o talento certo?",
  "Descreva o perfil ideal e eu encontro.",
  "3 entrevistas hoje. Quer revisar os perfis?",
  "Oi! Por onde quer começar hoje?",
]

const TYPING_SPEED = 38  // ms por caractere
const PAUSE_AFTER  = 2200 // ms depois de digitar tudo
const ERASE_SPEED  = 18  // ms por caractere apagando

type Phase = "typing" | "pausing" | "erasing" | "waiting"

export function FrasesTyping() {
  const [displayed, setDisplayed] = useState("")
  const [phraseIdx, setPhraseIdx] = useState(0)
  const [phase, setPhase] = useState<Phase>("typing")
  const [showCursor, setShowCursor] = useState(true)
  const charRef = useRef(0)

  // Cursor piscante independente
  useEffect(() => {
    const t = setInterval(() => setShowCursor(v => !v), 530)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    charRef.current = 0
    setDisplayed("")
    setPhase("typing")
  }, [phraseIdx])

  useEffect(() => {
    const target = PHRASES[phraseIdx]

    if (phase === "typing") {
      if (charRef.current < target.length) {
        const t = setTimeout(() => {
          charRef.current++
          setDisplayed(target.slice(0, charRef.current))
        }, TYPING_SPEED)
        return () => clearTimeout(t)
      } else {
        const t = setTimeout(() => setPhase("pausing"), 80)
        return () => clearTimeout(t)
      }
    }

    if (phase === "pausing") {
      const t = setTimeout(() => setPhase("erasing"), PAUSE_AFTER)
      return () => clearTimeout(t)
    }

    if (phase === "erasing") {
      if (charRef.current > 0) {
        const t = setTimeout(() => {
          charRef.current--
          setDisplayed(target.slice(0, charRef.current))
        }, ERASE_SPEED)
        return () => clearTimeout(t)
      } else {
        const t = setTimeout(() => {
          setPhraseIdx(i => (i + 1) % PHRASES.length)
        }, 300)
        return () => clearTimeout(t)
      }
    }
  }, [phase, displayed, phraseIdx])

  const cursorVisible = phase === "pausing" ? false : showCursor

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-10 px-8 font-sans">

      {/* Label */}
      <div className="text-xs font-semibold uppercase tracking-widest text-[#60BED1] mb-2">
        ✨ Com efeito typing
      </div>

      {/* Chat empty state */}
      <div className="flex flex-col items-center gap-3 w-full max-w-md">
        <div className="w-14 h-14 rounded-full border border-gray-200 flex items-center justify-center bg-white shadow-sm">
          <Brain className="w-7 h-7 text-[#60BED1]" strokeWidth={1.5} />
        </div>

        <h2 className="text-xl font-semibold text-gray-800 text-center min-h-[2.5rem] flex items-center">
          <span>{displayed}</span>
          <span
            className="ml-0.5 inline-block w-[2px] h-[1.2em] rounded-full"
            style={{
              background: "#60BED1",
              opacity: cursorVisible ? 1 : 0,
              transition: "opacity 0.1s",
              verticalAlign: "middle",
              marginBottom: "1px",
            }}
          />
        </h2>

        <p className="text-xs text-gray-400">
          (digita → pausa → apaga → próxima frase)
        </p>
      </div>

      {/* Funil de talentos */}
      <div className="flex flex-col items-center gap-3 w-full max-w-md border-t pt-8">
        <div className="text-xs text-gray-400 mb-1">— versão Funil de Talentos —</div>

        <div className="flex items-center gap-2 min-h-[2rem]">
          <Brain className="w-6 h-6 text-[#60BED1] flex-shrink-0" strokeWidth={2} />
          <h2 className="text-xl font-semibold text-gray-800">
            <span>{displayed}</span>
            <span
              className="ml-0.5 inline-block w-[2px] h-[1.1em] rounded-full"
              style={{
                background: "#60BED1",
                opacity: cursorVisible ? 1 : 0,
                transition: "opacity 0.1s",
                verticalAlign: "middle",
              }}
            />
          </h2>
        </div>
      </div>

    </div>
  )
}
