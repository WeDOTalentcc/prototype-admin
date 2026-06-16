import { CheckCircle2 } from "lucide-react";

export function CompletionScreen() {
  return (
    <div className="max-w-[420px] mx-auto min-h-screen bg-[#f8f9fa] flex flex-col font-['Open_Sans',sans-serif]">
      <div className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md bg-white border border-gray-200 rounded-xl shadow-sm p-6 space-y-6">
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="w-12 h-12 rounded-full bg-emerald-500/15 flex items-center justify-center">
              <CheckCircle2 className="w-7 h-7 text-emerald-500" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 font-['Open_Sans',sans-serif]">
              Triagem concluída com sucesso.
            </h2>
            <p className="text-sm text-gray-600 font-['Open_Sans',sans-serif]">
              Obrigada, Maria Silva. Suas respostas foram registradas.
            </p>
          </div>

          <div className="flex items-center justify-center gap-4 text-xs text-gray-400 font-['Inter',sans-serif]">
            <span>12 perguntas respondidas</span>
            <span className="w-1 h-1 rounded-full bg-gray-300" />
            <span>22 minutos</span>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-900 font-['Open_Sans',sans-serif]">
              Próximos passos:
            </h3>
            <ul className="space-y-2">
              {[
                "Você receberá um e-mail de confirmação em instantes",
                "A equipe da Acme Corp avaliará seu perfil nos próximos dias",
                "Fique atento ao seu e-mail para atualizações",
              ].map((step, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-sm text-gray-600 font-['Open_Sans',sans-serif]"
                >
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-['Inter',sans-serif] font-medium text-gray-400 mt-0.5">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ul>
          </div>

          <button
            type="button"
            className="w-full h-10 flex items-center justify-center rounded-lg bg-white text-gray-900 text-sm font-medium border border-gray-300 hover:bg-gray-50 transition-colors font-['Open_Sans',sans-serif]"
          >
            Fechar
          </button>

          <div className="pt-2 border-t border-gray-200 text-center">
            <span className="text-[10px] text-gray-300 font-['Open_Sans',sans-serif]">
              Powered by{" "}
              <span className="text-[#00BCD4] font-medium">LIA</span> ·
              WeDOTalent
            </span>
          </div>
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
