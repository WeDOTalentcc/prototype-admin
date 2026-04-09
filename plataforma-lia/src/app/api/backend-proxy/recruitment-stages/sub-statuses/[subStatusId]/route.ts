import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, PUT, DELETE, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/recruitment-stages/sub-statuses/:subStatusId",
  methods: ["PUT", "DELETE", "PATCH"],
  backendTarget: "fastapi",
})
