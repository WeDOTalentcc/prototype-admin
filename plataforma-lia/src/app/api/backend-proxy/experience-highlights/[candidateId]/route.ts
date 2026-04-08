import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, DELETE } = createProxyHandlers({
  backendPath: "/api/v1/experience-highlights/:candidateId",
  methods: ["GET", "DELETE"],
  auth: false,
})
