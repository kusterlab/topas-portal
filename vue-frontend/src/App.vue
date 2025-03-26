<template>
  <v-app>
    <v-main>
      <explorer />
    </v-main>
  </v-app>
</template>

<script>

import axios from 'axios'
import { mapActions } from 'vuex'
import Explorer from './components/Explorer'

export default {
  name: 'App',
  components: {
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
    this.fetchAllDiseases()
    window.addEventListener('keydown', this.escapeListener)
  },

  methods: {
    ...mapActions({
      fetchAllDiseases: 'fetchAllDiseases'
    }),
    async loaderChange () {
      await axios.get(`${process.env.VUE_APP_API_HOST}/reload`)
    }
  }
}
</script>
