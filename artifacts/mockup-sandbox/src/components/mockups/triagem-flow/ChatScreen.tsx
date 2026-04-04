import { Send, Mic } from "lucide-react";

function LIAAvatar() {
  return (
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#00BCD4]/20 flex items-center justify-center">
      <span className="text-[10px] font-bold text-[#00BCD4]">LIA</span>
    </div>
  );
}

function CandidateAvatar() {
  return (
    <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-xs font-semibold text-gray-500 font-['Inter',sans-serif]">
      MS
    </div>
  );
}

function LiaMessage({ text, time }: { text: string; time: string }) {
  return (
    <div className="flex gap-3 justify-start">
      <div className="mt-1">
        <LIAAvatar />
      </div>
      <div className="flex flex-col gap-1 max-w-[80%]">
        <div className="px-4 py-3 text-sm font-['Open_Sans',sans-serif] leading-relaxed rounded-lg bg-[#00BCD4]/[0.04] text-gray-900">
          <span dangerouslySetInnerHTML={{ __html: text }} />
        </div>
        <span className="text-[10px] font-['Inter',sans-serif] text-gray-300 text-left">
          {time}
        </span>
      </div>
    </div>
  );
}

function CandidateMessage({ text, time }: { text: string; time: string }) {
  return (
    <div className="flex gap-3 justify-end">
      <div className="flex flex-col gap-1 max-w-[80%]">
        <div className="px-4 py-3 text-sm font-['Open_Sans',sans-serif] leading-relaxed rounded-lg bg-[#00BCD4] text-white">
          {text}
        </div>
        <span className="text-[10px] font-['Inter',sans-serif] text-gray-300 text-right">
          {time}
        </span>
      </div>
      <div className="mt-1">
        <CandidateAvatar />
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-3">
      <div className="mt-1">
        <LIAAvatar />
      </div>
      <div className="flex items-center gap-3 rounded-lg bg-white border border-gray-200 px-4 py-3">
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
        <span className="text-xs font-['Open_Sans',sans-serif] text-gray-500">
          LIA está digitando...
        </span>
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
            <span className="font-['Inter',sans-serif]">7</span>
            {" · "}Habilidades Técnicas
          </span>
          <span className="text-[10px] font-['Inter',sans-serif] text-gray-300">
            43%
          </span>
        </div>
        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#00BCD4] rounded-full transition-all duration-500 ease-out"
            style={{ width: "43%" }}
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <LiaMessage
          text="Olá, <strong>Maria</strong>! Que bom te ter aqui! 😊<br /><br />Vamos começar com algumas perguntas sobre sua <strong>experiência profissional</strong>. Pode ficar à vontade, é uma conversa tranquila."
          time="14:32"
        />

        <CandidateMessage
          text="Oi LIA! Obrigada, estou animada com essa oportunidade. Pode perguntar!"
          time="14:33"
        />

        <LiaMessage
          text="Ótimo! 🎉 Me conta, há quanto tempo você trabalha com <strong>análise de dados</strong>? Quais ferramentas e linguagens você domina?"
          time="14:33"
        />

        <CandidateMessage
          text="Trabalho com dados há 4 anos. Domino Python (pandas, scikit-learn), SQL avançado, Power BI e tenho experiência com Databricks e dbt."
          time="14:35"
        />

        <LiaMessage
          text="Muito bom, Maria! Experiência sólida com ferramentas relevantes. 💪<br /><br />Agora, como você avalia sua capacidade de <strong>trabalhar sob pressão</strong> com prazos apertados?"
          time="14:35"
        />

        <TypingDots />
      </div>

      <div className="sticky bottom-0 z-10 bg-white border-t border-gray-200 px-4 py-3">
        <div className="flex items-end gap-2">
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
