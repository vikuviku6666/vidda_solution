"use client";

import { useState } from "react";

type Module = {
  id: string;
  title: string;
  roleResponsibility?: string;
  amlrArticle?: string;
  riskTheme?: string;
  competency?: string;
  confidence?: number;
  behaviouralOutcomes?: string[];
};

export default function ExplainabilityPanel({
  modules = [],
}: {
  modules?: Module[];
}) {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className="w-full max-w-3xl">
      <h2 className="text-lg font-semibold mb-2">Explainability</h2>
      <div className="space-y-2">
        {modules.map((m) => (
          <div key={m.id} className="rounded-md border bg-card p-3">
            <button
              onClick={() => setOpenId(openId === m.id ? null : m.id)}
              className="flex w-full items-center justify-between"
            >
              <div className="font-medium flex items-center gap-3">
                {m.title}
                {m.confidence !== undefined && (
                  <div className="text-sm">
                    <span className="px-2 py-0.5 rounded bg-primary text-primary-foreground text-xs">{Math.round(m.confidence*100)}%</span>
                  </div>
                )}
              </div>
              <div className="text-sm text-muted">{openId === m.id ? "−" : "+"}</div>
            </button>

            {openId === m.id && (
              <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                <div>
                  <div className="text-xs text-muted">Role responsibility</div>
                  <div className="font-medium">{m.roleResponsibility ?? "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-muted">AMLR article</div>
                  <div className="font-medium">{m.amlrArticle ?? "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-muted">Risk theme</div>
                  <div className="font-medium">{m.riskTheme ?? "—"}</div>
                </div>
                <div>
                  <div className="text-xs text-muted">Competency</div>
                  <div className="font-medium">{m.competency ?? "—"}</div>
                </div>
                <div className="sm:col-span-2">
                  <div className="mt-2">
                    <div className="text-xs text-muted">Behavioural outcomes</div>
                    <div className="font-medium text-sm">
                      {(m.behaviouralOutcomes && m.behaviouralOutcomes.length>0) ? (
                        <ul className="list-disc pl-5">
                          {m.behaviouralOutcomes.map((o, i) => <li key={i}>{o}</li>)}
                        </ul>
                      ) : (
                        <div className="text-sm text-muted">—</div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
