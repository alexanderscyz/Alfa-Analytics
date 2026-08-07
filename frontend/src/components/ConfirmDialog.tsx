type Props = {
  open: boolean;
  title: string;
  message: string;
  confirmLabel: string;
  variant?: "primary" | "danger";
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  variant = "primary",
  busy = false,
  onConfirm,
  onCancel,
}: Props) {
  if (!open) {
    return null;
  }

  const confirmStyle =
    variant === "danger"
      ? "bg-red-500 text-white hover:bg-red-400"
      : "bg-cyan-500 text-slate-950 hover:bg-cyan-400";

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/80 p-5 backdrop-blur-sm">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirmation-title"
        className="w-full max-w-md rounded-2xl border border-slate-700 bg-[#0d1728] p-6 shadow-2xl shadow-black/40"
      >
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-500/15 text-xl text-cyan-400">
          ?
        </div>

        <h2
          id="confirmation-title"
          className="mt-5 text-xl font-semibold text-white"
        >
          {title}
        </h2>

        <p className="mt-3 leading-6 text-slate-400">
          {message}
        </p>

        <div className="mt-7 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-50"
          >
            Cancelar
          </button>

          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className={`rounded-xl px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 ${confirmStyle}`}
          >
            {busy ? "Procesando..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}