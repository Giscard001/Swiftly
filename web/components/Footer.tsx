import { Lock, ShieldCheck, Trash2, Heart } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-black/5 dark:border-white/10">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          FilesConvert — pour l’usage perso et les proches.
        </p>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-gray-400 dark:text-gray-500">
          <span className="flex items-center gap-1.5"><ShieldCheck className="h-3.5 w-3.5" /> Transfert chiffré</span>
          <span className="flex items-center gap-1.5"><Trash2 className="h-3.5 w-3.5" /> Suppression auto après 1h</span>
          <span className="flex items-center gap-1.5"><Lock className="h-3.5 w-3.5" /> Stockage hors-ligne web</span>
          <span className="flex items-center gap-1.5"><Heart className="h-3.5 w-3.5 text-rose-400" /> Sans inscription</span>
        </div>
      </div>
    </footer>
  );
}
