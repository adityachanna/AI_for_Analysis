import type { GraphData } from "@/lib/api";

const NODE_COLORS: Record<string, string> = {
  asset: "#00ff88",
  violation: "#ff0055",
  platform: "#88ffff",
  domain: "#ffa500",
  default: "#8b8b9b",
};

export function PropagationGraph({ graph }: { graph: GraphData }) {
  if (!graph.nodes.length) {
    return <div className="empty">Run a scan to build the propagation graph.</div>;
  }

  const W = 560, H = 360;
  const cx = W / 2, cy = H / 2;

  const positions = graph.nodes.map((node, i) => {
    const isCenter = node.type === "asset";
    if (isCenter) return { ...node, x: cx, y: cy };
    const angle = (i / Math.max(graph.nodes.length - 1, 1)) * Math.PI * 2;
    const radius = node.type === "violation" ? 130 : 185;
    return {
      ...node,
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
    };
  });

  const byId = new Map(positions.map((n) => [n.id, n]));

  return (
    <svg
      className="graph"
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label="Propagation graph"
      style={{ background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
      {/* Edge glow filter */}
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge><feMergeNode in="coloredBlur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Edges */}
      {graph.edges.map((edge) => {
        const src = byId.get(edge.source);
        const tgt = byId.get(edge.target);
        if (!src || !tgt) return null;
        const strokeColor = edge.weight > 0.7 ? "#ff0055" : edge.weight > 0.4 ? "#ffa500" : "#4a4a5a";
        const midX = (src.x + tgt.x) / 2;
        const midY = (src.y + tgt.y) / 2;
        return (
          <g key={edge.id}>
            <line
              x1={src.x} y1={src.y} x2={tgt.x} y2={tgt.y}
              stroke={strokeColor} strokeWidth={edge.weight > 0.7 ? 2 : 1}
              strokeDasharray={edge.weight < 0.5 ? "4 4" : undefined}
              opacity={0.7}
            />
            <rect
              x={midX - 22} y={midY - 9}
              width={44} height={18}
              fill="rgba(3,3,4,0.7)" rx="2"
            />
            <text x={midX} y={midY + 4} textAnchor="middle" fill={strokeColor}
              fontSize="9" fontFamily="Syncopate, sans-serif" letterSpacing="0.05em">
              {Math.round(edge.weight * 100)}%
            </text>
          </g>
        );
      })}

      {/* Nodes */}
      {positions.map((node) => {
        const isAsset = node.type === "asset";
        const r = isAsset ? 32 : node.type === "violation" ? 24 : 18;
        const color = NODE_COLORS[node.type] || NODE_COLORS.default;
        const label = node.label.length > 18 ? node.label.slice(0, 16) + "..." : node.label;
        return (
          <g key={node.id} filter={isAsset ? "url(#glow)" : undefined}>
            <circle
              cx={node.x} cy={node.y} r={r}
              fill="rgba(3,3,4,0.9)"
              stroke={color}
              strokeWidth={isAsset ? 2.5 : 1.5}
            />
            <text x={node.x} y={node.y + 4}
              textAnchor="middle" fill={color}
              fontSize={isAsset ? 8 : 7} fontFamily="Syncopate, sans-serif"
              fontWeight="700" letterSpacing="0.05em">
              {node.type.replace(/_/g, " ").toUpperCase()}
            </text>
            <text x={node.x} y={node.y + r + 14}
              textAnchor="middle" fill="rgba(255,255,255,0.65)"
              fontSize="10" fontFamily="Manrope, sans-serif">
              {label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
