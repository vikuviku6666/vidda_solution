"use client";

import React from "react";

export default function ExportControls({
  modules = [],
  quarters = [],
  governance = {},
  outcomes = {},
}: {
  modules?: any[];
  quarters?: { key: string; title: string }[];
  governance?: any;
  outcomes?: any;
}) {
  const exportJSON = () => {
    const payload = { modules, quarters, governance, outcomes };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "training_plan.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const toCSV = () => {
    const rows: string[][] = [];
    // header
    rows.push([
      "type",
      "moduleId",
      "moduleTitle",
      "roleResponsibility",
      "amlrArticle",
      "riskTheme",
      "competency",
      "quarter",
      "quarterTitle",
    ]);

    modules.forEach((m) => {
      rows.push([
        "module",
        m.id ?? "",
        m.title ?? "",
        m.roleResponsibility ?? "",
        m.amlrArticle ?? "",
        m.riskTheme ?? "",
        m.competency ?? "",
        m.confidence ?? "",
        (m.behaviouralOutcomes || []).join(" | "),
      ]);
    });

    quarters.forEach((q) => {
      rows.push([
        "quarter",
        "",
        "",
        "",
        "",
        "",
        "",
        q.key,
        q.title,
      ]);
    });

    // governance as rows
    rows.push(["governance", JSON.stringify(governance)]);

    // outcomes as rows
    rows.push(["behaviouralOutcomes", JSON.stringify(outcomes)]);

    const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "training_plan.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex gap-2">
      <button onClick={exportJSON} className="rounded-md border px-3 py-1">Export JSON</button>
      <button onClick={toCSV} className="rounded-md bg-primary px-3 py-1 text-primary-foreground">Export CSV</button>
    </div>
  );
}
