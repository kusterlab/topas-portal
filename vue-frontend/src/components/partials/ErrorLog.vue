<template>
  <v-container
    fluid
    class="pa-0"
  >
    <v-card flat>
      <v-card-title>Data loading logs</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="11">
            <v-textarea
              label="Loading Logs"
              style="width:100%;"
              filled
              hide-details
              :value="infoLogs"
            />
          </v-col>
          <v-col cols="1">
            <v-btn
              color="primary"
              @click="updateInfoLogs"
            >
              <v-icon
                dark
              >
                mdi-refresh
              </v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    <v-card
      class="mt-4"
      flat
    >
      <v-card-title>Error logs</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="11">
            <v-textarea
              label="Error Logs"
              style="width:100%;"
              filled
              hide-details
              :value="errorLogs"
            />
          </v-col>
          <v-col cols="1">
            <v-btn
              color="primary"
              @click="updateErrorLogs"
            >
              <v-icon
                dark
              >
                mdi-refresh
              </v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
import axios from 'axios'
export default {
  name: 'ErrorLog',
  data: () => ({
    errorLogs: '',
    infoLogs: ''
  }),
  mounted () {
    this.updateInfoLogs()
    this.updateErrorLogs()
  },
  methods: {
    async updateInfoLogs () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/update/logs`)
      this.infoLogs = response.data.replace(/topas_separator/g, '\n')
    },
    async updateErrorLogs () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/error/logs`)
      this.errorLogs = response.data.replace(/topas_separator/g, '\n')
    }
  }
}
</script>
