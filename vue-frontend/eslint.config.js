import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import vuetify from 'eslint-plugin-vuetify'
import parser from '@typescript-eslint/parser'
// import love from 'eslint-config-love'
import globals from 'globals'

export default [
  { ignores: ['**/*.{json,ico,html,png,svg,css.prdb}'] },
  {
    files: ['**/*.{js,mjs,cjs,ts,vue}'],
    languageOptions: {
      ecmaVersion: 2021,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node
      },
      parser,
      parserOptions: {
        tsconfigRootDir: import.meta.dirname
      }
    }
  },

  js.configs.recommended,
  ...vue.configs['flat/essential'],
  ...vuetify.configs['flat/base'],
  // love,

  {
    files: ['**/*.+(js|vue|jsx)'],
    rules: {
      'no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^e|_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
          destructuredArrayIgnorePattern: '^_'
        }
      ],

      'no-console': 'warn',
      'vue/multi-word-component-names': 'off',
      'vue/no-v-text-v-html-on-component': 'off'
    }
  }
]
