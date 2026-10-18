import { useEffect, useRef, useState } from 'react'
import GraphCanvas from './components/GraphCanvas'
import { api, preset, validateGraph } from './api'
import './App.css'

const topics = {coloring:'Vertex coloring',planarity:'Planarity',bipartite:'Bipartiteness',connectivity:'Connectivity & trees',eulerian:'Euler walks'}
const empty = {nodes:[],edges:[]}

function Instructor() {
  const [policy,setPolicy]=useState('')
  const [submissions,setSubmissions]=useState([])
  const [notice,setNotice]=useState('')
  const refresh=()=>api('/instructor/submissions').then(setSubmissions).catch(e=>setNotice(e.message))
  useEffect(()=>{api('/instructor/policy').then(p=>setPolicy(JSON.stringify(p,null,2))).catch(e=>setNotice(e.message));refresh()},[])
  return <section className="panel instructor"><h2>Course controls</h2><p>Release topics, set timezone-aware release_at dates, and register protected graphs. Protection recognizes vertex relabeling.</p>
    <label>Course policy JSON<textarea rows="10" value={policy} onChange={e=>setPolicy(e.target.value)} /></label>
    <button onClick={async()=>{try{await api('/instructor/policy',JSON.parse(policy),'PUT');setNotice('Course policy saved.')}catch(e){setNotice(e.message)}}}>Save policy</button>
    <p role="status">{notice}</p><h3>Written proofs awaiting review</h3>
    {submissions.map(s=><article key={s.id}><strong>{s.topic}</strong><pre>{JSON.stringify(JSON.parse(s.proof),null,2)}</pre>{[true,false].map(approve=><button key={String(approve)} onClick={async()=>{try{await api(`/instructor/submissions/${s.id}`,{approve});refresh()}catch(e){setNotice(e.message)}}}>{approve?'Approve':'Request revision'}</button>)}</article>)}
  </section>
}

function Result({result}) {
  if(!result) return null
  const d=result.data
  return <div className="result" role="status"><strong>{topics[result.topic]}</strong>
    {result.topic==='coloring' && <p>{d.exact?`Chromatic number: ${d.upper_bound}`:`Color bounds: ${d.lower_bound}–${d.upper_bound}. Optimality not established.`} Colors are labeled on the canvas.</p>}
    {result.topic==='planarity' && <p>{d.planar?'Planar — a crossing-free embedding exists. This drawing may still have crossings.':'Non-planar — changing this drawing cannot remove all crossings.'}</p>}
    {result.topic==='bipartite' && <p>{d.bipartite?'Bipartite: a two-part coloring is shown.':'Not bipartite.'}</p>}
    {result.topic==='connectivity' && <p>{d.components.length} component(s). {d.tree?'This graph is a tree.':'This graph is not a tree.'}</p>}
    {result.topic==='eulerian' && <p>{d.circuit?'Euler circuit exists.':d.trail?'Euler trail exists, but no circuit.':'No nonempty Euler trail.'} {d.walk.length>0?'Edge labels show traversal order. ':''}{d.convention}</p>}
  </div>
}

export default function App() {
  const [config,setConfig]=useState(null), [user,setUser]=useState(null), [ready,setReady]=useState(false)
  const [graph,setGraph]=useState(empty), [mode,setMode]=useState('vertex'), [past,setPast]=useState([]), [future,setFuture]=useState([])
  const [result,setResult]=useState(null), [rights,setRights]=useState({}), [error,setError]=useState(''), [busy,setBusy]=useState(false)
  const [name,setName]=useState('My graph'), [saved,setSaved]=useState([]), [topic,setTopic]=useState('planarity')
  const [proof,setProof]=useState(''), [witness,setWitness]=useState(''), [proofResult,setProofResult]=useState(null)
  const [message,setMessage]=useState(''), [chat,setChat]=useState([]), [assigned,setAssigned]=useState(false), [consent,setConsent]=useState(false)
  const [tab,setTab]=useState('explore')
  const version=useRef(0), file=useRef(null)
  const topology=JSON.stringify({nodes:graph.nodes.map(n=>({id:n.id})),edges:graph.edges})
  useEffect(()=>{Promise.all([api('/config').then(setConfig),api('/me').then(setUser).catch(()=>{})]).catch(e=>setError(e.message)).finally(()=>setReady(true))},[])
  useEffect(()=>{if(user) api('/graphs').then(setSaved).catch(e=>setError(e.message))},[user])
  useEffect(()=>{let cancelled=false;if(user) api('/access',JSON.parse(topology)).then(r=>{if(!cancelled)setRights(r)}).catch(e=>{if(!cancelled)setError(e.message)});return()=>{cancelled=true}},[topology,user])

  function change(next,moving=false) {
    try {validateGraph(next)} catch(e) {setError(e.message);return}
    if(!moving) setPast(p=>[...p.slice(-39),graph])
    setFuture([]);setGraph(next);if(!moving){setResult(null);setProofResult(null)}version.current++
  }
  async function action(fn) {setError('');setBusy(true);try{await fn()}catch(e){setError(e.message)}finally{setBusy(false)}}
  async function inspect(t) {
    setTopic(t)
    if(!rights[t]?.allowed) {setTab('proof');return}
    await action(async()=>{const v=version.current;const data=await api('/analyze',{graph,topic:t});if(v===version.current)setResult({topic:t,data})})
  }
  function undo(redo=false) {
    const source=redo?future:past
    if(!source.length)return
    const next=source.at(-1)
    if(redo){setFuture(source.slice(0,-1));setPast([...past,graph])}else{setPast(source.slice(0,-1));setFuture([...future,graph])}
    setGraph(next);setResult(null);setProofResult(null);version.current++
  }
  const refreshSaved=async()=>setSaved(await api('/graphs'))
  const adjacency=Object.fromEntries(graph.nodes.map(n=>[n.id,graph.edges.filter(e=>e.source===n.id||e.target===n.id).map(e=>e.source===n.id?e.target:e.source)]))

  if(!ready) return <main className="welcome"><h1>Opening Septimatica…</h1></main>
  if(!user) return <main className="welcome"><div className="brand">S<span>SEPTIMATICA / MATH 55</span></div><p className="eyebrow">A SPACE TO THINK VISUALLY</p><h1>Small graphs.<br/>Big discoveries.</h1><p className="intro">Build a graph, follow a conjecture, and find the joy in figuring it out. A graph theory notebook inspired by Harvey Mudd’s Discrete Mathematics course.</p>
    <a className={`button primary ${!config?.sso_configured?'disabled':''}`} href={config?.sso_configured?'/api/auth/login':undefined}>Continue with HMC SSO ↗</a>
    {!config?.sso_configured && <p>School sign-in awaits HMC IT’s application registration. No school passwords are collected here.</p>}
    {config?.demo_available && <button disabled={busy} onClick={()=>action(async()=>{await api('/auth/demo',{});setUser(await api('/me'))})}>Try a local practice session</button>}
    <p className="fine">Practice mode is not a school account. <a href="https://math.hmc.edu/su/math55/">Read the course’s AI policy</a>.</p><p role="alert">{error}</p></main>

  return <><header className="topbar"><div className="brand">S<span>SEPTIMATICA</span></div><nav>THE GRAPH NOTEBOOK <span className="tag">MATH 55</span></nav><div>{user.email} <button onClick={()=>action(async()=>{await api('/auth/logout',{});setUser(null);setGraph(empty);setChat([])})}>Sign out</button></div></header>
    <main className="workspace"><div className="heading"><div><p className="eyebrow">EXPLORE • CONJECTURE • JUSTIFY</p><h1>Make your thinking visible.</h1><p>Every edge is a possibility. What will you notice?</p></div><a href="https://math.hmc.edu/su/math55/" target="_blank" rel="noreferrer">Course & honor code ↗</a></div>
      {user.email==='demo@localhost' && <p className="banner">Local practice session · tools are open for exploration. School accounts follow instructor release and proof rules.</p>}
      {error && <div className="error" role="alert">{error}<button onClick={()=>setError('')}>Dismiss</button></div>}
      <div className="layout"><section className="graph-panel"><div className="canvas-heading"><input aria-label="Graph name" value={name} onChange={e=>setName(e.target.value)} maxLength="100"/><span>{graph.nodes.length} vertices · {graph.edges.length} edges</span></div>
        <div className="toolbar">{['vertex','edge','move','pan','erase'].map(m=><button key={m} className={mode===m?'active':''} onClick={()=>setMode(m)}>{m==='vertex'?'+ Vertex':m==='edge'?'↗ Edge':m==='move'?'↔ Move':m==='pan'?'✥ Pan':'− Erase'}</button>)}<span className="spacer"/><button disabled={!past.length} onClick={()=>undo()}>Undo</button><button disabled={!future.length} onClick={()=>undo(true)}>Redo</button></div>
        <GraphCanvas graph={graph} onChange={change} onMoveStart={()=>setPast(p=>[...p.slice(-39),graph])} mode={mode} result={result}/>
        <p className="canvas-hint">{mode==='vertex'?'Click empty space to add a vertex.':mode==='edge'?'Click two vertices to connect them.':mode==='move'?'Drag a vertex to rearrange your drawing.':mode==='pan'?'Drag the canvas to explore in any direction.':'Click a vertex or edge to remove it.'} Scroll to zoom · Shift-drag or middle-drag to pan in any mode. Unbounded workspace; analysis supports up to 80 vertices.</p>
        <div className="toolbar"><label>Start from <select defaultValue="" onChange={e=>{if(e.target.value)change(preset(e.target.value));e.target.value=''}}><option value="">an example…</option>{['Cycle','Tree','Petersen','K₅','K₃,₃'].map(n=><option key={n}>{n}</option>)}</select></label>
          <label>Arrange <select defaultValue="" disabled={busy} onChange={e=>{const method=e.target.value;if(method)action(async()=>{const v=version.current;const pos=await api('/layout',{graph,method});if(v===version.current)change({...graph,nodes:graph.nodes.map(n=>({...n,...pos[n.id]}))})});e.target.value=''}}><option value="">layout…</option><option value="spring">Force-directed</option><option value="circular">Circular</option><option value="spectral">Spectral</option></select></label><button onClick={()=>change(empty)}>Clear</button></div>
        <Result result={result}/>
        <details><summary>See the adjacency list & matrix</summary><pre>{JSON.stringify(adjacency,null,2)}</pre><div className="matrix"><table><thead><tr><th>v</th>{graph.nodes.map(n=><th key={n.id}>{n.id}</th>)}</tr></thead><tbody>{graph.nodes.map(n=><tr key={n.id}><th>{n.id}</th>{graph.nodes.map(m=><td key={m.id}>{adjacency[n.id].includes(m.id)?1:0}</td>)}</tr>)}</tbody></table></div></details>
        <div className="toolbar"><button disabled={busy||!name.trim()} onClick={()=>action(async()=>{await api('/graphs',{name,graph});await refreshSaved()})}>Save to notebook</button><button onClick={()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(graph,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='graph.json';a.click();URL.revokeObjectURL(url)}}>Export JSON</button><button onClick={()=>file.current.click()}>Import JSON</button><input hidden ref={file} type="file" accept=".json" onChange={e=>{const f=e.target.files[0];if(f)action(async()=>{if(f.size>100000)throw new Error('Graph file is too large.');change(validateGraph(JSON.parse(await f.text()))) });e.target.value=''}}/></div>
        <details><summary>Your saved graphs ({saved.length})</summary>{saved.map(s=><div className="saved" key={s.id}><button onClick={()=>{change(validateGraph(s.graph));setName(s.name)}}>{s.name}</button><button aria-label={`Delete ${s.name}`} onClick={()=>action(async()=>{await api(`/graphs/${s.id}`,undefined,'DELETE');await refreshSaved()})}>Delete</button></div>)}</details>
      </section>
      <aside className="panel"><div className="tabs">{[['explore','Explore'],['proof','Show your thinking'],['chat','Tutor']].map(([id,label])=><button key={id} className={tab===id?'active':''} onClick={()=>setTab(id)}>{label}</button>)}</div>
        {tab==='explore' && <><p className="eyebrow">LOOK A LITTLE CLOSER</p><h2>What makes this graph tick?</h2><p>Choose a property to investigate. Course tools unlock as you demonstrate understanding.</p>{Object.entries(topics).map(([t,label])=><button className="tool" key={t} disabled={busy} onClick={()=>inspect(t)}><span>{label}</span><span>{rights[t]?.allowed?'Explore ↗':'Locked ◇'}</span></button>)}<p className="fine">Coloring reports proven optimality only when established; larger searches may return bounds.</p></>}
        {tab==='proof' && <><p className="eyebrow">YOUR REASONING COMES FIRST</p><h2>Show what you know.</h2><label>Investigate<select value={topic} onChange={e=>{setTopic(e.target.value);setProofResult(null)}}>{Object.entries(topics).map(([t,label])=><option key={t} value={t}>{label}</option>)}</select></label><p className="fine">{rights[topic]?.reason}</p><label>Your argument<textarea rows="6" value={proof} onChange={e=>setProof(e.target.value)} placeholder="I think… because… My claim follows from…" maxLength="6000"/></label>
          <details><summary>Add a checkable certificate (optional)</summary><p className="fine">Coloring/bipartite: {`{"colors":{"0":0,"1":1}}`}. Non-bipartite: {`{"odd_cycle":[0,1,2]}`}. Planarity: a rotation map (clockwise neighbors for each vertex), or five/six disjoint connected branch_sets forming a K₅/K₃,₃ minor. Six sets use the first three and last three as opposite parts.</p><textarea aria-label="Certificate JSON" rows="4" value={witness} onChange={e=>setWitness(e.target.value)} placeholder="{}"/></details>
          <button className="primary" disabled={busy||proof.trim().length<15} onClick={()=>action(async()=>{const v=version.current;const data=await api('/proofs',{graph,topic,proof,witness:witness.trim()?JSON.parse(witness):{}});if(v===version.current){setProofResult(data);setRights(await api('/access',graph))}})}>Check certificate / submit for review</button>
          {proofResult && <div className="result"><strong>{proofResult.valid?'Witness checked. Nice work!':'Saved for instructor review.'}</strong><p>{proofResult.claim}</p><p>{proofResult.note}</p>{proofResult.lean && <p>Lean: {proofResult.lean.status}. Scope: {proofResult.lean.scope}.</p>}</div>}<p className="fine">A certificate verifies a specific claim, not every sentence of your argument. Written proofs need instructor approval to unlock tools. A proper coloring alone does not prove minimality; coloring unlocks require instructor review.</p></>}
        {tab==='chat' && <><p className="eyebrow">A NUDGE, NOT THE ANSWER</p><h2>Think it through together.</h2><p>Gemini sees your current graph and your question. It offers hints and informal feedback, not formal proof certification.</p><label className="check"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>Send my graph and messages to Google Gemini.</label><label className="check"><input type="checkbox" checked={assigned} onChange={e=>setAssigned(e.target.checked)}/>This concerns assigned homework or an exam.</label><div className="chat" aria-live="polite">{chat.map((m,i)=><div key={i} className={`bubble ${m.role}`}><strong>{m.role==='user'?'You':'Septimatica'}</strong><p>{m.text}</p></div>)}</div>
          <form onSubmit={e=>{e.preventDefault();action(async()=>{const v=version.current;const response=await api('/chat',{graph,message,history:chat.slice(-12),assigned_work:assigned});if(v!==version.current)throw new Error('Your graph changed. Ask again about the current graph.');setChat([...chat,{role:'user',text:message},{role:'assistant',text:response.feedback}]);setMessage('')})}}><label>Your question<textarea rows="3" value={message} maxLength="6000" onChange={e=>setMessage(e.target.value)} placeholder="Where does my reasoning need more justification?"/></label><button className="primary" disabled={busy||!consent||!message.trim()}>{busy?'Thinking…':'Ask for a nudge ↗'}</button></form><button onClick={()=>setChat([])}>Clear conversation</button><p className="fine">AI can make mistakes. Assigned work belongs with your instructor and peers.</p></>}
      </aside></div>{user.instructor && <Instructor/>}<footer>Built for curiosity. Grounded in reasoning. <span>Graph theory · Math 55</span></footer>
    </main></>
}
