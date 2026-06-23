import { useQuery } from "@tanstack/react-query";
import { metrics } from "@/api/admin";

export default function AdminHome() {
  const { data, isLoading } = useQuery({ queryKey: ["admin", "metrics"], queryFn: metrics });
  if (isLoading || !data) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">System metrics</h1>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {Object.entries(data).map(([k, v]) => (
          <div key={k} className="card">
            <p className="text-sm text-slate-500 capitalize">{k.replace(/_/g, " ")}</p>
            <p className="text-3xl font-bold mt-1">{v}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
