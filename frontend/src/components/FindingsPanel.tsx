type Finding = {
  id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
  estimated_savings: string;
  status: string;
};

type Props = {
  findings: Finding[];
};

const severityStyles: Record<string, string> = {
  high: "bg-red-500/15 text-red-400",
  medium: "bg-amber-500/15 text-amber-400",
  low: "bg-blue-500/15 text-blue-400",
};

export default function FindingsPanel({ findings }: Props) {
  if (findings.length === 0) {
    return null;
  }

  const totalSavings = findings.reduce(
    (total, finding) => total + Number(finding.estimated_savings),
    0,
  );

  return (
    <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold">
            Hallazgos y recomendaciones
          </h3>
          <p className="mt-1 text-sm text-slate-400">
            Riesgos y oportunidades detectados automáticamente
          </p>
        </div>

        <div className="text-right">
          <p className="text-sm text-slate-400">
            Ahorro mensual potencial
          </p>
          <p className="text-2xl font-bold text-emerald-400">
            ${totalSavings.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {findings.map((finding) => (
          <article
            key={finding.id}
            className="rounded-xl border border-slate-800 bg-slate-950 p-5"
          >
            <div className="flex items-center justify-between gap-3">
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  severityStyles[finding.severity] ??
                  "bg-slate-700 text-slate-300"
                }`}
              >
                {finding.severity}
              </span>

              <span className="text-sm uppercase text-slate-500">
                {finding.category}
              </span>
            </div>

            <h4 className="mt-4 font-semibold">{finding.title}</h4>

            <p className="mt-2 text-sm text-slate-400">
              {finding.description}
            </p>

            <div className="mt-4 border-t border-slate-800 pt-4">
              <p className="text-xs uppercase text-slate-500">
                Recomendación
              </p>
              <p className="mt-2 text-sm text-slate-300">
                {finding.recommendation}
              </p>
            </div>

            {Number(finding.estimated_savings) > 0 && (
              <p className="mt-4 text-sm font-semibold text-emerald-400">
                Ahorro estimado: $
                {Number(finding.estimated_savings).toFixed(2)}/mes
              </p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}