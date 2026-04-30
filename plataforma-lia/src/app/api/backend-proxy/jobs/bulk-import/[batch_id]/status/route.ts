import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/jobs/bulk-import/:batch_id/status",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
