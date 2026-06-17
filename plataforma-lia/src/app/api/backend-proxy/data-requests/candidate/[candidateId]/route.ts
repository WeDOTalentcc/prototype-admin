import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/data-requests/candidate/:candidateId",
  methods: ["GET"],
  backendTarget: "fastapi",
})
