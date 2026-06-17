import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/jobs/:id/pipeline",
  methods: ["GET", "PUT"],
  backendTarget: "fastapi",
})
