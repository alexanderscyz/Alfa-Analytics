export type NotificationData = {
  type: "success" | "error" | "info";
  title: string;
  message: string;
};

type Props = {
  notification: NotificationData | null;
  onClose: () => void;
};

const styles = {
  success: {
    border: "border-emerald-500/30",
    background: "bg-emerald-500/10",
    icon: "bg-emerald-500/20 text-emerald-400",
    symbol: "✓",
  },
  error: {
    border: "border-red-500/30",
    background: "bg-red-500/10",
    icon: "bg-red-500/20 text-red-400",
    symbol: "!",
  },
  info: {
    border: "border-blue-500/30",
    background: "bg-blue-500/10",
    icon: "bg-blue-500/20 text-blue-400",
    symbol: "i",
  },
};

export default function NotificationToast({
  notification,
  onClose,
}: Props) {
  if (!notification) {
    return null;
  }

  const style = styles[notification.type];

  return (
    <div
      role="status"
      className={`fixed right-5 top-24 z-[70] w-[calc(100%-2.5rem)] max-w-md rounded-2xl border p-4 shadow-2xl backdrop-blur ${style.border} ${style.background}`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl font-bold ${style.icon}`}
        >
          {style.symbol}
        </div>

        <div className="min-w-0 flex-1">
          <p className="font-semibold text-slate-100">
            {notification.title}
          </p>

          <p className="mt-1 whitespace-pre-line text-sm leading-6 text-slate-300">
            {notification.message}
          </p>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar notificación"
          className="rounded-lg px-2 py-1 text-slate-400 hover:bg-white/5 hover:text-white"
        >
          ×
        </button>
      </div>
    </div>
  );
}