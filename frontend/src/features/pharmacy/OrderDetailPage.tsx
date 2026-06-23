import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getOrder } from "@/api/orders";
import StatusBadge from "@/components/StatusBadge";
import { useAuth } from "@/auth/AuthContext";

// Shows the order's items + the full audit trail of state transitions.
// The audit trail is what makes "order tracking" defendable: every change
// recorded with its from/to/timestamp.
export default function OrderDetailPage() {
  const { id } = useParams();
  const orderId = Number(id);
  const { user } = useAuth();
  const backTo = user?.role === "DISTRIBUTOR" ? "/distributor/orders" : "/pharmacy/orders";
  const { data, isLoading } = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId),
    enabled: !Number.isNaN(orderId),
  });

  if (isLoading || !data) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-4">
      <div>
        <Link to={backTo} className="text-sm text-brand-600 hover:underline">
          ← Back to orders
        </Link>
        <h1 className="text-2xl font-bold mt-1 flex items-center gap-3">
          Order #{data.id} <StatusBadge status={data.status} />
        </h1>
        <p className="text-sm text-slate-500">
          Total: {data.total_amount.toFixed(2)} EGP • Created{" "}
          {new Date(data.created_at).toLocaleString()}
        </p>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-2">Items</h2>
        <ul className="divide-y divide-slate-100">
          {data.items.map((it) => (
            <li key={it.id} className="py-2 flex justify-between gap-3">
              <div>
                <p className="font-medium">{it.medication.name}</p>
                <p className="text-xs text-slate-500">
                  {it.medication.strength} • qty {it.quantity}
                </p>
              </div>
              <div className="text-right text-sm">
                <p>
                  {it.unit_price.toFixed(2)} × {it.quantity} − {it.discount_percent}%
                </p>
                <p className="font-semibold">{it.line_total.toFixed(2)} EGP</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-2">Audit trail</h2>
        <ol className="space-y-1 text-sm">
          {data.events.map((e) => (
            <li key={e.id} className="text-slate-600">
              <span className="text-xs text-slate-400">
                {new Date(e.created_at).toLocaleString()}
              </span>{" "}
              — {e.from_status ?? "—"} → <span className="font-semibold">{e.to_status}</span>
              {e.note && <span className="text-slate-500"> · {e.note}</span>}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
