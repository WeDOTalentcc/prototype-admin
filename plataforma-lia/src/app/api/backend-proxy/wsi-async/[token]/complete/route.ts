export const dynamic = "force-dynamic"
import { NextResponse } from "next/server";
import { z } from 'zod'
import { validateParams } from '@/lib/api/validate'

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const routeParamsSchema = z.object({
  token: z.string().min(1, 'token is required'),
})

export async function GET(
  req: Request,
  { params }: { params: { token: string } }
) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/wsi/async/${params.token}/complete`, {
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });
  }
}
