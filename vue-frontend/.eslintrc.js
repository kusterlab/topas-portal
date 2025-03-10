module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es6: true
  },
  extends: [
    'plugin:vue/vue3-essential',
    'standard-with-typescript'
  ],
  overrides: [
    {
      files: '**/*.+(js|vue|jsx)',
      extends: [
        'standard',
        'eslint:recommended',
        'plugin:vue/recommended'
      ],
      rules: {
        'no-console': 'warn',
        'vue/multi-word-component-names': 'off',
        // Currently no way around this with help html
        // Make sure to always use `$sanitizeHtml(html)` when using `v-html`
        'vue/no-v-text-v-html-on-component': 'off'
      }
    }
  ],

  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module'
  },
  plugins: [
    'vue'
  ],
  rules: {
  }
}
