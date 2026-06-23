import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { listUsers, setSuspension } from "@/api/admin";

export default function AdminUsersPage() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["admin", "users"], queryFn: listUsers });

  const toggle = useMutation({
    mutationFn: ({ id, suspended }: { id: number; suspended: boolean }) =>
      setSuspension(id, suspended),
    onSuccess: () => {
      toast.success("Updated");
      void qc.invalidateQueries({ queryKey: ["admin", "users"] });
    },
    onError: () => toast.error("Failed"),
  });

  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-bold">Users</h1>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500">
            <tr>
              <th className="py-2">ID</th>
              <th>Email</th>
              <th>Name</th>
              <th>Role</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data?.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="py-2">{u.id}</td>
                <td>{u.email}</td>
                <td>{u.full_name}</td>
                <td>
                  <span className="badge bg-slate-100">{u.role}</span>
                </td>
                <td>
                  {u.is_suspended ? (
                    <span className="badge bg-rose-100 text-rose-700">Suspended</span>
                  ) : (
                    <span className="badge bg-emerald-100 text-emerald-700">Active</span>
                  )}
                </td>
                <td className="text-right">
                  {u.role !== "ADMIN" && (
                    <button
                      className={u.is_suspended ? "btn-secondary text-xs" : "btn-danger text-xs"}
                      onClick={() => toggle.mutate({ id: u.id, suspended: !u.is_suspended })}
                      disabled={toggle.isPending}
                    >
                      {u.is_suspended ? "Unsuspend" : "Suspend"}
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
