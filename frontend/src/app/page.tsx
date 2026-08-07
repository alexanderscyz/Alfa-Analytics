"use client";

import { useCallback, useEffect, useState } from "react";

import AddCloudAccountForm from "@/components/AddCloudAccountForm";
import AppShell from "@/components/AppShell";
import AWSSetupPanel from "@/components/AWSSetupPanel";
import CloudResourceTable from "@/components/CloudResourceTable";
import FindingsPanel from "@/components/FindingsPanel";
import SyncHistoryPanel from "@/components/SyncHistoryPanel";
import type { CloudAccount } from "@/types/cloud";
import ConfirmDialog from "@/components/ConfirmDialog";
import NotificationToast, {
  type NotificationData,
} from "@/components/NotificationToast";

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

type ConfirmationState = {
  action: "sync" | "delete";
  account: CloudAccount;
} | null;

type MultiRegionDiscoveryResult = {
  status: "success" | "partial_success";
  requested_regions: string[];
  successful_regions: string[];
  failed_regions: string[];
  resource_count: number;
  resources: CloudResource[];
};

const AWS_REGIONS = [
  { value: "us-east-1", label: "US East (N. Virginia)" },
  { value: "us-east-2", label: "US East (Ohio)" },
  { value: "us-west-2", label: "US West (Oregon)" },
  { value: "sa-east-1", label: "South America (São Paulo)" },
  { value: "eu-west-1", label: "Europe (Ireland)" },
] as const;

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [accounts, setAccounts] = useState<CloudAccount[]>([]);
  const [resources, setResources] = useState<CloudResource[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [setupAccount, setSetupAccount] = useState<CloudAccount | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(
    null,
  );

  const [selectedRegions, setSelectedRegions] = useState<string[]>([
    "us-east-1",
  ]);

  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);

  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(
    null,
  );

  const [notification, setNotification] = useState<NotificationData | null>(
    null,
  );

  const [confirmation, setConfirmation] = useState<ConfirmationState>(null);

  const selectedAccount =
    accounts.find((account) => account.id === selectedAccountId) ?? null;
  const selectedResources = selectedAccountId
    ? resources.filter(
        (resource) => resource.cloud_account_id === selectedAccountId,
      )
    : [];
  const selectedFindings = selectedAccountId
    ? findings.filter(
        (finding) => finding.cloud_account_id === selectedAccountId,
      )
    : [];

  function toggleRegion(region: string) {
    setSelectedRegions((currentRegions) =>
      currentRegions.includes(region)
        ? currentRegions.filter((currentRegion) => currentRegion !== region)
        : [...currentRegions, region],
    );
  }

  const loadAccounts = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/cloud-accounts/`);

      if (!response.ok) {
        throw new Error("API request failed");
      }

      const result: CloudAccount[] = await response.json();
      setAccounts(result);
      setSelectedAccountId((currentAccountId) => {
        const currentAccountStillExists = result.some(
          (account) => account.id === currentAccountId,
        );

        return currentAccountStillExists
          ? currentAccountId
          : (result[0]?.id ?? null);
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAccounts();
  }, [loadAccounts]);

  useEffect(() => {
    async function loadResources() {
      const response = await fetch(`${API_URL}/api/v1/cloud-resources/`);

      if (response.ok) {
        const result: CloudResource[] = await response.json();
        setResources(result);
      }
    }

    void loadResources();
  }, []);

  useEffect(() => {
    async function loadFindings() {
      const response = await fetch(`${API_URL}/api/v1/findings/`);

      if (response.ok) {
        const result: Finding[] = await response.json();
        setFindings(result);
      }
    }

    void loadFindings();
  }, []);

  async function deleteAccount(account: CloudAccount) {
    setDeletingAccountId(account.id);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/cloud-accounts/${account.id}`,
        { method: "DELETE" },
      );

      if (!response.ok) {
        throw new Error("No se pudo eliminar la cuenta");
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

      if (selectedAccountId === account.id) {
        const nextAccount = accounts.find(
          (currentAccount) => currentAccount.id !== account.id,
        );
        setSelectedAccountId(nextAccount?.id ?? null);
      }

      if (setupAccount?.id === account.id) {
        setSetupAccount(null);
      }

      setNotification({
        type: "success",
        title: "Cuenta eliminada",
        message: `"${account.name}" fue eliminada correctamente.`,
      });
    } catch (error) {
      setNotification({
        type: "error",
        title: "No se pudo eliminar",
        message:
          error instanceof Error
            ? error.message
            : "Ocurrió un error inesperado",
      });
    } finally {
      setDeletingAccountId(null);
    }
  }

  async function generateDemoInventory(account: CloudAccount) {
    setSelectedAccountId(account.id);

    const response = await fetch(
      `${API_URL}/api/v1/cloud-resources/demo/${account.id}`,
      { method: "POST" },
    );

    if (!response.ok) {
      setNotification({
        type: "error",
        title: "Error al cargar la demostración",
        message: "No se pudo generar el inventario demo.",
      });
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
    setNotification({
      type: "success",
      title: "Inventario demo cargado",
      message: `Se cargaron ${demoResources.length} recursos de demostración.`,
    });
  }

  async function synchronizeAWS(account: CloudAccount) {
    setSelectedAccountId(account.id);
    setSyncingAccountId(account.id);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/aws/discover/${account.id}/multi-region`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ regions: selectedRegions }),
        },
      );

      if (!response.ok) {
        const result = await response.json();
        throw new Error(
          result.detail ?? "No se pudo sincronizar la cuenta AWS",
        );
      }

      const result: MultiRegionDiscoveryResult = await response.json();
      const discoveredResources = result.resources;

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
            ? {
                ...currentAccount,
                status: "connected",
                last_sync_at: new Date().toISOString(),
                last_sync_region: "multi-region",
                last_sync_status: result.status,
                resource_count: result.resource_count,
              }
            : currentAccount,
        ),
      );
      setNotification({
        type: result.status === "partial_success" ? "info" : "success",
        title:
          result.status === "partial_success"
            ? "Sincronización parcialmente completada"
            : "Sincronización completada",
        message: [
          `Regiones correctas: ${result.successful_regions.join(", ")}`,
          result.failed_regions.length > 0
            ? `Regiones fallidas: ${result.failed_regions.join(", ")}`
            : null,
          `Recursos encontrados: ${result.resource_count}`,
        ]
          .filter(Boolean)
          .join("\n"),
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "No se pudo sincronizar la cuenta AWS";

      setNotification({
        type: "error",
        title: "No se pudo sincronizar",
        message,
      });
      void loadAccounts();
    } finally {
      setSyncingAccountId(null);
    }
  }

  async function analyzeAccount(account: CloudAccount) {
    setSelectedAccountId(account.id);

    const response = await fetch(
      `${API_URL}/api/v1/findings/analyze/${account.id}`,
      { method: "POST" },
    );

    if (!response.ok) {
      const result = await response.json();
      setNotification({
        type: "error",
        title: "No se pudo analizar",
        message: result.detail ?? "No se pudo analizar la cuenta",
      });
      return;
    }

    const accountFindings: Finding[] = await response.json();

    setFindings((currentFindings) => [
      ...currentFindings.filter(
        (finding) => finding.cloud_account_id !== account.id,
      ),
      ...accountFindings,
    ]);
    setNotification({
      type: "success",
      title: "Análisis completado",
      message: `Se detectaron ${accountFindings.length} hallazgos en "${account.name}".`,
    });
  }

  function confirmPendingAction() {
    if (!confirmation) {
      return;
    }

    const pendingConfirmation = confirmation;
    setConfirmation(null);

    if (pendingConfirmation.action === "sync") {
      void synchronizeAWS(pendingConfirmation.account);
      return;
    }

    void deleteAccount(pendingConfirmation.account);
  }

  return (
    <AppShell>
      <NotificationToast
        notification={notification}
        onClose={() => setNotification(null)}
      />

      <ConfirmDialog
        open={confirmation !== null}
        title={
          confirmation?.action === "delete"
            ? "Eliminar cuenta AWS"
            : "Sincronizar inventario AWS"
        }
        message={
          confirmation?.action === "delete"
            ? `Se eliminarán la cuenta "${confirmation.account.name}" y todos sus datos asociados.`
            : `Se consultará "${confirmation?.account.name ?? ""}" en ${selectedRegions.length} región${selectedRegions.length === 1 ? "" : "es"}: ${selectedRegions.join(", ")}.`
        }
        confirmLabel={
          confirmation?.action === "delete" ? "Eliminar cuenta" : "Sincronizar"
        }
        variant={confirmation?.action === "delete" ? "danger" : "primary"}
        busy={
          confirmation?.action === "delete"
            ? deletingAccountId !== null
            : syncingAccountId !== null
        }
        onConfirm={confirmPendingAction}
        onCancel={() => setConfirmation(null)}
      />

      <section className="mx-auto max-w-7xl px-8 py-10">
        <div className="mb-8">
          <h2 className="text-3xl font-semibold">Resumen ejecutivo</h2>

          <p className="mt-2 text-slate-400">
            Estado general de la infraestructura cloud conectada.
          </p>
        </div>

        {showForm && (
          <AddCloudAccountForm
            onCancel={() => setShowForm(false)}
            onCreated={(account) => {
              setShowForm(false);
              setSelectedAccountId(account.id);
              setSetupAccount(account);
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
            value={selectedResources.length.toString()}
            detail={
              selectedAccount
                ? `Inventario de ${selectedAccount.name}`
                : "Selecciona una cuenta"
            }
          />

          <MetricCard
            title="Hallazgos"
            value={selectedFindings.length.toString()}
            detail={
              selectedAccount
                ? `Análisis de ${selectedAccount.name}`
                : "Selecciona una cuenta"
            }
          />
        </div>

        <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="mb-6 flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
            <div>
              <h3 className="text-xl font-semibold">Cuentas AWS</h3>

              <p className="mt-1 text-sm text-slate-400">
                Ambientes registrados en Alfa Analytics
              </p>
            </div>

            <div className="flex flex-col items-start gap-3 xl:items-end">
              <button
                onClick={() => setShowForm(true)}
                className="rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950"
              >
                Agregar cuenta
              </button>
            </div>
          </div>

          <div className="mb-6 rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-200">
                  Regiones para sincronizar
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Selecciona una o varias regiones AWS.
                </p>
              </div>

              <span className="rounded-full bg-blue-500/10 px-3 py-1 text-xs text-blue-300">
                {selectedRegions.length} seleccionada
                {selectedRegions.length === 1 ? "" : "s"}
              </span>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {AWS_REGIONS.map((region) => {
                const selected = selectedRegions.includes(region.value);

                return (
                  <button
                    key={region.value}
                    type="button"
                    onClick={() => toggleRegion(region.value)}
                    className={`rounded-lg border px-3 py-2 text-sm transition ${
                      selected
                        ? "border-blue-400 bg-blue-500/15 text-blue-200"
                        : "border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200"
                    }`}
                  >
                    <span
                      className={`mr-2 inline-block h-2 w-2 rounded-full ${
                        selected ? "bg-blue-400" : "bg-slate-600"
                      }`}
                    />
                    {region.label}
                  </button>
                );
              })}
            </div>

            {selectedRegions.length === 0 && (
              <p className="mt-3 text-sm text-amber-400">
                Selecciona al menos una región para sincronizar.
              </p>
            )}
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
                  className={`flex flex-col gap-4 border-b border-slate-800 p-5 last:border-b-0 lg:flex-row lg:items-center lg:justify-between ${
                    selectedAccountId === account.id ? "bg-cyan-500/5" : ""
                  }`}
                >
                  <div>
                    <p className="font-medium">{account.name}</p>

                    <p className="mt-1 text-sm text-slate-400">
                      AWS · {account.aws_account_id}
                    </p>

                    {account.last_sync_at && (
                      <div className="mt-2 space-y-1 text-xs text-slate-500">
                        <p>
                          Última sincronización:{" "}
                          {new Date(account.last_sync_at).toLocaleString(
                            "es-PE",
                            {
                              dateStyle: "short",
                              timeStyle: "short",
                            },
                          )}
                        </p>

                        <p>
                          Región: {account.last_sync_region ?? "No disponible"}
                          {" · "}
                          {account.resource_count} recursos
                          {" · "}
                          {account.last_sync_status}
                        </p>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center justify-end gap-3">
                    <button
                      onClick={() => setSelectedAccountId(account.id)}
                      className={`rounded-lg border px-3 py-1 text-sm ${
                        selectedAccountId === account.id
                          ? "border-cyan-400 bg-cyan-500/15 text-cyan-300"
                          : "border-slate-500/30 text-slate-300 hover:bg-slate-500/10"
                      }`}
                    >
                      {selectedAccountId === account.id
                        ? "Seleccionada"
                        : "Ver datos"}
                    </button>

                    <span className="rounded-full bg-amber-500/15 px-3 py-1 text-sm text-amber-400">
                      {account.status}
                    </span>

                    {account.status !== "demo" && (
                      <button
                        onClick={() => setSetupAccount(account)}
                        className="rounded-lg border border-slate-500/30 px-3 py-1 text-sm text-slate-300 hover:bg-slate-500/10"
                      >
                        Configurar AWS
                      </button>
                    )}

                    {account.status === "demo" && (
                      <button
                        onClick={() => generateDemoInventory(account)}
                        className="rounded-lg border border-cyan-500/30 px-3 py-1 text-sm text-cyan-400 hover:bg-cyan-500/10"
                      >
                        Cargar demo
                      </button>
                    )}

                    {account.status !== "demo" && (
                      <button
                        onClick={() =>
                          setConfirmation({
                            action: "sync",
                            account,
                          })
                        }
                        disabled={
                          syncingAccountId !== null ||
                          selectedRegions.length === 0
                        }
                        className="rounded-lg border border-blue-500/30 px-3 py-1 text-sm text-blue-400 hover:bg-blue-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {syncingAccountId === account.id
                          ? "Sincronizando..."
                          : "Sincronizar AWS"}
                      </button>
                    )}

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
                      onClick={() =>
                        setConfirmation({
                          action: "delete",
                          account,
                        })
                      }
                      disabled={deletingAccountId !== null}
                      className="rounded-lg border border-red-500/30 px-3 py-1 text-sm text-red-400 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {deletingAccountId === account.id
                        ? "Eliminando..."
                        : "Eliminar"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedAccount ? (
          <>
            <div className="mt-8 rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-5 py-4">
              <p className="text-sm text-slate-400">Vista actual</p>
              <p className="mt-1 font-semibold text-cyan-300">
                {selectedAccount.name}
              </p>
            </div>

            <div className="mt-8">
              <SyncHistoryPanel
                accountId={selectedAccount.id}
                refreshKey={selectedAccount.last_sync_at}
              />
            </div>

            {selectedResources.length > 0 ? (
              <CloudResourceTable resources={selectedResources} />
            ) : (
              <EmptyState
                title="Inventario cloud"
                message={`No se descubrieron recursos para ${selectedAccount.name}.`}
              />
            )}

            {selectedFindings.length > 0 ? (
              <FindingsPanel findings={selectedFindings} />
            ) : (
              <EmptyState
                title="Hallazgos y recomendaciones"
                message={
                  selectedResources.length > 0
                    ? "No se detectaron riesgos u oportunidades para esta cuenta."
                    : "Sin recursos inventariados no hay elementos para analizar."
                }
              />
            )}
          </>
        ) : (
          <EmptyState
            title="Inventario cloud"
            message="Selecciona una cuenta para consultar sus datos."
          />
        )}
      </section>
    </AppShell>
  );
}

function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <h3 className="text-xl font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-slate-400">{message}</p>
    </section>
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
