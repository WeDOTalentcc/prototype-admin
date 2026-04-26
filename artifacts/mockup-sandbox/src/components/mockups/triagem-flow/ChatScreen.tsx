import { Send, Mic, Volume2, VolumeX, Brain } from "lucide-react";

const CANDIDATE_NAME = "Mariana Ribeiro";
const CANDIDATE_INITIALS = "MR";

function LIAAvatar() {
  return (
    <div
      className="relative inline-flex items-center justify-center rounded-full w-7 h-7 bg-wedo-cyan/10"
      aria-hidden="true"
    >
      <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
    </div>
  );
}

function CandidateAvatar() {
  return (
    <div
      className="w-7 h-7 rounded-full bg-lia-interactive-active flex items-center justify-center text-xs font-semibold text-lia-text-tertiary font-['Inter',sans-serif]"
      aria-hidden="true"
    >
      {CANDIDATE_INITIALS}
    </div>
  );
}

function LiaMessage({ html, time }: { html: string; time: string }) {
  return (
    <div className="flex gap-2.5 justify-start" aria-label="Mensagem da LIA">
      <div className="flex-shrink-0 mt-0.5">
        <LIAAvatar />
      </div>

      <div className="flex flex-col gap-1 max-w-[80%] items-start">
        <div className="flex items-center gap-1.5 px-1">
          <span className="text-xs font-bold text-lia-text-primary font-['Inter',sans-serif]">
            LIA
          </span>
          <span className="text-xs text-lia-text-disabled font-['Inter',sans-serif] tabular-nums">
            {time}
          </span>
        </div>

        <div className="flex items-end gap-1.5">
          <div
            className="px-3.5 py-2.5 text-sm leading-relaxed bg-wedo-cyan/[0.04] text-lia-text-primary rounded-[14px] rounded-bl-[4px]"
            dangerouslySetInnerHTML={{ __html: html }}
          />
          <button
            type="button"
            aria-label="Ouvir mensagem"
            className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-transparent text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
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
    <div className="flex gap-2.5 justify-end" aria-label="Sua mensagem">
      <div className="flex flex-col gap-1 max-w-[80%] items-end">
        <div className="flex items-end gap-1.5">
          <div className="px-3.5 py-2.5 text-sm leading-relaxed bg-lia-bg-tertiary text-lia-text-secondary rounded-[14px] rounded-br-[4px]">
            {text}
          </div>
        </div>
        <span className="text-xs text-lia-text-disabled font-['Inter',sans-serif] tabular-nums px-1">
          {time}
        </span>
      </div>

      <div className="flex-shrink-0 mt-0.5">
        <CandidateAvatar />
      </div>
    </div>
  );
}

function MultipleChoiceCard({
  options,
}: {
  options: { id: string; label: string }[];
}) {
  return (
    <div className="mx-4 my-2 space-y-3" role="group">
      <div className="flex flex-col gap-2">
        {options.map((option) => (
          <button
            key={option.id}
            type="button"
            className="w-full min-h-[44px] px-4 py-3 text-sm text-left rounded-lg font-medium transition-colors duration-200 bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-primary border border-lia-border-default dark:border-lia-border-default hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated"
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function ProgressBar({
  currentBlock,
  totalBlocks,
  blockName,
  percentage,
}: {
  currentBlock: number;
  totalBlocks: number;
  blockName: string;
  percentage: number;
}) {
  return (
    <div
      className="sticky top-0 z-20 bg-lia-bg-primary dark:bg-lia-bg-secondary border-b border-lia-border-subtle dark:border-lia-border-subtle px-4 py-3"
      role="progressbar"
      aria-valuenow={currentBlock}
      aria-valuemin={0}
      aria-valuemax={totalBlocks}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-lia-text-secondary">
          Etapa{" "}
          <span className="font-['Inter',sans-serif]">{currentBlock}</span> de{" "}
          <span className="font-['Inter',sans-serif]">{totalBlocks}</span>
          {" · "}
          {blockName}
        </span>
        <span className="text-micro font-['Inter',sans-serif] text-lia-text-disabled">
          {percentage}%
        </span>
      </div>
      <div className="w-full h-1.5 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-full overflow-hidden">
        <div
          className="h-full bg-lia-btn-primary-bg rounded-full transition-[width] duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function InputBar() {
  return (
    <div className="sticky bottom-0 z-10 bg-lia-bg-primary dark:bg-lia-bg-secondary border-t border-lia-border-subtle dark:border-lia-border-subtle px-4 py-3">
      <div className="flex items-end gap-2">
        <button
          type="button"
          aria-label="Ativar leitura automática"
          title="Leitura automática desativada"
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg border border-lia-border-default dark:border-lia-border-default text-lia-text-tertiary hover:text-lia-text-secondary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated transition-colors"
        >
          <VolumeX className="w-4 h-4" />
        </button>

        <textarea
          rows={1}
          placeholder="Digite sua resposta..."
          aria-label="Campo de resposta"
          className="flex-1 resize-none w-full px-3 py-2 text-sm border border-lia-border-default dark:border-lia-border-default rounded-lg bg-lia-bg-primary dark:bg-lia-bg-primary text-lia-text-primary placeholder-lia-input-placeholder dark:placeholder-lia-input-placeholder focus:border-lia-input-border-focus dark:focus:border-lia-input-border-focus focus:ring-2 focus:ring-wedo-cyan/20 focus:outline-none"
          readOnly
        />

        <button
          type="button"
          aria-label="Gravar resposta por voz"
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg border border-lia-border-default dark:border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-secondary text-lia-text-tertiary hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-elevated hover:text-wedo-cyan transition-colors"
        >
          <Mic className="w-4 h-4" />
        </button>

        <button
          type="button"
          aria-label="Enviar mensagem"
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover transition-colors disabled:opacity-50"
          disabled
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function LGPDFooter() {
  return (
    <div className="py-3 px-4 text-center">
      <p className="text-micro text-lia-text-tertiary dark:text-lia-text-secondary">
        Powered by <span className="text-wedo-cyan font-medium">LIA</span> · WeDOTalent ·{" "}
        <a
          href="/privacidade"
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-lia-text-primary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none"
          aria-label="Saiba mais sobre avaliação por IA"
        >
          Política de Privacidade
        </a>
      </p>
    </div>
  );
}

export function ChatScreen() {
  return (
    <div className="h-screen w-full bg-lia-bg-primary dark:bg-lia-bg-primary flex justify-center overflow-hidden">
      <div
        className="max-w-[640px] w-full mx-auto h-screen bg-lia-bg-secondary dark:bg-lia-bg-primary flex flex-col rounded-xl overflow-hidden"
        role="main"
        aria-label="Chat de triagem"
      >
        <ProgressBar
          currentBlock={5}
          totalBlocks={11}
          blockName="Habilidades Comportamentais"
          percentage={45}
        />

        <div
          className="flex-1 overflow-y-auto px-4 py-4 space-y-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          role="log"
          aria-live="polite"
          aria-label="Mensagens da triagem"
        >
          <LiaMessage
            html={`Oi, ${CANDIDATE_NAME.split(" ")[0]}! Eu sou a <strong>LIA</strong>. Vamos conversar sobre a vaga de <strong>Analista de Customer Success Pleno</strong> na Aurora Tecnologia. Pode responder por texto, áudio ou múltipla escolha.`}
            time="14:32"
          />

          <CandidateMessage
            text="Oi, LIA! Pode mandar, estou pronta. Tenho 4 anos de CS em SaaS B2B."
            time="14:33"
          />

          <LiaMessage
            html={`Conta pra mim uma situação recente em que você precisou <strong>recuperar um cliente em risco de churn</strong>. O que você fez e qual foi o resultado?`}
            time="14:33"
          />

          <CandidateMessage
            text="Cliente enterprise com NPS em queda. Montei plano de sucesso, revisões quinzenais e roadmap conjunto. Em 90 dias: NPS +28 pontos e renovação com upsell de 22%."
            time="14:35"
          />

          <LiaMessage
            html={`Excelente — adorei a clareza dos números. Agora uma situação hipotética: <strong>três contas estratégicas abrem ticket crítico ao mesmo tempo</strong> e seu time de suporte está sobrecarregado. Como você prioriza?`}
            time="14:36"
          />

          <MultipleChoiceCard
            options={[
              {
                id: "a",
                label:
                  "Atendo primeiro o cliente com maior ARR e comunico os outros dois com previsão.",
              },
              {
                id: "b",
                label:
                  "Avalio impacto no negócio de cada caso antes de definir a ordem de atendimento.",
              },
              {
                id: "c",
                label:
                  "Escalo internamente, mobilizo um responsável por conta e acompanho os três de perto.",
              },
            ]}
          />
        </div>

        <InputBar />
        <LGPDFooter />
      </div>
    </div>
  );
}
