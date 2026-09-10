export type ScanCheck = { key: string; label: string; points: number; max: number; passed: boolean; detail: string };

const AGENTS = ["GPTBot", "ChatGPT-User", "Google-Extended", "ClaudeBot", "Claude-Web", "PerplexityBot", "Applebot-Extended"];

export function normalizeDomain(input: string) {
  const raw = String(input || "").trim();
  if (!raw) throw new Error("Domain is required");
  const withScheme = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  const url = new URL(withScheme);
  const host = url.hostname.toLowerCase().replace(/^www\./, "");
  if (!host || !host.includes(".")) throw new Error("Enter a valid domain");
  return host;
}

async function get(url: string) {
  try {
    const res = await fetch(url, { redirect: "follow", signal: AbortSignal.timeout(8000), headers: { "user-agent": "X.page Scanner/1.0" } });
    const text = await res.text();
    return { ok: res.ok, status: res.status, text, url: res.url };
  } catch (error) {
    return { ok: false, status: 0, text: "", url, error: error instanceof Error ? error.message : String(error) };
  }
}

function readableText(html: string) {
  return html.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<[^>]+>/g, " ").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim();
}

function robotsAllowsAI(text: string) {
  if (!text.trim()) return true;
  const lower = text.toLowerCase();
  for (const agent of AGENTS) {
    const block = new RegExp(`user-agent:\\s*${agent.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}[\\s\\S]*?(?=user-agent:|$)`, "i").exec(lower)?.[0] || "";
    if (/disallow:\s*\//i.test(block)) return false;
  }
  const wildcard = /user-agent:\s*\*[\s\S]*?(?=user-agent:|$)/i.exec(lower)?.[0] || "";
  return !/disallow:\s*\/$/im.test(wildcard);
}

function usefulSchema(html: string) {
  const hasLd = /application\/ld\+json/i.test(html);
  const businessType = /LocalBusiness|Organization|ProfessionalService|Store|Restaurant|Corporation/i.test(html);
  const fields = ["name", "address", "telephone", "url", "openingHours", "priceRange", "areaServed"].filter((k) => new RegExp(`\"${k}\"\\s*:`, "i").test(html));
  return hasLd && businessType && fields.length >= 3;
}

function usefulLlms(text: string) {
  const lower = text.toLowerCase();
  const groups = [
    ["service", "services", "offer", "offers", "product", "products"],
    ["contact", "phone", "email", "book", "booking"],
    ["hours", "open", "opening hours"],
    ["address", "location", "service area", "areas served"]
  ];
  return groups.filter((g) => g.some((term) => lower.includes(term))).length >= 3 && text.trim().length >= 120;
}

export async function scanSite(input: string) {
  const domain = normalizeDomain(input);
  const base = `https://${domain}`;
  const [home, robots, llms] = await Promise.all([get(base), get(`${base}/robots.txt`), get(`${base}/llms.txt`)]);
  const text = readableText(home.text);
  const checks: ScanCheck[] = [];
  const add = (key: string, label: string, max: number, passed: boolean, detail: string) => checks.push({ key, label, points: passed ? max : 0, max, passed, detail });

  add("https", "HTTPS homepage", 20, home.ok && home.url.startsWith("https://"), home.ok ? `Loaded ${home.status}` : `Could not load homepage${home.status ? ` (${home.status})` : ""}`);
  const allowed = robotsAllowsAI(robots.text);
  add("robots", "robots allow AI crawlers", 16, allowed, robots.ok ? (allowed ? "No blocking rule detected for major AI crawlers" : "A blocking rule was detected") : "robots.txt missing or unavailable; no explicit block detected");
  const schema = usefulSchema(home.text);
  add("schema", "useful business schema", 18, schema, schema ? "Business JSON-LD with useful fields detected" : "Add LocalBusiness/Organization JSON-LD with name, address, phone, hours and service area");
  add("text", "readable HTML text >800", 16, text.length > 800, `${text.length} readable characters detected`);
  const llmsExists = llms.ok && llms.text.trim().length > 0;
  add("llms-exists", "llms.txt exists", 10, llmsExists, llmsExists ? "llms.txt found" : "No usable /llms.txt found");
  const llmsUseful = llmsExists && usefulLlms(llms.text);
  add("llms-useful", "llms.txt useful", 20, llmsUseful, llmsUseful ? "Offer/contact/hours/location details detected" : "llms.txt should describe offer, contact/booking, hours and location/service area");

  const score = checks.reduce((sum, c) => sum + c.points, 0);
  const status = score >= 80 ? "agent-ready" : score >= 50 ? "needs-work" : "invisible";
  const next = checks.filter((c) => !c.passed).map((c) => c.detail).slice(0, 3);
  return { domain, score, status, checks, next, page: `/p/${domain}` };
}
