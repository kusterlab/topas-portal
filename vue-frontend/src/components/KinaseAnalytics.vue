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
            Substrate Phosph. scores
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="cohortName"
              prepend-icon="mdi-database"
              class="cohort"
              dense
              outlined
              hide-details
              :items="all_cohorts"
              label="Cohort"
            />
            <v-radio-group
              v-model="selectPatient"
              label="Filter patients"
              @change="getEntityOrPatientslist"
            >
              <v-radio
                label="All Patients"
                value="all"
              />
              <v-radio
                label="Select Entities"
                value="selectedEntities"
              />
            </v-radio-group>
            <v-checkbox
              v-if="selectPatient !== 'all' && selectPatient !== 'selectedPatients'"
              v-model="oneVsAll"
              label="One Entity Vs all"
              hide-details
            />
            <v-autocomplete
              v-if="selectPatient !== 'all'"
              v-model="activePatients"
              :items="allPatients"
              outlined
              dense
              chips
              small-chips
              :label="selectPatient"
              :multiple="!oneVsAll"
            />
            <v-radio-group
              v-model="selectKinase"
              label="Filter kinases"
              hide-details
            >
              <v-radio
                label="All Kinases"
                value="all"
              />
              <v-radio
                label="Select Kinases"
                value="selected"
              />
            </v-radio-group>
            <v-checkbox
              v-if="selectKinase !== 'all'"
              v-model="multiKinase"
              label="Multi Kinase selection"
              hide-details
            />
            <protein-select
              v-if="selectKinase !== 'all'"
              :cohort-index="cohortIndex"
              :multiple="multiKinase"
              data-layer="kinase"
              class="mt-4"
              @select-protein="updateKinase"
            />
            <v-radio-group
              v-model="plotType"
              class="mt-8"
              @change="react"
            >
              <v-radio
                label="Multi swarm plot"
                value="multiswarm"
              />
              <v-radio
                label="Heatmap"
                value="heatmap"
              />
              <v-radio
                label="Dendrogram"
                value="dendro"
              />
            </v-radio-group>
            <v-btn
              class="ma-2"
              color="primary"
              @click="react"
            >
              Plot
            </v-btn>
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
                  In this tab you can visualize Substrate phosphorylation scores to interrogate the activity of protein kinases based on the abundance of kinase substrate phosphorylation sites annotated in Phosphositeplus.
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
                <kinasescore-table
                  :data-source="url"
                  @onRowSelect="updateSelectedRows"
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
                      v-if="swarmShow"
                      :swarm-data="singleswarmData"
                      swarm-id="kinasescore"
                      :swarm-sel-ids="plotSelIds"
                      :swarm-title="proteinidentifier"
                      swarm-title-prefix="kinase_scores"
                      field-name="Sample name"
                      :draw-box-plot="true"
                      field-values="Z-score"
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-col>
            </v-row>
            <v-row>
              <v-card>
                <v-col
                  sm="12"
                  md="7"
                  lg="7"
                >
                  <multi-group-plot
                    v-if="swarmData.length > 0 && plotType==='multiswarm'"
                    i-d="kinasePlot"
                    field-x="Gene names"
                    field-y="score"
                    title="Sample"
                    :plot-data="swarmData"
                    :selected-patients="null"
                    selected-color="red"
                    :show-legends="showLegends"
                  />

                  <plotly
                    v-if="showPlot && (plotType==='heatmap' || plotType==='dendro' )"
                    :data="heatmapData.data"
                    :layout="heatmapData.layout"
                  />
                </v-col>
              </v-card>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-app>
</template>

<script>
import axios from 'axios'
import kinasescoreTable from '@/components/tables/KinasescoreTable.vue'
import SwarmPlot from '@/components/plots/SwarmPlot'
import { mapGetters, mapState } from 'vuex'
import { Plotly } from 'vue-plotly'
import multiGroupPlot from '@/components/plots/MultiGroupPlot'
import ProteinSelect from '@/components/partials/ProteinSelect'
import explorerComponent from './partials/scoresComponent.vue'

export default {
  name: 'KinaseComponent',
  components: {
    Plotly,
    kinasescoreTable,
    multiGroupPlot,
    SwarmPlot,
    explorerComponent,
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
    heatmapData: [],
    cohortName: '',
    selectedData: [],
    showLegends: true,
    oneVsAll: false,
    allPatients: [],
    singleswarmData: [],
    multiKinase: false,
    url: '',
    plotSelIds: [],
    proteinidentifier: '',
    loading: false,
    activeKinases: [],
    swarmData: [],
    swarmShow: false,
    activePatients: [],
    selectPatient: 'all',
    plotType: 'heatmap',
    selectKinase: 'selected',
    showPlot: false
  }),
  computed: {
    ...mapState({
      all_cohorts: state => state.all_cohorts
    }),
    ...mapGetters({
      hasData: 'hasData'
    }),
    cohortIndex () {
      return this.all_cohorts.indexOf(this.cohortName)
    }
  },
  methods: {
    async getEntityOrPatientslist () {
      this.activePatients = ''
      let response = null
      if (this.selectPatient === 'selectedPatients') {
        this.oneVsAll = false
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/annotation/${this.cohortIndex}/allpatients`)
      } else {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/patients/${this.cohortIndex}/all_entities`)
      }
      const patients = []
      response.data.forEach(element => {
        if (this.selectPatient === 'selectedPatients') {
          patients.push(element.result)
        } else {
          patients.push(element.Entity)
        }
      })
      this.allPatients = patients
    },
    updateKinase ({ dataSource, identifier }) {
      this.activeKinases = identifier
      this.react()
    },
    updateSelectedRows (selectedIds, selectedData) {
      this.plotSelIds = []
      selectedData.forEach((rowData) => {
        this.plotSelIds.push(rowData.index) // selected indices on the swarm plot
      })
      this.selectedData = selectedData
    },
    async react () {
      let activePatients = this.activePatients
      let activeKinases = this.activeKinases
      this.showPlot = false
      this.swarmShow = false
      this.loading = true
      let patientOrEntity = 'patient'
      const plotType = this.plotType
      const oneVsAll = this.oneVsAll ? 'one_vs_all' : 'none_vs_all'
      if (this.selectKinase === 'all') { activeKinases = 'all' } // including all kinases for the plot
      if (this.selectPatient === 'all') { activePatients = 'all' } else {
        if (this.selectPatient === 'selectedPatients') {
          this.showLegends = false
          patientOrEntity = 'patient'
        } else {
          this.showLegends = true
          patientOrEntity = 'entity'
        }
      }
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/kinasescores/${this.cohortIndex}/${patientOrEntity}/${activePatients}/${activeKinases}/${plotType}/${oneVsAll}`)
      this.heatmapData = response.data
      // swarm
      if ((!this.multiKinase) & (this.selectPatient === 'all') & (this.selectKinase === 'selected')) {
        const firstKinase = activeKinases
        this.proteinidentifier = firstKinase
        const query = `${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/kinase/abundance/${firstKinase}/noimpute`
        this.url = query
        const singleSwarm = await axios.get(query)
        this.swarmShow = true
        this.singleswarmData = singleSwarm.data
      } else {
        this.showPlot = true
        const swarm = await axios.get(`${process.env.VUE_APP_API_HOST}/kinasescores/${this.cohortIndex}/${patientOrEntity}/${activePatients}/${activeKinases}/swarm/${oneVsAll}`)
        this.swarmData = swarm.data
      }
      this.loading = false
    }

  }
}
</script>

<style>

</style>
