/**
 * Sensor: Onda 2 (PLAN_FIX_wizard_memory_loss 2026-05-10) — useWizardFlow
 * extrai e propaga thread_id do payload `lia:wizard-stage-payload`.
 *
 * Backend (Onda 2 commit anterior) ja envia thread_id no evento WS
 * wizard_stage. Esse sensor garante que o frontend:
 *   1. Recebe thread_id no detail do CustomEvent emitido por useChatSocket
 *   2. Despacha SET_THREAD no reducer quando recebe novo thread_id
 *   3. Inclui thread_id no envelope de mensagens subsequentes do wizard
 *
 * Pattern canonical: guards estruturais via regex sobre source code
 * (mesmo padrao de useChatTransport.metadata.test.ts), nao runtime mocks.
 *
 * Disciplinas CLAUDE.md aplicadas:
 *   - TDD-IA red-green-refactor: RED hoje (thread_id ausente em 3 callsites),
 *     GREEN apos fix Onda 2.E.
 *   - harness-engineering: sensor computacional sobre source.
 *   - canonical-fix: minimal regex assertions.
 */
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { describe, expect, test } from "vitest"

const SOCKET_SRC = readFileSync(
  join(__dirname, "..", "..", "..", "..", "hooks", "chat", "useChatSocket.ts"),
  "utf8",
)
const WIZARD_SRC = readFileSync(
  join(__dirname, "..", "useWizardFlow.ts"),
  "utf8",
)
const CONTRACT_SRC = readFileSync(
  join(__dirname, "..", "..", "..", "..", "types", "generated", "wizard-contract.ts"),
  "utf8",
)

describe("Onda 2 FE — thread_id propagation across wizard_stage events", () => {
  test("Guard 1: useChatSocket includes thread_id in lia:wizard-stage-payload CustomEvent detail", () => {
    // Locate the dispatch of CustomEvent("lia:wizard-stage-payload", ...)
    const wizStageBlock = SOCKET_SRC.match(
      /lia:wizard-stage-payload[\s\S]{0,600}/,
    )
    expect(wizStageBlock).not.toBeNull()
    const block = wizStageBlock![0]
    expect(block).toMatch(/thread_id\s*:\s*wsEvent\.thread_id/)
  })

  test("Guard 2: useWizardFlow subscriber dispatches SET_THREAD when payload.thread_id present", () => {
    // The handle() function inside the lia:wizard-stage-payload subscriber
    // must dispatch SET_THREAD when payload contains a non-empty thread_id.
    const subscriberBlock = WIZARD_SRC.match(
      /addEventListener\("lia:wizard-stage-payload"[\s\S]{0,1000}/,
    )
    // Subscriber lives just above (in the useEffect with handle)
    const handleBlock = WIZARD_SRC.match(
      /function\s+handle\s*\(event:\s*Event\)[\s\S]{0,800}/,
    )
    expect(handleBlock).not.toBeNull()
    const block = handleBlock![0]
    // After validating payload.type === "wizard_stage", must dispatch SET_THREAD
    expect(block).toMatch(/dispatch\(\s*\{\s*type:\s*"SET_THREAD"/)
    expect(block).toMatch(/payload\.thread_id/)
  })

  test("Guard 3: useWizardFlow state holds threadId via reducer SET_THREAD case", () => {
    // SET_THREAD reducer case sets state.threadId from action.threadId
    expect(WIZARD_SRC).toMatch(/case\s+"SET_THREAD"[\s\S]{0,200}threadId\s*:\s*action\.threadId/)
  })

  test("Guard 4: WizardStagePayload type optional thread_id field declared (auto-generated)", () => {
    // Type signature lives in the auto-generated wizard-contract.ts
    // (regenerated from app/contracts/wizard_contract.py). thread_id is
    // an optional ThreadId alias of string in the generated TS file.
    expect(CONTRACT_SRC).toMatch(/thread_id\?\s*:\s*ThreadId/)
  })
})
