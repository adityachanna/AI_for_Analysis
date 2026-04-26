import type { GraphData } from "@/lib/api";

export function PropagationGraph({ graph }: { graph: GraphData }) {
  if (!graph.nodes.length) {
    return <div className="empty">Run a scan to create propagation evidence.</div>;
  }

  const positions = graph.nodes.map((node, index) => {
    const angle = (index / Math.max(graph.nodes.length, 1)) * Math.PI * 2;
    return {
      ...node,
      x: 260 + Math.cos(angle) * 170,
      y: 160 + Math.sin(angle) * 105,
    };
  });
  const byId = new Map(positions.map((node) => [node.id, node]));

  return (
    <svg className="graph" viewBox="0 0 520 320" role="img" aria-label="Propagation graph">
      {graph.edges.map((edge) => {
        const source = byId.get(edge.source);
        const target = byId.get(edge.target);
        if (!source || !target) return null;
        return (
          <g key={edge.id}>
            <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke="#8ca0b3" strokeWidth="2" />
            <text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2 - 6} fill="#637083" fontSize="11">
              {edge.relation}
            </text>
          </g>
        );
      })}
      {positions.map((node) => (
        <g key={node.id}>
          <circle cx={node.x} cy={node.y} r={node.type === "asset" ? 34 : 28} fill={node.type === "asset" ? "#0b7a75" : "#ffffff"} stroke="#0b7a75" strokeWidth="2" />
          <text x={node.x} y={node.y + 48} textAnchor="middle" fill="#17212b" fontSize="12">
            {node.label.length > 24 ? `${node.label.slice(0, 21)}...` : node.label}
          </text>
          <text x={node.x} y={node.y + 4} textAnchor="middle" fill={node.type === "asset" ? "#ffffff" : "#0b7a75"} fontSize="10" fontWeight="700">
            {node.type.replace("_", " ")}
          </text>
        </g>
      ))}
    </svg>
  );
}
