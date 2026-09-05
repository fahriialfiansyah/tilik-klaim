import { create } from 'zustand'

/**
 * Engine and dataset identity, mirroring the backend's `VersionStamp`.
 *
 * `sprint/00-app-spec.md` § 2 makes this a global element (G3): it appears on every page and
 * must be copyable, because it is what an operator quotes when reporting a result or
 * comparing two sessions. Every screening response carries it, so whichever page loaded most
 * recently fills this in and the shell renders it.
 */
export type VersionStamp = {
  readonly schema_version: string
  readonly ruleset_version: string
  readonly engine_version: string
  readonly dataset_version: string
}

type EngineVersionStore = {
  readonly versions: VersionStamp | null
  readonly setVersions: (versions: VersionStamp) => void
}

export const useEngineVersion = create<EngineVersionStore>((set) => ({
  versions: null,
  setVersions: (versions) => set({ versions }),
}))

/** Compact one-line form for the header chip, e.g. `r1.4.2 · m0.9.1 · ds-2026-08-c`. */
export function shortStamp(versions: VersionStamp | null): string {
  if (versions === null) {
    return '-'
  }
  return `r${versions.ruleset_version} · m${versions.engine_version} · ${versions.dataset_version}`
}


/**
 * Copy the stamp, reporting whether it actually worked.
 *
 * Clipboard access is denied in some browsers outside a user-gesture context, and the promise
 * rejects rather than resolving false. Callers must not show a success state on a copy that did
 * not happen — the stamp is what an operator quotes when reporting a result.
 */
export async function copyStamp(versions: VersionStamp | null): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(shortStamp(versions))
    return true
  } catch {
    return false
  }
}
