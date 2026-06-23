import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { getMedication, rankForMedication } from "@/api/medications";
import { placeOrder } from "@/api/orders";

// The marquee feature: side-by-side comparison of distributor offers for one
// medication, sorted by total_score. Each row shows the score breakdown so
// the user can see *why* an offer ranks where it does (transparency = trust).
export default function ComparePage() {
  const { id } = useParams();
  const medId = Number(id);
  const [quantity, setQuantity] = useState(10);
  const nav = useNavigate();
  const qc = useQueryClient();

  const med = useQuery({
    queryKey: ["medication", medId],
    queryFn: () => getMedication(medId),
    enabled: !Number.isNaN(medId),
  });

  const ranking = useQuery({
    queryKey: ["ranking", medId, quantity],
    queryFn: () => rankForMedication(medId, quantity),
    enabled: !Number.isNaN(medId),
  });

  const order = useMutation({
    mutationFn: (distributorId: number) =>
      placeOrder({
        distributor_id: distributorId,
        items: [{ medication_id: medId, quantity }],
      }),
    onSuccess: (o) => {
      toast.success(`Order #${o.id} placed`);
      void qc.invalidateQueries({ queryKey: ["orders", "mine"] });
      nav(`/pharmacy/orders/${o.id}`);
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Could not place order";
      toast.error(msg);
    },
  });

  if (!med.data) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-5">
      <div>
        <Link to="/pharmacy/search" className="text-sm text-brand-600 hover:underline">
          ← Back to search
        </Link>
        <h1 className="text-2xl font-bold mt-1">{med.data.name}</h1>
        <p className="text-sm text-slate-500">
          {med.data.active_ingredient} • {med.data.strength} • {med.data.manufacturer}
        </p>
      </div>

      <div className="card flex items-end gap-3 flex-wrap">
        <div>
          <label className="label">Quantity to order</label>
          <input
            className="input w-32"
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
          />
        </div>
        <p className="text-xs text-slate-500 flex-1">
          Offers ranked by:
          <span className="font-semibold"> 60% price</span>,
          <span className="font-semibold"> 25% stock vs. requested quantity</span>,
          <span className="font-semibold"> 15% distributor reliability</span>.
        </p>
      </div>

      {ranking.isFetching && <p className="text-sm text-slate-500">Calculating…</p>}

      {ranking.data && ranking.data.length === 0 && (
        <div className="card text-slate-500">No distributors carry this medication yet.</div>
      )}

      <div className="grid gap-3">
        {ranking.data?.map((r, idx) => (
          <div key={r.offer_id} className="card flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-3 min-w-0">
              <span
                className={`badge ${
                  idx === 0 ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
                }`}
              >
                #{idx + 1}
              </span>
              <div className="min-w-0">
                <p className="font-semibold truncate">{r.distributor.company_name}</p>
                <p className="text-xs text-slate-500">
                  Reliability: {(r.distributor.reliability_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 sm:gap-6 text-sm">
              <div>
                <p className="text-xs text-slate-500">Final price</p>
                <p className="font-semibold">{r.final_unit_price.toFixed(2)} EGP</p>
                <p className="text-xs text-slate-400 line-through">{r.unit_price.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Discount</p>
                <p className="font-semibold">{r.discount_percent.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Stock</p>
                <p className="font-semibold">{r.stock}</p>
              </div>
            </div>
            <details className="text-xs text-slate-500">
              <summary className="cursor-pointer">Why this rank?</summary>
              <ul className="mt-1 space-y-0.5">
                <li>price_score: {r.price_score}</li>
                <li>stock_score: {r.stock_score}</li>
                <li>reliability_score: {r.reliability_score}</li>
                <li>
                  <span className="font-semibold">total: {r.total_score}</span>
                </li>
              </ul>
            </details>
            <button
              className="btn-primary sm:ml-auto"
              disabled={r.stock < quantity || order.isPending}
              onClick={() => order.mutate(r.distributor.id)}
            >
              {r.stock < quantity ? "Insufficient stock" : "Order"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
