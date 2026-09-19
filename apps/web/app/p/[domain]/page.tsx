import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Provider profile — CityVerified",
  description: "CityVerified provider profile. Business claims remain unpublished until evidence-qualified and verified.",
  robots: { index: false, follow: true }
};

export default async function AgentPage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  const decoded = decodeURIComponent(domain);
  return <main className="shell scanner">
    <nav className="nav"><a className="brand" href="/">CITYVERIFIED.CA</a><div className="navlinks"><a href="/scan">Scan</a></div></nav>
    <p className="eyebrow">PROVIDER PROFILE</p>
    <h1>{decoded}</h1>
    <p className="lede">This profile is reserved for evidence-qualified, structured business information that AI agents and people can evaluate.</p>
    <div className="card"><h2>Verification status</h2><p className="muted">Unverified draft. No business claims are published until verified.</p></div>
    <div className="actions"><a className="button primary" href={`/scan?domain=${encodeURIComponent(decoded)}`}>Scan this domain</a></div>
  </main>;
}
