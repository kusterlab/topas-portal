<template>
  <v-container fluid>
    <v-row class="grey lighten-3">
      <!-- Sidebar for Filters and Controls -->
      <v-col
        sm="12"
        md="3"
        lg="2"
      >
        <v-card flat>
          <v-card-title tag="h1">
            Patient Reports
          </v-card-title>
          <v-card-text>
            <cohort-select
              @select-cohort="updateCohort"
            />
            <v-select
              v-model="scoreType"
              class="input_data_type mb-2 mt-4"
              prepend-icon="mdi-filter"
              dense
              outlined
              hide-details
              :items="allInputDataTypes"
              label="Data Type"
              @change="getscoresTable"
            />
            <v-checkbox
              v-model="showCorrelation"
              label="Show FPKM/protein correlation histogram"
              @change="getpatientData"
            />
            <v-checkbox
              v-show="false"
              v-model="openReport"
              label="Open Report from pipeline Folder"
              @change="getscoresTable"
            />
          </v-card-text>
        </v-card>
      </v-col>
      <!-- Main Content -->
      <v-col
        sm="12"
        md="9"
        lg="10"
      >
        <v-container
          fluid
          class="pa-0"
        >
          <v-row>
            <v-col
              sm="12"
              md="6"
              lg="6"
            >
              <v-card flat>
                <v-card-text>
                  <patient-report-table
                    :data-source="patientData"
                    :patient-report-url="patientReportUrl"
                    @onRowSelect="updateSelectedRows"
                  />
                </v-card-text>
              </v-card>
              <v-card
                flat
                class="mt-4"
              >
                <v-card-text>
                  <patientscore-table :data-source="patientscoresDataurl" />
                </v-card-text>
              </v-card>
            </v-col>
            <v-col
              sm="12"
              md="6"
              lg="6"
            >
              <v-card flat>
                <v-card-text>
                  <!-- Top Row: Patient Table and Histograms -->
                  <v-row>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <histogram
                        id="proteinfreq"
                        ref="histogram"
                        :full-chart-data="proteinCount"
                        :plot-histogram="true"
                        :plot-k-d-e="false"
                        :selected-lines="selectedFPLines"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="No identified proteins across all patients"
                        :margin="histogramMargin"
                        :min-dose="0"
                        :max-dose="20000"
                        dose-unit="standard deviations"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <histogram
                        id="peptidefpfreq"
                        ref="histogram"
                        :full-chart-data="peptidefpCount"
                        :plot-histogram="true"
                        :plot-k-d-e="false"
                        :selected-lines="selectedfppepLines"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="No identified peptides across all patients"
                        :margin="histogramMargin"
                        :min-dose="0"
                        :max-dose="150000"
                        dose-unit="standard deviations"
                      />
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <histogram
                        id="pepppfreq"
                        ref="histogram"
                        :full-chart-data="peptideCount"
                        :plot-histogram="true"
                        :plot-k-d-e="false"
                        :selected-lines="selectedpepLines"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="No identified psites across all patients"
                        :margin="histogramMargin"
                        :min-dose="0"
                        :max-dose="150000"
                        dose-unit="standard deviations"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <histogram
                        id="ppintensity"
                        ref="histogram"
                        :full-chart-data="ppintensitySum"
                        :plot-histogram="false"
                        :plot-k-d-e="true"
                        :selected-lines="selectedLineppintensity"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="Sum of Normalized PP intensities all patients"
                        :margin="histogramMargin"
                        :min-dose="0"
                        :max-dose="500000"
                        dose-unit="standard deviations"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <histogram
                        id="fpintensity"
                        ref="histogram"
                        :full-chart-data="fpintensitySum"
                        :plot-histogram="false"
                        :plot-k-d-e="true"
                        :selected-lines="selectedLinefpintensity"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="Sum of Normalized FP intensities all patients"
                        :margin="histogramMargin"
                        :min-dose="0"
                        :max-dose="300000"
                        dose-unit="standard deviations"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <histogram
                        id="correlation"
                        ref="histogram"
                        :v-if="showCorrelation"
                        :full-chart-data="correlationCount"
                        :plot-histogram="true"
                        :plot-k-d-e="false"
                        :selected-lines="selectedLinecorrelation"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="FPKM/protein correlation across all patients"
                        :margin="histogramMargin"
                        :min-dose="-0.1"
                        :max-dose="0.8"
                        dose-unit="standard deviations"
                      />
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
          <v-row>
            <v-col
              sm="12"
              md="12"
              lg="12"
            >
              <v-card flat>
                <v-card-text>
                  <v-btn-toggle
                    v-model="type"
                  >
                    <v-btn
                      value="rtk"
                    >
                      RTK Downstream
                    </v-btn>
                    <v-btn
                      value="tumor"
                    >
                      Tumor Antigens
                    </v-btn>
                    <v-btn
                      value="lolipop"
                    >
                      RTKs TOPAS vs Expression
                    </v-btn>
                  </v-btn-toggle>
                  <!-- Lollipop and Circular Plots -->
                  <v-row>
                    <v-col
                      sm="12"
                      md="7"
                      lg="7"
                    >
                      <Lolipop-plot
                        v-if="lolipopData && displayrtkBar"
                        :width="800"
                        lollipop-id="topas2Lolipop"
                        loli-title="TOPAS Z-scores"
                        :fixed-domain="fixedDomain"
                        :vline="2"
                        :loliradian="1"
                        :plot-data="lolipopData"
                        :show-legends="true"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="5"
                      lg="5"
                    >
                      <Circularbar-plot
                        v-if="lolipopData && displayrtkBar"
                        plot-id="circular2Patway"
                        :plot-data="lolipopData"
                        :patient-name="firstPatient"
                      />
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col
                      sm="12"
                      md="7"
                      lg="7"
                    >
                      <Lolipop-plot
                        v-if="lolipopDataTumor && displayTumorbar"
                        :width="800"
                        lollipop-id="topas2LolipopTumorantigen"
                        loli-title="Expression Z-scores"
                        :fixed-domain="fixedDomain"
                        :vline="2"
                        :loliradian="1"
                        :plot-data="lolipopDataTumor"
                        :show-legends="true"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="5"
                      lg="5"
                    >
                      <Circularbar-plot
                        v-if="lolipopDataTumor && displayTumorbar"
                        plot-id="circular2Tumor"
                        :plot-data="lolipopDataTumor"
                        :patient-name="firstPatient"
                      />
                    </v-col>
                  </v-row>
                  <!-- Full-Width Lollipop Plots -->
                  <v-row>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <Lolipop-plot
                        v-if="expressionDataRTK && displaylolipop"
                        :width="1600"
                        :height="400"
                        :fixed-domain="fixedDomain"
                        loli-mode="true"
                        loliradian="4"
                        loli-title="Topas Z-scores | EXPRESSION Z-scores"
                        lollipop-id="topas2ExpressionplotRTk"
                        :plot-data="expressionDataRTK"
                        overlapping-y="true"
                        show-legends="true"
                      />
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col
                      sm="12"
                      md="6"
                      lg="6"
                    >
                      <Lolipop-plot
                        v-if="expressionDataDownstream && displaylolipop"
                        :width="1600"
                        :height="400"
                        :fixed-domain="fixedDomain"
                        loli-mode="true"
                        loliradian="2"
                        loli-title="TOPAS Z-scores | EXPRESSION Z-scores"
                        lollipop-id="topas2ExpressionplotDownSignaling"
                        :plot-data="expressionDataDownstream"
                        overlapping-y="true"
                        show-legends="true"
                      />
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-container>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import axios from 'axios'
import { mapMutations } from 'vuex'

import CohortSelect from './partials/CohortSelect.vue'
import patientscoreTable from '@/components/tables/PatientscoreTable.vue'
import PatientReportTable from '@/components/tables/PatientReportTable.vue'
import LolipopPlot from '@/components/plots/LolipopPlot'
import CircularbarPlot from '@/components/plots/CircularbarPlot'
import histogram from '@/components/plots/GenericHistogram.vue'
import { DataType } from '@/constants'
import { api } from '@/routes.ts'

export default {
  name: 'ReportComponent',
  components: {
    CohortSelect,
    PatientReportTable,
    LolipopPlot,
    histogram,
    CircularbarPlot,
    patientscoreTable
  },
  props: {
    minWidth: {
      type: Number,
      default: 400
    },
    minHeight: {
      type: Number,
      default: 300
    }
  },
  data: () => ({
    cohortIndex: -1,
    topasName: '',
    isCollapsed: true,
    fixedDomain: false,
    sumIntesitiespp: [],
    sumIntesitiesfp: [],
    patientData: [],
    selectedLineppintensity: [],
    selectedLinefpintensity: [],
    scoreType: DataType.TOPAS_SCORE,
    Showcircular: true,
    lolipopData: false,
    showCorrelation: false,
    lolipopDataTumor: false,
    openReport: false,
    histogramMargin: { top: 20, right: 10, bottom: 50, left: 70 },
    proteinSatitistics: [],
    peptideSatitistics: [],
    correlationStatistics: [],
    firstPatient: '',
    patientscoresDataurl: '',
    expressionDataRTK: false,
    expressionDataDownstream: false,
    type: 'tumor',
    peptidefpSatitistics: [],
    selectedFPLines: [],
    selectedLinecorrelation: [],
    selectedpepLines: [],
    selectedfppepLines: [],
    selectedData: [],
    allInputDataTypes: [
      {
        text: 'TOPAS score',
        value: DataType.TOPAS_SCORE
      },
      {
        text: 'Full proteome',
        value: DataType.FULL_PROTEOME
      },
      {
        text: 'Phosphopeptides',
        value: DataType.PHOSPHO_PROTEOME
      },
      {
        text: 'Kinases',
        value: DataType.KINASE_SCORE
      },
      {
        text: 'P-protein scores',
        value: DataType.PHOSPHO_SCORE
      },
      {
        text: 'TOPAS subscore',
        value: DataType.TOPAS_SUBSCORE
      },
      {
        text: 'Biomarker',
        value: DataType.BIOMARKER
      }
    ]
  }),
  computed: {
    proteinCount () {
      return this.proteinSatitistics.map(d => d.identified)
    },
    peptideCount () {
      return this.peptideSatitistics.map(d => d.identified)
    },
    peptidefpCount () {
      return this.peptidefpSatitistics.map(d => d.identified)
    },
    correlationCount () {
      return this.correlationStatistics.map(d => d.correlation)
    },
    ppintensitySum () {
      return this.sumIntesitiespp.map(d => d.sumIntensities)
    },
    fpintensitySum () {
      return this.sumIntesitiesfp.map(d => d.sumIntensities)
    },
    displayrtkBar () {
      return this.type === 'rtk'
    },
    displayTumorbar () {
      return this.type === 'tumor'
    },
    displaylolipop () {
      return this.type === 'lolipop'
    },
    patientReportUrl () {
      return api.PATIENT_REPORT_TABLE_XLSX({ cohort_index: this.cohortIndex, patients: ':patients' })
    }
  },
  watch: {
    cohortIndex () {
      this.getpatientData()
    }
  },
  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    toggleDiv (type) {
      this.type = type
    },
    async getpatientData () {
      this.patientData = null
      let response = []
      try {
        response = await axios.get(api.PATIENTS_METADATA({ cohort_index: this.cohortIndex }))
        this.patientData = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: 'Error: Probably no meta data exists for this cohort'
        })
      }
      try {
        response = await axios.get(api.PATIENT_CENTRIC_PROTEIN_COUNTS({ cohort_index: this.cohortIndex, fp_pp: 'fp' }))
        this.proteinSatitistics = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: 'Error: could not load protein counts data'
        })
      }
      try {
        response = await axios.get(api.PATIENT_CENTRIC_PP_INTENSITY({ cohort_index: this.cohortIndex, dtype: 'pp' }))
        this.sumIntesitiespp = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: 'Error: could not load phospho intensities data'
        })
      }
      try {
        response = await axios.get(api.PATIENT_CENTRIC_PP_INTENSITY({ cohort_index: this.cohortIndex, dtype: 'fp' }))
        this.sumIntesitiesfp = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: 'Error: could not load full proteome intensities data'
        })
      }
      try {
        response = await axios.get(api.PATIENT_CENTRIC_PROTEIN_COUNTS({ cohort_index: this.cohortIndex, fp_pp: 'pp' }))
        this.peptideSatitistics = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: 'Error: could not load phosphoproteome peptide counts data'
        })
      }
      try {
        response = await axios.get(api.PATIENT_CENTRIC_PROTEIN_COUNTS({ cohort_index: this.cohortIndex, fp_pp: 'fppeptide' }))
        this.peptidefpSatitistics = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: 'Error: could not load full proteome peptide counts data'
        })
      }
      if (this.showCorrelation) {
        try {
          response = await axios.get(api.CORRELATION_FPKM_PROTEIN({ cohort_index: this.cohortIndex }))
          this.correlationStatistics = response.data
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: 'Error: could not load FPKM-protein correlation statistics data'
          })
        }
      }
    },
    getscoresTable () {
      this.patientscoresDataurl = api.PATIENT_REPORT_TABLE({
        cohort_index: this.cohortIndex,
        patient: this.firstPatient,
        level: this.scoreType,
        downloadmethod: this.openReport ? 'fromreport' : 'onfly'
      })
      // this.patientscoresData = response.data
    },
    async updateSelectedRows (selectedIds, selectedData) {
      this.selectedData = selectedData
      this.lolipopData = false
      this.expressionDataRTK = false
      this.expressionDataDownstream = false
      this.lolipopDataTumor = false
      if (selectedData.length > 0) {
        const firstPatient = selectedData[0]['Sample name']
        this.firstPatient = firstPatient
        let response = await axios.get(api.TOPAS_LOLLIPOP({ cohort_index: this.cohortIndex, patient: firstPatient }))
        this.lolipopData = response.data
        response = await axios.get(api.TOPAS_LOLLIPOP_TUMOR({ cohort_index: this.cohortIndex, patient: firstPatient }))
        this.lolipopDataTumor = response.data
        response = await axios.get(api.TOPAS_EXPRESSION_DOWNSTREAM({ cohort_index: this.cohortIndex, patient: firstPatient }))
        this.expressionDataRTK = response.data
        response = await axios.get(api.TOPAS_EXPRESSION_RTK({ cohort_index: this.cohortIndex, patient: firstPatient }))
        this.expressionDataDownstream = response.data
        this.getscoresTable()
        this.selectedFPLines = [] // for full proteome
        this.selectedfppepLines = [] // for FP peptideLevel
        this.selectedpepLines = [] // for PP at peptide level
        this.selectedLineppintensity = [] // for PP peptide level
        this.selectedLinefpintensity = [] // for FP peptide level
        this.selectedLinecorrelation = [] // FPKM protein transcript level
        this.proteinSatitistics.forEach(element => {
          if (element.patients === firstPatient) {
            this.selectedFPLines.push({ color: 'red', value: element.identified, curveid: -1, dash: ('5, 5') })
          }
        })

        this.peptideSatitistics.forEach(element => {
          if (element.patients === firstPatient) {
            this.selectedpepLines.push({ color: 'blue', value: element.identified, curveid: -1, dash: ('5, 5') })
          }
        })

        this.peptidefpSatitistics.forEach(element => {
          if (element.patients === firstPatient) {
            this.selectedfppepLines.push({ color: 'red', value: element.identified, curveid: -1, dash: ('5, 5') })
          }
        })

        this.sumIntesitiespp.forEach(element => {
          if (element.patients === firstPatient) {
            this.selectedLineppintensity.push({ color: 'blue', value: element.sumIntensities, curveid: -1, dash: ('5, 5') })
          }
        })

        this.sumIntesitiesfp.forEach(element => {
          if (element.patients === firstPatient) {
            this.selectedLinefpintensity.push({ color: 'orange', value: element.sumIntensities, curveid: -1, dash: ('5, 5') })
          }
        })

        if (this.showCorrelation) {
          this.correlationStatistics.forEach(element => {
            if (element.patients === firstPatient) {
              this.selectedLinecorrelation.push({ color: 'black', value: element.correlation, curveid: -1, dash: ('5, 5') })
            }
          })
        }
      }
    }
  }
}
</script>

<style>
.collapsible-container {
  margin: 1em;
  border: 1px solid #ccc;
  border-radius: 5px;
  padding: 1em;
}

button {
  margin-bottom: 1em;
}

.collapsible-content {
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.button-show-score {
  background-color: #e0e0e0;
  border: none;
  padding: 10px 20px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
  box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.2), -3px -3px 6px rgba(255, 255, 255, 0.7);
  transition: box-shadow 0.2s ease-in-out;
}
</style>
