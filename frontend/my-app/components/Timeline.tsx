"use client";

export default function Timeline({ recommendations = [] }: { recommendations?: any[] }) {
  const getQuarterRec = (quarterKey: string) => {
    return recommendations.find((r) => r.quarter.includes(quarterKey));
  };

  const quarters = [
    { key: "Q1", title: "Foundation" },
    { key: "Q2", title: "Application" },
    { key: "Q3", title: "Deepening" },
    { key: "Q4", title: "Embedding" },
  ];

  return (
    <div className="w-full max-w-3xl">
      <h2 className="text-lg font-semibold mb-4 text-foreground">Timeline</h2>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-stretch">
        {quarters.map((q) => {
          const rec = getQuarterRec(q.key);
          return (
            <div key={q.key} className="flex-1 rounded-md border bg-card p-4">
              <div className="text-sm text-muted-foreground">{q.key}</div>
              <div className="mt-2 font-semibold text-card-foreground">{q.title}</div>
              
              {rec ? (
                <>
                  <div className="mt-2 text-xs font-medium text-primary">{rec.module}</div>
                  <ul className="mt-2 text-sm list-disc pl-5 space-y-1 text-muted-foreground">
                    {rec.activities?.map((activity: string, i: number) => (
                      <li key={i}>{activity}</li>
                    ))}
                  </ul>
                </>
              ) : (
                <ul className="mt-3 text-sm list-disc pl-5 space-y-1 text-muted-foreground">
                  <li>No activities generated</li>
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
