import type { Violation } from "@/lib/api";

export function ConfidenceBars({ violation }: { violation: Violation }) {
  const fields = [
    { label: "SynthID Token", value: violation.synthid_match ? 1 : 0, detail: violation.synthid_match ? "FOUND" : "not found", highlight: !!violation.synthid_match },
    { label: "dHash Hamming", value: 1 - Math.min(violation.dhash_distance, 64) / 64, detail: `${violation.dhash_distance}/64`, highlight: violation.dhash_distance < 15 },
    { label: "Embedding Cosine", value: violation.embedding_similarity, detail: (violation.embedding_similarity || 0).toFixed(2), highlight: violation.embedding_similarity > 0.7 },
    { label: "Semantic Passport", value: violation.semantic_description_similarity, detail: (violation.semantic_description_similarity || 0).toFixed(2), highlight: violation.semantic_description_similarity > 0.7 },
    { label: "Audio Transcript", value: violation.audio_transcript_match, detail: (violation.audio_transcript_match || 0).toFixed(2), highlight: violation.audio_transcript_match > 0.7 },
    { label: "Gemini Reasoning", value: violation.confidence_gemini, detail: (violation.confidence_gemini || 0).toFixed(2), highlight: violation.confidence_gemini > 0.7 },
    { label: "Overall Confidence", value: violation.confidence_overall, detail: `${Math.round(violation.confidence_overall * 100)}%`, highlight: true },
  ];

  return (
    <div className="bars">
      {fields.map((field) => {
        const pct = Math.round(Number(field.value || 0) * 100);
        return (
          <div className="bar-line" key={field.label}>
            <div className="bar-label">
              <span>{field.label}</span>
              <strong style={{ color: field.highlight ? 'var(--ink)' : 'var(--muted)' }}>{field.detail}</strong>
            </div>
            <div className="bar-track">
              <div
                className={`bar-fill ${field.highlight ? 'match' : ''}`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
