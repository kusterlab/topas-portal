// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'
import { fileURLToPath, URL } from 'node:url'
import { resolve } from 'node:path'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

export default defineConfig({
  plugins: [
    vue({
      template: {
        transformAssetUrls,
        compilerOptions: {
          isCustomElement: tag => tag.startsWith('biowc-')
        }
      }
    }),
    vuetify({ autoImport: true })
  ],
  define: {
    global: 'globalThis',
    'process.env': {
      NODE_ENV: JSON.stringify(process.env.NODE_ENV || 'development')
    }
  },

  resolve: {
    alias: {
      '../node_modules/fmin/index.js': 'fmin',
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'ptmnavigator-vue3': resolve(__dirname, 'node_modules/ptmnavigator-vue3')
    }
  },

  build: {
    outDir: 'dist',
    assetsDir: 'static',
    sourcemap: true
  },
  base: process.env.NODE_ENV === 'production' ? '/master_topas-portal/' : '/',

  optimizeDeps: {
    include: ['vuetify', 'fmin', 'uuid', 'venn.js']
  }
})
