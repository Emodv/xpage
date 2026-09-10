export default function HomePage() {
  return (
    <main className="shell">
      <nav className="nav"><a className="brand" href="/">X.PAGE</a><div className="navlinks"><a href="/scan">Scan</a><a href="/llms.txt">llms.txt</a></div></nav>
      <section className="hero">
        <p className="eyebrow">BUSINESS IDENTITY FOR AI AGENTS</p>
        <h1>Businesses are invisible to AI agents.</h1>
        <p className="lede">X.page scores the gap and hosts a verified page an agent can cite.</p>
        <div className="actions"><a className="button primary" href="/scan">Scan your site</a><a className="button" href="/p/example.com">View agent page</a></div>
      </section>
      <section className="section">
        <p className="eyebrow">HOW IT WORKS</p>
        <div className="grid">
          <div className="card"><div className="metric">01</div><h2>Scan</h2><p className="muted">Check HTTPS, crawler access, schema, readable text and llms.txt.</p></div>
          <div className="card"><div className="metric">02</div><h2>Fix the gap</h2><p className="muted">Turn missing machine-readable identity into concrete next actions.</p></div>
          <div className="card"><div className="metric">03</div><h2>Get cited</h2><p className="muted">Publish a structured X.page profile an AI agent can discover and cite.</p></div>
        </div>
      </section>
      <section className="section"><p className="eyebrow">GTA LAUNCH</p><h2>Built for real local businesses, starting in the Greater Toronto Area.</h2><p className="lede">One identity layer for humans, search engines and autonomous agents.</p></section>
      <footer className="footer">X.page · Toronto, Canada · Verified business identity for AI agents.</footer>
    </main>
  );
}
