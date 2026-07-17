"use client";

import { useEffect, useState } from "react";

type CloudAccount = {
  id: string;
  name: string;
  provider: string;
  aws_account_id: string;
  status: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/cloud-accounts/`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("API request failed");
        }

        return response.json();
      })
      .then(setAccounts)
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-5">
          <div>
            <h1 className="text-2xl font-bold text-cyan-400">
              Alfa Analytics
            </h1>
            <p className="text-sm text-slate-400">
              Cloud intelligence platform
            </p>
          </div>

          <span className="rounded-full bg-emerald-500/15 px-4 py-2 text-sm text-emerald-400">
            Sistema operativo
          </span>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-8 py-10">
        <div className="mb-8">
          <h2 className="text-3xl font-semibold">Resumen ejecutivo</h2>
          <p className="mt-2 text-slate-400">
            Estado general de la infraestructura cloud conectada.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          <MetricCard
            title="Cuentas cloud"
            value={loading ? "..." : accounts.length.toString()}
            detail="Cuentas registradas"
          />
          <MetricCard
            title="Recursos"
            value="0"
            detail="Pendiente de inventario"
          />
          <MetricCard
            title="Hallazgos"
            value="0"
            detail="Sin análisis ejecutado"
          />
        </div>

        <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold">Cuentas AWS</h3>
              <p className="mt-1 text-sm text-slate-400">
                Ambientes registrados en Alfa Analytics
              </p>
            </div>

            <button className="rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950">
              Agregar cuenta
            </button>
          </div>

          {loading ? (
            <p className="text-slate-400">Cargando cuentas...</p>
          ) : accounts.length === 0 ? (
            <p className="text-slate-400">
              Todavía no existen cuentas registradas.
            </p>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-800">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center justify-between border-b border-slate-800 p-5 last:border-b-0"
                >
                  <div>
                    <p className="font-medium">{account.name}</p>
                    <p className="mt-1 text-sm text-slate-400">
                      AWS · {account.aws_account_id}
                    </p>
                  </div>

                  <span className="rounded-full bg-amber-500/15 px-3 py-1 text-sm text-amber-400">
                    {account.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function MetricCard({
  title,
  value,
  detail,
}: {
  title: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <p className="text-sm text-slate-400">{title}</p>
      <p className="mt-3 text-4xl font-bold">{value}</p>
      <p className="mt-2 text-sm text-slate-500">{detail}</p>
    </article>
  );
}