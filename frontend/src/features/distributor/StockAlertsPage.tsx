import { useQuery } from "@tanstack/react-query";
import { myForecast } from "@/api/forecast";
import EmptyState from "@/components/EmptyState";

// Stock-depletion view (Upgrade #4). Rows are sorted server-side with at-risk
// items first, ascending by predicted days to stockout - so what needs
// attention is at the top.
export default function StockAlertsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["forecast", "mine"], queryFn: myForecast });

  if (isLoading) return <p className="text-sm text-slate-500">Loading…</p>;
  if (!data || data.length === 0)
    return <EmptyState title="No stock data" hint="Add offers to your catalog first." />;

  return (
    <div className="space-y-3">
      <div>
        <h1 className="text-2xl font-bold">Stock alerts</h1>
        <p className="text-sm text-slate-500">
          Forecast = current stock ÷ average daily units sold over the last 30 days. Items predicted
          to run out within 7 days are flagged.
        </p>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">Medication</th>
              <th>Stock</th>
              <th>Avg daily units</th>
              <th>Days left</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((f) => (
              <tr key={f.offer_id} className="border-t border-slate-100">
                <td className="py-2">{f.medication_name}</td>
                <td>{f.current_stock}</td>
                <td>{f.avg_daily_units}</td>
                <td>{f.predicted_days_until_stockout ?? "—"}</td>
                <td>
                  {f.at_risk ? (
                    <span className="badge bg-rose-100 text-rose-700">At risk</span>
                  ) : (
                    <span className="badge bg-slate-100 text-slate-600">OK</span>
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
