<template>
  <v-container class="bg-grey-lighten-3" fluid>
    <v-row>
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Substrate Phosph. scores </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <sample-filter-select @update-sample-filter="updateSampleFilter" />
            <protein-select
              :cohort-index="cohortIndex"
              data-layer="kinase"
              class="mt-4"
              @select-protein="updateKinase"
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
                  In this tab you can visualize Substrate phosphorylation scores to interrogate the
                  activity of protein kinases based on the abundance of kinase substrate
                  phosphorylation sites annotated in Phosphositeplus.
                </v-expansion-panel-text>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> How to use </v-expansion-panel-title>
                <v-expansion-panel-text>
                  Use the dropdown menu to select a cohort. To visualize specific samples in the
                  swarm plot, select samples in the table, pick a name in the field "Group" above
                  the plot, adjust the color and click the blue edit button. Click the refresh
                  button to reset the swarmplot. To export the plot, click the export button on the
                  right handside above the plot.
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
              <v-col sm="12" md="7" lg="7">
                <kinasescore-table
                  :data-source="url"
                  @onRowSelect="updateSelectedRows"
                  @table-ready="loadSwarmplot"
                />
              </v-col>
              <v-col sm="12" md="5" lg="5">
                <v-skeleton-loader
                  :loading="loading"
                  height="200"
                  width="200"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <swarm-plot
                      v-show="activeKinase"
                      :swarm-data="singleswarmData"
                      swarm-id="kinasescore"
                      :swarm-sel-ids="plotSelIds"
                      :swarm-title="activeKinase"
                      swarm-title-prefix="kinase_scores"
                      field-name="Sample name"
                      :draw-box-plot="true"
                      field-values="Z-score"
                    />
                  </v-responsive>
                </v-skeleton-loader>
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
  import CohortSelect from './partials/CohortSelect.vue'
  import SampleFilterSelect from '@/components/partials/SampleFilterSelect.vue'
  import kinasescoreTable from '@/components/tables/KinasescoreTable.vue'
  import SwarmPlot from '@/components/plots/SwarmPlot.vue'
  import ProteinSelect from '@/components/partials/ProteinSelect.vue'
  import { DataType, SampleFilter, ImputationMode } from '@/constants'
  import { api } from '@/routes.ts'

  export default {
    name: 'KinaseComponent',
    components: {
      CohortSelect,
      SampleFilterSelect,
      kinasescoreTable,
      SwarmPlot,
      ProteinSelect
    },
    data: () => ({
      cohortIndex: 0,
      sampleFilter: SampleFilter.ONLY_PATIENTS,
      selectedData: [],
      singleswarmData: [],
      url: '',
      lastDataSource: '',
      plotSelIds: [],
      loading: false,
      activeKinase: ''
    }),
    watch: {
      cohortIndex: function () {
        this.getKinaseData()
      },
      sampleFilter: function () {
        this.getKinaseData()
      }
    },
    methods: {
      updateCohort({ cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      updateSampleFilter({ sampleFilter }) {
        this.sampleFilter = sampleFilter
      },
      updateKinase({ identifier }) {
        this.activeKinase = identifier
        this.getKinaseData()
      },
      getKinaseData() {
        this.loading = true
        this.url = api.ABUNDANCE({
          cohort_index: this.cohortIndex,
          level: DataType.KINASE_SCORE,
          identifier: this.activeKinase,
          imputation: ImputationMode.NO_IMPUTE,
          include_ref: this.sampleFilter
        })
      },
      updateSelectedRows(selectedIds, selectedData) {
        this.plotSelIds = []
        selectedData.forEach(rowData => {
          this.plotSelIds.push(rowData.index) // selected indices on the swarm plot
        })
        this.selectedData = selectedData
      },
      async loadSwarmplot({ dataSource }) {
        if (dataSource.length === 0 || this.lastDataSource === dataSource) return

        this.lastDataSource = dataSource
        const singleSwarm = await axios.get(dataSource)
        this.loading = false
        this.swarmShow = true
        this.singleswarmData = singleSwarm.data
      }
    }
  }
</script>

<style></style>
