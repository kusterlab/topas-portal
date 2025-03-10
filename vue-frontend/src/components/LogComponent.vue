<template>
  <v-row class="pa-4 grey lighten-3">
    <v-text-field
      v-if="passwordIsValid"
      :value="configPath"
      label="Config file of the portal"
      readonly
    />
    <v-col cols="12">
      <v-card flat>
        <v-card-title
          tag="h1"
        >
          Admin tools
        </v-card-title>
        <v-card-text>
          <div style="display: flow-root">
            <v-text-field
              v-model="password"
              :disabled="passwordIsValid"
              class="float-left"
              label="Password"
              type="password"
              @change="checkPassValidity"
            />
            <v-icon
              v-if="passwordIsValid"
              large
              color="green darken-2"
              class="float-left mt-2"
            >
              mdi-check-circle
            </v-icon>
            <v-icon
              v-if="!passwordIsValid"
              large
              color="red darken-2"
              class="float-left mt-2"
            >
              mdi-minus-circle
            </v-icon>
          </div>
        </v-card-text>
        <v-card-text>
          <v-btn-toggle
            v-if="passwordIsValid"
            v-model="logtype"
            color="primary"
            mandatory
            class="mt-4 mb-6"
          >
            <v-btn value="loadingLog">
              Data loading - update
            </v-btn>
            <v-btn value="errorsLog">
              Error logs
            </v-btn>
            <v-btn value="integration">
              Validation test
            </v-btn>
            <v-btn value="fileavailability">
              Needed files status
            </v-btn>
            <v-btn value="addCohort">
              Add new cohort
            </v-btn>
            <v-btn value="configEdit">
              Config File
            </v-btn>
          </v-btn-toggle>
          <v-card-title
            tag="h1"
          />
          <config-table
            v-if="logtype==='fileavailability'"
            :data-source="PathvalidationUrl"
          />
        </v-card-text>
      </v-card>
      <config-update
        v-if="passwordIsValid && logtype=='loadingLog'"
      />
      <integration-test
        v-if="passwordIsValid && logtype==='integration'"
      />
      <error-log
        v-if="passwordIsValid && logtype==='errorsLog'"
      />
      <add-cohort
        v-if="passwordIsValid && logtype==='addCohort'"
      />
      <config-edit
        v-if="passwordIsValid && logtype==='configEdit'"
      />
    </v-col>
  </v-row>
</template>
<script>
import AddCohort from './partials/AddCohort.vue'
import ConfigUpdate from './partials/ConfigUpdate.vue'
import IntegrationTest from './partials/IntegrationTest.vue'
import ErrorLog from './partials/ErrorLog.vue'
import configTable from '@/components/tables/configTable.vue'
import ConfigEdit from './partials/ConfigEdit.vue'
import axios from 'axios'
export default {
  name: 'LogComponent',
  components: {
    configTable,
    ConfigEdit,
    ConfigUpdate,
    IntegrationTest,
    AddCohort,
    ErrorLog
  },
  data: () => ({
    logValue: [],
    errorValue: [],
    configPath: '',
    integrationValue: [],
    diseaseName: '',
    logtype: 'loading',
    reportDir: '',
    password: '',
    passwordIsValid: false,
    file: null,
    PathvalidationUrl: `${process.env.VUE_APP_API_HOST}/config/checkall`,
    checkPath: ''
  }),
  mounted () {
    this.getConfigpath()
  },
  methods: {
    async getConfigpath () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/config/config_path`)
      this.configPath = response.data.path
    },
    async checkPassValidity () {
      const pass = this.password
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/password/${pass}`)
      if (response.data.pass === 'valid') {
        this.passwordIsValid = true
      }
    }
  }

}
</script>
