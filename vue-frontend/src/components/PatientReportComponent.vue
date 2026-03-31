<template>
  <v-container class="bg-grey-lighten-3" fluid>
    <v-row>
      <!-- Sidebar for Filters and Controls -->
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Patient Reports </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <sample-filter-select @update-sample-filter="updateSampleFilter" />
            <v-select
              v-model="scoreType"
              class="input_data_type mb-2 mt-4"
              prepend-icon="mdi-layers-triple"
              :items="allInputDataTypes"
              label="Data Type"
              @update:model-value="getscoresTable"
            />
            <v-checkbox
              v-model="showCorrelation"
              label="Show FPKM/protein correlation histogram"
              @update:model-value="getPatientData"
            />
          </v-card-text>
        </v-card>
        <!-- Collapsible Help Box -->
        <v-card variant="flat" class="mt-4">
          <v-card-title>Help</v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> Tab info </v-expansion-panel-title>
                <v-expansion-panel-text>
                  In this tab you can browse and download patient-specific reports. It also shows QC
                  statistics and detailed plots regarding tumor antigens, RTKs, cytoplasmic kinases
                  and immune status.
                </v-expansion-panel-text>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> How to use </v-expansion-panel-title>
                <v-expansion-panel-text>
                  Use the dropdown menu to select a cohort, then select a sample by checking the
                  corresponding checkbox in the table to the right to interactively explore the
                  patient report for that sample. You can download the patient report(s) in Excel
                  format by selecting one or more samples in the patient table and clicking the
                  'Download report(s)' button.
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
      <!-- Main Content -->
      <v-col sm="12" md="9" lg="10">
        <v-container fluid class="pa-0">
          <v-row>
            <v-col sm="12" md="6" lg="6">
              <v-card variant="flat">
                <v-card-text>
                  <patient-report-table
                    :data-source="patientData"
                    :patient-report-url="patientReportUrl"
                    @onRowSelect="updateSelectedRows"
                  />
                </v-card-text>
              </v-card>
              <v-card v-if="!firstPatient" variant="flat" class="mt-4">
                <v-card-text> Please select a patient in the table above </v-card-text>
              </v-card>
              <v-card v-if="firstPatient" variant="flat" class="mt-4">
                <v-card-title>{{ firstPatient }} - {{ scoreTypeText }}</v-card-title>
                <v-card-text>
                  <patientscore-table :data-source="patientScoresDataURL" />
                </v-card-text>
              </v-card>
            </v-col>
            <v-col sm="12" md="6" lg="6">
              <v-card variant="flat">
                <v-card-text>
                  <!-- Top Row: Patient Table and Histograms -->
                  <v-row>
                    <v-col sm="12" md="6" lg="6">
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
                    <v-col sm="12" md="6" lg="6">
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
                    <v-col sm="12" md="6" lg="6">
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
                    <v-col sm="12" md="6" lg="6">
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
                    <v-col sm="12" md="6" lg="6">
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
                    <v-col sm="12" md="6" lg="6">
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
            <v-col sm="12" md="12" lg="12">
              <v-card variant="flat">
                <v-card-title>
                  Advanced plots
                  <v-spacer></v-spacer>
                  <v-btn
                    color="primary"
                    :disabled="!canDownloadReportPptx"
                    :loading="downloadingPptx"
                    @click="downloadPatientReportPptx"
                  >
                    Download Patient Report
                  </v-btn>
                </v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" sm="6" md="4">
                      <v-select
                        v-model="backgroundCohort"
                        :items="backgroundCohortOptions"
                        label="Background cohort"
                      />
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col>
                      <div class="d-flex justify-end mb-2">
                        <v-btn
                          v-if="firstPatient"
                          size="small"
                          variant="text"
                          icon
                          title="Download tumor antigens"
                          @click="downloadPlot(getTumorUrl(), plotFilename('tumor-antigens'))"
                        >
                          <v-icon> mdi-cloud-download </v-icon>
                        </v-btn>
                      </div>
                      <v-img
                        v-if="firstPatient"
                        :key="`${plotsReloadKey}-tumor`"
                        :src="getTumorUrl()"
                        aspect-ratio="1.78"
                        @load="onTumorLoad"
                        @error="onTumorError"
                      >
                        <template #placeholder>
                          <v-col class="fill-height ma-0" align="center" justify="center">
                            <v-progress-circular indeterminate color="primary" size="64" />
                            <p>Loading tumor antigens...</p>
                          </v-col>
                        </template>
                      </v-img>
                    </v-col>
                    <v-col>
                      <div class="d-flex justify-end mb-2">
                        <v-btn
                          v-if="firstPatient"
                          size="small"
                          variant="text"
                          icon
                          title="Download RTKs"
                          @click="downloadPlot(getRtkUrl(), plotFilename('rtk'))"
                        >
                          <v-icon> mdi-cloud-download </v-icon>
                        </v-btn>
                      </div>
                      <v-img
                        v-if="firstPatient"
                        :key="`${plotsReloadKey}-rtk`"
                        :src="getRtkUrl()"
                        aspect-ratio="1.78"
                        @load="onRtkLoad"
                        @error="onRtkError"
                      >
                        <template #placeholder>
                          <v-col class="fill-height ma-0" hei align="center" justify="center">
                            <v-progress-circular indeterminate color="primary" size="64" />
                            <p>Loading RTKs...</p>
                          </v-col>
                        </template>
                      </v-img>
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col>
                      <div class="d-flex justify-end mb-2">
                        <v-btn
                          v-if="firstPatient"
                          size="small"
                          variant="text"
                          icon
                          title="Download CK/NK"
                          @click="downloadPlot(getCknkUrl(), plotFilename('ck-nk'))"
                        >
                          <v-icon> mdi-cloud-download </v-icon>
                        </v-btn>
                      </div>
                      <v-img
                        v-if="firstPatient"
                        :key="`${plotsReloadKey}-cknk`"
                        :src="getCknkUrl()"
                        aspect-ratio="1.78"
                        @load="onCknkLoad"
                        @error="onCknkError"
                      >
                        <template #placeholder>
                          <v-col class="fill-height ma-0" align="center" justify="center">
                            <v-progress-circular indeterminate color="primary" size="64" />
                            <p class="mt-4"> Loading CK/NK... </p>
                          </v-col>
                        </template>
                      </v-img>
                    </v-col>
                    <v-col>
                      <div class="d-flex justify-end mb-2">
                        <v-btn
                          v-if="firstPatient"
                          size="small"
                          variant="text"
                          icon
                          title="Download immune status"
                          @click="downloadPlot(getImmuneUrl(), plotFilename('immune-status'))"
                        >
                          <v-icon> mdi-cloud-download </v-icon>
                        </v-btn>
                      </div>
                      <v-img
                        v-if="firstPatient"
                        :key="`${plotsReloadKey}-immune`"
                        :src="getImmuneUrl()"
                        aspect-ratio="1.78"
                        @load="onImmuneLoad"
                        @error="onImmuneError"
                      >
                        <template #placeholder>
                          <v-col class="fill-height ma-0" align="center" justify="center">
                            <v-progress-circular indeterminate color="primary" size="64" />
                            <p class="mt-4"> Loading immune status... </p>
                          </v-col>
                        </template>
                      </v-img>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col>
                      <div class="d-flex justify-end mb-2">
                        <v-btn
                          v-if="firstPatient"
                          size="small"
                          variant="text"
                          icon
                          title="Download PROdict scores"
                          @click="downloadPlot(getProdictProbUrl(), plotFilename('prodict-scores'))"
                        >
                          <v-icon> mdi-cloud-download </v-icon>
                        </v-btn>
                      </div>
                      <v-img
                        v-if="firstPatient"
                        :key="`${plotsReloadKey}-prodict-prob`"
                        :src="getProdictProbUrl()"
                        aspect-ratio="1.78"
                        @load="onProdictProbLoad"
                        @error="onProdictProbError"
                      >
                        <template #placeholder>
                          <v-col class="fill-height ma-0" align="center" justify="center">
                            <v-progress-circular indeterminate color="primary" size="64" />
                            <p class="mt-4"> Loading PROdictions... </p>
                          </v-col>
                        </template>
                      </v-img>
                    </v-col>
                    <v-col>
                      <div class="d-flex justify-end mb-2">
                        <v-btn
                          v-if="firstPatient"
                          size="small"
                          variant="text"
                          icon
                          title="Download PROdict UMAP"
                          @click="downloadPlot(getProdictUmapUrl(), plotFilename('prodict-umap'))"
                        >
                          <v-icon> mdi-cloud-download </v-icon>
                        </v-btn>
                      </div>
                      <v-img
                        v-if="firstPatient"
                        :key="`${plotsReloadKey}-prodict-umap`"
                        :src="getProdictUmapUrl()"
                        aspect-ratio="1.78"
                        @load="onProdictUmapLoad"
                        @error="onProdictUmapError"
                      >
                        <template #placeholder>
                          <v-col class="fill-height ma-0" align="center" justify="center">
                            <v-progress-circular indeterminate color="primary" size="64" />
                            <p class="mt-4"> Loading UMAP... </p>
                          </v-col>
                        </template>
                      </v-img>
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
  import SampleFilterSelect from '@/components/partials/SampleFilterSelect.vue'
  import patientscoreTable from '@/components/tables/PatientScoresTable.vue'
  import PatientReportTable from '@/components/tables/PatientReportTable.vue'
  import histogram from '@/components/plots/GenericHistogram.vue'
  import { DataType, SampleFilter } from '@/constants'
  import { api } from '@/routes.ts'

  export default {
    name: 'ReportComponent',
    components: {
      CohortSelect,
      SampleFilterSelect,
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
      sampleFilter: SampleFilter.ONLY_PATIENTS,
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
          title: 'Report summary',
          value: DataType.REPORT_SUMMARY
        },
        {
          title: 'TOPAS CK score',
          value: DataType.TOPAS_CK_SCORE
        },
        {
          title: 'TOPAS RTK score',
          value: DataType.TOPAS_RTK_SCORE
        },
        {
          title: 'Full proteome',
          value: DataType.FULL_PROTEOME
        },
        {
          title: 'Phosphopeptides',
          value: DataType.PHOSPHO_PROTEOME
        },
        {
          title: 'Kinases',
          value: DataType.KINASE_SCORE
        },
        {
          title: 'P-protein scores',
          value: DataType.PHOSPHO_SCORE
        },
        {
          title: 'TOPAS subscore',
          value: DataType.TOPAS_SUBSCORE
        },
        {
          title: 'Biomarker',
          value: DataType.BIOMARKER
        }
      ],
      loadingTumor: false,
      loadingRtk: false,
      loadingCknk: false,
      loadingImmune: false,
      loadingProdictProb: false,
      loadingProdictUmap: false,
      tumorLoaded: false,
      rtkLoaded: false,
      cknkLoaded: false,
      immuneLoaded: false,
      prodictProbLoaded: false,
      prodictUmapLoaded: false,
      backgroundCohort: 'default'
    }),
    computed: {
      canDownloadReportPptx() {
        return (
          this.immuneLoaded &&
          this.rtkLoaded &&
          this.cknkLoaded &&
          this.tumorLoaded &&
          this.prodictProbLoaded &&
          this.prodictUmapLoaded
        )
      },
      proteinCount() {
        return this.proteinCounts.map(d => d.identified)
      },
      peptideCount() {
        return this.ppeptideCounts.map(d => d.identified)
      },
      peptidefpCount() {
        return this.peptideCounts.map(d => d.identified)
      },
      correlationCount() {
        return this.correlationStatistics.map(d => d.correlation)
      },
      ppintensitySum() {
        return this.summedIntensitiesPhospho.map(d => d.sumIntensities)
      },
      fpintensitySum() {
        return this.summedIntensitiesFull.map(d => d.sumIntensities)
      },
      patientReportUrl() {
        return api.PATIENT_REPORT_TABLE_XLSX({
          cohort_index: this.cohortIndex,
          patients: ':patients'
        })
      },
      firstPatient() {
        if (this.selectedData.length > 0) {
          return this.selectedData[0]['Sample name']
        }
        return ''
      },
      scoreTypeText() {
        const found = this.allInputDataTypes.find(item => item.value === this.scoreType)
        return found ? found.text : ''
      },
      backgroundCohortOptions() {
        const options = [{ title: 'Default (Sample Oncotree)', value: 'default' }]
        if (!Array.isArray(this.patientData)) return options

        const uniqueValues = new Set()
        this.patientData.forEach(row => {
          const value = row && row.code_oncotree
          if (value) uniqueValues.add(value)
        })

        return options.concat(
          Array.from(uniqueValues)
            .sort()
            .map(value => ({ title: value, value }))
        )
      },
      backgroundCohortParam() {
        return this.backgroundCohort || 'default'
      },
      plotsReloadKey() {
        return `${this.firstPatient}-${this.backgroundCohortParam}`
      }
    },
    watch: {
      cohortIndex() {
        this.backgroundCohort = 'default'
        this.getPatientData()
      },
      patientData() {
        const values = this.backgroundCohortOptions.map(option => option.value)
        if (!values.includes(this.backgroundCohort)) {
          this.backgroundCohort = 'default'
        }
      },
      sampleFilter() {
        this.getPatientData()
      },
      firstPatient() {
        this.backgroundCohort = 'default'
        this.loadingTumor = true
        this.loadingRtk = true
        this.loadingCknk = true
        this.loadingImmune = true
        this.loadingProdictProb = true
        this.loadingProdictUmap = true
        this.tumorLoaded = false
        this.rtkLoaded = false
        this.cknkLoaded = false
        this.immuneLoaded = false
        this.prodictProbLoaded = false
        this.prodictUmapLoaded = false
      },
      backgroundCohort() {
        if (!this.firstPatient) return
        this.loadingTumor = true
        this.loadingRtk = true
        this.loadingCknk = true
        this.loadingImmune = true
        this.loadingProdictUmap = true
        this.tumorLoaded = false
        this.rtkLoaded = false
        this.cknkLoaded = false
        this.immuneLoaded = false
        this.prodictProbLoaded = false
        this.prodictUmapLoaded = false
      }
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      async downloadPatientReportPptx() {
        this.downloadingPptx = true
        try {
          const response = await axios.get(
            api.PATIENT_REPORT_PPTX({
              cohort_index: this.cohortIndex,
              patient: this.firstPatient,
              background_cohort: this.backgroundCohortParam
            }),
            {
              responseType: 'blob' // important for binary files
            }
          )

          // Axios headers are plain objects
          const disposition = response.headers['content-disposition']
          let filename = this.firstPatient + '_patient_report.pptx' // default
          if (disposition && disposition.includes('filename=')) {
            filename = disposition.split('filename=')[1].replace(/"/g, '').trim()
          }

          // response.data is already a Blob because of responseType
          const url = window.URL.createObjectURL(response.data)
          const a = document.createElement('a')
          a.href = url
          a.download = filename
          document.body.appendChild(a)
          a.click()
          a.remove()
          window.URL.revokeObjectURL(url)
        } catch (err) {
          console.error(err)
        } finally {
          this.downloadingPptx = false
        }
      },
      onImmuneLoad() {
        this.loadingImmune = false
        this.immuneLoaded = true
      },
      onImmuneError() {
        this.loadingImmune = false
        this.immuneLoaded = false
      },
      onTumorLoad() {
        this.loadingTumor = false
        this.tumorLoaded = true
      },
      onTumorError() {
        this.loadingTumor = false
        this.tumorLoaded = false
      },
      onRtkLoad() {
        this.loadingRtk = false
        this.rtkLoaded = true
      },
      onRtkError() {
        this.loadingRtk = false
        this.rtkLoaded = false
      },
      onCknkLoad() {
        this.loadingCknk = false
        this.cknkLoaded = true
      },
      onCknkError() {
        this.loadingCknk = false
        this.cknkLoaded = false
      },
      onProdictProbLoad() {
        this.loadingProdictProb = false
        this.prodictProbLoaded = true
      },
      onProdictProbError() {
        this.loadingProdictProb = false
        this.prodictProbLoaded = false
      },
      onProdictUmapLoad() {
        this.loadingProdictUmap = false
        this.prodictUmapLoaded = true
      },
      onProdictUmapError() {
        this.loadingProdictUmap = false
        this.prodictUmapLoaded = false
      },
      updateCohort({ cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      updateSampleFilter({ sampleFilter }) {
        this.sampleFilter = sampleFilter
      },
      toggleDiv(type) {
        this.type = type
      },
      async getPatientData() {
        this.patientData = null
        const requests = [
          {
            name: 'patientData',
            endpoint: api.PATIENTS_METADATA({
              cohort_index: this.cohortIndex,
              include_ref: this.sampleFilter
            }),
            errorMessage: 'Error: Could not load patient metadata'
          },
          {
            name: 'summedIntensitiesPhospho',
            endpoint: api.PATIENT_CENTRIC_SUMMED_INTENSITY({
              cohort_index: this.cohortIndex,
              level: DataType.PHOSPHO_PROTEOME,
              include_ref: this.sampleFilter
            }),
            errorMessage: 'Error: could not load phospho intensities data'
          },
          {
            name: 'summedIntensitiesFull',
            endpoint: api.PATIENT_CENTRIC_SUMMED_INTENSITY({
              cohort_index: this.cohortIndex,
              level: DataType.FULL_PROTEOME,
              include_ref: this.sampleFilter
            }),
            errorMessage: 'Error: could not load full proteome intensities data'
          },
          {
            name: 'proteinCounts',
            endpoint: api.PATIENT_CENTRIC_COUNTS({
              cohort_index: this.cohortIndex,
              level: DataType.FULL_PROTEOME,
              include_ref: this.sampleFilter
            }),
            errorMessage: 'Error: could not load protein counts data'
          },
          {
            name: 'ppeptideCounts',
            endpoint: api.PATIENT_CENTRIC_COUNTS({
              cohort_index: this.cohortIndex,
              level: DataType.PHOSPHO_PROTEOME,
              include_ref: this.sampleFilter
            }),
            errorMessage: 'Error: could not load phosphoproteome peptide counts data'
          },
          {
            name: 'peptideCounts',
            endpoint: api.PATIENT_CENTRIC_COUNTS({
              cohort_index: this.cohortIndex,
              level: DataType.FULL_PROTEOME_NUM_PEPTIDES,
              include_ref: this.sampleFilter
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
      async processRequestsAsync(requests) {
        // Start all requests immediately and handle them independently
        for (const { name, endpoint, errorMessage } of requests) {
          axios
            .get(endpoint)
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
      getscoresTable() {
        if (this.firstPatient.length === 0) return

        this.patientScoresDataURL = api.PATIENT_REPORT_TABLE({
          cohort_index: this.cohortIndex,
          patient: this.firstPatient,
          level: this.scoreType
        })
      },
      async updateSelectedRows(selectedIds, selectedData) {
        this.selectedData = selectedData

        if (selectedData.length > 0) {
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
      },
      getTumorUrl() {
        return api.TUMOR_ANTIGENS_SWARM_PLOT({
          cohort_index: this.cohortIndex,
          patient: this.firstPatient,
          background_cohort: this.backgroundCohortParam
        })
      },

      getRtkUrl() {
        return api.RTKS_SWARM_PLOT({
          cohort_index: this.cohortIndex,
          patient: this.firstPatient,
          background_cohort: this.backgroundCohortParam
        })
      },

      getCknkUrl() {
        return api.CKS_NKS_SWARM_PLOT({
          cohort_index: this.cohortIndex,
          patient: this.firstPatient,
          background_cohort: this.backgroundCohortParam
        })
      },

      getImmuneUrl() {
        return api.IMMUNE_STATUS_HEATMAP({
          cohort_index: this.cohortIndex,
          patient: this.firstPatient
        })
      },

      getProdictProbUrl() {
        return api.PRODICT_PATIENT_PROBABILITES({
          cohort_index: this.cohortIndex,
          patient: this.firstPatient
        })
      },

      getProdictUmapUrl() {
        return api.PRODICT_PATIENT_UMAP({
          cohort_index: this.cohortIndex,
          patient: this.firstPatient,
          background_cohort: this.backgroundCohortParam
        })
      },
      plotFilename(label) {
        const patient = this.firstPatient || 'patient'
        const cohort =
          this.backgroundCohortParam && this.backgroundCohortParam !== 'default'
            ? this.backgroundCohortParam
            : 'default'
        return `${patient}_${label}_${cohort}`.replace(/[^a-zA-Z0-9_.-]+/g, '_')
      },
      async downloadPlot(url, filename) {
        try {
          const response = await axios.get(url, { responseType: 'blob' })
          const blob = new Blob([response.data], { type: 'image/svg+xml' })
          const link = document.createElement('a')
          link.href = URL.createObjectURL(blob)
          link.download = `${filename}.svg`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          URL.revokeObjectURL(link.href)
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: 'Error: could not download plot'
          })
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
    box-shadow:
      3px 3px 6px rgba(0, 0, 0, 0.2),
      -3px -3px 6px rgba(255, 255, 255, 0.7);
    transition: box-shadow 0.2s ease-in-out;
  }

  .chart-container {
    position: relative;
    min-height: 400px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .loader {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
  }
</style>
