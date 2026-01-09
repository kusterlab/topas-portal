import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import store from './store/store.js'
import router from './router'
import VueCookies from 'vue-cookies'
import PTMNavigatorPlugin from 'ptmnavigator-vue3'

createApp(App)
  .use(VueCookies, { expires: '1d' })
  .use(PTMNavigatorPlugin)
  .use(router)
  .use(store)
  .use(vuetify)
  .mount('#app')
