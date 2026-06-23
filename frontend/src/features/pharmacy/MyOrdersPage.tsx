import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { changeOrderStatus, listMyOrders } from "@/api/orders";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";

export default function MyOrdersPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["orders", "mine"], queryFn: listMyOrders });

  const cancel = useMutation({
    mutationFn: (id: number) => changeOrderStatus(id, "CANCELLED", "Cancelled by pharmacy"),
    onSuccess: () => {
      toast.success("Order cancelled");
      void qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Could not cancel");
    },
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!data || data.length === 0)
    return <EmptyState title="No orders yet" hint="Use Search & Compare to place your first order." />;

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">My orders</h1>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">#</th>
              <th>Items</th>
              <th>Total</th>
              <th>Status</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data.map((o) => (
              <tr key={o.id} className="border-t border-slate-100">
                <td className="py-2">
                  <Link to={`/pharmacy/orders/${o.id}`} className="text-brand-600 hover:underline">
                    #{o.id}
                  </Link>
                </td>
                <td>{o.items.length}</td>
                <td>{o.total_amount.toFixed(2)}</td>
                <td>
                  <StatusBadge status={o.status} />
                </td>
                <td className="whitespace-nowrap">{new Date(o.created_at).toLocaleString()}</td>
                <td className="text-right">
                  {o.status === "PENDING" && (
                    <button
                      className="btn-secondary text-xs"
                      onClick={() => cancel.mutate(o.id)}
                      disabled={cancel.isPending}
                    >
                      Cancel
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
