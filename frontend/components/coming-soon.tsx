import { Construction } from "lucide-react";

export function ComingSoon({ title }: { title: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100">
        <Construction className="h-8 w-8 text-slate-400" />
      </div>
      <h1 className="mt-6 text-2xl font-bold text-slate-900">{title}</h1>
      <p className="mt-2 text-sm text-slate-500">
        This section is coming soon. Check back later.
      </p>
    </div>
  );
}
