import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listMyOrders } from "@/api/orders";
import { myForecast } from "@/api/forecast";
import { listMyOffers } from "@/api/offers";
import StatusBadge from "@/components/StatusBadge";

export default function DistributorHome() {
  const orders = useQuery({ queryKey: ["orders", "mine"], queryFn: listMyOrders });
  const offers = useQuery({ queryKey: ["offers", "mine"], queryFn: listMyOffers });
  const forecast = useQuery({ queryKey: ["forecast", "mine"], queryFn: myForecast });

  const pending = orders.data?.filter((o) => o.status === "PENDING").length ?? 0;
  const atRisk = forecast.data?.filter((f) => f.at_risk).length ?? 0;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Distributor Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-slate-500">Catalog size</p>
          <p className="text-3xl font-bold mt-1">{offers.data?.length ?? "—"}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Pending orders</p>
          <p className="text-3xl font-bold mt-1">{pending}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Products at stockout risk</p>
          <p className="text-3xl font-bold mt-1 text-rose-600">{atRisk}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link to="/distributor/catalog" className="btn-primary">
          Manage catalog
        </Link>
        <Link to="/distributor/orders" className="btn-secondary">
          View orders
        </Link>
        <Link to="/distributor/alerts" className="btn-secondary">
          Stock alerts
        </Link>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-3">Pending orders</h2>
        {pending === 0 ? (
          <p className="text-sm text-slate-500">All caught up.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {orders
              .data!.filter((o) => o.status === "PENDING")
              .slice(0, 5)
              .map((o) => (
                <li key={o.id} className="py-2 flex items-center gap-3">
                  <Link to={`/distributor/orders/${o.id}`} className="font-medium hover:underline">
                    #{o.id}
                  </Link>
                  <StatusBadge status={o.status} />
                  <span className="text-sm text-slate-500 ml-auto">
                    {o.total_amount.toFixed(2)} EGP
                  </span>
                </li>
              ))}
          </ul>
        )}
      </div>
    </div>
  );
}
