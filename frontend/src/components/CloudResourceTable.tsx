type CloudResource = {
  id: string;
  cloud_account_id: string;
  service: string;
  name: string;
  region: string;
  status: string;
  monthly_cost: string;
};

type Props = {
  resources: CloudResource[];
};

export default function CloudResourceTable({ resources }: Props) {
  const totalCost = resources.reduce(
    (total, resource) => total + Number(resource.monthly_cost),
    0,
  );

  if (resources.length === 0) {
    return null;
  }

  return (
    <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold">Inventario cloud</h3>
          <p className="mt-1 text-sm text-slate-400">
            Recursos descubiertos en las cuentas conectadas
          </p>
        </div>

        <div className="text-right">
          <p className="text-sm text-slate-400">Costo mensual estimado</p>
          <p className="text-2xl font-bold text-cyan-400">
            ${totalCost.toFixed(2)}
          </p>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-950 text-slate-400">
            <tr>
              <th className="px-5 py-4">Servicio</th>
              <th className="px-5 py-4">Recurso</th>
              <th className="px-5 py-4">Región</th>
              <th className="px-5 py-4">Estado</th>
              <th className="px-5 py-4 text-right">Costo mensual</th>
            </tr>
          </thead>

          <tbody>
            {resources.map((resource) => (
              <tr
                key={resource.id}
                className="border-t border-slate-800"
              >
                <td className="px-5 py-4 font-semibold text-cyan-400">
                  {resource.service}
                </td>
                <td className="px-5 py-4">{resource.name}</td>
                <td className="px-5 py-4 text-slate-400">
                  {resource.region}
                </td>
                <td className="px-5 py-4">
                  <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-emerald-400">
                    {resource.status}
                  </span>
                </td>
                <td className="px-5 py-4 text-right">
                  ${Number(resource.monthly_cost).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}