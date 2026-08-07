"use client";

import { useEffect, useState } from "react";

type SyncRun = {
  id: string;
  cloud_account_id: string;
  region: string;
  status: string;
  resource_count: number;
  duration_ms: number | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
};

type Props = {
  accountId: string;
  refreshKey: string | null;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function SyncHistoryPanel({
  accountId,
  refreshKey,
}: Props) {
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadHistory() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch(
          `${API_URL}/api/v1/cloud-accounts/${accountId}/sync-runs?limit=10`,
        );

        if (!response.ok) {
          throw new Error(
            "No se pudo consultar el historial",
          );
        }

        const result: SyncRun[] = await response.json();

        if (!cancelled) {
          setRuns(result);
        }
      } catch (requestError) {
        if (!cancelled) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "No se pudo consultar el historial",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [accountId, refreshKey]);

  function formatDuration(durationMs: number | null) {
    if (durationMs === null) {
      return "En proceso";
    }

    if (durationMs < 1000) {
      return `${durationMs} ms`;
    }

    return `${(durationMs / 1000).toFixed(2)} s`;
  }

  function formatDate(value: string) {
    return new Intl.DateTimeFormat("es-PE", {
      dateStyle: "short",
      timeStyle: "medium",
    }).format(new Date(value));
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div>
        <h2 className="text-xl font-semibold">
          Historial de sincronizaciones
        </h2>

        <p className="mt-1 text-sm text-slate-400">
          Últimos intentos realizados para la cuenta seleccionada
        </p>
      </div>

      {loading ? (
        <p className="mt-5 text-sm text-slate-400">
          Cargando historial...
        </p>
      ) : error ? (
        <p className="mt-5 text-sm text-red-400">
          {error}
        </p>
      ) : runs.length === 0 ? (
        <p className="mt-5 text-sm text-slate-400">
          Todavía no existen sincronizaciones para esta cuenta.
        </p>
      ) : (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 text-slate-400">
              <tr>
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Región</th>
                <th className="px-4 py-3">Resultado</th>
                <th className="px-4 py-3">Recursos</th>
                <th className="px-4 py-3">Duración</th>
                <th className="px-4 py-3">Detalle</th>
              </tr>
            </thead>

            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="border-b border-slate-800 last:border-b-0"
                >
                  <td className="px-4 py-3 text-slate-300">
                    {formatDate(run.started_at)}
                  </td>

                  <td className="px-4 py-3">
                    {run.region}
                  </td>

                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-3 py-1 text-xs ${
                        run.status === "success"
                          ? "bg-emerald-500/15 text-emerald-400"
                          : run.status === "failed"
                            ? "bg-red-500/15 text-red-400"
                            : "bg-amber-500/15 text-amber-400"
                      }`}
                    >
                      {run.status === "success"
                        ? "Exitosa"
                        : run.status === "failed"
                          ? "Fallida"
                          : "En proceso"}
                    </span>
                  </td>

                  <td className="px-4 py-3">
                    {run.resource_count}
                  </td>

                  <td className="px-4 py-3">
                    {formatDuration(run.duration_ms)}
                  </td>

                  <td className="max-w-xs px-4 py-3 text-slate-400">
                    {run.error_message ?? "Sin errores"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}