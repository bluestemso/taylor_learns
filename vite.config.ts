import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  plugins: [
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './assets/javascript'),
      // this may not be needed anymore, but leaving it shouldn't hurt
      'use-sync-external-store/shim': path.resolve(__dirname, './node_modules/use-sync-external-store/shim'),
    },
  },
  base: '/static/', // Should match Django's STATIC_URL
  build: {
    manifest: true, // The manifest.json file is needed for django-vite
    outDir: path.resolve(__dirname, './static'), // Output directory for production build
    emptyOutDir: false, // Preserve the outDir to not clobber Django's other files.
    cssMinify: 'esbuild',
    rollupOptions: {
      onwarn(warning, warn) {
        if (warning.code === 'EVAL' && warning.id?.includes('node_modules/htmx.org/')) {
          return;
        }
        warn(warning);
      },
      input: {
        'site-base-css': path.resolve(__dirname, './assets/styles/site-base.css'),
        'site-tailwind-css': path.resolve(__dirname, './assets/styles/site-tailwind.css'),
        'site': path.resolve(__dirname, './assets/javascript/site.js'),
        'app': path.resolve(__dirname, './assets/javascript/app.js'),
        'chat-ws-initialize': path.resolve(__dirname, './assets/javascript/chat/ws_initialize.ts'),
      },
      output: {
        // Use hashed entry names to prevent stale browser/CDN caches
        entryFileNames: `js/[name]-[hash].js`,
        // Shared chunks stay hashed
        chunkFileNames: `js/[name]-[hash].js`,
        // Keep CSS in css/ with hashed names; hash all other assets
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith('.css')) {
            return `css/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
      },
    },
  },
  server: {
    port: 5173, // Default Vite dev server port, must match DJANGO_VITE settings
    strictPort: true, // Vite will exit if the port is already in use
    hmr: {
      // host: 'localhost', // default of localhost is fine as long as Django is running there.
      // protocol: 'ws', // default of ws is fine. Change to 'wss' if Django (dev) server uses HTTPS.
    },
  },
});
