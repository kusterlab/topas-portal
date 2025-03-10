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
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/reload`)
      console.log(response)
    }
    /*
      escapeListener(event) {

        if(event.key === "F4" ){
          alert('Attempting to reset the Backend and it takes a bit time. Please check the console log of the browser for Success status.')
          console.log("The new data will be re-uploaded from the backend side. Please wait for the success status")
          this.loaderChange()
        }

    }
    */
  }

  /*
      we removed the previous old reload button
      <div class="d-flex align-center">
        <v-btn id="reload"
          class="ma-2"
          :loading="loading"
          :disabled="loading"
          color="secondary"
          @click="loader = 'loading'"
        >
          Load data
        </v-btn>
    </div>

*/

}
</script>
