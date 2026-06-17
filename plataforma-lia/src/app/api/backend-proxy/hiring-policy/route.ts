import { createProxyHandlers } from "@/lib/api/proxy-handler"
import { resolveCompanyId } from "@/lib/api/resolve-company-id"
import { NextRequest } from "next/server"

export const { dynamic, GET: _rawGET, PUT: _rawPUT } = createProxyHandlers({
  backendPath: "/api/v1/company-hiring-policy/:companyId",
  methods: ["GET", "PUT"],
  auth: true,
  backendTarget: "fastapi",
})

async function withCompanyId(
  request: NextRequest,
  handler: (req: NextRequest, ctx: { params: Promise<Record<string, string>> }) => Promise<Response>,
): Promise<Response> {
  const companyId = await resolveCompanyId(request)
  if (!companyId) {
    return Response.json({ error: "Company ID não disponível" }, { status: 401 })
  }
  return handler(request, { params: Promise.resolve({ companyId }) })
}

export async function GET(request: NextRequest) {
  return withCompanyId(request, _rawGET)
}

export async function PUT(request: NextRequest) {
  return withCompanyId(request, _rawPUT)
}
