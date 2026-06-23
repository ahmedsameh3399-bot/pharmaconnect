import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listMyOrders } from "@/api/orders";
import StatusBadge from "@/components/StatusBadge";

// Pharmacy landing page: high-level stats + recent orders. Keeps the user
// oriented after login so they're never staring at a blank screen.
export default function PharmacyHome() {
  const { data: orders } = useQuery({ queryKey: ["orders", "mine"], queryFn: listMyOrders });
  const orderCount = orders?.length ?? 0;
  const pendingCount = orders?.filter((o) => o.status === "PENDING").length ?? 0;
  const totalSpent =
    orders
      ?.filter((o) => o.status === "COMPLETED")
      .reduce((acc, o) => acc + o.total_amount, 0)
      .toFixed(2) ?? "0.00";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Pharmacy Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-slate-500">Total orders</p>
          <p className="text-3xl font-bold mt-1">{orderCount}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Pending</p>
          <p className="text-3xl font-bold mt-1">{pendingCount}</p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Total spent (completed)</p>
          <p className="text-3xl font-bold mt-1">{totalSpent}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link className="btn-primary" to="/pharmacy/search">
          Search & compare medications
        </Link>
        <Link className="btn-secondary" to="/pharmacy/chatbot">
          Ask the assistant
        </Link>
      </div>

      <div className="card">
        <h2 className="font-semibold mb-3">Recent orders</h2>
        {orderCount === 0 ? (
          <p className="text-sm text-slate-500">No orders yet.</p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {orders!.slice(0, 5).map((o) => (
              <li key={o.id} className="py-3 flex items-center gap-3">
                <Link to={`/pharmacy/orders/${o.id}`} className="font-medium hover:underline">
                  #{o.id}
                </Link>
                <StatusBadge status={o.status} />
                <span className="text-sm text-slate-500 ml-auto">{o.total_amount.toFixed(2)} EGP</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
