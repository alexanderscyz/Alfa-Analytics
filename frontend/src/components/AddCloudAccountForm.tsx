"use client";

import { FormEvent, useState } from "react";
import type { CloudAccount } from "@/types/cloud";

type Props = {
  onCreated: (account: CloudAccount) => void;
  onCancel: () => void;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function AddCloudAccountForm({
  onCreated,
  onCancel,
}: Props) {
  const [name, setName] = useState("");
  const [accountId, setAccountId] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/api/v1/cloud-accounts/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name,
            aws_account_id: accountId,
          }),
        },
      );

      if (!response.ok) {
        const result = await response.json();

        setError(
          typeof result.detail === "string"
            ? result.detail
            : "No se pudo registrar la cuenta",
        );
        return;
      }

      onCreated(await response.json());
    } catch {
      setError(
        "No se pudo establecer conexión con Alfa Analytics",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6"
    >
      <h3 className="text-xl font-semibold">
        Agregar cuenta AWS
      </h3>

      <p className="mt-1 text-sm text-slate-400">
        Alfa Analytics generará automáticamente el ARN del rol y el
        External ID.
      </p>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <input
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Nombre del ambiente"
          className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
        />

        <input
          required
          minLength={12}
          maxLength={12}
          inputMode="numeric"
          pattern="[0-9]{12}"
          value={accountId}
          onChange={(event) =>
            setAccountId(
              event.target.value.replace(/\D/g, ""),
            )
          }
          placeholder="AWS Account ID de 12 dígitos"
          className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
        />
      </div>

      {error && (
        <p className="mt-4 text-sm text-red-400">
          {error}
        </p>
      )}

      <div className="mt-5 flex justify-end gap-3">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-slate-700 px-4 py-2"
        >
          Cancelar
        </button>

        <button
          disabled={saving}
          className="rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950 disabled:opacity-50"
        >
          {saving ? "Guardando..." : "Registrar cuenta"}
        </button>
      </div>
    </form>
  );
}