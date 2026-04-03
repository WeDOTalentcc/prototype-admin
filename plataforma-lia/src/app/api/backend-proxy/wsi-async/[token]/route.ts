export const dynamic = "force-dynamic"
import { NextResponse } from "next/server";
import { validateParams } from '@/lib/api/validate'
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const routeParamsSchema = z.object({
  token: z.string().min(1, 'token is required'),
})


export async function GET(
  req: Request,
  { params }: { params: { token: string } }
) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/wsi/async/${params.token}`, {
      headers: { "Content-Type": "application/json" },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });
  }
}

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(
  req: Request,
  { params }: { params: { token: string } }
) {
  try {
    const body = await req.json();
    const url = new URL(req.url);
    const path = url.pathname.includes("/answer") ? "answer" : "complete";
    const res = await fetch(`${BACKEND_URL}/api/v1/wsi/async/${params.token}/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 503 });
  }
}
