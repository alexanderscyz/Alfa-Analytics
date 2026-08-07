import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
};

const navigation = [
  { label: "Resumen", symbol: "⌂", active: true },
  { label: "Infraestructura", symbol: "◇", active: false },
  { label: "Costos", symbol: "$", active: false },
  { label: "Seguridad", symbol: "✓", active: false },
  { label: "Historial", symbol: "↻", active: false },
  { label: "Reportes", symbol: "▤", active: false },
  { label: "Configuración", symbol: "⚙", active: false },
];

export default function AppShell({ children }: Props) {
  return (
    <div className="min-h-screen bg-[#050b18] text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-slate-800 bg-[#08111f] lg:flex">
        <div className="flex h-20 items-center border-b border-slate-800 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 text-xl font-black text-white shadow-lg shadow-cyan-500/20">
            A
          </div>

          <div className="ml-3">
            <p className="text-lg font-bold tracking-[0.18em] text-white">
              ALFA
            </p>
            <p className="text-[10px] tracking-[0.28em] text-cyan-400">
              ANALYTICS
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-4 py-6">
          {navigation.map((item) => (
            <div
              key={item.label}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm transition ${
                item.active
                  ? "bg-blue-600/20 text-cyan-300 ring-1 ring-blue-500/30"
                  : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-100"
              }`}
            >
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-lg ${
                  item.active
                    ? "bg-blue-500/20 text-cyan-300"
                    : "bg-slate-800 text-slate-500"
                }`}
              >
                {item.symbol}
              </span>

              <span>{item.label}</span>
            </div>
          ))}
        </nav>

        <div className="m-4 rounded-xl border border-slate-800 bg-slate-900/80 p-4">
          <p className="text-xs uppercase tracking-wider text-slate-500">
            Entorno
          </p>

          <div className="mt-3 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.8)]" />
            <span className="text-sm text-emerald-400">
              Sistema operativo
            </span>
          </div>

          <p className="mt-2 text-xs text-slate-500">
            Ejecución local
          </p>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-slate-800 bg-[#08111f]/95 backdrop-blur">
          <div className="flex h-20 items-center justify-between px-5 sm:px-8">
            <div>
              <p className="text-lg font-semibold text-white">
                Resumen General
              </p>
              <p className="text-xs text-slate-400">
                Visión general de la infraestructura AWS
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden rounded-xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-500 md:block">
                Alfa Analytics
              </div>

              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 font-semibold text-white">
                AS
              </div>
            </div>
          </div>
        </header>

        <main>{children}</main>
      </div>
    </div>
  );
}