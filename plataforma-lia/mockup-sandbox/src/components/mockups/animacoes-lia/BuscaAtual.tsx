/**
 * BuscaAtual — SearchLoadingAnimation atual, para comparação.
 */
import { Check, Search } from "lucide-react"

export function BuscaAtual() {
  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center gap-6 px-8 font-sans">

      <div className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">
        Atual — busca loading
      </div>

      {/* Header igual ao LiaPromptHeader */}
      <div className="flex items-center gap-2 mb-2">
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="#60BED1" className="w-7 h-7" style={{animation:"pulse 2s ease-in-out infinite"}}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636-.707.707M21 12h-1M4 12H3m3.343-5.657-.707-.707m2.828 9.9a5 5 0 1 1 7.072 0l-.548.547A3.374 3.374 0 0 0 14 18.469V19a2 2 0 1 1-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
        </svg>
        <h2 className="text-xl font-semibold text-gray-800" style={{animation:"pulse 2s ease-in-out infinite"}}>
          IA está buscando...
        </h2>
      </div>

      {/* Card loading */}
      <div className="p-4 rounded-xl bg-gray-50 max-w-sm w-full border-l-4 border-l-gray-300">
        <style>{`
          @keyframes ping-c { 75%,100%{transform:scale(2);opacity:0} }
          @keyframes pulse-c { 0%,100%{opacity:1} 50%{opacity:.7} }
          @keyframes spin-c { from{transform:rotate(0)} to{transform:rotate(360deg)} }
          @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }
        `}</style>

        <div className="flex items-center gap-3 mb-3">
          <div className="relative flex items-center justify-center w-12 h-12">
            <div className="absolute w-10 h-10 rounded-full bg-[#60BED1]/40"
              style={{animation:"ping-c 1s cubic-bezier(0,0,.2,1) infinite"}} />
            <div className="relative w-10 h-10 rounded-full flex items-center justify-center z-10 bg-[#60BED1]/20"
              style={{animation:"pulse-c 2s cubic-bezier(.4,0,.6,1) infinite"}}>
              <Search className="w-5 h-5 text-gray-500" />
            </div>
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">Processando busca...</p>
            <p className="text-xs text-gray-500">Analisando critérios e perfis</p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <div className="w-4 h-4 rounded-full flex items-center justify-center bg-[#5DA47A]">
              <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
            </div>
            <span>Interpretando</span>
          </div>
          <span className="text-gray-400 text-xs">•</span>
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <div className="w-4 h-4 rounded-full flex items-center justify-center bg-gray-800"
              style={{animation:"spin-c 1s linear infinite"}}>
              <div className="w-2 h-2 border-2 border-white border-t-transparent rounded-full" />
            </div>
            <span>Buscando</span>
          </div>
          <span className="text-gray-400 text-xs">•</span>
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <div className="w-4 h-4 rounded-full bg-gray-200" />
            <span>Rankeando</span>
          </div>
        </div>
      </div>

    </div>
  )
}
