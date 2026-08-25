import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' keeps asset paths relative so this works on GitHub Pages
// under /<repo>/ without hardcoding the repository name.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: { outDir: 'dist' },
})
