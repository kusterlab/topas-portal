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
              @update-group="updateSampleGroup"
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
        <v-card
          v-show="selectionMethod === 'table'"
          flat
          class="mb-4"
        >
          <v-card-text>
            <v-row>
              <v-col
                sm="12"
                md="12"
                lg="12"
              >
                <patient-select-table
                  :cohort-index="cohortIndex"
                  @onRowSelect="updateSelectedSamples"
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
                  :data-source="zscoreTableUrl"
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
                <swarm-plot
                  v-if="swarmPlotData.length>0"
                  :swarm-data="swarmPlotData"
                  swarm-id="singleGene"
                  :swarm-sel-ids="swarmSelIds"
                  :swarm-title="identifier"
                  swarm-title-prefix="z-score"
                  field-name="Sample name"
                  :draw-box-plot="true"
                  field-values="subcohort_zscore"
                  @onDotClick="selectDot"
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
import { mapMutations } from 'vuex'

import CohortSelect from './partials/CohortSelect.vue'
import SwarmPlot from '@/components/plots/SwarmPlot'
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
    SwarmPlot,
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
    zscoreTableUrl: '',
    swarmPlotData: [],
    swarmSelIds: [],
    selectedDotsInPlot: [],
    componentKey: 0,
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
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    updateProtein ({ dataSource, identifier }) {
      this.identifier = identifier
    },
    updateSampleGroup (selectedPatients) {
      this.customGroup = selectedPatients
    },
    updateBasket ({ dataSource, identifier }) {
      this.identifier = identifier
    },
    selectDot (value) {
      this.selectedDotsInPlot = value
    },
    async updateSelectedSamples (selectedIds, selectedData) {
      const selectedPatients = []
      selectedData.forEach(element => {
        selectedPatients.push(element['Sample name'])
      })
      this.customGroup = selectedPatients
      this.getData()
    },
    updateSelectionMethodGroup (selectionMethod) {
      this.selectionMethod = selectionMethod
    },
    async updateSelectedRows (selectedIds, selectedData) {
      const selIds = []
      this.swarmSelIds = []
      if (selectedData.length > 0) {
        selectedData.forEach((rowData) => {
          this.multiGroupPlotSelectedColor = 'red'
          selIds.push(rowData.index) // selected indices on the swarm plot
        })
      } else {
        this.swarmSelIds = null
      }
      this.swarmSelIds = selIds
    },
    async getData () {
      try {
        if (this.identifier.length === 0) {
          this.addNotification({
            color: 'warning',
            message: 'Please select a protein/p-peptide in the left menu.'
          })
          return
        }
        if (this.customGroup.length === 0) {
          this.addNotification({
            color: 'warning',
            message: 'Please select samples for your subcohort in the left menu.'
          })
          return
        }
        this.loading = true
        this.zscoreTableUrl = `${process.env.VUE_APP_API_HOST}/zscore/${this.mode}/${this.cohortIndex}/${this.identifier}/${this.customGroup}`
        const response = await axios.get(this.zscoreTableUrl)
        this.componentKey = this.componentKey + 1
        this.swarmPlotData = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `Error while loading cohort data: ${error.response.data}`
        })
      }
      this.loading = false
    }
  }
}
</script>
