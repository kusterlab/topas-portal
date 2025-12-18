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
  created () {
    this.fetchAllCohorts()
    this.fetchCommonFields()
    window.addEventListener('keydown', this.escapeListener)
  },

  methods: {
    ...mapActions({
      fetchAllCohorts: 'fetchAllCohorts',
      fetchCommonFields: 'fetchCommonFields'
    })
  }
}
</script>
