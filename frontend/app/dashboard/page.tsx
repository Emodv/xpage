"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import type { Lead, LeadStatus } from "@/lib/types";

const STATUS_STYLES: Record<LeadStatus, string> = {
  new: "bg-blue-100 text-blue-700",
  qualified: "bg-amber-100 text-amber-700",
  booked: "bg-green-100 text-green-700",
  lost: "bg-slate-200 text-slate-600",
};

export default function DashboardPage() {
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [statusFilter, setStatusFilter] = useState<LeadStatus | "all">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      if (!user) return;

      // A dashboard user typically belongs to exactly one tenant (their business).
      const { data: membership } = await supabase
        .from("tenant_users")
        .select("tenant_id")
        .eq("user_id", user.id)
        .limit(1)
        .single();

      if (!membership) {
        setLoading(false);
        return;
      }
      setTenantId(membership.tenant_id);

      const { data: leadRows } = await supabase
        .from("leads")
        .select("*")
        .eq("tenant_id", membership.tenant_id)
        .order("updated_at", { ascending: false });

      setLeads(leadRows ?? []);
      setLoading(false);
    }
    load();
  }, []);

  useEffect(() => {
    if (!tenantId) return;

    const channel = supabase
      .channel(`leads-${tenantId}`)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "leads", filter: `tenant_id=eq.${tenantId}` },
        (payload) => {
          setLeads((current) => {
            const incoming = payload.new as Lead;
            if (payload.eventType === "DELETE") {
              return current.filter((l) => l.id !== (payload.old as Lead).id);
            }
            const withoutIncoming = current.filter((l) => l.id !== incoming.id);
            return [incoming, ...withoutIncoming].sort(
              (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
            );
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [tenantId]);

  const visibleLeads = statusFilter === "all" ? leads : leads.filter((l) => l.status === statusFilter);

  if (loading) return <p className="text-sm text-slate-500">Loading leads...</p>;

  if (!tenantId) {
    return (
      <p className="text-sm text-slate-500">
        Your account isn&apos;t linked to a business yet. Ask your admin to add you to a tenant.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        {(["all", "new", "qualified", "booked", "lost"] as const).map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`rounded-full px-3 py-1 text-sm capitalize ${
              statusFilter === status ? "bg-slate-900 text-white" : "bg-white text-slate-600 border border-slate-200"
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Lead</th>
              <th className="px-4 py-3 font-medium">Channel</th>
              <th className="px-4 py-3 font-medium">Service</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {visibleLeads.map((lead) => (
              <tr key={lead.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link href={`/dashboard/leads/${lead.id}`} className="font-medium text-slate-900 hover:underline">
                    {lead.display_name || lead.phone || lead.external_id}
                  </Link>
                </td>
                <td className="px-4 py-3 capitalize">{lead.channel}</td>
                <td className="px-4 py-3">{lead.service_needed || "—"}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[lead.status]}`}>
                    {lead.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500">{new Date(lead.updated_at).toLocaleString()}</td>
              </tr>
            ))}
            {visibleLeads.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No leads yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
