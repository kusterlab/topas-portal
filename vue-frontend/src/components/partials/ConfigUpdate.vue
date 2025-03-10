<template>
  <div>
    <v-card
      class="mt-2 mb-2"
      flat
    >
      <v-textarea
        label="Loading Logs"
        style="width:100%;"
        :value="logValue"
      />
      <v-btn
        class="mt-4 ml-2"
        color="primary"
        @click="updateLog"
      >
        <v-icon
          dark
        >
          mdi-refresh
        </v-icon>
      </v-btn>
      <v-card-title
        tag="h1"
      >
        Cohort configuration
      </v-card-title>
      <v-card-text>
        <v-select
          v-if="updateMode"
          v-model="diseaseName"
          class="cohort"
          dense
          outlined
          :items="all_diseases"
          label="Cohort"
          @change="getcohortPath"
        />
        <v-row>
          <v-col
            sm="8"
            lg="8"
            md="8"
          >
            <v-text-field
              v-model="patientAnnot"
              style="width:1000px;"
              label="Patient Annotation"
            />
          </v-col>
          <v-col
            sm="4"
            lg="4"
            md="4"
          >
            <v-btn
              :disabled="!showUpdateCohorts"
              @click="patientAnnotationUpdater"
            >
              Update Patient Annotation path
            </v-btn>
          </v-col>
        </v-row>
        <v-row>
          <v-col
            sm="8"
            lg="8"
            md="8"
          >
            <v-text-field
              v-model="sampleAnnot"
              style="width:1000px;"
              label="Sample Annotation"
            />
          </v-col>
          <v-col
            sm="4"
            lg="4"
            md="4"
          >
            <v-btn
              :disabled="!showUpdateCohorts"
              @click="sampleAnnotationUpdater"
            >
              Update Sample Annotation path
            </v-btn>
          </v-col>
        </v-row>
        <v-row>
          <v-col
            sm="8"
            lg="8"
            md="8"
          >
            <v-text-field
              v-model="reportDir"
              style="width:1000px;"
              label="Report Directory"
            />
          </v-col>
          <v-col
            sm="4"
            lg="4"
            md="4"
          >
            <v-btn
              :disabled="!showUpdateCohorts"
              @click="reportDirUpdater"
            >
              Update Cohort Directory Path
            </v-btn>
          </v-col>
        </v-row>
        <v-btn
          class="mt-4"
          :loading="!showUpdateCohorts"
          @click="reloadCohort(allCohorts=false)"
        >
          Reload selected cohort
        </v-btn>
        <v-btn
          v-if="updateMode"
          class="mt-4 ml-2"
          :loading="!showUpdateCohorts"
          @click="reloadCohort(allCohorts=true)"
        >
          Reload all cohorts
        </v-btn>
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
    cohortName: {
      type: String,
      default: ''
    },
    updateMode: {
      type: Boolean,
      default: true
    }
  },
  data: () => ({
    diseaseName: '',
    patientAnnot: '',
    sampleAnnot: '',
    logValue: '',
    showUpdateCohorts: true,
    reportDir: ''
  }),
  computed: {
    ...mapState({
      all_diseases: state => state.all_diseases
    }),
    ...mapGetters({
      hasData: 'hasData'
    })
  },
  watch: {
    cohortName: function () {
      this.getcohortPath()
    }
  },
  mounted () {
    this.updateLog()
  },
  methods: {
    ...mapActions({
      fetchAllDiseases: 'fetchAllDiseases'
    }),
    async reloadCohort (allCohorts = false) {
      alert('Loading cohort data, this can take some time')
      this.showUpdateCohorts = false
      let response = ''
      try {
        if (allCohorts) {
          response = await axios.get(`${process.env.VUE_APP_API_HOST}/drugs/load`)
          response = await axios.get(`${process.env.VUE_APP_API_HOST}/reload`)
          this.showUpdateCohorts = true
          alert(response.data)
        } else {
          const cohort = this.updateMode ? this.diseaseName : this.cohortName
          response = await axios.get(`${process.env.VUE_APP_API_HOST}/reload/${cohort}`)
          alert(response.data)
          this.showUpdateCohorts = true
          this.checkValidity(cohort)
        }
      } catch (error) {
        alert(`Error while loading cohort data: ${error.response.data}`)
      }
      this.updateLog()
      this.fetchAllDiseases()
    },
    async updateLog () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/update/logs`)
      this.logValue = response.data.replace(/topas_separator/g, '\n')
    },
    async getcohortPath () {
      const diseaseName = this.updateMode ? this.diseaseName : this.cohortName
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/config`)
      this.patientAnnot = response.data.patient_annotation_path[diseaseName]
      this.reportDir = response.data.report_directory[diseaseName]
      this.sampleAnnot = response.data.sample_annotation_path[diseaseName]
    },
    patientAnnotationUpdater () {
      this.generalUpdatePath('patient_annotation_path', this.patientAnnot)
    },
    sampleAnnotationUpdater () {
      this.generalUpdatePath('sample_annotation_path', this.sampleAnnot)
    },
    reportDirUpdater () {
      this.generalUpdatePath('report_directory', this.reportDir)
    },
    async generalUpdatePath (key, annotation) {
      const diseaseName = this.updateMode ? this.diseaseName : this.cohortName
      const pathValue = annotation.replace(/[/]/g, 'topas_slash')
      const pathCheck = await axios.get(`${process.env.VUE_APP_API_HOST}/path/check/${pathValue}`)
      if (pathCheck.data === 'True') {
        await axios.get(`${process.env.VUE_APP_API_HOST}/update/${key}/${diseaseName}/${pathValue}`)
        alert(`Updated to ${annotation}`)
      } else {
        alert('Wrong Path, Not Updated')
      }
    }
  }
}
</script>
