import { Send, Mic, Volume2 } from "lucide-react";

function LIAAvatar() {
  return (
    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-[#00BCD4]/20 flex items-center justify-center">
      <span className="text-[9px] font-bold text-[#00BCD4]">LIA</span>
    </div>
  );
}

function CandidateAvatar() {
  return (
    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center text-xs font-semibold text-gray-500 font-['Inter',sans-serif]">
      MS
    </div>
  );
}

function LiaMessage({ text, time }: { text: string; time: string }) {
  return (
    <div className="flex gap-2.5 justify-start">
      <div className="mt-0.5">
        <LIAAvatar />
      </div>
      <div className="flex flex-col gap-1 max-w-[80%] items-start">
        <div className="flex items-center gap-1.5 px-1">
          <span className="text-xs font-bold text-gray-900 font-['Inter',sans-serif]">LIA</span>
          <span className="text-xs text-gray-300 font-['Inter',sans-serif] tabular-nums">{time}</span>
        </div>
        <div className="flex items-end gap-1.5">
          <div className="px-3.5 py-2.5 text-sm font-['Open_Sans',sans-serif] leading-relaxed rounded-[14px] rounded-bl-[4px] bg-[#00BCD4]/[0.04] text-gray-900">
            <span dangerouslySetInnerHTML={{ __html: text }} />
          </div>
          <button
            type="button"
            title="Ouvir mensagem"
            className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full text-gray-300 hover:text-gray-500 hover:bg-gray-100 transition-colors"
          >
            <Volume2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

function CandidateMessage({ text, time }: { text: string; time: string }) {
  return (
    <div className="flex gap-2.5 justify-end">
      <div className="flex flex-col gap-1 max-w-[80%] items-end">
        <div className="px-3.5 py-2.5 text-sm font-['Open_Sans',sans-serif] leading-relaxed rounded-[14px] rounded-br-[4px] bg-gray-100 text-gray-600">
          {text}
        </div>
        <span className="text-xs text-gray-300 font-['Inter',sans-serif] tabular-nums px-1">
          {time}
        </span>
      </div>
      <div className="mt-0.5">
        <CandidateAvatar />
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="mt-0.5">
        <LIAAvatar />
      </div>
      <div className="flex flex-col gap-1 items-start">
        <div className="flex items-center gap-1.5 px-1">
          <span className="text-xs font-bold text-gray-900 font-['Inter',sans-serif]">LIA</span>
        </div>
        <div className="flex items-center gap-3 rounded-[14px] rounded-bl-[4px] bg-[#00BCD4]/[0.04] px-3.5 py-2.5">
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="w-2 h-2 rounded-full bg-[#00BCD4]"
                style={{
                  animation: "typingDot 1.4s ease-in-out infinite",
                  animationDelay: `${i * 0.2}s`,
                }}
              />
            ))}
          </div>
        </div>
      </div>
      <style>{`
        @keyframes typingDot {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

export function ChatScreen() {
  return (
    <div className="max-w-[420px] mx-auto min-h-screen bg-[#f8f9fa] flex flex-col font-['Open_Sans',sans-serif]">
      <div className="sticky top-0 z-20 bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium font-['Open_Sans',sans-serif] text-gray-600">
            Etapa{" "}
            <span className="font-['Inter',sans-serif]">3</span> de{" "}
            <span className="font-['Inter',sans-serif]">6</span>
            {" · "}Habilidades Técnicas
          </span>
          <span className="text-[10px] font-['Inter',sans-serif] text-gray-300">
            50%
          </span>
        </div>
        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#00BCD4] rounded-full transition-all duration-500 ease-out"
            style={{ width: "50%" }}
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <LiaMessage
          text="Vamos começar falando sobre sua <strong>experiência profissional</strong>. Conte-me um pouco sobre sua trajetória."
          time="14:32"
        />

        <CandidateMessage
          text="Trabalho na área de dados há 4 anos. Comecei como analista júnior e hoje atuo como pleno no time de BI de uma empresa de tecnologia."
          time="14:33"
        />

        <LiaMessage
          text="Entendido. Quais ferramentas e linguagens de programação você utiliza no dia a dia para <strong>análise de dados</strong>?"
          time="14:33"
        />

        <CandidateMessage
          text="Domino Python (pandas, scikit-learn), SQL avançado, Power BI e tenho experiência com Databricks e dbt."
          time="14:35"
        />

        <LiaMessage
          text="Obrigada. Agora, como você lida com <strong>prazos apertados</strong> e demandas simultâneas no seu trabalho?"
          time="14:35"
        />

        <TypingDots />
      </div>

      <div className="sticky bottom-0 z-10 bg-white border-t border-gray-200 px-4 py-3">
        <div className="flex items-end gap-2">
          <button
            type="button"
            title="Leitura automática desativada"
            className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg border border-gray-300 text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <Volume2 className="w-4 h-4" />
          </button>
          <textarea
            placeholder="Digite sua resposta..."
            rows={1}
            className="flex-1 resize-none w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:border-[#00BCD4] focus:ring-2 focus:ring-[#00BCD4]/20 focus:outline-none font-['Open_Sans',sans-serif]"
            readOnly
          />
          <button
            type="button"
            title="Gravar resposta por voz"
            className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg border border-gray-300 bg-white text-gray-500 hover:bg-gray-50 hover:text-[#00BCD4] transition-colors"
          >
            <Mic className="w-4 h-4" />
          </button>
          <button
            type="button"
            className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-[#00BCD4] text-white hover:bg-[#00ACC1] transition-colors opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="py-3 px-4 text-center">
        <p className="text-[10px] text-gray-400 font-['Open_Sans',sans-serif]">
          Powered by{" "}
          <span className="text-[#00BCD4] font-medium">LIA</span> · WeDOTalent
          ·{" "}
          <span className="underline">Política de Privacidade</span>
        </p>
      </div>
    </div>
  );
}
