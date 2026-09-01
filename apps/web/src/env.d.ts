/// <reference types="@rsbuild/core/types" />

// Rsbuild hanya membocorkan variabel berawalan `PUBLIC_` ke kode peramban. Deklarasi ini
// yang membuat `import.meta.env.PUBLIC_API_BASE_URL` bertipe, bukan `any`.
interface ImportMetaEnv {
  readonly PUBLIC_API_BASE_URL?: string
}
