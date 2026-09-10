"use client";

import { FormEvent, useState } from "react";

type Check = { key:string; label:string; points:number; max:number; passed:boolean; detail:string };
type Scan = { domain:string; score:number; status:string; checks:Check[]; next:string[]; page:string };

export default function ScanPage(){
  const [domain,setDomain]=useState("");
  const [result,setResult]=useState<Scan|null>(null);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  async function submit(e:FormEvent){
    e.preventDefault(); setError(""); setResult(null); setLoading(true);
    try{
      const res=await fetch("/api/scan",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({domain})});
      const data=await res.json();
      if(!res.ok) throw new Error(typeof data?.error==="string"?data.error:"Scan failed");
      setResult(data);
    }catch(err){setError(err instanceof Error?err.message:String(err));}
    finally{setLoading(false);}
  }
  return <main className="shell scanner">
    <nav className="nav"><a className="brand" href="/">X.PAGE</a><div className="navlinks"><a href="/">Home</a></div></nav>
    <p className="eyebrow">AI VISIBILITY SCAN</p><h1>Can an agent understand your business?</h1><p className="lede">A 100-point diagnostic based on machine-readable usefulness, not vanity metrics.</p>
    <form className="form" onSubmit={submit}><input className="input" value={domain} onChange={e=>setDomain(e.target.value)} placeholder="example.com" aria-label="Domain"/><button className="button primary" disabled={loading}>{loading?"Scanning…":"Scan site"}</button></form>
    {error?<div className="error">{error}</div>:null}
    {result?<section className="result"><div className="score">{result.score}</div><p className="eyebrow">{result.status}</p><div className="checks">{result.checks.map(c=><div className="check" key={c.key}><div><strong>{c.label}</strong><div className="small">{c.detail}</div></div><div className="pass">{c.points}/{c.max}</div></div>)}</div><div className="actions"><a className="button primary" href={result.page}>Get an agent page</a></div></section>:null}
  </main>;
}
