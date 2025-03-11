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
            <v-select
              v-model="diseaseName"
              class="cohort"
              dense
              outlined
              hide-details
              prepend-icon="mdi-database"
              :items="all_diseases"
              label="Cohort / Cell Type"
              @change="getbasketData"
            />

            <basket-select
              :cohort-index="all_diseases.indexOf(diseaseName)"
              @select-basket="updateBasket"
            />
            <v-checkbox
              v-model="ShowSubBaskets"
              label="Show TOPAS Subscores"
              @change="getbasketData"
            />
            <plot-save-vue
              @status="changePlotSavestaus"
            />
          </v-card-text>
        </v-card>
        <!-- Collapsible Help Box -->
        <v-card
          elevation="2"
          class="pa-4 mt-4"
        >
          <v-expansion-panels>
            <v-expansion-panel>
              <v-expansion-panel-header>
                More info?
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <p class="text-body-2">
                  In this tab you can visualize the TOPAS scores and TOPAS z-scores to interrogate the activation of receptor tyrosine kinases based on protein expression, abundance of auto- and total phosphorylation and RTK substrate phosphorylation as annotated in Phosphositeplus. Use the dropdown menu to select a cohort, then apply filters as required to stratify samples. To visualize specific samples in the swarm plot, select samples in the list, pick a name in the field "Group" above the plot, adjust the color and click the blue edit button. Click the circled arrow to come back to default. To export the plot, click the export button on the right handside above the plot.
                </p>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card>
      </v-col>
      <v-col
        sm="12"
        md="9"
        lg="10"
      >
        <v-card flat>
          <v-card-text>
            <div class="collapsible-container">
              <v-row>
                <v-col
                  sm="12"
                  md="7"
                  lg="7"
                >
                  <basket-table
                    :data-source="basketData"
                    :selected-patient="selectedDotsInPlot"
                    @onRowSelect="updateSelectedRows"
                  >
                    >
                  </basket-table>
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
                        v-if="basketName"
                        :save-plot="savePlot"
                        :swarm-data="swarmPLotData"
                        :swarm-sel-ids="swarmSelIds"
                        swarm-id="singleBasket"
                        :swarm-title="basketName"
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
            </div>
            <div class="collapsible-container">
              <v-row>
                <v-card
                  plain
                  outlined
                >
                  <multi-group-plot
                    v-if="ShowSubBaskets"
                    :save-plot="savePlot"
                    i-d="basketPlot"
                    field-x="basket"
                    field-y="score"
                    title="sample"
                    :plot-data="subbasketData"
                    :selected-patients="multiGroupPlotSelectedPatients"
                    :selected-color="multiGroupPlotSelectedColor"
                  />
                </v-card>
              </v-row>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-app>
</template>

<script>
import axios from 'axios'
import { mapGetters, mapState } from 'vuex'
import SwarmPlot from '@/components/plots/SwarmPlot'
import BasketTable from '@/components/tables/BasketTable'
import BasketSelect from '@/components/partials/BasketSelect'
import multiGroupPlot from '@/components/plots/MultiGroupPlot'
import PlotSaveVue from './partials/PlotSave.vue'
import ExplorerComponent from '@/components/partials/scoresComponent.vue'

export default {
  name: 'BasketComponent',
  components: {
    BasketTable,
    PlotSaveVue,
    SwarmPlot,
    ExplorerComponent,
    BasketSelect,
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
    basketName: '',
    savePlot: false,
    diseaseName: '',
    firstPatient: '',
    selectedDotsInPlot: '',
    basketType: '',
    fixedDomain: false,
    basketData: [],
    allBaskets: [],
    swarmPLotData: [],
    subbasketData: [],
    ShowSubBaskets: false,
    swarmSelIds: [],
    loading: false,
    multiGroupPlotSelectedPatients: [],
    multiGroupPlotSelectedColor: null,
    swarmField: ''
  }),
  computed: {
    ...mapState({
      all_diseases: state => state.all_diseases
    }),
    ...mapGetters({
      hasData: 'hasData'
    }),
    swarmPrefix () {
      return this.basketType === 'basket_score' ? 'TOPAS score' : 'TOPAS Z-score'
    }
  },
  watch: {
    basketType: function () {
      this.getbasketData()
    }
  },
  methods: {
    selectDot (value) {
      this.selectedDotsInPlot = value
    },
    changePlotSavestaus ({ status }) {
      this.savePlot = status
    },
    getSelectedCells (value) {
      const selectedPatients = []
      value.selectedPatiens.forEach(element => {
        selectedPatients.push(this.basketData[element]['Sample name'])
      })
      this.multiGroupPlotSelectedPatients = selectedPatients
      this.multiGroupPlotSelectedColor = value.colorCode
    },

    async getbasketData () {
      if (this.basketName.length === 0) return
      this.loading = true
      this.swarmPLotData = []
      this.swarmSelIds = []
      this.basketData = []
      const bskid = this.basketName
      const bsktyp = this.basketType
      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      let response = await axios.get(`${process.env.VUE_APP_API_HOST}/basket/${cohortIndex}/${bskid}/${bsktyp}`)
      if (response.data.length > 0) {
        this.basketData = response.data
        this.swarmPLotData = response.data
        this.loading = false
        this.swarmField = 'Z-score'
        for (let i = 0; i < this.swarmPLotData.length; i++) {
          this.swarmPLotData[i].colorID = 'grey'
          this.swarmPLotData[i].sizeR = 2
        }
      }
      if (this.ShowSubBaskets) {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/basket/subbasket/${cohortIndex}/${bskid}`)
        this.subbasketData = response.data
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
    updateBasket ({ dataSource, identifier }) {
      this.basketType = dataSource
      this.basketName = identifier
      this.swarmField = dataSource
      this.getbasketData()
    }

  }
}
</script>

<style>

</style>
