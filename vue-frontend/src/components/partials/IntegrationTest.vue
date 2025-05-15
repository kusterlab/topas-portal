<template>
  <div>
    <v-card
      class="mt-2 mb-2"
      flat
    >
      <v-textarea
        label="Integration Logs"
        style="width:100%;"
        :value="logValue"
      />
      <v-card-title
        tag="h1"
      >
        Cohort configuration
      </v-card-title>
      <v-card-text>
        <v-select
          v-model="diseaseName"
          class="cohort"
          dense
          outlined
          :items="all_diseases"
          label="Cohort"
        />
        <v-btn
          class="mt-4"
          :disabled="!showUpdateCohorts || diseaseName === ''"
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
        <v-btn
          class="mt-4 ml-2"
          @click="updateLog"
        >
          update Log
        </v-btn>
        <v-col>
          <v-row>
            <p class="mt-4">
              Protein and basket for validity checks
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
              v-model="basketCheck"
              style="width:100px"
              label="Basket"
            />
          </v-row>
        </v-col>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import axios from 'axios'
import { mapActions, mapGetters, mapState } from 'vuex'
export default {
  name: 'ConfigureUpdate',
  props: {
    cohortIndex: {
      type: Number,
      default: -1
    }
  },
  data: () => ({
    diseaseName: '',
    showUpdateCohorts: true,
    logValue: '',
    proteinCheck: 'EGFR',
    basketCheck: 'ABL1'
  }),
  computed: {
    ...mapState({
      all_diseases: state => state.all_diseases
    }),
    ...mapGetters({
      hasData: 'hasData'
    })
  },
  mounted () {
    this.updateLog()
  },
  methods: {
    ...mapActions({
      fetchAllDiseases: 'fetchAllDiseases'
    }),
    async updateLog () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/integration/logs`)
      this.logValue = response.data.replace(/topas_separator/g, '\n')
    },
    async checkCohort () {
      this.showUpdateCohorts = false
      let response = ''
      const cohort = this.diseaseName
      response = await axios.get(`${process.env.VUE_APP_API_HOST}/check/integrability/${cohort}`)
      this.showUpdateCohorts = true
      alert(response.data)
      this.updateLog()
    },
    async checkvalidityallCohorts () {
      await axios.get(`${process.env.VUE_APP_API_HOST}/integration/clearlogs`)
      for (let i = 0; i < this.all_diseases.length; i++) {
        this.checkValidity(this.all_diseases[i])
      }
      this.updateLog()
    },
    async checkValidity (cohort = this.diseaseName) {
      if (cohort) {
        const proteinName = this.proteinCheck
        const basketName = this.basketCheck
        // a sample validity test for the z_scores for one protein and basket
        await axios.get(`${process.env.VUE_APP_API_HOST}/check/validity_z_score/${cohort}/${proteinName}`)
        await axios.get(`${process.env.VUE_APP_API_HOST}/check/validity_basket_score/${cohort}/${basketName}`)
        this.updateLog()
      } else {
        alert('You should select a cohort name')
      }
    }
  }
}
</script>
