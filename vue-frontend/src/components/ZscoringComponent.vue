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
            Subcohort z-scores
          </v-card-title>
          <v-card-text>
            <cohort-select
              @select-cohort="updateCohort"
            />
            <sample-select
              class="mt-4"
              :cohort-index="cohortIndex"
              :show-table-select="true"
              :sample-ids="customGroup"
              @update-field="updateSampleGroup"
              @update-selection-method="updateSelectionMethodGroup"
            />
          </v-card-text>
        </v-card>
        <v-card
          flat
          class="mt-4"
        >
          <v-card-title
            tag="h1"
          >
            Select protein/p-peptide
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="mode"
              class="input_data_type mb-2"
              dense
              prepend-icon="mdi-filter"
              outlined
              hide-details
              :items="allInputDataTypes"
              label="Data Type"
            />
            <basket-select
              v-if="mode=== 'tupac'"
              :score-type="false"
              :cohort-index="cohortIndex"
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
            <v-btn
              :loading="loading"
              class="mt-4"
              color="primary"
              @click="getData"
            >
              Compute z-scores
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
                  In this tab you can calculate the z-scores for each group of patients based on the metadata and compare it with the z-scores across all patients.
                </v-expansion-panel-content>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-header class="mb-0">
                  How to use
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  Select a group of patients based on one of the metadata columns. Then select a protein or phosphopeptide of interest and press the "Compute z-scores" button compute the z-scores within that subcohort.
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
      <v-card flat v-show="selectionMethod === 'table'" class="mb-4">
        <v-card-text>
          <v-row>
            <v-col
              sm="12"
              md="12"
              lg="12"
            >
              <patient-select-table
                :cohort-index="cohortIndex"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
        <v-card
          plain
          outlined
        >
          <v-row>
            <v-col
              sm="12"
              md="6"
              lg="6"
            >
              <v-card-text>
                <zscore-table
                  :ref="componentKey"
                  :data-source="plotData"
                  @onRowSelect="updateSelectedRows"
                />
              </v-card-text>
            </v-col>
            <v-col
              sm="12"
              md="6"
              lg="6"
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
import CohortSelect from './partials/CohortSelect.vue'
import multiGroupPlot from '@/components/plots/MultiGroupPlot'
import proteinSelect from './partials/ProteinSelect.vue'
import SampleSelect from './partials/SampleSelect.vue'
import ZscoreTable from './tables/ZscoreTable.vue'
import PatientSelectTable from './tables/DifferentialmetaTable.vue'
import { DataType } from '@/constants'
import BasketSelect from '@/components/partials/BasketSelect'
import explorerComponent from './partials/scoresComponent.vue'

export default {
  name: 'ZscoreComponent',
  components: {
    multiGroupPlot,
    CohortSelect,
    ZscoreTable,
    PatientSelectTable,
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
    cohortIndex: 0,
    firstPatient: '',
    identifier: '',
    loading: false,
    mode: DataType.FULL_PROTEOME,
    fixedDomain: false,
    customGroup: [],
    selectionMethod: '',
    plotData: [],
    componentKey: 0,
    activeMeta: 'index',
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
  },
  watch: {
  },
  methods: {
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
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
    updateSelectionMethodGroup (selectionMethod) {
      this.selectionMethod = selectionMethod
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
      try {
        this.loading = true
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/zscore/${this.mode}/${this.cohortIndex}/${this.identifier}/${this.customGroup}/${this.activeMeta}`)
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
