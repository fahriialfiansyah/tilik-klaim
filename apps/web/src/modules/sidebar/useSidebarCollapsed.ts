import { create } from 'zustand'

const STORAGE_KEY = 'tilik-sidebar'
const COLLAPSED = 'collapsed'
const EXPANDED = 'expanded'

/**
 * Membaca pilihan operator. Rail terbuka adalah bawaan: label menu adalah cara
 * seorang peninjau baru tahu halaman apa saja yang ada, dan itu tidak boleh
 * bergantung pada menebak ikon.
 */
function initialCollapsed(): boolean {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === COLLAPSED
  } catch {
    // Mode privat dan penyimpanan situs yang diblokir sama-sama melempar di sini.
    // Rail terbuka adalah jawaban yang utuh, jadi ini bukan kegagalan yang ditelan.
    return false
  }
}

function persist(collapsed: boolean): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, collapsed ? COLLAPSED : EXPANDED)
  } catch {
    // Menyimpan hanya kenyamanan; sesi ini tetap memakai pilihan yang baru dibuat.
  }
}

type SidebarStore = {
  readonly collapsed: boolean
  readonly toggle: () => void
}

/**
 * Apakah rail navigasi sedang diciutkan.
 *
 * Disimpan dengan pola yang sama seperti `modules/theme/useTheme.ts` — pilihan tata
 * letak yang dibuat sekali sebaiknya tidak perlu dibuat ulang setiap kali halaman dimuat.
 */
export const useSidebarCollapsed = create<SidebarStore>((set, get) => ({
  collapsed: initialCollapsed(),
  toggle: () => {
    const next = !get().collapsed
    persist(next)
    set({ collapsed: next })
  },
}))
