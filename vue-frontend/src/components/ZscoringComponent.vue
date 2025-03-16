<template>
  <v-app>
    <explorer-component />
    <v-row class="pa-4 grey lighten-3">
      <v-col
        sm="12"
        md="2"
        lg="2"
      >
        <v-card flat>
          <v-card-title
            tag="h1"
          >
            z-scores
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="diseaseName"
              prepend-icon="mdi-database"
              class="cohort"
              dense
              outlined
              hide-details
              :items="all_diseases"
              label="Cohort / Cell Type"
            />
            <v-select
              v-model="mode"
              class="input_data_type mb-2 mt-4"
              dense
              prepend-icon="mdi-filter"
              outlined
              hide-details
              :items="allInputDataTypes"
              label="Input Data Type"
              @change="updateHeatmap"
            />
            <basket-select
              v-if="mode=== 'tupac'"
              :score-type="false"
              :cohort-index="all_diseases.indexOf(diseaseName)"
              @select-basket="updateBasket"
            />
            <v-text-field
              v-if="mode === 'psite'"
              v-model="identifier"
              :label="identifierLabel"
              :placeholder="placeholder"
              hide-details
              dense
            />
            <protein-select
              v-if="mode === 'protein' || mode === 'kinase' || mode === 'phospho_score' "
              :cohort-index="cohortIndex"
              :data-layer="mode"
              @select-protein="updateProtein"
            />
            <sample-select
              :show-toggle="false"
              :cohort-index="cohortIndex"
              :sample-ids="customGroup"
              @update-field="updateSampleGroup"
              @update-meta="updateSelectionMethodGroup"
            />
            <v-btn
              :loading="loading"
              class="ma-2"
              color="primary"
              @click="getData"
            >
              calculate
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
                  In this tab you can calculate the z-scores for each group of patients based on the metadata and compare it with the precalculated z-scores across all patients.
                </v-expansion-panel-content>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-header class="mb-0">
                  How to use
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  Search and select a protein of interest, then apply filters as required to compute z-scores for a certain group of patients.
                </v-expansion-panel-content>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col
        sm="12"
        md="10"
        lg="10"
      >
        <v-card
          plain
          outlined
        >
          <v-row>
            <v-col
              sm="12"
              md="3"
              lg="3"
            >
              <v-card-text>
                <zscore-table
                  :ref="componentKey"
                  :data-source="plotData"
                  @onRowSelect="updateSelectedRows"
                >
                  >
                </zscore-table>
              </v-card-text>
            </v-col>
            <v-col
              sm="12"
              md="9"
              lg="9"
            >
              <v-card flat>
                <multi-group-plot
                  i-d="zscorePlot"
                  field-x="data_type"
                  field-y="zscores"
                  title="Sample name"
                  :plot-data="plotData"
                  :selected-patients="multiGroupPlotSelectedPatients"
                  :selected-color="multiGroupPlotSelectedColor"
                />
              </v-card>
            </v-col>
          </v-row>
        </v-card>
      </v-col>
    </v-row>
  </v-app>
</template>

<script>
import axios from 'axios'
import { mapGetters, mapState } from 'vuex'
import multiGroupPlot from '@/components/plots/MultiGroupPlot'
import proteinSelect from './partials/ProteinSelect.vue'
import SampleSelect from './partials/SampleSelect.vue'
import ZscoreTable from './tables/ZscoreTable.vue'
import { DataType } from '@/constants'
import BasketSelect from '@/components/partials/BasketSelect'
import explorerComponent from './partials/scoresComponent.vue'

export default {
  name: 'ZscoreComponent',
  components: {
    multiGroupPlot,
    ZscoreTable,
    SampleSelect,
    explorerComponent,
    proteinSelect,
    BasketSelect
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
    diseaseName: '',
    firstPatient: '',
    identifier: '',
    loading: false,
    mode: DataType.FULL_PROTEOME,
    fixedDomain: false,
    customGroup: [],
    selectionMethod: [],
    plotData: [],
    componentKey: 0,
    activeMeta: 'code_oncotree',
    multiGroupPlotSelectedPatients: [],
    multiGroupPlotSelectedColor: 'red',
    allInputDataTypes: [
      {
        text: 'TOPAS Scores',
        value: DataType.TUPAC_SCORE
      },
      {
        text: 'Full proteome',
        value: DataType.FULL_PROTEOME
      },
      {
        text: 'Psites',
        value: DataType.PHOSPHO_PROTEOME
      },
      {
        text: 'Substrate Phosphorylation scores',
        value: DataType.KINASE_SCORE
      },
      {
        text: 'Protein Phosphorylation scores',
        value: DataType.PHOSPHO_SCORE
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
    cohortIndex () {
      return this.all_diseases.indexOf(this.diseaseName)
    }
  },
  watch: {
  },
  methods: {
    updateProtein ({ dataSource, identifier }) {
      this.identifier = identifier
    },
    updateSampleGroup (filedsInterest) {
      this.customGroup = filedsInterest
      console.log(this.customGroup)
    },
    updateBasket ({ dataSource, identifier }) {
      this.identifier = identifier
    },
    updateSelectionMethodGroup (activeMeta) {
      this.activeMeta = activeMeta
    },
    async updateSelectedRows (selectedIds, selectedData) {
      const SelIds = []
      this.multiGroupPlotSelectedPatients = []
      if (selectedData.length > 0) {
        selectedData.forEach((rowData) => {
          this.multiGroupPlotSelectedColor = 'red'
          SelIds.push(rowData['Sample name']) // selected indices on the swarm plot
        })
      } else {
        this.multiGroupPlotSelectedPatients = null
      }
      this.multiGroupPlotSelectedPatients = SelIds
    },
    async getData () {
      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      const customGroup = this.customGroup
      const activeMeta = this.activeMeta
      const identifier = this.identifier
      const mode = this.mode
      try {
        this.loading = true
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/zscore/${mode}/${cohortIndex}/${identifier}/${customGroup}/${activeMeta}`)
        this.componentKey = this.componentKey + 1
        this.plotData = response.data
      } catch (error) {
        alert(`Error while loading cohort data: ${error.response.data}`)
      }
      this.loading = false
    }
  }
}
</script>

<style>

</style>
