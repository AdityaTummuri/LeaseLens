import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

/**
 * Ultimate Vite Configuration for LeaseLens Frontend
 * Optimized for:
 * - Aggressive Terser minification & dead code elimination
 * - Stripping console.*, debugger, and AST comments
 * - Tree-shaking to keep total bundle < 150KB (well below 10MB repo/build limit)
 * - Deterministic vendor code splitting
 */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2022',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug', 'console.trace'],
        passes: 2,
        dead_code: true,
      },
      format: {
        comments: false,
      },
      mangle: {
        toplevel: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
      treeshake: {
        preset: 'smallest',
        moduleSideEffects: 'no-external',
      },
    },
    chunkSizeWarningLimit: 300,
    assetsInlineLimit: 0,
    sourcemap: false,
    cssMinify: true,
    cssCodeSplit: true,
  },
});
