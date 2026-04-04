import { Send, ClipboardCheck, Mic } from "lucide-react";

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
      <div className="mt-1"><LIAAvatar /></div>
      <div className="flex flex-col gap-1 max-w-[80%]">
        <div className="px-4 py-3 text-sm font-['Open_Sans',sans-serif] leading-relaxed rounded-lg bg-[#00BCD4]/[0.04] text-gray-900">
          <span dangerouslySetInnerHTML={{ __html: text }} />
        </div>
        <span className="text-[10px] font-['Inter',sans-serif] text-gray-300 text-left">{time}</span>
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
        <span className="text-[10px] font-['Inter',sans-serif] text-gray-300 text-right">{time}</span>
      </div>
      <div className="mt-1"><CandidateAvatar /></div>
    </div>
  );
}

export function ConfirmationScreen() {
  return (
    <div className="max-w-[420px] mx-auto min-h-screen bg-[#f8f9fa] flex flex-col font-['Open_Sans',sans-serif]">
      <div className="sticky top-0 z-20 bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium font-['Open_Sans',sans-serif] text-gray-600">
            Etapa <span className="font-['Inter',sans-serif]">7</span> de{" "}
            <span className="font-['Inter',sans-serif]">7</span>
            {" · "}Encerramento
          </span>
          <span className="text-[10px] font-['Inter',sans-serif] text-gray-300">100%</span>
        </div>
        <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-[#00BCD4] rounded-full" style={{ width: "100%" }} />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        <LiaMessage
          text="Para finalizar, o que mais te motiva a buscar essa <strong>oportunidade</strong>?"
          time="14:52"
        />

        <CandidateMessage
          text="Estou buscando um ambiente que valorize dados como motor de decisões estratégicas. A cultura da WeDO se alinha muito com o que procuro."
          time="14:54"
        />

        <LiaMessage
          text="Muito obrigada pelas suas respostas, Maria! 🙏<br /><br />Foi ótimo conversar com você. Sua experiência é muito relevante para essa posição."
          time="14:54"
        />

        <div className="mx-0 my-4 bg-white border border-gray-200 rounded-xl shadow-sm p-5 space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
              <ClipboardCheck className="w-5 h-5 text-gray-500" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 font-['Open_Sans',sans-serif]">
                Chegamos ao final!
              </h3>
              <p className="text-xs text-gray-400 mt-1 font-['Open_Sans',sans-serif]">
                Quer revisar algo antes de concluir?
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-gray-400 font-['Inter',sans-serif]">
            <span>12 perguntas respondidas</span>
            <span className="w-1 h-1 rounded-full bg-gray-300" />
            <span>22 minutos</span>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              className="flex-1 h-10 flex items-center justify-center rounded-lg bg-white text-gray-900 text-sm font-medium border border-gray-300 hover:bg-gray-50 transition-colors font-['Open_Sans',sans-serif]"
            >
              Quero revisar
            </button>
            <button
              type="button"
              className="flex-1 h-10 flex items-center justify-center rounded-lg bg-[#00BCD4] text-white text-sm font-medium hover:bg-[#00ACC1] transition-colors font-['Open_Sans',sans-serif]"
            >
              Finalizar Triagem
            </button>
          </div>
        </div>
      </div>

      <div className="sticky bottom-0 z-10 bg-white border-t border-gray-200 px-4 py-3">
        <div className="flex items-end gap-2">
          <textarea
            placeholder="Digite sua resposta..."
            rows={1}
            disabled
            className="flex-1 resize-none w-full px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 opacity-50 font-['Open_Sans',sans-serif]"
            readOnly
          />
          <button
            type="button"
            disabled
            title="Gravar resposta por voz"
            className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg border border-gray-300 bg-white text-gray-500 opacity-50"
          >
            <Mic className="w-4 h-4" />
          </button>
          <button
            type="button"
            disabled
            className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-[#00BCD4] text-white opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="py-3 px-4 text-center">
        <p className="text-[10px] text-gray-400 font-['Open_Sans',sans-serif]">
          Powered by <span className="text-[#00BCD4] font-medium">LIA</span> · WeDOTalent · <span className="underline">Política de Privacidade</span>
        </p>
      </div>
    </div>
  );
}
