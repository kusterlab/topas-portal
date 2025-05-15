<template>
  <v-container fluid>
    <v-card
      flat
    >
      <v-row>
        <v-col cols="11">
          <v-textarea
            label="Integration Logs"
            style="width:100%;"
            filled
            :value="logValue"
          />
        </v-col><v-col cols="1">
          <v-btn
            color="primary"
            @click="updateLog"
          >
            <v-icon dark>
              mdi-refresh
            </v-icon>
          </v-btn>
        </v-col>
      </v-row>
      <v-card-title
        tag="h1"
      >
        Cohort configuration
      </v-card-title>
      <v-card-text>
        <v-select
          v-model="cohortName"
          class="cohort"
          dense
          outlined
          :items="all_cohorts"
          label="Cohort"
        />
        <v-btn
          class="mt-4"
          :disabled="!showUpdateCohorts || cohortName === ''"
          @click="checkCohort"
        >
          Validate current cohort
        </v-btn>
        <v-btn
          class="mt-4 ml-2"
          :disabled="!showUpdateCohorts"
          @click="checkvalidityallCohorts"
        >
          Validate all cohorts
        </v-btn>
        <v-col>
          <v-row>
            <p class="mt-4">
              Protein and topas for validity checks
            </p>
          </v-row>
          <v-row>
            <v-text-field
              v-model="proteinCheck"
              style="width:100px"
              label="Protein"
            />
          </v-row>
          <v-row>
            <v-text-field
              v-model="topasCheck"
              style="width:100px"
              label="Topas"
            />
          </v-row>
        </v-col>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
import axios from 'axios'
import { mapGetters, mapState, mapMutations } from 'vuex'
export default {
  name: 'ConfigureUpdate',
  props: {
    cohortIndex: {
      type: Number,
      default: -1
    }
  },
  data: () => ({
    cohortName: '',
    showUpdateCohorts: true,
    logValue: '',
    proteinCheck: 'EGFR',
    topasCheck: 'ABL1'
  }),
  computed: {
    ...mapState({
      all_cohorts: state => state.all_cohorts
    }),
    ...mapGetters({
      hasData: 'hasData'
    })
  },
  mounted () {
    this.updateLog()
  },
  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    async updateLog () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/integration/logs`)
      this.logValue = response.data.replace(/topas_separator/g, '\n')
    },
    async checkCohort () {
      this.showUpdateCohorts = false
      let response = ''
      const cohort = this.cohortName
      response = await axios.get(`${process.env.VUE_APP_API_HOST}/check/integrability/${cohort}`)
      this.showUpdateCohorts = true
      this.addNotification({
        color: 'info',
        message: `${response.data}`
      })
      this.updateLog()
    },
    async checkvalidityallCohorts () {
      await axios.get(`${process.env.VUE_APP_API_HOST}/integration/clearlogs`)
      for (let i = 0; i < this.all_cohorts.length; i++) {
        this.checkValidity(this.all_cohorts[i])
      }
      this.updateLog()
    },
    async checkValidity (cohort = this.cohortName) {
      if (cohort) {
        const proteinName = this.proteinCheck
        const topasName = this.topasCheck
        // a sample validity test for the z_scores for one protein and topas
        await axios.get(`${process.env.VUE_APP_API_HOST}/check/validity_z_score/${cohort}/${proteinName}`)
        await axios.get(`${process.env.VUE_APP_API_HOST}/check/validity_topas_score/${cohort}/${topasName}`)
        this.updateLog()
      } else {
        this.addNotification({
          color: 'warning',
          message: 'Select a cohort to perform the validity tests on'
        })
      }
    }
  }
}
</script>
