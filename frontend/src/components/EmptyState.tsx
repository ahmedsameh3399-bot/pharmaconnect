export default function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="card text-center text-slate-500">
      <p className="font-medium">{title}</p>
      {hint && <p className="text-sm mt-1">{hint}</p>}
    </div>
  );
}
