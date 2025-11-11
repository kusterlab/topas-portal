<template>
  <v-app>
    <explorer-component />
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
            TOPAS scores
          </v-card-title>
          <v-card-text>
            <cohort-select
              @select-cohort="updateCohort"
            />
            <topas-select
              class="mt-4"
              :cohort-index="activeCohortIndex"
              @select-topas="updateTopas"
            />
            <v-checkbox
              v-model="showTopasSubscore"
              label="Show TOPAS subscore plots"
              dense
              hide-details
              @change="getTopasData"
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
                  In this tab you can visualize the TOPAS scores and TOPAS z-scores to interrogate the activation of receptor tyrosine kinases based on protein expression, abundance of auto- and total phosphorylation and RTK substrate phosphorylation as annotated in Phosphositeplus.
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
                lg="7"
              >
                <topas-table
                  :data-source="topasData"
                  :selected-patient="selectedDotsInPlot"
                  @onRowSelect="updateSelectedRows"
                  @table-ready="loadSwarmplot"
                />
              </v-col>
              <v-col
                sm="12"
                md="5"
                lg="5"
              >
                <v-skeleton-loader
                  :loading="loading"
                  height="200"
                  width="200"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <swarm-plot
                      v-show="topasName"
                      :swarm-data="swarmPlotData"
                      :swarm-sel-ids="swarmSelIds"
                      swarm-id="singleTopas"
                      :swarm-title="topasName"
                      :swarm-title-prefix="swarmPrefix"
                      field-name="Sample name"
                      :draw-box-plot="true"
                      :field-values="swarmField"
                      @selectedCells="getSelectedCells"
                      @onDotClick="selectDot"
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        <v-card
          v-show="showTopasSubscore"
          flat
          class="mt-4"
        >
          <v-card-text>
            <multi-group-plot
              i-d="topasPlot"
              field-x="topas"
              field-y="score"
              title="sample"
              :plot-data="topasSubscoreData"
              :selected-patients="multiGroupPlotSelectedPatients"
              :selected-color="multiGroupPlotSelectedColor"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-app>
</template>

<script>
import axios from 'axios'
import CohortSelect from './partials/CohortSelect.vue'
import SwarmPlot from '@/components/plots/SwarmPlot'
import TopasTable from '@/components/tables/TopasTable'
import TopasSelect from '@/components/partials/TopasSelect'
import multiGroupPlot from '@/components/plots/MultiGroupPlot'
import ExplorerComponent from '@/components/partials/scoresComponent.vue'
import { api } from '@/routes.ts'

export default {
  name: 'TopasComponent',
  components: {
    TopasTable,
    SwarmPlot,
    CohortSelect,
    ExplorerComponent,
    TopasSelect,
    multiGroupPlot
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
    topasName: '',
    cohortIndex: 0,
    firstPatient: '',
    selectedDotsInPlot: '',
    topasType: '',
    fixedDomain: false,
    topasData: [],
    allTopass: [],
    swarmPlotData: [],
    topasSubscoreData: [],
    showTopasSubscore: false,
    swarmSelIds: [],
    loading: false,
    multiGroupPlotSelectedPatients: [],
    multiGroupPlotSelectedColor: null,
    swarmField: ''
  }),
  computed: {
    swarmPrefix () {
      return this.topasType === 'topas_score' ? 'TOPAS score' : 'TOPAS Z-score'
    },
    activeCohortIndex () {
      return this.cohortIndex
    }
  },
  watch: {
    topasType: function () {
      this.getTopasData()
    },
    activeCohortIndex: function () {
      this.getTopasData()
    }
  },
  methods: {
    selectDot (value) {
      this.selectedDotsInPlot = value
    },
    getSelectedCells (value) {
      const selectedPatients = []
      value.selectedPatiens.forEach(element => {
        selectedPatients.push(this.topasData[element]['Sample name'])
      })
      this.multiGroupPlotSelectedPatients = selectedPatients
      this.multiGroupPlotSelectedColor = value.colorCode
    },
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    loadSwarmplot () {
    },
    async getTopasData () {
      if (this.topasName.length === 0) return
      this.loading = true
      this.swarmPlotData = []
      this.swarmSelIds = []
      this.topasData = []
      const dataSource = api.TOPAS({ cohort_index: this.cohortIndex, topas_names: this.topasName, score_type: this.topasType })
      let response = await axios.get(dataSource)
      if (response.data.length > 0) {
        this.topasData = response.data
        this.swarmPlotData = response.data
        this.loading = false
        this.swarmField = 'Z-score'
        for (let i = 0; i < this.swarmPlotData.length; i++) {
          this.swarmPlotData[i].colorID = 'grey'
          this.swarmPlotData[i].sizeR = 2
        }
      }
      if (this.showTopasSubscore) {
        response = await axios.get(api.TOPAS_SUBSCORE({ cohort_index: this.cohortIndex, topasname: this.topasName }))
        this.topasSubscoreData = response.data
        this.multiGroupPlotSelectedPatients = []
      }
    },
    async updateSelectedRows (selectedIds, selectedData) {
      this.swarmSelIds = []
      if (selectedData.length > 0) {
        selectedData.forEach((rowData) => {
          this.swarmSelIds.push(rowData.index) // selected indices on the swarm plot
        })
      }
    },
    updateTopas ({ dataSource, identifier }) {
      this.topasType = dataSource
      this.topasName = identifier
      this.swarmField = dataSource
      this.getTopasData()
    }

  }
}
</script>

<style>

</style>
