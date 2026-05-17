"use client";

export default function BehaviouralOutcomes({ outcomes = [] }: { outcomes?: string[] }) {
  if (!outcomes || outcomes.length === 0) {
    return <div className="text-sm text-muted-foreground">No behavioural outcomes defined.</div>;
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-foreground">Behavioural outcomes</h4>
      <ul className="list-disc pl-5 text-sm text-muted-foreground">
        {outcomes.map((o, i) => (
          <li key={i}>{o}</li>
        ))}
      </ul>
    </div>
  );
}
