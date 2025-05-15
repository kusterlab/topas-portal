<template>
  <div>
    <v-card
      class="mt-2 mb-2"
      flat
    >
      <v-card-title
        tag="h1"
      >
        Config - File
      </v-card-title>
      <textarea
        v-model="configValue"
        rows="10"
        cols="200"
        readonly
      />
      <v-row>
        <v-btn
          class="ma-2"
          color="primary"
          @click="showConfig"
        >
          <v-icon
            dark
          >
            mdi-refresh
          </v-icon>
        </v-btn>
      </v-row>
    </v-card>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  name: 'ShowConfig',
  data: () => ({
    configValue: '',
    item: ''
  }),
  mounted () {
    this.showConfig()
  },
  methods: {
    async showConfig () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/config`)
      this.configValue = JSON.stringify(response.data, null, 2)
      console.log(response)
    }
  }
}
</script>
