import React, { useState, useRef } from "react";

const GraphCanvas = () => {
  // --- STATE MANAGEMENT ---
  // These represent G = (V, E)
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  // Interaction State
  const [drawingEdge, setDrawingEdge] = useState(null); // Stores the starting node ID
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 }); // For the temporary line

  // Refs for tracking unique IDs
  const nextNodeId = useRef(1);

  // --- EVENT HANDLERS ---

  // 1. Add Node (Click on empty space)
  const handleCanvasClick = (e) => {
    // If we were drawing an edge, cancel it
    if (drawingEdge) {
      setDrawingEdge(null);
      return;
    }

    // Get coordinates relative to the SVG container
    const svgRect = e.target.getBoundingClientRect();
    const x = e.clientX - svgRect.left;
    const y = e.clientY - svgRect.top;

    const newNode = {
      id: nextNodeId.current++,
      x,
      y,
    };

    setNodes([...nodes, newNode]);
  };

  // 2. Start Edge (Mouse Down on a Node)
  const handleNodeMouseDown = (e, nodeId) => {
    e.stopPropagation(); // Prevent canvas click
    setDrawingEdge(nodeId);
  };

  // 3. Complete Edge (Mouse Up on a different Node)
  const handleNodeMouseUp = (e, targetNodeId) => {
    e.stopPropagation();

    if (drawingEdge && drawingEdge !== targetNodeId) {
      // Check if edge already exists to prevent duplicates
      const exists = edges.some(
        (edge) =>
          (edge.source === drawingEdge && edge.target === targetNodeId) ||
          (edge.source === targetNodeId && edge.target === drawingEdge)
      );

      if (!exists) {
        setEdges([...edges, { source: drawingEdge, target: targetNodeId }]);
      }
    }
    setDrawingEdge(null);
  };

  // 4. Track Mouse (For drawing the temporary line)
  const handleMouseMove = (e) => {
    if (drawingEdge) {
      const svgRect = e.currentTarget.getBoundingClientRect();
      setMousePos({
        x: e.clientX - svgRect.left,
        y: e.clientY - svgRect.top,
      });
    }
  };

  // --- RENDERING HELPERS ---

  // Find node object by ID to get coordinates for edges
  const getNode = (id) => nodes.find((n) => n.id === id);

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif" }}>
      <h3>Graph Builder: $G=(V, E)$</h3>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        • <strong>Click empty space</strong> to add a Vertex ($v$).
        <br />• <strong>Drag from one vertex to another</strong> to add an Edge
        ($e$).
      </p>

      <svg
        width="800"
        height="500"
        style={{
          border: "2px solid #333",
          borderRadius: "8px",
          cursor: "crosshair",
          backgroundColor: "#f9f9f9",
        }}
        onClick={handleCanvasClick}
        onMouseMove={handleMouseMove}
      >
        {/* 1. Render Existing Edges */}
        {edges.map((edge, index) => {
          const source = getNode(edge.source);
          const target = getNode(edge.target);
          return (
            <line
              key={index}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="#333"
              strokeWidth="2"
            />
          );
        })}

        {/* 2. Render Temporary Edge (Visual feedback while dragging) */}
        {drawingEdge && (
          <line
            x1={getNode(drawingEdge).x}
            y1={getNode(drawingEdge).y}
            x2={mousePos.x}
            y2={mousePos.y}
            stroke="#999"
            strokeWidth="2"
            strokeDasharray="5,5" // Dashed line for "temporary" feel
          />
        )}

        {/* 3. Render Vertices (Nodes) */}
        {nodes.map((node) => (
          <g
            key={node.id}
            transform={`translate(${node.x}, ${node.y})`}
            onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
            onMouseUp={(e) => handleNodeMouseUp(e, node.id)}
            style={{ cursor: "pointer" }}
          >
            {/* The visual circle */}
            <circle r="20" fill="white" stroke="#d63384" strokeWidth="3" />

            {/* Label (Vertex ID) */}
            <text
              textAnchor="middle"
              dy=".3em"
              fill="#333"
              fontWeight="bold"
              pointerEvents="none" // Allows clicking "through" text to the circle
            >
              {node.id}
            </text>
          </g>
        ))}
      </svg>

      {/* Debug View: Useful for you to see the Adjacency List building up */}
      <div style={{ marginTop: "20px", background: "#eee", padding: "10px" }}>
        <strong>Current State (Adjacency List):</strong>
        <pre>
          {JSON.stringify(
            {
              V: nodes.map((n) => n.id),
              E: edges,
            },
            null,
            2
          )}
        </pre>
      </div>
    </div>
  );
};

export default GraphCanvas;
