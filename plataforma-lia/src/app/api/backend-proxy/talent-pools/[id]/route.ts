import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Migrado de proxy hand-rolled (res.text() passthrough) para
// createProxyHandlers, que desembrulha o ResponseEnvelopeMiddleware do
// FastAPI ({ok,data,meta}). Sem unwrap, o FE recebia data.data aninhado
// (bug "Banco criado mas nao foi possivel abrir"). Encaminha query string,
// params dinamicos, body e auth headers automaticamente.
export const { dynamic, GET, PATCH, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/talent_pools/:id",
  methods: ["GET", "PATCH", "DELETE"],
})
