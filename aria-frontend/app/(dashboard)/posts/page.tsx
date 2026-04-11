// filename: app/(dashboard)/posts/page.tsx
// purpose: Paginated company posts list using TanStack Table.

"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";

import { useCompanyPosts } from "@/hooks/useCompanyPosts";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";
import type { PostResult } from "@/types";

const columnHelper = createColumnHelper<PostResult>();

export default function PostsPage() {
  const [page, setPage] = useState(0);
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;

  const query = useCompanyPosts(companyId, page);

  const columns = useMemo(
    () => [
      columnHelper.accessor("post_id", {
        header: "Post ID",
        cell: (info) => <span className="font-mono text-xs">{info.getValue()}</span>
      }),
      columnHelper.accessor("status", {
        header: "Status",
        cell: (info) => {
          const status = info.getValue();
          const cls =
            status === "generated"
              ? "bg-emerald-100 text-emerald-700"
              : status === "generating"
                ? "bg-sky-100 text-sky-700"
                : "bg-red-100 text-red-700";
          return <span className={`rounded-full px-2 py-1 text-xs ${cls}`}>{status}</span>;
        }
      }),
      columnHelper.display({
        id: "actions",
        header: "Actions",
        cell: (info) => {
          const row = info.row.original;
          return (
            <div className="flex gap-2">
              <Link href={`/posts/${row.post_id}/result`} className="text-xs text-sky-700 underline">
                Result
              </Link>
              <Link href={`/posts/${row.post_id}/schedule`} className="text-xs text-teal-700 underline">
                Schedule
              </Link>
            </div>
          );
        }
      })
    ],
    []
  );

  const table = useReactTable({
    data: query.data ?? [],
    columns,
    getCoreRowModel: getCoreRowModel()
  });

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="space-y-4 rounded-2xl border bg-white p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Posts</h1>
        <Link href="/posts/new" className="rounded-lg bg-slate-900 px-3 py-2 text-sm text-white">
          New post
        </Link>
      </header>

      {query.isLoading ? <p className="text-sm text-slate-600">Loading posts...</p> : null}

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id} className="border-b">
                {hg.headers.map((header) => (
                  <th key={header.id} className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-3 py-3 text-sm text-slate-700">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          disabled={page === 0}
          className="rounded border px-3 py-1 text-xs disabled:opacity-50"
          onClick={() => setPage((p) => Math.max(0, p - 1))}
        >
          Prev
        </button>
        <span className="text-xs text-slate-500">Page {page + 1}</span>
        <button
          type="button"
          disabled={!query.data || query.data.length < 20}
          className="rounded border px-3 py-1 text-xs disabled:opacity-50"
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </main>
  );
}
