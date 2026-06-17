import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Migrado de proxy hand-rolled (res.text() passthrough) para
// createProxyHandlers, que desembrulha o ResponseEnvelopeMiddleware do
// FastAPI ({ok,data,meta}). Sem unwrap, o FE recebia data.data aninhado
// (bug "Banco criado mas nao foi possivel abrir"). Encaminha query string,
// params dinamicos, body e auth headers automaticamente.
// Backend usa paths distintos por metodo: GET /candidates, POST /add_candidates.
const list = createProxyHandlers({ backendPath: "/api/v1/talent_pools/:id/candidates", methods: ["GET"] })
const add = createProxyHandlers({ backendPath: "/api/v1/talent_pools/:id/add_candidates", methods: ["POST"] })

// Next.js exige string literal estática neste export (não pode ser
// member-expression como `list.dynamic`, que quebra o build com
// "Unsupported node type MemberExpression at dynamic"). O valor é o mesmo
// que createProxyHandlers usa internamente.
export const dynamic = "force-dynamic"
export const GET = list.GET
export const POST = add.POST
