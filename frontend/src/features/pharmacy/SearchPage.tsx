import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { searchMedications } from "@/api/medications";

// Pharmacy search entry point. The user types a query; we debounce-by-typing
// (no fetch until they pause), then list matching medications with a deep
// link into the compare view.
export default function SearchPage() {
  const [q, setQ] = useState("");
  const { data, isFetching } = useQuery({
    queryKey: ["medications", q],
    queryFn: () => searchMedications(q || undefined),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Search medications</h1>
      <input
        className="input max-w-md"
        placeholder="e.g. Panadol, paracetamol, GSK"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <div className="card">
        {isFetching && <p className="text-sm text-slate-500">Searching…</p>}
        {!isFetching && data && data.length === 0 && (
          <p className="text-sm text-slate-500">No matches.</p>
        )}
        <ul className="divide-y divide-slate-100">
          {data?.map((m) => (
            <li key={m.id} className="py-3 flex flex-wrap items-center gap-3">
              <div className="min-w-0">
                <p className="font-medium truncate">{m.name}</p>
                <p className="text-xs text-slate-500 truncate">
                  {m.active_ingredient} • {m.strength} • {m.manufacturer}
                </p>
              </div>
              <Link
                to={`/pharmacy/compare/${m.id}`}
                className="ml-auto btn-secondary text-xs"
              >
                Compare offers
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
