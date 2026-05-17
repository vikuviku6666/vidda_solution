"use client";

export default function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round((confidence ?? 0) * 100);
  const bg = pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className={`inline-flex items-center gap-2 rounded px-2 py-1 text-xs font-medium text-white ${bg}`}>
      <span>Confidence</span>
      <span className="font-semibold">{pct}%</span>
    </div>
  );
}
