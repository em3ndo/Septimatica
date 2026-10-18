export async function api(path, data, method) {
  const response = await fetch(`/api${path}`, {
    method: method || (data === undefined ? 'GET' : 'POST'),
    headers: { 'Content-Type': 'application/json', 'X-Septimatica': '1' },
    ...(data !== undefined ? { body: JSON.stringify(data) } : {}),
  })
  if (response.redirected) return null
  const result = await response.json()
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Please check the graph or form fields.')
  return result
}

export function validateGraph(value) {
  if (!value || !Array.isArray(value.nodes) || !Array.isArray(value.edges) || value.nodes.length > 80 || value.edges.length > 500) throw new Error('Use a graph with at most 80 vertices and 500 edges.')
  const ids = new Set()
  for (const n of value.nodes) {
    if (!Number.isInteger(n.id) || n.id < 0 || n.id > 1000000 || ids.has(n.id) || !Number.isFinite(n.x) || !Number.isFinite(n.y) || Math.abs(n.x)>1e12 || Math.abs(n.y)>1e12) throw new Error('Invalid or duplicate vertex, or coordinates outside numerical limits.')
    ids.add(n.id)
  }
  const pairs = new Set()
  for (const e of value.edges) {
    const key = [e.source, e.target].sort((a,b) => a-b).join(':')
    if (!ids.has(e.source) || !ids.has(e.target) || e.source === e.target || pairs.has(key)) throw new Error('Edges must connect distinct existing vertices without duplicates.')
    pairs.add(key)
  }
  return { nodes: value.nodes.map(({id,x,y}) => ({id,x,y})), edges: value.edges.map(({source,target}) => ({source,target})) }
}

export function preset(name) {
  let n = name === 'Petersen' ? 10 : name === 'K₅' ? 5 : 6
  const nodes = Array.from({length:n}, (_,i) => {
    const ring = name === 'Petersen' && i >= 5 ? 100 : 205
    const angle = (i % (name === 'Petersen' ? 5 : n)) * 2*Math.PI / (name === 'Petersen' ? 5 : n) - Math.PI/2
    return {id:i, x:400 + ring*Math.cos(angle), y:260 + ring*Math.sin(angle)}
  })
  const edges = []
  const add = (source,target) => edges.push({source,target})
  if (name === 'Petersen') {
    for(let i=0;i<5;i++) { add(i,(i+1)%5); add(i,i+5); add(i+5,(i+2)%5+5) }
  } else if(name === 'K₅') {
    for(let i=0;i<n;i++) for(let j=i+1;j<n;j++) add(i,j)
  } else if(name === 'K₃,₃') {
    for(let i=0;i<3;i++) for(let j=3;j<6;j++) add(i,j)
  } else if(name === 'Tree') {
    for(let i=1;i<n;i++) add(Math.floor((i-1)/2),i)
  } else {
    for(let i=0;i<n;i++) add(i,(i+1)%n)
  }
  return {nodes, edges}
}
