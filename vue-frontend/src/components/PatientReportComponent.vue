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
                        xlabel="No identified p-peptides across all patients"
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
                        xlabel="log10(Summed PP intensities)"
                        :margin="histogramMargin"
                        :min-dose="0"
                        :max-dose="12"
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
                        xlabel="log10(Summed FP intensities)"
                        :margin="histogramMargin"
                        :min-dose="0"
                        :max-dose="12"
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
                      value="lollipop"
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
                      <Lollipop-plot
                        v-if="lollipopData && displayrtkBar"
                        :width="800"
                        lollipop-id="topas2Lollipop"
                        lolli-title="TOPAS Z-scores"
                        :fixed-domain="fixedDomain"
                        :vline="2"
                        :lolliradian="1"
                        :plot-data="lollipopData"
                        :show-legends="true"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="5"
                      lg="5"
                    >
                      <Circularbar-plot
                        v-if="lollipopData && displayrtkBar"
                        plot-id="circular2Patway"
                        :plot-data="lollipopData"
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
                      <Lollipop-plot
                        v-if="lollipopDataTumor && displayTumorbar"
                        :width="800"
                        lollipop-id="topas2LollipopTumorantigen"
                        lolli-title="Expression Z-scores"
                        :fixed-domain="fixedDomain"
                        :vline="2"
                        :lolliradian="1"
                        :plot-data="lollipopDataTumor"
                        :show-legends="true"
                      />
                    </v-col>
                    <v-col
                      sm="12"
                      md="5"
                      lg="5"
                    >
                      <Circularbar-plot
                        v-if="lollipopDataTumor && displayTumorbar"
                        plot-id="circular2Tumor"
                        :plot-data="lollipopDataTumor"
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
                      <Lollipop-plot
                        v-if="expressionDataRTK && displaylollipop"
                        :width="1600"
                        :height="400"
                        :fixed-domain="fixedDomain"
                        lolli-mode="true"
                        lolliradian="4"
                        lolli-title="Topas Z-scores | EXPRESSION Z-scores"
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
                      <Lollipop-plot
                        v-if="expressionDataDownstream && displaylollipop"
                        :width="1600"
                        :height="400"
                        :fixed-domain="fixedDomain"
                        lolli-mode="true"
                        lolliradian="2"
                        lolli-title="TOPAS Z-scores | EXPRESSION Z-scores"
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
import LollipopPlot from '@/components/plots/LollipopPlot'
import CircularbarPlot from '@/components/plots/CircularbarPlot'
import histogram from '@/components/plots/GenericHistogram.vue'
import { DataType } from '@/constants'
import { api } from '@/routes.ts'

export default {
  name: 'ReportComponent',
  components: {
    CohortSelect,
    PatientReportTable,
    LollipopPlot,
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
    summedIntensitiesPhospho: [],
    summedIntensitiesFull: [],
    patientData: [],
    selectedLineppintensity: [],
    selectedLinefpintensity: [],
    scoreType: DataType.REPORT_SUMMARY,
    Showcircular: true,
    lollipopData: false,
    showCorrelation: false,
    lollipopDataTumor: false,
    histogramMargin: { top: 20, right: 10, bottom: 50, left: 70 },
    proteinCounts: [],
    peptideCounts: [],
    ppeptideCounts: [],
    correlationStatistics: [],
    firstPatient: '',
    patientscoresDataurl: '',
    expressionDataRTK: false,
    expressionDataDownstream: false,
    type: 'tumor',
    selectedFPLines: [],
    selectedLinecorrelation: [],
    selectedpepLines: [],
    selectedfppepLines: [],
    selectedData: [],
    allInputDataTypes: [
      {
        text: 'Report summary',
        value: DataType.REPORT_SUMMARY
      },
      {
        text: 'TOPAS CK score',
        value: DataType.TOPAS_CK_SCORE
      },
      {
        text: 'TOPAS RTK score',
        value: DataType.TOPAS_RTK_SCORE
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
      return this.proteinCounts.map(d => d.identified)
    },
    peptideCount () {
      return this.ppeptideCounts.map(d => d.identified)
    },
    peptidefpCount () {
      return this.peptideCounts.map(d => d.identified)
    },
    correlationCount () {
      return this.correlationStatistics.map(d => d.correlation)
    },
    ppintensitySum () {
      return this.summedIntensitiesPhospho.map(d => d.sumIntensities)
    },
    fpintensitySum () {
      return this.summedIntensitiesFull.map(d => d.sumIntensities)
    },
    displayrtkBar () {
      return this.type === 'rtk'
    },
    displayTumorbar () {
      return this.type === 'tumor'
    },
    displaylollipop () {
      return this.type === 'lollipop'
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
      const requests = [
        {
          name: 'patientData',
          endpoint: api.PATIENTS_METADATA({
            cohort_index: this.cohortIndex
          }),
          errorMessage: 'Error: Could not load patient metadata'
        },
        {
          name: 'summedIntensitiesPhospho',
          endpoint: api.PATIENT_CENTRIC_SUMMED_INTENSITY({
            cohort_index: this.cohortIndex,
            level: DataType.PHOSPHO_PROTEOME
          }),
          errorMessage: 'Error: could not load phospho intensities data'
        },
        {
          name: 'summedIntensitiesFull',
          endpoint: api.PATIENT_CENTRIC_SUMMED_INTENSITY({
            cohort_index: this.cohortIndex,
            level: DataType.FULL_PROTEOME
          }),
          errorMessage: 'Error: could not load full proteome intensities data'
        },
        {
          name: 'proteinCounts',
          endpoint: api.PATIENT_CENTRIC_COUNTS({
            cohort_index: this.cohortIndex,
            level: DataType.FULL_PROTEOME
          }),
          errorMessage: 'Error: could not load protein counts data'
        },
        {
          name: 'ppeptideCounts',
          endpoint: api.PATIENT_CENTRIC_COUNTS({
            cohort_index: this.cohortIndex,
            level: DataType.PHOSPHO_PROTEOME
          }),
          errorMessage: 'Error: could not load phosphoproteome peptide counts data'
        },
        {
          name: 'peptideCounts',
          endpoint: api.PATIENT_CENTRIC_COUNTS({
            cohort_index: this.cohortIndex,
            level: DataType.FULL_PROTEOME_NUM_PEPTIDES
          }),
          errorMessage: 'Error: could not load full proteome peptide counts data'
        }
      ]

      if (this.showCorrelation) {
        requests.push({
          name: 'correlationStatistics',
          endpoint: api.CORRELATION_FPKM_PROTEIN({
            cohort_index: this.cohortIndex
          }),
          errorMessage: 'Error: could not load FPKM-protein correlation statistics data'
        })
      }

      this.processRequestsAsync(requests)
    },
    async processRequestsAsync (requests) {
      // Start all requests immediately and handle them independently
      for (const { name, endpoint, errorMessage } of requests) {
        axios.get(endpoint)
          .then(response => {
            // Update the corresponding reactive variable as soon as data arrives
            this[name] = response.data
          })
          .catch(() => {
            // Handle errors individually
            this.addNotification({
              color: 'error',
              message: errorMessage
            })
          })
      }
    },
    getscoresTable () {
      if (this.firstPatient.length === 0) return

      this.patientscoresDataurl = api.PATIENT_REPORT_TABLE({
        cohort_index: this.cohortIndex,
        patient: this.firstPatient,
        level: this.scoreType
      })
      // this.patientscoresData = response.data
    },
    async updateSelectedRows (selectedIds, selectedData) {
      this.selectedData = selectedData
      this.lollipopData = false
      this.expressionDataRTK = false
      this.expressionDataDownstream = false
      this.lollipopDataTumor = false
      if (selectedData.length > 0) {
        const firstPatient = selectedData[0]['Sample name']
        this.firstPatient = firstPatient
        const requests = [
          {
            name: 'lollipopData',
            endpoint: api.TOPAS_LOLLIPOP({
              cohort_index: this.cohortIndex,
              patient: firstPatient
            }),
            errorMessage: 'Error: Could not load lollipop data'
          },
          {
            name: 'lollipopDataTumor',
            endpoint: api.TOPAS_LOLLIPOP_TUMOR({
              cohort_index: this.cohortIndex,
              patient: firstPatient
            }),
            errorMessage: 'Error: Could not load lollipop tumor data'
          },
          {
            name: 'expressionDataRTK',
            endpoint: api.TOPAS_EXPRESSION_RTK({
              cohort_index: this.cohortIndex,
              patient: firstPatient
            }),
            errorMessage: 'Error: Could not load RTK expression data'
          },
          {
            name: 'expressionDataDownstream',
            endpoint: api.TOPAS_EXPRESSION_DOWNSTREAM({
              cohort_index: this.cohortIndex,
              patient: firstPatient
            }),
            errorMessage: 'Error: Could not load downstream expression data'
          }
        ]
        this.processRequestsAsync(requests)

        this.getscoresTable()
        const dashStyle = '5, 5'

        const mappings = [
          {
            source: 'proteinCounts',
            target: 'selectedFPLines',
            color: 'red',
            valueKey: 'identified'
          },
          {
            source: 'ppeptideCounts',
            target: 'selectedpepLines',
            color: 'blue',
            valueKey: 'identified'
          },
          {
            source: 'peptideCounts',
            target: 'selectedfppepLines',
            color: 'red',
            valueKey: 'identified'
          },
          {
            source: 'summedIntensitiesPhospho',
            target: 'selectedLineppintensity',
            color: 'blue',
            valueKey: 'sumIntensities'
          },
          {
            source: 'summedIntensitiesFull',
            target: 'selectedLinefpintensity',
            color: 'orange',
            valueKey: 'sumIntensities'
          }
        ]

        if (this.showCorrelation) {
          mappings.push({
            source: 'correlationStatistics',
            target: 'selectedLinecorrelation',
            color: 'black',
            valueKey: 'correlation'
          })
        }

        // Populate each in one pass
        for (const { source, target, color, valueKey } of mappings) {
          this[target] = []
          this[source].forEach(element => {
            if (element.patients === firstPatient) {
              this[target].push({
                color,
                value: element[valueKey],
                curveid: -1,
                dash: dashStyle
              })
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
