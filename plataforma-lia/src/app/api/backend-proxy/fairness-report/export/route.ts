export const dynamic = "force-dynamic"
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8001";
  const params = searchParams.toString();

  try {
    const response = await fetch(
      `${backendUrl}/api/v1/fairness/reports/export${params ? `?${params}` : ""}`,
      {
        headers: {
          Authorization: req.headers.get("Authorization") || "",
        },
      }
    );
    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "text/csv",
        "Content-Disposition":
          response.headers.get("Content-Disposition") ||
          "attachment; filename=fairness_report.csv",
      },
    });
  } catch (err) {
    return NextResponse.json({ error: "export_unavailable" }, { status: 503 });
  }
}
