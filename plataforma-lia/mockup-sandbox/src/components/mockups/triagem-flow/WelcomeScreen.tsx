import { Clock, Shield, CheckSquare, MapPin, Briefcase, DollarSign, Gift, Phone } from "lucide-react";

export function WelcomeScreen() {
  return (
    <div className="max-w-[420px] mx-auto min-h-screen bg-[#f8f9fa] flex flex-col font-['Open_Sans',sans-serif]">
      <div className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md bg-white border border-gray-200 rounded-xl shadow-sm p-6 space-y-5">
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="h-12 px-4 flex items-center justify-center bg-gray-100 rounded-lg">
              <span className="text-sm font-semibold text-gray-600 font-['Open_Sans',sans-serif]">
                Acme Corp
              </span>
            </div>
            <h1 className="text-lg font-semibold text-gray-900 font-['Open_Sans',sans-serif]">
              Analista de Dados Pleno
            </h1>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-gray-400 font-['Open_Sans',sans-serif]">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
              São Paulo, SP
            </span>
            <span className="flex items-center gap-1">
              <Briefcase className="w-3.5 h-3.5 flex-shrink-0" />
              Híbrido
            </span>
          </div>

          <p className="text-sm text-gray-600 font-['Open_Sans',sans-serif] leading-relaxed line-clamp-4">
            Buscamos profissional com experiência em análise de dados, SQL avançado e ferramentas de BI para atuar no time de Data Analytics. Atuação em projetos de alta complexidade com impacto direto nos resultados de negócio.
          </p>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-gray-400 font-['Open_Sans',sans-serif]">
              <DollarSign className="w-3.5 h-3.5 flex-shrink-0" />
              <span>R$ 8.000 - R$ 12.000</span>
            </div>
            <div className="flex items-start gap-2 text-xs text-gray-400 font-['Open_Sans',sans-serif]">
              <Gift className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
              <span>VR · Plano de saúde · Gympass · PLR</span>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-[#00BCD4]/10 rounded-lg">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#00BCD4]/20 flex items-center justify-center">
              <span className="text-xs font-bold text-[#00BCD4]">LIA</span>
            </div>
            <div className="text-sm text-gray-600 font-['Open_Sans',sans-serif] leading-relaxed">
              <p className="font-semibold text-gray-900 mb-1">
                Olá, Maria Silva. Eu sou a LIA.
              </p>
              <p>
                Vou conduzir sua triagem para a vaga de <strong>Analista de Dados Pleno</strong> na <strong>Acme Corp</strong>. A conversa tem 6 etapas e dura aproximadamente 15-20 minutos. Você pode responder por texto ou gravar áudio. Vamos começar?
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-gray-400 font-['Open_Sans',sans-serif]">
            <Clock className="w-3.5 h-3.5" />
            <span>
              Tempo estimado:{" "}
              <span className="font-['Inter',sans-serif] font-medium">~20</span>{" "}minutos
            </span>
          </div>

          <label className="flex items-start gap-3 cursor-pointer group">
            <div className="mt-0.5 flex-shrink-0">
              <CheckSquare className="w-5 h-5 text-[#00BCD4]" />
            </div>
            <span className="text-xs text-gray-600 font-['Open_Sans',sans-serif] leading-relaxed select-none">
              Concordo com o tratamento dos meus dados pessoais para fins desta triagem, conforme a{" "}
              <span className="underline text-gray-900">Política de Privacidade</span>{" "}
              e a Lei Geral de Proteção de Dados (LGPD).
            </span>
          </label>

          <div className="flex gap-3">
            <button
              type="button"
              className="flex-1 h-11 flex items-center justify-center rounded-lg bg-[#00BCD4] text-white text-sm font-medium hover:bg-[#00ACC1] transition-colors font-['Open_Sans',sans-serif]"
            >
              Iniciar Conversa
            </button>
            <button
              type="button"
              className="h-11 flex items-center justify-center gap-2 px-4 rounded-lg border border-gray-200 text-gray-900 text-sm font-medium hover:bg-gray-50 transition-colors font-['Open_Sans',sans-serif]"
            >
              <Phone className="w-4 h-4" />
              Receber Ligação
            </button>
          </div>

          <a
            href="#"
            className="flex items-center justify-center gap-1.5 text-xs text-gray-400 hover:text-gray-500 transition-colors font-['Open_Sans',sans-serif]"
          >
            <Shield className="w-3 h-3" />
            Política de Privacidade
          </a>
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
