"use client";

export default function GovernanceDashboard({
  kpis = {},
}: {
  kpis?: { [key: string]: number };
}) {
  const defaultKpis = {
    approvalsPending: kpis.approvalsPending ?? 2,
    publishedCount: kpis.publishedCount ?? 5,
    auditEvents: kpis.auditEvents ?? 12,
    complianceScore: kpis.complianceScore ?? 0.87,
  };

  return (
    <div className="w-full max-w-3xl rounded-md border bg-card p-4">
      <h2 className="text-lg font-semibold mb-3 text-card-foreground">Governance dashboard</h2>

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded bg-popover p-3 border">
          <div className="text-sm text-muted-foreground">Approvals pending</div>
          <div className="text-2xl font-semibold text-popover-foreground">{defaultKpis.approvalsPending}</div>
        </div>
        <div className="rounded bg-popover p-3 border">
          <div className="text-sm text-muted-foreground">Published trainings</div>
          <div className="text-2xl font-semibold text-popover-foreground">{defaultKpis.publishedCount}</div>
        </div>
        <div className="rounded bg-popover p-3 border">
          <div className="text-sm text-muted-foreground">Audit events</div>
          <div className="text-2xl font-semibold text-popover-foreground">{defaultKpis.auditEvents}</div>
        </div>
        <div className="rounded bg-popover p-3 border">
          <div className="text-sm text-muted-foreground">Compliance score</div>
          <div className="text-2xl font-semibold text-popover-foreground">{Math.round((defaultKpis.complianceScore ?? 0) * 100)}%</div>
        </div>
      </div>

      <div className="mt-4">
        <h4 className="text-sm font-medium text-card-foreground">Auditability</h4>
        <p className="text-sm text-muted-foreground">All actions are logged and exportable for audits.</p>
      </div>
    </div>
  );
}
