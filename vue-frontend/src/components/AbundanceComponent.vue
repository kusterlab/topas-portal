<template>
  <v-container fluid>
    <v-row class="grey lighten-3">
      <!-- Sidebar Section -->
      <v-col
        sm="12"
        md="3"
        lg="2"
      >
        <v-card
          flat
          class="mb-4"
        >
          <v-card-title tag="h1">
            Protein/p-site abundance
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
            <v-radio-group
              v-model="mode"
              label="Input type"
              hide-details
              class="mt-4"
              @change="updateId"
            >
              <v-radio
                v-for="(label, value) in radioOptions"
                :key="value"
                :label="label"
                :value="value"
              />
            </v-radio-group>
            <v-radio-group
              v-model="intensityUnit"
              label="Swarmplot intensity unit"
              hide-details
              class="mt-4"
              @change="updateId"
            >
              <v-radio
                label="Z-score"
                value="Z-score"
              />
              <v-radio
                label="Intensity"
                value="Intensity"
              />
            </v-radio-group>
          </v-card-text>
        </v-card>

        <v-card flat>
          <v-card-title tag="h1">
            Select {{ radioOptions[mode] }}
          </v-card-title>
          <v-card-text>
            <v-text-field
              v-if="mode === 'psite'"
              v-model="identifier"
              :label="identifierLabel"
              :placeholder="placeholder"
              hide-details
              dense
              @change="updateId"
            />
            <protein-select
              v-if="mode !== 'psite'"
              :cohort-index="cohortIndex"
              :data-layer="mode"
              @select-protein="updateProtein"
            />
            <v-checkbox
              v-if="mode !== 'psite'"
              v-model="showOncokbcnv"
              dense
              hide-details
              label="Load OncoKB annotations"
            />
            <v-textarea
              v-if="showOncokbcnv"
              v-model="cnvDescription"
              :readonly="true"
              outlined
              hide-details
              height="120"
            />
          </v-card-text>
        </v-card>
        <!-- Collapsible Help Box -->
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
                  In this tab you can visualize the normalized intensity and z-score of proteins and phosphopeptides.
                </v-expansion-panel-content>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-header class="mb-0">
                  How to use
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  Use the dropdown menu to select a cohort, then apply filters as required to stratify samples. To visualize specific samples in the swarm plot, select samples in the list, pick a name in the field "Group" above the plot, adjust the color and click the blue edit button. Click the circled arrow to come back to default. To export the plot, click the export button on the right handside above the plot.
                </v-expansion-panel-content>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Main Content Section -->
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
                md="7"
              >
                <expression-table
                  :data-source="zScoreHistogramData"
                  :selected-patient="selectedDotsInPlot"
                  @onRowSelect="updateSelectedRows"
                />
              </v-col>
              <v-col
                sm="12"
                md="5"
              >
                <v-skeleton-loader
                  :loading="loading"
                  height="200"
                  width="200"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <v-btn
                      class="ma-2"
                      color="primary"
                      @click="plotSelectedRows"
                    >
                      Render Selected samples
                    </v-btn>
                    <swarm-plot
                      v-if="swarmPlotData.length>0"
                      :swarm-data="swarmPlotData"
                      swarm-id="singleGene"
                      :swarm-sel-ids="swarmSelIds"
                      :swarm-title="identifier"
                      :swarm-title-prefix="swarmPrefix"
                      field-name="Sample name"
                      :draw-box-plot="true"
                      :field-values="swarmField"
                      @onDotClick="selectDot"
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-col>
            </v-row>
            <v-row class="mt-4">
              <v-col
                sm="12"
                md="4"
              >
                <histogram
                  id="numPep"
                  ref="histogram"
                  :full-chart-data="numPep"
                  :plot-histogram="true"
                  :plot-k-d-e="true"
                  :selected-lines="selectedLinesnumPep"
                  :min-height="minHeight"
                  :min-width="minWidth"
                  title=""
                  xlabel="num_peptides"
                  :margin="histogramMargin"
                  :min-dose="0"
                  :max-dose="100"
                  dose-unit="standard deviations"
                />
              </v-col>
              <v-col
                sm="12"
                md="4"
              >
                <histogram
                  id="ec50Histogram"
                  ref="histogram"
                  :full-chart-data="chartData"
                  :plot-histogram="true"
                  :plot-k-d-e="false"
                  :selected-lines="selectedLines"
                  :min-height="minHeight"
                  :min-width="minWidth"
                  title=""
                  :xlabel="swarmPrefix"
                  :margin="histogramMargin"
                  :min-dose="minChart"
                  :max-dose="maxChart"
                  dose-unit="standard deviations"
                />
              </v-col>
              <v-col
                sm="12"
                md="4"
              >
                <histogram
                  id="confidence"
                  ref="histogram"
                  :full-chart-data="confidenceScore"
                  :plot-histogram="true"
                  :plot-k-d-e="false"
                  :selected-lines="selectedLinesConfidence"
                  :min-height="minHeight"
                  :min-width="minWidth"
                  title=""
                  xlabel="Confidence_score"
                  :margin="histogramMargin"
                  :min-dose="-200"
                  :max-dose="200"
                  dose-unit="standard deviations"
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
import expressionTable from '@/components/tables/ExpressionTable'
import histogram from '@/components/plots/GenericHistogram'
import SwarmPlot from '@/components/plots/SwarmPlot'
import ProteinSelect from '@/components/partials/ProteinSelect.vue'
import CohortSelect from './partials/CohortSelect.vue'
import { DataType, IncludeRef } from '@/constants'
import { api } from '@/routes.ts'

export default {
  name: 'AbundanceComponent',
  components: {
    expressionTable,
    histogram,
    CohortSelect,
    SwarmPlot,
    ProteinSelect
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
    identifier: '',
    cohortIndex: 0,
    mode: DataType.FULL_PROTEOME,
    includeRefChannels: false,
    showOncokbcnv: false,
    swarmShow: false,
    radioOptions: {
      protein: 'Protein',
      psite: 'Phosphopeptide',
      fpkm: 'mRNA (FPKM)'
    },
    intensityUnit: 'Z-score',
    selectedDotsInPlot: '',
    cnvDescription: '',
    allProteins: [],
    swarmPlotData: [],
    swarmSelIds: [],
    zScoreHistogramData: [],
    histogramMargin: { top: 20, right: 10, bottom: 50, left: 70 },
    selectedLines: [],
    selectedLinesConfidence: [],
    selectedLinesnumPep: [],
    selectedData: [],
    swarmField: '',
    loading: false
  }),
  computed: {
    chartData () {
      const hData = this.swarmPlotData.filter(z => z[this.intensityUnit] !== 'n.d.')
      return hData.map(d => d[this.intensityUnit])
    },
    maxChart () {
      return this.intensityUnit === 'Z-score' ? 4 : 10
    },
    minChart () {
      return this.intensityUnit === 'Z-score' ? -4 : 5
    },
    numPep () {
      return this.swarmPlotData.map(d => d.num_pep)
    },
    confidenceScore () {
      const confData = this.swarmPlotData.filter(d => d.confidence_score !== 'n.d.')
      return confData.map(d => d.confidence_score)
    },
    identifierLabel () {
      if (this.mode === DataType.TRANSCRIPTOMICS) {
        return 'Gene name'
      } else {
        return 'Modified sequence'
      }
    },
    swarmPrefix () {
      return this.intensityUnit === 'Z-score' ? 'Z-Score' : 'log10 abundance'
    },
    placeholder () {
      if (this.mode === DataType.TRANSCRIPTOMICS) {
        return 'EGFR'
      } else {
        return '_AAAAAPApSED_'
      }
    }
  },
  watch: {
    showOncokbcnv: function () {
      this.getoncoKB(this.identifier)
    },
    cohortIndex: function () {
      this.updateId()
    },
    includeRefChannels: function () {
      this.updateId()
    }
  },
  mounted () {
    this.selectedData = []
    this.swarmSelIds = []
  },
  methods: {
    selectDot (value) {
      this.selectedDotsInPlot = value
    },
    updateProtein ({ dataSource, identifier }) {
      this.identifier = identifier
      this.updateId()
    },
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    updateId () {
      this.swarmShow = false
      if (this.identifier.length > 0) { // gene mode
        this.swarmPlotData = []
        this.swarmSelIds = []
        if (this.showOncokbcnv) {
          this.getoncoKB(this.identifier)
        }
        this.getExpression(this.mode, this.identifier)
      }
    },
    async getExpression (mode, key) {
      this.swarmShow = false
      this.loading = true
      this.zScoreHistogramData = []
      this.swarmPlotData = []
      this.swarmSelIds = []
      const includeRef = this.includeRefChannels ? IncludeRef.INCLUDE_REF : IncludeRef.EXCLUDE_REF
      const query = api.ABUNDANCE({ cohort_index: this.cohortIndex, level: mode, identifier: key, imputation: 'noimpute', include_ref: includeRef })
      this.zScoreHistogramData = query
      const response = await axios.get(query)
      this.swarmShow = true
      this.swarmField = this.intensityUnit
      // this.swarmPlotData = response.data.filter(element => element[this.intensityUnit] !== 'n.d.')
      this.swarmPlotData = response.data
      this.loading = false
    },
    async fetchOncoKB (gene, alterationType) {
      try {
        const query = api.ONCOKB_CNV({ identifier: gene, cnv_type: alterationType })
        const response = await axios.get(query)
        const effect = response.data?.mutationEffect?.description

        if (effect && effect.length > 0) {
          return effect
        } else if (effect === '') {
          return `no ${alterationType.toLowerCase()} information in OncoKB.`
        } else if (response.data?.status !== 200) {
          if (response.data?.status === 401) {
            return 'invalid OncoKB API token.'
          }
          return 'unable to connect to OncoKB.'
        } else {
          return `unable to retrieve ${alterationType.toLowerCase()} information.`
        }
      } catch (error) {
        return `error retrieving ${alterationType.toLowerCase()} information.`
      }
    },
    async getoncoKB (gene) {
      if (!gene || gene.length === 0) return

      const [amplification, deletion] = await Promise.all([
        this.fetchOncoKB(gene, 'AMPLIFICATION'),
        this.fetchOncoKB(gene, 'DELETION')
      ])

      this.cnvDescription = `${amplification}\n${deletion}`
    },
    plotSelectedRows () {
      this.swarmShow = true
      this.swarmField = this.intensityUnit
      this.swarmPlotData = this.selectedData
    },

    updateSelectedRows (selectedIds, selectedData) {
      // selectedData = selectedData.filter(element => element[this.intensityUnit] !== 'n.d.')
      this.selectedLines = []
      this.selectedLinesnumPep = []
      this.selectedLinesConfidence = []
      this.swarmSelIds = []
      selectedData.forEach((rowData) => {
        this.swarmSelIds.push(rowData.index) // selected indices on the swarm plot
        this.selectedLines.push({ color: 'black', value: rowData[this.intensityUnit], curveid: -1, dash: ('5, 5') })
        this.selectedLinesnumPep.push({ color: 'black', value: rowData.num_pep, curveid: -1, dash: ('5, 5') })
        this.selectedLinesConfidence.push({ color: 'black', value: rowData.confidence_score, curveid: -1, dash: ('5, 5') })
      })
      this.selectedData = selectedData
    }
  }
}
</script>
<style scoped>
  .scroll{
    overflow-x:scroll;
  }
 .sequence-gene{
      width: 600px;
      background-color: rgb(255, 255, 255);
}
</style>
