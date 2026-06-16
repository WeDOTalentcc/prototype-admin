import { z } from "zod"

export const jobBasicSchema = z.object({
  title: z.string().min(3, "Título deve ter no mínimo 3 caracteres").max(100),
  department: z.string().min(1, "Departamento é obrigatório"),
  location: z.string().min(1, "Local é obrigatório"),
  employmentType: z.enum(["CLT", "PJ", "Estágio", "Temporário", "Freelancer"]),
  salaryMin: z.number().min(0).optional(),
  salaryMax: z.number().min(0).optional(),
  description: z.string().min(10, "Descrição deve ter no mínimo 10 caracteres"),
})

export type JobBasicFormData = z.infer<typeof jobBasicSchema>
