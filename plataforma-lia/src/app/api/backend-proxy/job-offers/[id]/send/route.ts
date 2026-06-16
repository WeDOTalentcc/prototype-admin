import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/job-offers/:id/send",
  methods: ["PATCH"],
  auth: true,
  backendTarget: "fastapi",
})
