<template>
  <div>
    <v-card
      class="mt-2 mb-2"
      flat
    >
      <v-textarea
        label="Error Logs"
        style="width:100%;"
        :value="logValue"
      />
      <v-btn
        class="mt-4 ml-2"
        @click="updateLog"
      >
        update Log
      </v-btn>
    </v-card>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'ErrorLog',
  data: () => ({
    logValue: ''
  }),
  mounted () {
    this.updateLog()
  },
  methods: {
    async updateLog () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/error/logs`)
      this.logValue = response.data.replace(/topas_separator/g, '\n')
    }
  }
}
</script>
