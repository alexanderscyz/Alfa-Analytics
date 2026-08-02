"use client";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type CloudAccount = {
  id: string;
  name: string;
  aws_account_id: string;
  role_arn: string;
  external_id: string | null;
};

type Props = {
  account: CloudAccount;
  onClose: () => void;
};

export default function AWSSetupPanel({
  account,
  onClose,
}: Props) {
  async function copyExternalId() {
    if (account.external_id) {
      await navigator.clipboard.writeText(account.external_id);
    }
  }

  return (
    <section className="mb-8 rounded-2xl border border-blue-500/30 bg-slate-900 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold">
            Configurar conexión AWS
          </h3>

          <p className="mt-1 text-sm text-slate-400">
            Crea mediante CloudFormation el rol de solo lectura que
            utilizará Alfa Analytics.
          </p>
        </div>

        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white"
        >
          Cerrar
        </button>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
          <p className="text-xs uppercase text-slate-500">
            AWS Account ID
          </p>

          <p className="mt-2 font-mono text-sm">
            {account.aws_account_id}
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
          <p className="text-xs uppercase text-slate-500">
            IAM Role ARN
          </p>

          <p className="mt-2 break-all font-mono text-sm">
            {account.role_arn}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950 p-4">
        <p className="text-xs uppercase text-slate-500">
          External ID
        </p>

        <div className="mt-2 flex items-center justify-between gap-4">
          <p className="break-all font-mono text-sm text-cyan-400">
            {account.external_id ?? "Pendiente de generación"}
          </p>

          <button
            onClick={copyExternalId}
            disabled={!account.external_id}
            className="rounded-lg border border-cyan-500/30 px-3 py-1 text-sm text-cyan-400 hover:bg-cyan-500/10 disabled:opacity-40"
          >
            Copiar
          </button>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-slate-800 p-4">
        <h4 className="font-semibold">Pasos de configuración</h4>

        <ol className="mt-3 list-inside list-decimal space-y-2 text-sm text-slate-300">
          <li>Descarga la plantilla generada para esta cuenta.</li>
          <li>
            Abre AWS CloudFormation y crea un stack con la plantilla.
          </li>
          <li>
            Confirma que el stack haya creado el rol de solo lectura.
          </li>
          <li>
            Regresa a Alfa Analytics y pulsa Sincronizar AWS.
          </li>
        </ol>

        <a
          href={`${API_URL}/api/v1/cloud-accounts/${account.id}/cloudformation`}
          download
          className="mt-5 inline-flex rounded-lg bg-orange-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-orange-400"
        >
          Descargar plantilla CloudFormation
        </a>
      </div>

      <p className="mt-4 text-sm text-emerald-400">
        La plantilla crea únicamente un rol IAM y una política de solo
        lectura. No crea servidores ni otros recursos facturables.
      </p>
    </section>
  );
}