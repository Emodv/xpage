export type LeadStatus = "new" | "qualified" | "booked" | "lost";
export type Channel = "whatsapp" | "telegram";

export interface Lead {
  id: string;
  tenant_id: string;
  channel: Channel;
  external_id: string;
  display_name: string | null;
  phone: string | null;
  language: string | null;
  service_needed: string | null;
  budget: string | null;
  timeline: string | null;
  status: LeadStatus;
  ai_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  tenant_id: string;
  lead_id: string;
  direction: "in" | "out";
  channel: Channel;
  body: string;
  ai_generated: boolean;
  created_at: string;
}

export interface Appointment {
  id: string;
  tenant_id: string;
  lead_id: string;
  calendar_event_id: string | null;
  start_time: string;
  end_time: string;
  status: "scheduled" | "completed" | "no_show" | "cancelled";
  revenue_amount: number | null;
  created_at: string;
}
