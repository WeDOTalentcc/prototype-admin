export const dynamic = "force-dynamic"
import { NextResponse } from "next/server";
import { z } from 'zod'

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const _bodySchema = z.record(z.string(), z.unknown())

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/api/v1/wsi/async/invite`, {
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
