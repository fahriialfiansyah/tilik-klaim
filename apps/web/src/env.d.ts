/// <reference types="@rsbuild/core/types" />

// Rsbuild hanya membocorkan variabel berawalan `PUBLIC_` ke kode peramban. Deklarasi ini
// yang membuat `import.meta.env.PUBLIC_API_BASE_URL` bertipe, bukan `any`.
interface ImportMetaEnv {
  readonly PUBLIC_API_BASE_URL?: string
}

// `?raw` gives a file's text as a string (Vite/Rsbuild/Vitest all honour it). Used only by
// tests that assert on what a module imports — the frontend counterpart of the backend's
// syntax-tree guards.
declare module '*?raw' {
  const source: string
  export default source
}
