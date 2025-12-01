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
            <v-checkbox
              v-model="includeRefChannels"
              label="Include ref channels"
              dense
              hide-details
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
              @change="getPatientData"
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
                  <patientscore-table :data-source="patientScoresDataURL" />
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
                        :max-dose="12000"
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
                        :max-dose="60000"
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
                        :plot-histogram="true"
                        :plot-k-d-e="false"
                        :selected-lines="selectedLineppintensity"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="log10(Summed PP intensities)"
                        :margin="histogramMargin"
                        :min-dose="8"
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
                        :plot-histogram="true"
                        :plot-k-d-e="false"
                        :selected-lines="selectedLinefpintensity"
                        :min-height="minHeight"
                        :min-width="minWidth"
                        xlabel="log10(Summed FP intensities)"
                        :margin="histogramMargin"
                        :min-dose="8"
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
                  <v-tabs
                    v-model="type"
                  >
                    <v-tab href="#tumor">TUMOR ANTIGENS</v-tab>
                    <v-tab href="#rtk">RTK</v-tab>
                    <v-tab href="#cknk">CK / NK</v-tab>
                    <v-tab href="#immune">IMMUNE STATUS</v-tab>
                    <v-tab href="#prodict">PRODICT</v-tab>
                  </v-tabs>

                  <v-divider></v-divider>

                  <v-tabs-items v-model="type" v-if="firstPatient" class="min-height-1000">
                    <v-tab-item value="tumor">
                      <v-card flat>
                        <v-card-text>
                          <img
                           :key="`tumor-${firstPatient}-${cohortIndex}`"
                           :src="api.TUMOR_ANTIGENS_SWARM_PLOT({cohort_index: this.cohortIndex, patient: this.firstPatient})"/>
                        </v-card-text>
                      </v-card>
                    </v-tab-item>

                    <v-tab-item value="rtk">
                      <v-card flat>
                        <v-card-text>
                          <img
                           :key="`rtk-${firstPatient}-${cohortIndex}`"
                           :src="api.RTKS_SWARM_PLOT({cohort_index: this.cohortIndex, patient: this.firstPatient})"/>
                        </v-card-text>
                      </v-card>
                    </v-tab-item>

                    <v-tab-item value="cknk">
                      <v-card flat>
                        <v-card-text>
                          <img
                           :key="`cknk-${firstPatient}-${cohortIndex}`"
                           :src="api.CKS_NKS_SWARM_PLOT({cohort_index: this.cohortIndex, patient: this.firstPatient})"/>
                        </v-card-text>
                      </v-card>
                    </v-tab-item>

                    <v-tab-item value="immune">
                      <v-card flat>
                        <v-card-text>
                          <img
                           :key="`immune-${firstPatient}-${cohortIndex}`"
                           :src="api.IMMUNE_STATUS_HEATMAP({cohort_index: this.cohortIndex, patient: this.firstPatient})"/>
                        </v-card-text>
                      </v-card>
                    </v-tab-item>

                    <v-tab-item value="prodict">
                      <v-card flat>
                        <v-card-text>
                          <img
                           :key="`prodict-${firstPatient}-${cohortIndex}`"
                           :src="api.PRODICT_PROBABILITES_UMAP({cohort_index: this.cohortIndex, patient: this.firstPatient})"/>
                        </v-card-text>
                      </v-card>
                    </v-tab-item>

                  </v-tabs-items>
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
import histogram from '@/components/plots/GenericHistogram.vue'
import { DataType, IncludeRef } from '@/constants'
import { api } from '@/routes.ts'

export default {
  name: 'ReportComponent',
  components: {
    CohortSelect,
    PatientReportTable,
    histogram,
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
    includeRefChannels: false,
    topasName: '',
    isCollapsed: true,
    fixedDomain: false,
    summedIntensitiesPhospho: [],
    summedIntensitiesFull: [],
    patientData: [],
    selectedLineppintensity: [],
    selectedLinefpintensity: [],
    scoreType: DataType.REPORT_SUMMARY,
    showCorrelation: false,
    histogramMargin: { top: 20, right: 10, bottom: 50, left: 70 },
    proteinCounts: [],
    peptideCounts: [],
    ppeptideCounts: [],
    correlationStatistics: [],
    firstPatient: '',
    patientScoresDataURL: '',
    type: 'tumor',
    selectedFPLines: [],
    selectedLinecorrelation: [],
    selectedpepLines: [],
    selectedfppepLines: [],
    selectedData: [],
    api,
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
    patientReportUrl () {
      return api.PATIENT_REPORT_TABLE_XLSX({ cohort_index: this.cohortIndex, patients: ':patients' })
    },
    includeRef () {
      return this.includeRefChannels ? IncludeRef.INCLUDE_REF : IncludeRef.EXCLUDE_REF
    }
  },
  watch: {
    cohortIndex () {
      this.getPatientData()
    },
    includeRefChannels () {
      this.getPatientData()
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
    async getPatientData () {
      this.patientData = null
      const requests = [
        {
          name: 'patientData',
          endpoint: api.PATIENTS_METADATA({
            cohort_index: this.cohortIndex,
            include_ref: this.includeRef
          }),
          errorMessage: 'Error: Could not load patient metadata'
        },
        {
          name: 'summedIntensitiesPhospho',
          endpoint: api.PATIENT_CENTRIC_SUMMED_INTENSITY({
            cohort_index: this.cohortIndex,
            level: DataType.PHOSPHO_PROTEOME,
            include_ref: this.includeRef
          }),
          errorMessage: 'Error: could not load phospho intensities data'
        },
        {
          name: 'summedIntensitiesFull',
          endpoint: api.PATIENT_CENTRIC_SUMMED_INTENSITY({
            cohort_index: this.cohortIndex,
            level: DataType.FULL_PROTEOME,
            include_ref: this.includeRef
          }),
          errorMessage: 'Error: could not load full proteome intensities data'
        },
        {
          name: 'proteinCounts',
          endpoint: api.PATIENT_CENTRIC_COUNTS({
            cohort_index: this.cohortIndex,
            level: DataType.FULL_PROTEOME,
            include_ref: this.includeRef
          }),
          errorMessage: 'Error: could not load protein counts data'
        },
        {
          name: 'ppeptideCounts',
          endpoint: api.PATIENT_CENTRIC_COUNTS({
            cohort_index: this.cohortIndex,
            level: DataType.PHOSPHO_PROTEOME,
            include_ref: this.includeRef
          }),
          errorMessage: 'Error: could not load phosphoproteome peptide counts data'
        },
        {
          name: 'peptideCounts',
          endpoint: api.PATIENT_CENTRIC_COUNTS({
            cohort_index: this.cohortIndex,
            level: DataType.FULL_PROTEOME_NUM_PEPTIDES,
            include_ref: this.includeRef
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

      this.patientScoresDataURL = api.PATIENT_REPORT_TABLE({
        cohort_index: this.cohortIndex,
        patient: this.firstPatient,
        level: this.scoreType
      })
    },
    async updateSelectedRows (selectedIds, selectedData) {
      this.selectedData = selectedData
      if (selectedData.length > 0) {
        this.firstPatient = selectedData[0]['Sample name']

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
            if (element.patients === this.firstPatient) {
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
