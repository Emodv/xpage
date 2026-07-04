const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

export async function sendManualReply(leadId: string, text: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/leads/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lead_id: leadId, text }),
  });
  if (!response.ok) {
    throw new Error(`Failed to send reply: ${response.status}`);
  }
}

export async function resumeAi(leadId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/resume-ai`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to resume AI: ${response.status}`);
  }
}
