const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  chainWebpack: config => {
  },
  transpileDependencies: [
    'vuetify'
  ],

  outputDir: '../dist',

  // relative to outputDir
  assetsDir: 'static',

  publicPath: process.env.NODE_ENV === 'production'
    ? '/master_topas-portal/'
    : '/'
})
