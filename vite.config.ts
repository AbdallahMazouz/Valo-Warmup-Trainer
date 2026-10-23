import { defineConfig } from 'vite';

export default defineConfig({
  base: '/valo-warmup-trainer/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    target: 'es2022',
  },
  server: {
    port: 5173,
    open: false,
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
});
