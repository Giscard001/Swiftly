"use client";

import { useMemo } from "react";
import type { Capabilities, CapabilityTarget } from "@/lib/converter-client";
import { categoryIcon, categoryLabel } from "@/lib/formats";
import { cn } from "@/lib/utils";

type Props = {
  sourceExt: string;
  capabilities: Capabilities | null;
  selected: string | null;
  onSelect: (target: string, category: string) => void;
};

export function FormatSelector({ sourceExt, capabilities, selected, onSelect }: Props) {
  const grouped = useMemo(() => {
    if (!capabilities || !sourceExt) return new Map<string, CapabilityTarget[]>();
    const list = capabilities.by_source[sourceExt] ?? [];
    const m = new Map<string, CapabilityTarget[]>();
    for (const t of list) {
      const arr = m.get(t.category) ?? [];
      arr.push(t);
      m.set(t.category, arr);
    }
    return m;
  }, [capabilities, sourceExt]);

  if (!sourceExt) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Déposez un fichier pour voir les formats de sortie disponibles.
      </p>
    );
  }

  if (grouped.size === 0) {
    return (
      <div className="rounded-xl border border-amber-300/40 bg-amber-50/60 p-4 text-sm text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-300">
        Aucune conversion disponible pour <code className="font-mono font-semibold">.{sourceExt}</code> avec les
        binaires actuellement installés. Voir la section « Binaires » du README.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {Array.from(grouped.entries()).map(([category, targets]) => (
        <div key={category}>
          <p className="mb-2.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400 dark:text-gray-500">
            <span className="text-base">{categoryIcon(category)}</span>
            {categoryLabel(category)}
          </p>
          <div className="flex flex-wrap gap-2">
            {targets.map((t) => {
              const active = selected === t.target;
              return (
                <button
                  key={`${category}-${t.target}`}
                  type="button"
                  onClick={() => onSelect(t.target, category)}
                  className={cn(
                    "rounded-xl border px-3.5 py-2 text-sm font-medium transition-all duration-150",
                    active
                      ? "border-brand-600 bg-brand-600 text-white shadow-md shadow-brand-600/20 scale-[1.03]"
                      : "border-black/5 bg-white hover:border-brand-400 hover:bg-brand-50/50 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-brand-400/60 dark:hover:bg-brand-500/5"
                  )}
                >
                  .{t.target}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
