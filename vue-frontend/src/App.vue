<template>
  <v-app>
    <v-main>
      <TheNotificationSnackbars />
      <explorer />
    </v-main>
  </v-app>
</template>

<script>
import TheNotificationSnackbars from './components/partials/TheNotificationSnackbars'

import axios from 'axios'
import { mapActions } from 'vuex'
import Explorer from './components/Explorer'

export default {
  name: 'App',
  components: {
    TheNotificationSnackbars,
    Explorer
  },
  data: () => ({
    imagesrc: require('@/assets/topas_logo.png')
  }),

  watch: {
    async loader () {
      this.loaderChange()
    }
  },
  created () {
    this.fetchAllCohorts()
    window.addEventListener('keydown', this.escapeListener)
  },

  methods: {
    ...mapActions({
      fetchAllCohorts: 'fetchAllCohorts'
    }),
    async loaderChange () {
      await axios.get(`${process.env.VUE_APP_API_HOST}/reload`)
    }
  }
}
</script>
