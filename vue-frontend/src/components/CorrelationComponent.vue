<template>
  <v-row class="pa-4 grey lighten-3">
    <v-col
      sm="12"
      md="3"
      lg="2"
    >
      <v-card flat>
        <v-card-title
          tag="h1"
        >
          Correlations
        </v-card-title>
        <v-card-text>
          <cohort-select
            @select-cohort="updateCohort"
          />
          <subcohort-select
            class="mt-4"
            :cohort-index="cohortIndex"
            :sample-ids="customGroup"
            @update-group="updateSampleGroup"
            @update-selection-method="updateSelectionMethodGroup"
          />
          <v-radio-group
            v-model="intensityUnit"
            class="mt-4"
            label="Intensity unit"
            hide-details
          >
            <v-radio
              label="Z-scores"
              value="z_scored"
            />
            <v-radio
              label="Intensity"
              value="intensity"
            />
          </v-radio-group>
        </v-card-text>
      </v-card>
      <v-card
        flat
        class="mt-4"
      >
        <v-card-title
          tag="h1"
        >
          Select correlation inputs
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="correlationInputType"
            prepend-icon="mdi-filter"
            :items="dataTypes"
            label="Input type"
            hide-details
            outlined
            dense
            @change="jsonUrl = ''"
          />
          <v-text-field
            v-if="correlationInputType === 'psite'"
            v-model="identifier1"
            :label="identifierLabel"
            class="mt-4"
            :placeholder="placeholder"
          />
          <basket-select
            v-if="correlationInputType === 'topas'"
            class="mt-4"
            :cohort-index="cohortIndex"
            @select-basket="updateIdentifier"
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
            hide-details
            dense
            outlined
            class="mt-4"
            @change="jsonUrl = ''"
          />

          <v-btn
            class="mt-4"
            color="primary"
            :loading="loading"
            @click="loadCorrelation"
          >
            Run Analysis
          </v-btn>
        </v-card-text>
      </v-card>
      <v-card
        flat
        class="mt-4"
      >
        <v-card-title>Help</v-card-title>
        <v-card-text>
          <v-expansion-panels>
            <v-expansion-panel>
              <v-expansion-panel-header class="mb-0">
                Tab info
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                In this tab you can visualize correlations between proteins, phosphopeptides, mRNA-transcripts, TOPAS scores, protein phosphorylation scores and substrate phosphorylation scores.
              </v-expansion-panel-content>
            </v-expansion-panel>
            <v-expansion-panel>
              <v-expansion-panel-header class="mb-0">
                How to use
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                To visualize the correlation for specific correlation partners, select one item in the upper table. In the lower table you can select specific samples to highlight them in the correlation plot. You can also click on individual data points in the correlation plot to display the corresponding sample. To remove samples where one correlation partner has not been detected/scored, uncheck the "Impute NA on plot" and click "Run analysis" again. You can also show a density distribution by checking the box next to "Show Density Distribution" and clicking on "Run analysis" again. To export plots, click the export button on the right handside above the plot.
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
      </v-card>
    </v-col>

    <v-col
      sm="12"
      md="9"
      lg="10"
    >
      <v-card flat>
        <v-card-text>
          <v-row>
            <v-col
              sm="12"
              md="8"
              lg="8"
            >
              <correlation-table
                :data-source="jsonUrl"
                :correlation-input-type="correlationInputType"
                :correlation-type="correlationType"
                @onRowSelect="updateSelectedRowsCorrelation"
              />
            </v-col>
            <v-col
              sm="12"
              md="4"
              lg="4"
            >
              <scatter-plot
                v-if="jsonUrl !== ''"
                id="correlationPlot"
                :identifier1="identifier1"
                :save-plot="true"
                add-trendlinte="true"
                :identifier2="identifier2"
                :remove-owncolor="false"
                :omics-type-x="correlationInputType.replace('topas','TOPAS score')"
                :omics-type-y="correlationType.replace('topas','TOPAS score')"
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
                hide-details
                dense
                label="Impute NA on Plot"
                @change="fetchExpressionData"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
      <v-card
        class="mt-4"
        flat
      >
        <v-card-text>
          <v-row>
            <v-col
              sm="12"
              md="8"
              lg="8"
            >
              <sample-table
                :key="componentKey"
                :data-source="sampleData"
                :selected-patient="selectedDotsInPlot"
                :x-axis="xaxisTable"
                :y-axis="yaxisTable"
                @onRowSelect="updateSelectedRowsSample"
              />
            </v-col>
            <v-col
              sm="12"
              md="4"
              lg="4"
            >
              <v-checkbox
                v-model="Showdensity"
                dense
                label="Show Density Distribution"
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
</template>

<script>
import axios from 'axios'
import { mapGetters, mapState } from 'vuex'
import correlationTable from '@/components/tables/CorrelationTable'
import CohortSelect from './partials/CohortSelect.vue'
import SubcohortSelect from './partials/SubcohortSelect.vue'
import sampleTable from '@/components/tables/CorrelationTableSamples'
import scatterPlot from '@/components/plots/ScatterPlot'
import basketSelect from '@/components/partials/BasketSelect'
import ProteinSelect from '@/components/partials/ProteinSelect'
import densityPlot from '@/components/plots/BarhistPlot'
import { DataType } from '@/constants'

export default {
  name: 'CorrelationComponent',
  components: {
    correlationTable,
    sampleTable,
    densityPlot,
    scatterPlot,
    basketSelect,
    ProteinSelect,
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
    intensityUnit: 'z_scored',
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
    allBaskets: [],
    expressionPlusMeta1: [],
    expressionPlusMeta2: [],
    densityData: [],
    Showdensity: false,
    densityType: 'All genes',
    identifier2: '',
    correlationInputType: DataType.FULL_PROTEOME,
    correlationType: DataType.FULL_PROTEOME,
    basketType: 'basket_score',
    expressionData2: [],
    chartData: [],
    jsonUrl: '',
    sampleData: [],
    response: [],
    selectedSamples: [],
    selectedDotsInPlot: '',
    plotScoreType: 'Z-score',
    dataTypes: [
      {
        text: 'Proteins',
        value: DataType.FULL_PROTEOME
      },
      {
        text: 'Phosphopeptides',
        value: DataType.PHOSPHO_PROTEOME
      },
      {
        text: 'Transcripts (FPKM)',
        value: DataType.TRANSCRIPTOMICS
      },
      {
        text: 'TOPAS scores',
        value: DataType.TOPAS_SCORE
      },
      // {
      //  text: 'Important Phosphorylation',
      //  value: 'important_phosphorylation'
      // },
      {
        text: 'Protein Poshphorylation scores',
        value: DataType.PHOSPHO_SCORE
      },
      {
        text: 'Substrate Phosphorylation scores',
        value: DataType.KINASE_SCORE
      }
    ]

  }),
  computed: {
    ...mapState({
      all_diseases: state => state.all_diseases
    }),
    ...mapGetters({
      hasData: 'hasData'
    }),
    identifierLabel () {
      if (this.correlationInputType === DataType.PHOSPHO_PROTEOME) {
        return 'Modified sequence'
      } else {
        return 'Gene name'
      }
    },
    placeholder () {
      if (this.correlationInputType === DataType.PHOSPHO_PROTEOME) {
        return '_AAAAAPApSED_'
      } else {
        return 'EGFR'
      }
    }
  },
  watch: {
    intensityUnit () {
      this.plotScoreType = (this.intensityUnit === 'z_scored') ? 'Z-score' : 'Intensity'
    }
  },
  methods: {
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    updateIdentifier ({ dataSource, identifier }) {
      this.identifier1 = identifier
      this.basketType = dataSource
    },
    loadCorrelation () {
      this.loading = true
      this.sampleData = []
      if (this.identifier1.length > 0) {
        this.getCorrelation(this.correlationType, this.correlationInputType, this.identifier1)
        this.fetchExpressionData(1)
        this.fetchDensityData()
      }
      this.loading = false
    },

    updateSampleGroup (sampleIdList) {
      this.customGroup = sampleIdList
    },

    updateSelectionMethodGroup (selectionMethod) {
      this.selectionMethod = selectionMethod
    },

    async fetchDensityData () {
      // for histogram
      if (this.Showdensity) {
        let url = ''
        if (this.correlationInputType === 'fpkm') {
          url = `${process.env.VUE_APP_API_HOST}/density/fpkm/${this.identifier1}/intensity`
        } else {
          url = `${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/density/protein/${this.identifier1}/intensity`
        }
        const response = await axios.get(url)
        this.histPlottitleVariables = [{ name: 'All intensities', color: 'blue' }, { name: this.identifier1, color: 'red' }]
        this.densityData = response.data
      }
    },

    async fetchExpressionData (identifierNumber) {
      const key = (identifierNumber === 1) ? this.identifier1 : this.identifier2
      if (!key) return
      this.labelX = this.plotScoreType
      this.labelY = this.plotScoreType
      const modality = (identifierNumber === 1) ? this.correlationInputType : this.correlationType
      let url = ''
      if (modality === DataType.TOPAS_IMPORTANT_PHOSPHO) {
        url = `${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/important_phospho/${key}`
        this.yaxisTable = 'ImportantPhosphorylation'
      } else if (modality === DataType.TOPAS_SCORE) {
        this.xaxisTable = 'TOPAS Scores'
        this.yaxisTable = 'TOPAS Scores'
        this.labelX = ''
        this.labelY = ''
        identifierNumber === 1 ? this.labelX = this.basketType : this.labelY = this.basketType
        url = `${process.env.VUE_APP_API_HOST}/basket/${this.cohortIndex}/${key}/${this.basketType}`
      } else {
        const imputeString = this.doImpute ? 'impute' : 'noimpute'
        url = `${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/${modality}/abundance/${key}/${imputeString}`
      }
      const response = await axios.get(url)
      if (response.data && response.data.length > 0) {
        response.data.forEach(element => { element.yValue = element[this.plotScoreType] })
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

    makeLimited (obj, selectedNames) {
      const result = []
      obj.forEach(element => {
        for (let i = 0; i < selectedNames.length; i++) {
          if (selectedNames[i] === element['Sample name']) {
            result.push(element)
          }
        }
      })
      return (result)
    },

    getCorrelation (level, inputLevel, key) {
      if (this.cohortIndex >= 0) {
        const customGroup = this.allPatients === 'cohort' ? 'all' : this.customGroup
        this.jsonUrl = `${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/${inputLevel}/correlation/${level}/${key}/${this.intensityUnit}/${customGroup}`
      }
    },
    updateSelectedRowsSample (selectedIds, selectedData) {
      const selectedPatients = []
      selectedData.forEach(element => {
        selectedPatients.push(element['Sample name'])
      })
      // this.forceRerender()
      this.selectedSamples = selectedPatients
    },

    selectDot (selectedDot) {
      this.selectedDotsInPlot = selectedDot
    },

    async updateSelectedRowsCorrelation (selectedIds, selectedData) {
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
          if (this.expressionPlusMeta1[k]['Sample name'] === element && this.expressionPlusMeta1[k][this.plotScoreType] !== 'n.d.') {
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
<style scoped>

</style>
