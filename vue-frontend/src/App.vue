<template>
  <v-app>
    <v-main>
      <TheNotificationSnackbars />
      <explorer />
    </v-main>
  </v-app>
</template>

<script>
  import { mapActions } from 'vuex'
  import TheNotificationSnackbars from './components/partials/TheNotificationSnackbars.vue'

  import Explorer from './components/Explorer.vue'

  export default {
    name: 'App',
    components: {
      TheNotificationSnackbars,
      Explorer
    },
    created() {
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
