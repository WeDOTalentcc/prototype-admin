import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PATCH } = createProxyHandlers({
  backendPath: "/api/v1/interview-notes/:noteId",
  methods: ["GET", "PATCH"],
  backendTarget: "fastapi",
})
