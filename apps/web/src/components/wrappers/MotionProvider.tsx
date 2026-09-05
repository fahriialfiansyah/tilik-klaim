import { MotionConfig } from 'motion/react'
import type { ReactNode } from 'react'

import { EASE_OUT, MOTION, seconds } from '@/modules/motion/timing'

/**
 * Adapter satu-satunya ke Motion. Semua animasi berbasis JavaScript di aplikasi ini
 * berjalan di dalamnya.
 *
 * Dua hal dipusatkan di sini alih-alih diulang di setiap komponen:
 *
 * `reducedMotion="user"` — Motion membaca `prefers-reduced-motion` sendiri dan
 * melewati animasi transform serta layout, hanya menyisakan opacity. Ini pasangan
 * JavaScript dari sakelar CSS di `src/styles/motion.css`; keduanya diperlukan karena
 * animasi Motion tidak melalui aturan `@media` mana pun.
 *
 * `transition` — durasi dan easing bawaan, sehingga komponen tidak perlu menyebut
 * angka sendiri. Komponen yang butuh durasi lain menimpanya di tempat, dan penimpaan
 * itu jadi keputusan yang terlihat saat dibaca.
 */
export function MotionProvider({ children }: { readonly children: ReactNode }) {
  return (
    <MotionConfig
      reducedMotion="user"
      transition={{ duration: seconds(MOTION.layout), ease: EASE_OUT }}
    >
      {children}
    </MotionConfig>
  )
}
