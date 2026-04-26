import type { Violation } from "@/lib/api";

export function ConfidenceBars({ violation }: { violation: Violation }) {
  const fields = [
    { label: "SynthID marker", value: violation.synthid_match ? 1 : 0, detail: violation.synthid_match ? "found" : "not found" },
    { label: "dHash Hamming", value: 1 - Math.min(violation.dhash_distance, 64) / 64, detail: `${violation.dhash_distance}/64` },
    { label: "Embedding cosine", value: violation.embedding_similarity, detail: violation.embedding_similarity.toFixed(2) },
    { label: "Semantic passport", value: violation.semantic_description_similarity, detail: violation.semantic_description_similarity.toFixed(2) },
    { label: "Audio transcript", value: violation.audio_transcript_match, detail: violation.audio_transcript_match.toFixed(2) },
    { label: "Gemini reasoning", value: violation.confidence_gemini, detail: violation.confidence_gemini.toFixed(2) },
    { label: "Overall", value: violation.confidence_overall, detail: `${Math.round(violation.confidence_overall * 100)}%` },
  ];

  return (
    <div className="bars">
      {fields.map((field) => {
        const value = Number(field.value || 0);
        return (
          <div className="bar-line" key={field.label}>
            <div className="bar-label">
              <span>{field.label}</span>
              <strong>{field.detail}</strong>
            </div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${Math.round(value * 100)}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
