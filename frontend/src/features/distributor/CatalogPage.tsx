import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { deleteMyOffer, listMyOffers, upsertMyOffer } from "@/api/offers";
import { searchMedications } from "@/api/medications";
import EmptyState from "@/components/EmptyState";

// Distributor catalog management. Two halves: a form to add or edit an offer
// (medication picker + price/discount/stock), and a table of existing offers
// with quick-edit and delete.
export default function CatalogPage() {
  const qc = useQueryClient();
  const offers = useQuery({ queryKey: ["offers", "mine"], queryFn: listMyOffers });

  const [medQuery, setMedQuery] = useState("");
  const [medId, setMedId] = useState<number | null>(null);
  const [unitPrice, setUnitPrice] = useState(50);
  const [discount, setDiscount] = useState(0);
  const [stock, setStock] = useState(100);

  const meds = useQuery({
    queryKey: ["medications", medQuery],
    queryFn: () => searchMedications(medQuery || undefined),
  });

  const upsert = useMutation({
    mutationFn: () =>
      upsertMyOffer({
        medication_id: medId!,
        unit_price: unitPrice,
        discount_percent: discount,
        stock,
      }),
    onSuccess: () => {
      toast.success("Offer saved");
      void qc.invalidateQueries({ queryKey: ["offers", "mine"] });
      setMedId(null);
      setMedQuery("");
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Save failed");
    },
  });

  const del = useMutation({
    mutationFn: (id: number) => deleteMyOffer(id),
    onSuccess: () => {
      toast.success("Offer removed");
      void qc.invalidateQueries({ queryKey: ["offers", "mine"] });
    },
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">My catalog</h1>

      <div className="card space-y-3">
        <h2 className="font-semibold">Add / update offer</h2>
        <div>
          <label className="label">Medication</label>
          <input
            className="input"
            placeholder="Type to search..."
            value={medQuery}
            onChange={(e) => {
              setMedQuery(e.target.value);
              setMedId(null);
            }}
          />
          {medQuery && !medId && meds.data && (
            <ul className="mt-1 max-h-40 overflow-y-auto border border-slate-200 rounded-md bg-white text-sm">
              {meds.data.slice(0, 8).map((m) => (
                <li
                  key={m.id}
                  className="px-2 py-1 hover:bg-slate-50 cursor-pointer"
                  onClick={() => {
                    setMedId(m.id);
                    setMedQuery(`${m.name} (${m.strength})`);
                  }}
                >
                  {m.name} — {m.strength} • {m.manufacturer}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="label">Unit price</label>
            <input
              type="number"
              className="input"
              min={0.01}
              step={0.01}
              value={unitPrice}
              onChange={(e) => setUnitPrice(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="label">Discount %</label>
            <input
              type="number"
              className="input"
              min={0}
              max={100}
              value={discount}
              onChange={(e) => setDiscount(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="label">Stock</label>
            <input
              type="number"
              className="input"
              min={0}
              value={stock}
              onChange={(e) => setStock(Number(e.target.value))}
            />
          </div>
        </div>
        <button
          className="btn-primary"
          disabled={!medId || upsert.isPending}
          onClick={() => upsert.mutate()}
        >
          Save offer
        </button>
      </div>

      <div className="card overflow-x-auto">
        <h2 className="font-semibold mb-2">Existing offers</h2>
        {!offers.data || offers.data.length === 0 ? (
          <EmptyState title="No offers yet" hint="Add your first medication above." />
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-2">Medication</th>
                <th>Price</th>
                <th>Discount</th>
                <th>Final</th>
                <th>Stock</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {offers.data.map((o) => (
                <tr key={o.id} className="border-t border-slate-100">
                  <td className="py-2">
                    <p className="font-medium">{o.medication.name}</p>
                    <p className="text-xs text-slate-500">{o.medication.strength}</p>
                  </td>
                  <td>{o.unit_price.toFixed(2)}</td>
                  <td>{o.discount_percent.toFixed(1)}%</td>
                  <td className="font-semibold">{o.final_unit_price.toFixed(2)}</td>
                  <td>{o.stock}</td>
                  <td className="text-right">
                    <button
                      className="btn-secondary text-xs"
                      onClick={() => {
                        setMedId(o.medication_id);
                        setMedQuery(`${o.medication.name} (${o.medication.strength})`);
                        setUnitPrice(o.unit_price);
                        setDiscount(o.discount_percent);
                        setStock(o.stock);
                      }}
                    >
                      Edit
                    </button>
                    <button
                      className="btn-danger text-xs ml-2"
                      onClick={() => del.mutate(o.id)}
                      disabled={del.isPending}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
