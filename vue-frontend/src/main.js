import { createApp } from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify'
import store from './store/store.js'
import router from './router'

createApp(App)
  .use(router)
  .use(store)
  .use(vuetify)
  .mount('#app')
