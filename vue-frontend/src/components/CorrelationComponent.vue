<template>
  <v-container class="bg-grey-lighten-3" fluid>
    <v-row>
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Correlations </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <subcohort-select
              class="mt-4"
              :cohort-index="cohortIndex"
              :sample-ids="customGroup"
              @update-group="updateSampleGroup"
              @update-selection-method="updateSelectionMethodGroup"
            />
            <v-radio-group v-model="intensityUnit" label="Intensity unit" class="mt-4">
              <v-radio
                v-for="u in intensityUnits"
                :key="u.value"
                :label="u.title"
                :value="u.value"
              />
            </v-radio-group>
          </v-card-text>
        </v-card>
        <v-card variant="flat" class="mt-4">
          <v-card-title tag="h1"> Select correlation inputs </v-card-title>
          <v-card-text>
            <v-select
              v-model="correlationInputType"
              prepend-icon="mdi-filter"
              :items="dataTypes"
              label="Input type"
              @update:model-value="jsonUrl = ''"
            />
            <phosphopeptide-select
              v-if="correlationInputType === 'psite'"
              :cohort-index="cohortIndex"
              :data-layer="correlationInputType"
              class="mt-4"
              @select-phosphopeptide="updateIdentifier"
            />
            <topas-select
              v-if="correlationInputType === 'topas'"
              class="mt-4"
              :cohort-index="cohortIndex"
              @select-topas="updateIdentifier"
            />
            <protein-select
              v-if="correlationInputType !== 'psite' && correlationInputType !== 'topas'"
              :cohort-index="cohortIndex"
              :data-layer="correlationInputType"
              class="mt-4"
              @select-protein="updateIdentifier"
            />

            <v-select
              v-model="correlationType"
              :items="dataTypes"
              prepend-icon="mdi-filter"
              label="Correlate against"
              class="mt-4"
              @update:model-value="jsonUrl = ''"
            />

            <v-btn class="mt-4" color="primary" :loading="loading" @click="loadCorrelation">
              Run Analysis
            </v-btn>
          </v-card-text>
        </v-card>
        <v-card variant="flat" class="mt-4">
          <v-card-title>Help</v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> Tab info </v-expansion-panel-title>
                <v-expansion-panel-text>
                  In this tab you can visualize correlations between proteins, phosphopeptides,
                  mRNA-transcripts, TOPAS scores, protein phosphorylation scores and substrate
                  phosphorylation scores.
                </v-expansion-panel-text>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> How to use </v-expansion-panel-title>
                <v-expansion-panel-text>
                  To visualize the correlation for specific correlation partners, select one item in
                  the upper table. In the lower table you can select specific samples to highlight
                  them in the correlation plot. You can also click on individual data points in the
                  correlation plot to display the corresponding sample. To remove samples where one
                  correlation partner has not been detected/scored, uncheck the "Impute NA on plot"
                  and click "Run analysis" again. You can also show a density distribution by
                  checking the box next to "Show Density Distribution" and clicking on "Run
                  analysis" again. To export plots, click the export button on the right handside
                  above the plot.
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col sm="12" md="9" lg="10">
        <v-card variant="flat">
          <v-card-text>
            <v-row>
              <v-col sm="12" md="8" lg="8">
                <correlation-table
                  :data-source="jsonUrl"
                  :correlation-input-type="correlationInputType"
                  :correlation-type="correlationType"
                  @onRowSelect="updateSelectedRowsCorrelation"
                />
              </v-col>
              <v-col sm="12" md="4" lg="4">
                <scatter-plot
                  v-if="jsonUrl !== ''"
                  id="correlationPlot"
                  :identifier1="identifier1"
                  :save-plot="true"
                  add-trendlinte="true"
                  :identifier2="identifier2"
                  :remove-owncolor="false"
                  :omics-type-x="correlationInputType.replace('topas', 'TOPAS score')"
                  :omics-type-y="correlationType.replace('topas', 'TOPAS score')"
                  :expressions1="expressionData1"
                  :expressions2="expressionData2"
                  :sel-ids="selectedSamples"
                  :score-type="plotScoreType"
                  :label-x="labelX"
                  :label-y="labelY"
                  class="mt-4"
                  @onDotSelect="selectDot"
                />
                <v-checkbox
                  v-if="jsonUrl !== ''"
                  v-model="doImpute"
                  label="Impute NA on Plot"
                  @update:model-value="fetchExpressionData"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        <v-card class="mt-4" variant="flat">
          <v-card-text>
            <v-row>
              <v-col sm="12" md="8" lg="8">
                <sample-table
                  :key="componentKey"
                  :data-source="sampleData"
                  :selected-patient="selectedDotsInPlot"
                  :x-axis="xaxisTable"
                  :y-axis="yaxisTable"
                  @onRowSelect="updateSelectedRowsSample"
                />
              </v-col>
              <v-col sm="12" md="4" lg="4">
                <v-checkbox
                  v-model="Showdensity"
                  label="Show Density Distribution"
                  @update:model-value="fetchDensityData"
                />
                <density-plot
                  v-if="Showdensity"
                  :save-plot="true"
                  :plot-data="densityData"
                  :title-variables="histPlottitleVariables"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import axios from 'axios'
  import { mapGetters, mapState } from 'vuex'
  import CorrelationTable from '@/components/tables/CorrelationTable.vue'
  import CohortSelect from './partials/CohortSelect.vue'
  import SubcohortSelect from './partials/SubcohortSelect.vue'
  import SampleTable from '@/components/tables/CorrelationTableSamples.vue'
  import ScatterPlot from '@/components/plots/ScatterPlot.vue'
  import TopasSelect from '@/components/partials/TopasSelect.vue'
  import ProteinSelect from '@/components/partials/ProteinSelect.vue'
  import PhosphopeptideSelect from '@/components/partials/PhosphopeptideSelect.vue'
  import DensityPlot from '@/components/plots/BarhistPlot.vue'

  import { DataType, IncludeRef, IntensityUnit, ImputationMode } from '@/constants'
  import { api } from '@/routes.ts'

  export default {
    name: 'CorrelationComponent',
    components: {
      CorrelationTable,
      SampleTable,
      DensityPlot,
      ScatterPlot,
      TopasSelect,
      ProteinSelect,
      PhosphopeptideSelect,
      CohortSelect,
      SubcohortSelect
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
      cohortIndex: 0,
      identifier1: '',
      expressionData1: [],
      xaxisTable: 'Scores1',
      yaxisTable: 'Scores2',
      intensityUnit: IntensityUnit.Z_SCORE,
      phospho: 'FP',
      labelX: '',
      labelY: '',
      doImpute: true,
      componentKey: 0,
      customGroup: [],
      selectionMethod: [],
      loading: false,
      allPatients: 'cohort',
      histPlottitleVariables: [],
      allTopass: [],
      expressionPlusMeta1: [],
      expressionPlusMeta2: [],
      densityData: [],
      Showdensity: false,
      densityType: 'All genes',
      identifier2: '',
      correlationInputType: DataType.FULL_PROTEOME,
      correlationType: DataType.FULL_PROTEOME,
      topasType: 'topas_score',
      expressionData2: [],
      chartData: [],
      jsonUrl: '',
      sampleData: [],
      response: [],
      selectedSamples: [],
      selectedDotsInPlot: '',
      plotScoreType: 'Z-score',
      intensityUnits: [
        {
          title: 'Z-scores',
          value: IntensityUnit.Z_SCORE
        },
        {
          title: 'Intensity',
          value: IntensityUnit.INTENSITY
        }
      ],
      dataTypes: [
        {
          title: 'Proteins',
          value: DataType.FULL_PROTEOME
        },
        {
          title: 'Phosphopeptides',
          value: DataType.PHOSPHO_PROTEOME
        },
        {
          title: 'Transcripts (FPKM)',
          value: DataType.TRANSCRIPTOMICS
        },
        {
          title: 'TOPAS scores',
          value: DataType.TOPAS_RTK_SCORE
        },
        {
          title: 'Protein Phoshphorylation scores',
          value: DataType.PHOSPHO_SCORE
        },
        {
          title: 'Substrate Phosphorylation scores',
          value: DataType.KINASE_SCORE
        }
      ]
    }),
    computed: {
      ...mapState({
        all_cohorts: state => state.all_cohorts
      }),
      ...mapGetters({
        hasData: 'hasData'
      }),
      identifierLabel() {
        if (this.correlationInputType === DataType.PHOSPHO_PROTEOME) {
          return 'Modified sequence'
        } else {
          return 'Gene name'
        }
      },
      placeholder() {
        if (this.correlationInputType === DataType.PHOSPHO_PROTEOME) {
          return 'AAAAAPAS(ph)ED'
        } else {
          return 'EGFR'
        }
      }
    },
    watch: {
      intensityUnit() {
        this.plotScoreType = this.intensityUnit === IntensityUnit.Z_SCORE ? 'Z-score' : 'Intensity'
      }
    },
    methods: {
      updateCohort({ cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      updateIdentifier({ dataSource, identifier }) {
        this.identifier1 = identifier
        this.topasType = dataSource
      },
      loadCorrelation() {
        this.loading = true
        this.sampleData = []
        if (this.identifier1.length > 0) {
          this.getCorrelation(this.correlationType, this.correlationInputType, this.identifier1)
          this.fetchExpressionData(1)
          this.fetchDensityData()
        }
        this.loading = false
      },

      updateSampleGroup(sampleIdList) {
        this.customGroup = sampleIdList
      },

      updateSelectionMethodGroup(selectionMethod) {
        this.selectionMethod = selectionMethod
      },

      async fetchDensityData() {
        // for histogram
        if (this.Showdensity) {
          let url = ''
          if (this.correlationInputType === 'fpkm') {
            url = api.DENSITY_FPKM({ identifier: this.identifier1, intensity_unit: 'intensity' })
          } else {
            url = api.DENSITY_PROTEIN({
              cohort_index: this.cohortIndex,
              identifier: this.identifier1,
              intensity_unit: 'intensity'
            })
          }
          const response = await axios.get(url)
          this.histPlottitleVariables = [
            { name: 'All intensities', color: 'blue' },
            { name: this.identifier1, color: 'red' }
          ]
          this.densityData = response.data
        }
      },

      async fetchExpressionData(identifierNumber) {
        const key = identifierNumber === 1 ? this.identifier1 : this.identifier2
        if (!key) return
        this.labelX = this.plotScoreType
        this.labelY = this.plotScoreType
        const modality = identifierNumber === 1 ? this.correlationInputType : this.correlationType
        const imputeString = this.doImpute ? ImputationMode.IMPUTE : ImputationMode.NO_IMPUTE
        const url = api.ABUNDANCE({
          cohort_index: this.cohortIndex,
          level: modality,
          identifier: key,
          imputation: imputeString,
          include_ref: IncludeRef.EXCLUDE_REF
        })
        const response = await axios.get(url)
        if (response.data && response.data.length > 0) {
          response.data.forEach(element => {
            element.yValue = element[this.plotScoreType]
          })
          const expressions = response.data.filter(d => d['Z-score'] !== 'n.d.')
          if (identifierNumber === 1) {
            this.expressionData1 = []
            this.expressionData1 = expressions
            this.expressionPlusMeta1 = response.data
            if (this.allPatients === 'subcohort') {
              this.expressionData1 = this.makeLimited(expressions, this.customGroup)
              this.expressionPlusMeta1 = this.makeLimited(response.data, this.customGroup)
            }
          } else {
            this.expressionData2 = []
            this.expressionData2 = expressions
            this.expressionPlusMeta2 = response.data
            if (this.allPatients === 'subcohort') {
              this.expressionData2 = this.makeLimited(expressions, this.customGroup)
              this.expressionPlusMeta2 = this.makeLimited(response.data, this.customGroup)
            }
          }
        }
      },

      makeLimited(obj, selectedNames) {
        const result = []
        obj.forEach(element => {
          for (let i = 0; i < selectedNames.length; i++) {
            if (selectedNames[i] === element['Sample name']) {
              result.push(element)
            }
          }
        })
        return result
      },

      getCorrelation(level, inputLevel, key) {
        if (this.cohortIndex >= 0) {
          const customGroup = this.allPatients === 'cohort' ? 'all' : this.customGroup
          this.jsonUrl = api.CORRELATION({
            cohort_index: this.cohortIndex,
            level: inputLevel,
            level_2: level,
            identifier: key,
            intensity_unit: this.intensityUnit,
            patients_list: customGroup
          })
        }
      },
      updateSelectedRowsSample(selectedIds, selectedData) {
        const selectedPatients = []
        selectedData.forEach(element => {
          selectedPatients.push(element['Sample name'])
        })
        // this.forceRerender()
        this.selectedSamples = selectedPatients
      },

      selectDot(selectedDot) {
        this.selectedDotsInPlot = selectedDot
      },

      async updateSelectedRowsCorrelation(selectedIds, selectedData) {
        this.identifier2 = selectedData[0].index
        await this.fetchExpressionData(2)
        this.selectDot(null)
        const tableData = []
        const sampleNames = []
        const xValues = []
        this.expressionPlusMeta2.forEach(element => {
          if (element[this.plotScoreType] !== 'n.d.') {
            sampleNames.push(element['Sample name'])
            xValues.push(element[this.plotScoreType])
          }
        })
        for (let k = 0; k < this.expressionPlusMeta1.length; k++) {
          let xvalueInd = 0
          sampleNames.forEach(element => {
            if (
              this.expressionPlusMeta1[k]['Sample name'] === element &&
              this.expressionPlusMeta1[k][this.plotScoreType] !== 'n.d.'
            ) {
              this.expressionPlusMeta1[k].xValue = xValues[xvalueInd]
              tableData.push(this.expressionPlusMeta1[k])
            }
            xvalueInd = xvalueInd + 1
          })
        }
        this.sampleData = tableData
      }
    }
  }
</script>
<style scoped></style>
