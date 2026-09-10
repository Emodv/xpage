export default async function AgentPage({ params }: { params: Promise<{ domain: string }> }) {
  const { domain } = await params;
  const decoded = decodeURIComponent(domain);
  return <main className="shell scanner">
    <nav className="nav"><a className="brand" href="/">X.PAGE</a><div className="navlinks"><a href="/scan">Scan</a></div></nav>
    <p className="eyebrow">DRAFT AGENT PAGE</p>
    <h1>{decoded}</h1>
    <p className="lede">This route is reserved for a verified, structured business identity that AI agents can discover and cite.</p>
    <div className="card"><h2>Verification status</h2><p className="muted">Unverified draft. No business claims are published until verified.</p></div>
    <div className="actions"><a className="button primary" href={`/scan?domain=${encodeURIComponent(decoded)}`}>Scan this domain</a></div>
  </main>;
}
