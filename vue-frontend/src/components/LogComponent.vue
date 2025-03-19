<template>
  <v-container fluid>
    <v-row class="grey lighten-3">
      <v-col
        sm="12"
        md="3"
        lg="2"
      >
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
              >
                <template #append>
                  <v-icon
                    v-if="passwordIsValid"
                    color="green darken-2"
                  >
                    mdi-check-circle
                  </v-icon>
                  <v-icon
                    v-if="!passwordIsValid"
                    color="red darken-2"
                  >
                    mdi-minus-circle
                  </v-icon>
                </template>
              </v-text-field>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col
        v-if="passwordIsValid"
        sm="12"
        md="9"
        lg="10"
      >
        <v-card flat>
          <v-card-text class="pa-0">
            <v-tabs
              v-model="tabs"
              show-arrows
            >
              <v-tab
                v-for="item of allTabs"
                :key="item"
              >
                {{ item }}
              </v-tab>
            </v-tabs>
            <v-tabs-items v-model="tabs">
              <v-tab-item class="tab">
                <config-update />
              </v-tab-item>
              <v-tab-item class="tab">
                <error-log />
              </v-tab-item>
              <v-tab-item class="tab">
                <integration-test />
              </v-tab-item>
              <v-tab-item class="tab">
                <v-card>
                  <v-card-text>
                    <config-table
                      :data-source="PathvalidationUrl"
                    />
                  </v-card-text>
                </v-card>
              </v-tab-item>
            </v-tabs-items>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
import ConfigUpdate from './partials/ConfigUpdate.vue'
import IntegrationTest from './partials/IntegrationTest.vue'
import ErrorLog from './partials/ErrorLog.vue'
import configTable from '@/components/tables/configTable.vue'
import axios from 'axios'
export default {
  name: 'LogComponent',
  components: {
    configTable,
    ConfigUpdate,
    IntegrationTest,
    ErrorLog
  },
  data: () => ({
    allTabs: ['Cohort data setup', 'Log & error messages', 'Service status', 'System Health'],
    tabs: null,
    logValue: [],
    errorValue: [],
    integrationValue: [],
    reportDir: '',
    password: '',
    passwordIsValid: false,
    file: null,
    PathvalidationUrl: `${process.env.VUE_APP_API_HOST}/config/checkall`,
    checkPath: ''
  }),
  mounted () {
  },
  methods: {
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
