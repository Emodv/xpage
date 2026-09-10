import { NextResponse } from "next/server";
import { scanSite } from "../../../../scan/scan";

export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => ({}));
    const domain = typeof body?.domain === "string" ? body.domain : "";
    const result = await scanSite(domain);
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : String(error) }, { status: 400 });
  }
}
