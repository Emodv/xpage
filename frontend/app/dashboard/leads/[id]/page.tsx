"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { supabase } from "@/lib/supabaseClient";
import { resumeAi, sendManualReply } from "@/lib/api";
import type { Lead, Message } from "@/lib/types";

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [lead, setLead] = useState<Lead | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const { data: leadRow } = await supabase.from("leads").select("*").eq("id", id).single();
      setLead(leadRow);

      const { data: messageRows } = await supabase
        .from("messages")
        .select("*")
        .eq("lead_id", id)
        .order("created_at", { ascending: true });
      setMessages(messageRows ?? []);
    }
    load();
  }, [id]);

  useEffect(() => {
    const channel = supabase
      .channel(`messages-${id}`)
      .on(
        "postgres_changes",
        { event: "INSERT", schema: "public", table: "messages", filter: `lead_id=eq.${id}` },
        (payload) => {
          setMessages((current) => [...current, payload.new as Message]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [id]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!reply.trim()) return;
    setSending(true);
    setError(null);
    try {
      await sendManualReply(id, reply.trim());
      setReply("");
      setLead((current) => (current ? { ...current, ai_enabled: false } : current));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setSending(false);
    }
  }

  async function handleResumeAi() {
    await resumeAi(id);
    setLead((current) => (current ? { ...current, ai_enabled: true } : current));
  }

  if (!lead) return <p className="text-sm text-slate-500">Loading...</p>;

  return (
    <div className="space-y-6">
      <button onClick={() => router.push("/dashboard")} className="text-sm text-slate-500 hover:underline">
        &larr; Back to leads
      </button>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">{lead.display_name || lead.phone || lead.external_id}</h2>
            <p className="text-sm text-slate-500">
              {lead.channel} · {lead.status} · {lead.language === "fa" ? "Farsi" : "English"}
            </p>
          </div>
          {!lead.ai_enabled && (
            <button onClick={handleResumeAi} className="rounded-md border border-slate-300 px-3 py-1.5 text-sm">
              Resume AI
            </button>
          )}
        </div>
        <dl className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div>
            <dt className="text-slate-400">Service</dt>
            <dd>{lead.service_needed || "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Budget</dt>
            <dd>{lead.budget || "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-400">Timeline</dt>
            <dd>{lead.timeline || "—"}</dd>
          </div>
        </dl>
      </div>

      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-5">
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.direction === "out" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-md rounded-lg px-3 py-2 text-sm ${
                m.direction === "out"
                  ? m.ai_generated
                    ? "bg-slate-900 text-white"
                    : "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-900"
              }`}
            >
              {m.body}
              {m.direction === "out" && (
                <div className="mt-1 text-[10px] opacity-70">{m.ai_generated ? "AI" : "You"}</div>
              )}
            </div>
          </div>
        ))}
        {messages.length === 0 && <p className="text-sm text-slate-400">No messages yet.</p>}
      </div>

      <form onSubmit={handleSend} className="flex gap-2">
        <input
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          placeholder="Write a manual reply (this turns off AI for this lead)..."
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={sending}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
