import { useEffect, useRef, useState } from 'react'

const palette = ['#225fbd','#d15f31','#26816c','#9b5bb5','#b88c14','#d74980','#58798e','#6863cc']
export default function GraphCanvas({graph, onChange, onMoveStart, mode, result}) {
  const [start,setStart]=useState(null)
  const [view,setView]=useState({x:0,y:0,w:800,h:520})
  const svg=useRef(null), gesture=useRef(null), camera=useRef(view)
  const get=id=>graph.nodes.find(n=>n.id===id)
  const point=e=>new DOMPoint(e.clientX,e.clientY).matrixTransform(svg.current.getScreenCTM().inverse())
  const updateView=next=>{camera.current=next;setView(next)}

  // A non-passive wheel listener prevents page scrolling only over the canvas.
  useEffect(()=>{
    const element=svg.current
    const wheel=e=>{
      e.preventDefault()
      const old=camera.current
      const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(element.getScreenCTM().inverse())
      const width=Math.max(60,Math.min(1e7,old.w*Math.exp(Math.max(-1,Math.min(1,e.deltaY*.002)))))
      const ratio=width/old.w
      const next={x:p.x-(p.x-old.x)*ratio,y:p.y-(p.y-old.y)*ratio,w:width,h:width*.65}
      camera.current=next;setView(next)
    }
    element.addEventListener('wheel',wheel,{passive:false})
    return()=>element.removeEventListener('wheel',wheel)
  },[])

  function zoom(factor) {
    const w=Math.max(60,Math.min(1e7,view.w*factor)),h=w*.65
    updateView({x:view.x+(view.w-w)/2,y:view.y+(view.h-h)/2,w,h})
  }
  function fit() {
    if(!graph.nodes.length){updateView({x:0,y:0,w:800,h:520});return}
    const xs=graph.nodes.map(n=>n.x),ys=graph.nodes.map(n=>n.y)
    const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys)
    const w=Math.max(250,(maxX-minX)*1.3,(maxY-minY)*2),h=w*.65
    updateView({x:(minX+maxX-w)/2,y:(minY+maxY-h)/2,w,h})
  }
  function select(id) {
    if(mode==='erase') onChange({nodes:graph.nodes.filter(n=>n.id!==id),edges:graph.edges.filter(e=>e.source!==id&&e.target!==id)})
    else if(mode==='edge') {
      if(start===null||!get(start))setStart(id)
      else {
        if(start!==id&&!graph.edges.some(e=>(e.source===start&&e.target===id)||(e.source===id&&e.target===start)))onChange({...graph,edges:[...graph.edges,{source:start,target:id}]})
        setStart(null)
      }
    }
  }
  const planar=result?.topic==='planarity'?result.data.planar:undefined
  const colors=result?.data.colors||{}
  const walk=result?.topic==='eulerian'?result.data.walk:[]
  const scale=view.w/800
  return <div className="canvas-wrap"><svg ref={svg} className={`canvas mode-${mode}`} viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`} aria-label="Interactive graph canvas" role="group" tabIndex="0"
    onKeyDown={e=>{if(e.key==='Escape')setStart(null);if(e.target!==e.currentTarget)return;const d=view.w*.1;const shifts={ArrowLeft:[-d,0],ArrowRight:[d,0],ArrowUp:[0,-d],ArrowDown:[0,d]};if(shifts[e.key]){e.preventDefault();updateView({...view,x:view.x+shifts[e.key][0],y:view.y+shifts[e.key][1]})}}}
    onPointerDown={e=>{
      if(e.button===1||e.shiftKey||mode==='pan'){
        e.preventDefault();gesture.current={kind:'pan',x:e.clientX,y:e.clientY,view:{...view}};e.currentTarget.setPointerCapture(e.pointerId);return
      }
      if(e.button!==0||e.target!==e.currentTarget||mode!=='vertex')return
      const p=point(e),id=Math.max(-1,...graph.nodes.map(n=>n.id))+1
      onChange({...graph,nodes:[...graph.nodes,{id,x:p.x,y:p.y}]})
    }}
    onPointerMove={e=>{
      const g=gesture.current;if(!g)return
      if(g.kind==='pan'){
        const rect=svg.current.getBoundingClientRect(),s=g.view.w/rect.width
        updateView({...g.view,x:g.view.x-(e.clientX-g.x)*s,y:g.view.y-(e.clientY-g.y)*s})
      }else{const p=point(e);onChange({...graph,nodes:graph.nodes.map(n=>n.id===g.id?{...n,x:p.x,y:p.y}:n)},true)}
    }} onPointerUp={()=>{gesture.current=null}} onPointerCancel={()=>{gesture.current=null}}>
    <defs><pattern id="dots" width={24*scale} height={24*scale} patternUnits="userSpaceOnUse"><circle cx={scale} cy={scale} r={scale} fill="#d9ddd5"/></pattern></defs>
    <rect x={view.x} y={view.y} width={view.w} height={view.h} fill="url(#dots)" pointerEvents="none"/>
    {!graph.nodes.length&&<text x={view.x+view.w/2} y={view.y+view.h/2} fontSize={16*scale} textAnchor="middle" fill="#737e75" pointerEvents="none">Click anywhere to plant your first vertex.</text>}
    {graph.edges.map((e,i)=>{const a=get(e.source),b=get(e.target);const step=walk?.findIndex(([u,v])=>(u===a.id&&v===b.id)||(u===b.id&&v===a.id));return <g key={`${e.source}-${e.target}`} onClick={ev=>{if(mode==='erase'&&!ev.shiftKey)onChange({...graph,edges:graph.edges.filter((_,j)=>j!==i)})}}>
      <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="transparent" strokeWidth={16*scale}/>
      <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={planar===false?'#b64c44':planar?'#26816c':'#87958b'} strokeWidth={2.5*scale}/>
      {step>=0&&<text x={(a.x+b.x)/2} y={(a.y+b.y)/2-5*scale} fontSize={13*scale} fill="#245d48">{step+1}</text>}
    </g>})}
    {graph.nodes.map(n=><g key={n.id} role="button" tabIndex="0" aria-label={`Vertex ${n.id}`} transform={`translate(${n.x},${n.y}) scale(${scale})`}
      onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(n.id)}}}
      onPointerDown={e=>{if(mode==='pan'||e.shiftKey||e.button===1)return;e.stopPropagation();if(mode==='move'){onMoveStart();gesture.current={kind:'node',id:n.id};e.currentTarget.setPointerCapture(e.pointerId)}}}
      onClick={e=>{if(!e.shiftKey)select(n.id)}}>
      <circle r="19" fill={colors[n.id]!==undefined?palette[colors[n.id]%palette.length]:'#fffcf5'} stroke={mode==='edge'&&start===n.id?'#d49e3b':planar===false?'#b64c44':'#23634f'} strokeWidth="3"/>
      <text textAnchor="middle" dy="5" fontSize="13" fontWeight="700" fill={colors[n.id]!==undefined?'white':'#243c30'} pointerEvents="none">{n.id}</text>
      {colors[n.id]!==undefined&&<text textAnchor="middle" dy="35" fontSize="11" fill="#344b40">c{colors[n.id]+1}</text>}
    </g>)}
  </svg><div className="camera-controls"><button aria-label="Zoom in" onClick={()=>zoom(.8)}>+</button><button aria-label="Zoom out" onClick={()=>zoom(1.25)}>−</button><button onClick={fit}>Fit graph</button><button onClick={()=>updateView({x:0,y:0,w:800,h:520})}>Reset view</button><span>{Math.round(800/view.w*100)}%</span></div></div>
}
