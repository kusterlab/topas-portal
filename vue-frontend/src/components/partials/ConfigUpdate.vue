<template>
  <v-card flat>
    <v-card-text>
      <v-text-field
        :value="configPath"
        style="width: 100%; white-space: nowrap; overflow-x: auto;"
        label="Portal config file"
        readonly
        disabled
        hide-details
      />
      <v-expansion-panels dense>
        <v-expansion-panel>
          <v-expansion-panel-header class="mb-0 grey lighten-2">
            Show config file
          </v-expansion-panel-header>
          <v-expansion-panel-content class="grey lighten-3">
            <v-btn
              class="ma-2 float-right"
              color="primary"
              @click="showConfig"
            >
              <v-icon dark>
                mdi-refresh
              </v-icon>
            </v-btn>
            <pre>{{ configValue }}</pre>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>
      <v-btn
        v-if="updateMode"
        class="mt-4 primary"
        :loading="!showUpdateCohorts"
        @click="reloadCohort(allCohorts = true)"
      >
        Reload all cohort data
      </v-btn>
      <v-row class="mt-4">
        <v-col cols="3">
          <v-select
            v-if="updateMode"
            v-model="cohortName"
            dense
            outlined
            hide-details
            :items="all_cohorts"
            label="Cohort"
            @change="getcohortPath"
          />
        </v-col>
        <v-col cols="1">
          <v-dialog
            v-model="dialog"
            max-width="600px"
          >
            <template #activator="{ on, attrs }">
              <v-btn
                v-bind="attrs"
                fab
                x-small
                dark
                hide-details
                color="green darken-2"
                v-on="on"
              >
                <v-icon>mdi-plus</v-icon>
              </v-btn>
            </template>
            <v-card>
              <v-card-title>
                Add new cohort
              </v-card-title>
              <v-card-text>
                <v-text-field
                  v-model="newCohortName"
                  style="width:1000px;"
                  label="Cohort name"
                />
                <v-btn
                  color="blue darken-1"
                  text
                  @click="addCohort"
                >
                  Add to config file
                </v-btn>
                <v-btn
                  class="ml-4"
                  color="blue darken-1"
                  text
                  @click="dialog = false"
                >
                  Cancel
                </v-btn>
              </v-card-text>
            </v-card>
          </v-dialog>
        </v-col>
      </v-row>
      <v-row class="mt-0">
        <v-col
          sm="8"
          lg="8"
          md="8"
        >
          <v-text-field
            v-model="patientAnnot"
            style="width:1000px;"
            hide-details
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
            hide-details
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
            hide-details
          />
        </v-col>
        <v-col
          sm="4"
          lg="4"
          md="4"
        >
          <v-btn
            :disabled="!showUpdateCohorts"
            hide-details
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
            label="Pipeline results directory"
            hide-details
          />
        </v-col>
        <v-col
          sm="4"
          lg="4"
          md="4"
        >
          <v-btn
            :disabled="!showUpdateCohorts"
            hide-details
            @click="reportDirUpdater"
          >
            Update Pipeline results Path
          </v-btn>
        </v-col>
      </v-row>
      <v-btn
        class="mt-4 primary"
        :loading="!showUpdateCohorts"
        :disabled="cohortName.length === 0"
        @click="reloadCohort(allCohorts = false)"
      >
        Reload selected cohort data
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script>
import axios from 'axios'
import { mapActions, mapGetters, mapState, mapMutations } from 'vuex'
import { api } from '@/routes.ts'

export default {
  name: 'ConfigUpdate',
  props: {
    updateMode: {
      type: Boolean,
      default: true
    }
  },
  data: () => ({
    configPath: '',
    cohortName: '',
    patientAnnot: '',
    sampleAnnot: '',
    showUpdateCohorts: true,
    reportDir: '',
    newCohortName: '',
    addedcohortName: '',
    configValue: '',
    dialog: false
  }),
  computed: {
    ...mapState({
      all_cohorts: state => state.all_cohorts
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
    this.getConfigpath()
    this.showConfig()
  },
  methods: {
    ...mapActions({
      fetchAllCohorts: 'fetchAllCohorts'
    }),
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    async reloadCohort (allCohorts = false) {
      this.addNotification({
        color: 'info',
        message: 'Loading cohort data, this can take some time'
      })
      this.showUpdateCohorts = false
      let response = ''
      try {
        if (allCohorts) {
          response = await axios.get(`${process.env.VUE_APP_API_HOST}/drugs/load`)
          response = await axios.get(api.RELOAD())
          this.showUpdateCohorts = true
          this.addNotification({
            color: 'info',
            message: `${response.data}`
          })
        } else {
          const cohort = this.updateMode ? this.cohortName : this.cohortName
          response = await axios.get(api.RELOAD_COHORT({ cohort }))
          this.addNotification({
            color: 'info',
            message: `${response.data}`
          })
          this.showUpdateCohorts = true
          this.checkValidity(cohort)
        }
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `Error while loading cohort data: ${error.response.data}`
        })
      }
      this.fetchAllCohorts()
    },
    async getcohortPath () {
      const cohortName = this.updateMode ? this.cohortName : this.cohortName
      const response = await axios.get(api.CONFIG())
      this.patientAnnot = response.data.patient_annotation_path[cohortName]
      this.reportDir = response.data.report_directory[cohortName]
      this.sampleAnnot = response.data.sample_annotation_path[cohortName]
    },
    async patientAnnotationUpdater () {
      await this.generalUpdatePath('patient_annotation_path', this.patientAnnot)
      await this.showConfig()
    },
    sampleAnnotationUpdater () {
      this.generalUpdatePath('sample_annotation_path', this.sampleAnnot)
    },
    reportDirUpdater () {
      this.generalUpdatePath('report_directory', this.reportDir)
    },
    async generalUpdatePath (key, annotation) {
      const cohortName = this.updateMode ? this.cohortName : this.cohortName
      const pathValue = annotation.replace(/[/]/g, 'topas_slash')
      const pathCheck = await axios.get(api.PATH_CHECK({ path: pathValue }))
      if (pathCheck.data === 'True') {
        await axios.get(api.CONFIG_UPDATE({ key, cohort: cohortName, value: pathValue }))
        this.addNotification({
          color: 'success',
          message: `Updated to ${annotation}`
        })
      } else {
        this.addNotification({
          color: 'error',
          message: 'Error: invalid path, update failed'
        })
      }
    },
    async addCohort () {
      await axios.get(api.ADD_COHORT({ cohort: this.newCohortName }))
      this.addNotification({
        color: 'success',
        message: `New cohort ${this.newCohortName} added. Update the paths and load the cohort below.`
      })
      this.addedcohortName = this.newCohortName
      this.dialog = false
      await this.showConfig()
    },
    async showConfig () {
      const response = await axios.get(api.CONFIG())
      this.configValue = JSON.stringify(response.data, null, 2)
    },
    async getConfigpath () {
      const response = await axios.get(api.CONFIG_PATH())
      this.configPath = response.data.path
    }
  }
}
</script>
