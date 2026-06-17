import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/job-vacancies/search",
  methods: ["GET"],
  defaultParams: {
    query: "",
    page: "1",
    page_size: "10",
  },
})
