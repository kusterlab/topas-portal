<template>
  <v-container fluid>
    <v-row class="bg-grey-lighten-3">
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Admin tools </v-card-title>
          <v-card-text>
            <div style="display: flow-root">
              <v-text-field
                v-model="password"
                :disabled="isLoggedIn"
                class="float-left"
                label="Password"
                type="password"
                @update:model-value="checkPassValidity"
              >
                <template #append>
                  <v-icon v-if="isLoggedIn" color="green-darken-2"> mdi-check-circle </v-icon>
                  <v-icon v-if="!isLoggedIn" color="red-darken-2"> mdi-minus-circle </v-icon>
                </template>
              </v-text-field>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col v-if="isLoggedIn" sm="12" md="9" lg="10">
        <v-card variant="flat">
          <v-card-text class="pa-0">
            <v-tabs v-model="tabs" show-arrows>
              <v-tab v-for="item of allTabs" :key="item">
                {{ item }}
              </v-tab>
            </v-tabs>
            <v-tabs-window v-model="tabs">
              <v-tabs-window-item class="tab">
                <config-update />
              </v-tabs-window-item>
              <v-tabs-window-item class="tab">
                <error-log />
              </v-tabs-window-item>
              <v-tabs-window-item class="tab">
                <integration-test />
              </v-tabs-window-item>
              <v-tabs-window-item class="tab">
                <v-card>
                  <v-card-text>
                    <config-table :data-source="PathvalidationUrl" />
                  </v-card-text>
                </v-card>
              </v-tabs-window-item>
            </v-tabs-window>
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
  import configTable from '@/components/tables/ConfigTable.vue'
  import axios from 'axios'
  import { api } from '@/routes.ts'

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
      isLoggedIn: false,
      file: null,
      PathvalidationUrl: api.CONFIG_CHECKALL(),
      checkPath: ''
    }),
    mounted() {},
    created() {
      this.checkAuth()
    },

    methods: {
      async checkAuth() {
        try {
          const token = localStorage.getItem('access_token')
          if (!token) {
            this.isLoggedIn = false
            return
          }

          // Example API request to validate token
          const res = await axios.get(api.AUTH_ME(), {
            headers: { Authorization: `Bearer ${token}` }
          })

          this.isLoggedIn = res.data.valid
        } catch (err) {
          this.isLoggedIn = false
        }
      },
      async checkPassValidity() {
        const pass = this.password
        const response = await axios.post(api.AUTH_LOGIN(), { password: pass })
        if (response.data.pass === 'valid') {
          localStorage.setItem('access_token', response.data.access_token)
          this.isLoggedIn = true
        }
      }
    }
  }
</script>
