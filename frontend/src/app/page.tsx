"use client";

import { useCallback, useEffect, useState } from "react";

import AddCloudAccountForm from "@/components/AddCloudAccountForm";
import AWSSetupPanel from "@/components/AWSSetupPanel";
import CloudResourceTable from "@/components/CloudResourceTable";
import FindingsPanel from "@/components/FindingsPanel";

type CloudAccount = {
  id: string;
  name: string;
  provider: string;
  aws_account_id: string;
  role_arn: string;
  external_id: string | null;
  status: string;
};

type CloudResource = {
  id: string;
  cloud_account_id: string;
  service: string;
  name: string;
  region: string;
  status: string;
  monthly_cost: string;
};

type Finding = {
  id: string;
  cloud_account_id: string;
  cloud_resource_id: string;
  category: string;
  severity: string;
  title: string;
  description: string;
  recommendation: string;
  estimated_savings: string;
  status: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [resources, setResources] = useState<CloudResource[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [setupAccount, setSetupAccount] =
    useState<CloudAccount | null>(null);

  const loadAccounts = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/v1/cloud-accounts/`,
      );

      if (!response.ok) {
        throw new Error("API request failed");
      }

      const result: CloudAccount[] = await response.json();
      setAccounts(result);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAccounts();
  }, [loadAccounts]);

  useEffect(() => {
    async function loadResources() {
      const response = await fetch(
        `${API_URL}/api/v1/cloud-resources/`,
      );

      if (response.ok) {
        const result: CloudResource[] = await response.json();
        setResources(result);
      }
    }

    void loadResources();
  }, []);

  useEffect(() => {
    async function loadFindings() {
      const response = await fetch(
        `${API_URL}/api/v1/findings/`,
      );

      if (response.ok) {
        const result: Finding[] = await response.json();
        setFindings(result);
      }
    }

    void loadFindings();
  }, []);

  async function deleteAccount(account: CloudAccount) {
    const confirmed = window.confirm(
      `¿Deseas eliminar la cuenta "${account.name}"?`,
    );

    if (!confirmed) {
      return;
    }

    const response = await fetch(
      `${API_URL}/api/v1/cloud-accounts/${account.id}`,
      { method: "DELETE" },
    );

    if (!response.ok) {
      window.alert("No se pudo eliminar la cuenta");
      return;
    }

    setAccounts((currentAccounts) =>
      currentAccounts.filter(
        (currentAccount) => currentAccount.id !== account.id,
      ),
    );

    setResources((currentResources) =>
      currentResources.filter(
        (resource) => resource.cloud_account_id !== account.id,
      ),
    );

    setFindings((currentFindings) =>
      currentFindings.filter(
        (finding) => finding.cloud_account_id !== account.id,
      ),
    );

    if (setupAccount?.id === account.id) {
      setSetupAccount(null);
    }
  }

  async function generateDemoInventory(account: CloudAccount) {
    const response = await fetch(
      `${API_URL}/api/v1/cloud-resources/demo/${account.id}`,
      { method: "POST" },
    );

    if (!response.ok) {
      window.alert("No se pudo generar el inventario demo");
      return;
    }

    const demoResources: CloudResource[] = await response.json();

    setResources((currentResources) => [
      ...currentResources.filter(
        (resource) => resource.cloud_account_id !== account.id,
      ),
      ...demoResources,
    ]);

    setFindings((currentFindings) =>
      currentFindings.filter(
        (finding) => finding.cloud_account_id !== account.id,
      ),
    );

    setAccounts((currentAccounts) =>
      currentAccounts.map((currentAccount) =>
        currentAccount.id === account.id
          ? { ...currentAccount, status: "demo" }
          : currentAccount,
      ),
    );
  }

  async function synchronizeAWS(account: CloudAccount) {
    const confirmed = window.confirm(
      `¿Deseas sincronizar recursos reales de "${account.name}"?`,
    );

    if (!confirmed) {
      return;
    }

    const response = await fetch(
      `${API_URL}/api/v1/aws/discover/${account.id}?region=us-east-1`,
      { method: "POST" },
    );

    if (!response.ok) {
      const result = await response.json();

      window.alert(
        result.detail ?? "No se pudo sincronizar la cuenta AWS",
      );
      return;
    }

    const discoveredResources: CloudResource[] =
      await response.json();

    setResources((currentResources) => [
      ...currentResources.filter(
        (resource) => resource.cloud_account_id !== account.id,
      ),
      ...discoveredResources,
    ]);

    setFindings((currentFindings) =>
      currentFindings.filter(
        (finding) => finding.cloud_account_id !== account.id,
      ),
    );

    setAccounts((currentAccounts) =>
      currentAccounts.map((currentAccount) =>
        currentAccount.id === account.id
          ? { ...currentAccount, status: "connected" }
          : currentAccount,
      ),
    );
  }

  async function analyzeAccount(account: CloudAccount) {
    const response = await fetch(
      `${API_URL}/api/v1/findings/analyze/${account.id}`,
      { method: "POST" },
    );

    if (!response.ok) {
      const result = await response.json();

      window.alert(
        result.detail ?? "No se pudo analizar la cuenta",
      );
      return;
    }

    const accountFindings: Finding[] = await response.json();

    setFindings((currentFindings) => [
      ...currentFindings.filter(
        (finding) => finding.cloud_account_id !== account.id,
      ),
      ...accountFindings,
    ]);
  }

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
          <h2 className="text-3xl font-semibold">
            Resumen ejecutivo
          </h2>

          <p className="mt-2 text-slate-400">
            Estado general de la infraestructura cloud conectada.
          </p>
        </div>

        {showForm && (
          <AddCloudAccountForm
            onCancel={() => setShowForm(false)}
            onCreated={() => {
              setShowForm(false);
              void loadAccounts();
            }}
          />
        )}

        {setupAccount && (
          <AWSSetupPanel
            account={setupAccount}
            onClose={() => setSetupAccount(null)}
          />
        )}

        <div className="grid gap-5 md:grid-cols-3">
          <MetricCard
            title="Cuentas cloud"
            value={loading ? "..." : accounts.length.toString()}
            detail="Cuentas registradas"
          />

          <MetricCard
            title="Recursos"
            value={resources.length.toString()}
            detail="Recursos inventariados"
          />

          <MetricCard
            title="Hallazgos"
            value={findings.length.toString()}
            detail="Riesgos y oportunidades detectadas"
          />
        </div>

        <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold">
                Cuentas AWS
              </h3>

              <p className="mt-1 text-sm text-slate-400">
                Ambientes registrados en Alfa Analytics
              </p>
            </div>

            <button
              onClick={() => setShowForm(true)}
              className="rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950"
            >
              Agregar cuenta
            </button>
          </div>

          {loading ? (
            <p className="text-slate-400">
              Cargando cuentas...
            </p>
          ) : accounts.length === 0 ? (
            <p className="text-slate-400">
              Todavía no existen cuentas registradas.
            </p>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-800">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className="flex flex-col gap-4 border-b border-slate-800 p-5 last:border-b-0 lg:flex-row lg:items-center lg:justify-between"
                >
                  <div>
                    <p className="font-medium">{account.name}</p>

                    <p className="mt-1 text-sm text-slate-400">
                      AWS · {account.aws_account_id}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-end gap-3">
                    <span className="rounded-full bg-amber-500/15 px-3 py-1 text-sm text-amber-400">
                      {account.status}
                    </span>

                    <button
                      onClick={() => setSetupAccount(account)}
                      className="rounded-lg border border-slate-500/30 px-3 py-1 text-sm text-slate-300 hover:bg-slate-500/10"
                    >
                      Configurar AWS
                    </button>

                    <button
                      onClick={() =>
                        generateDemoInventory(account)
                      }
                      className="rounded-lg border border-cyan-500/30 px-3 py-1 text-sm text-cyan-400 hover:bg-cyan-500/10"
                    >
                      Cargar demo
                    </button>

                    <button
                      onClick={() => synchronizeAWS(account)}
                      className="rounded-lg border border-blue-500/30 px-3 py-1 text-sm text-blue-400 hover:bg-blue-500/10"
                    >
                      Sincronizar AWS
                    </button>

                    <button
                      onClick={() => analyzeAccount(account)}
                      className="rounded-lg border border-violet-500/30 px-3 py-1 text-sm text-violet-400 hover:bg-violet-500/10"
                    >
                      Analizar
                    </button>

                    <a
                      href={`${API_URL}/api/v1/reports/${account.id}/executive`}
                      className="rounded-lg border border-emerald-500/30 px-3 py-1 text-sm text-emerald-400 hover:bg-emerald-500/10"
                    >
                      Descargar reporte
                    </a>

                    <button
                      onClick={() => deleteAccount(account)}
                      className="rounded-lg border border-red-500/30 px-3 py-1 text-sm text-red-400 hover:bg-red-500/10"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <CloudResourceTable resources={resources} />
        <FindingsPanel findings={findings} />
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