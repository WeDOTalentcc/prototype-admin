export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod'

const BACKEND_URL = process.env.LIA_BACKEND_URL || 'http://localhost:8000';

const _bodySchema = z.record(z.unknown())

export async function POST(request: NextRequest) {
  try {
    const body = _bodySchema.parse(await request.json());
    
    const response = await fetch(`${BACKEND_URL}/api/v1/lia/job-wizard/interpret`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${response.status}`, details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to interpret message', details: String(error) },
      { status: 500 }
    );
  }
}
