"use client";

import { FormEvent, useState } from "react";

type CloudAccount = {
  id: string;
  name: string;
  provider: string;
  aws_account_id: string;
  status: string;
};

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
  const [roleArn, setRoleArn] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");

    const response = await fetch(
      `${API_URL}/api/v1/cloud-accounts/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          aws_account_id: accountId,
          role_arn: roleArn,
        }),
      },
    );

    if (!response.ok) {
      const result = await response.json();
      setError(result.detail ?? "No se pudo registrar la cuenta");
      setSaving(false);
      return;
    }

    onCreated(await response.json());
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="mb-8 rounded-2xl border border-slate-800 bg-slate-900 p-6"
    >
      <h3 className="text-xl font-semibold">Agregar cuenta AWS</h3>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
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
          value={accountId}
          onChange={(event) => setAccountId(event.target.value)}
          placeholder="AWS Account ID"
          className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
        />

        <input
          required
          value={roleArn}
          onChange={(event) => setRoleArn(event.target.value)}
          placeholder="IAM Role ARN"
          className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 outline-none focus:border-cyan-500"
        />
      </div>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

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