"use client"
import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function NovoProjetoRoute() {
  const router = useRouter()
  useEffect(() => { router.replace("/pt/projetos") }, [router])
  return null
}
