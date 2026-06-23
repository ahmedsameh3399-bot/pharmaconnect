import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { changeOrderStatus, listMyOrders } from "@/api/orders";
import StatusBadge from "@/components/StatusBadge";
import EmptyState from "@/components/EmptyState";
import type { Order, OrderStatus } from "@/api/types";

// Distributor-side order inbox. The next valid action depends on current
// status - we let services/order_state.py be the source of truth, but UI
// suggests the most likely next step inline.
const NEXT_STEPS: Partial<Record<OrderStatus, { label: string; next: OrderStatus }[]>> = {
  PENDING: [
    { label: "Accept", next: "ACCEPTED" },
    { label: "Reject", next: "REJECTED" },
  ],
  ACCEPTED: [{ label: "Start preparing", next: "PREPARING" }],
  PREPARING: [{ label: "Mark shipped", next: "SHIPPED" }],
  SHIPPED: [{ label: "Mark completed", next: "COMPLETED" }],
};

export default function IncomingOrdersPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["orders", "mine"], queryFn: listMyOrders });

  const mutate = useMutation({
    mutationFn: ({ id, next }: { id: number; next: OrderStatus }) => changeOrderStatus(id, next),
    onSuccess: (_, vars) => {
      toast.success(`Order #${vars.id} → ${vars.next}`);
      void qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Update failed");
    },
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!data || data.length === 0)
    return <EmptyState title="No orders yet" />;

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Incoming orders</h1>
      <div className="grid gap-3">
        {data.map((o: Order) => (
          <div key={o.id} className="card flex flex-wrap items-center gap-3">
            <Link to={`/distributor/orders/${o.id}`} className="font-semibold hover:underline">
              #{o.id}
            </Link>
            <StatusBadge status={o.status} />
            <span className="text-sm text-slate-500">{o.items.length} items</span>
            <span className="text-sm font-medium ml-auto">{o.total_amount.toFixed(2)} EGP</span>
            {NEXT_STEPS[o.status]?.map((step) => (
              <button
                key={step.next}
                className={step.next === "REJECTED" ? "btn-danger text-xs" : "btn-primary text-xs"}
                disabled={mutate.isPending}
                onClick={() => mutate.mutate({ id: o.id, next: step.next })}
              >
                {step.label}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
