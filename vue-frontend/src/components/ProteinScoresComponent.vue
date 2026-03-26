<template>
  <v-container class="bg-grey-lighten-3" fluid>
    <v-row>
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Protein Phosph. Scores </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <v-checkbox
              v-model="includeRefChannels"
              label="Include ref channels"
              density="comfortable"
              hide-details
            />
            <protein-select
              :cohort-index="cohortIndex"
              label-override="Phosphoprotein"
              data-layer="phospho_score"
              class="mt-4"
              @select-protein="updateProtein"
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
                  In this tab you can visualize the protein phosphorylation scores to interrogate
                  the relative phosphorylation of proteins based on the abundance of all protein
                  phosphorylation sites.
                </v-expansion-panel-text>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> How to use </v-expansion-panel-title>
                <v-expansion-panel-text>
                  You can select a protein- or sample-centric view. Use the dropdown menu to select
                  a cohort, then apply filters as required to stratify samples. To visualize
                  specific samples in the swarm plot, select samples in the list, pick a name in the
                  field "Group" above the plot, adjust the color and click the blue edit button.
                  Click the circled arrow to come back to default. To export the plot, click the
                  export button on the right handside above the plot.
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
                <proteinscore-table
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
                      v-show="proteinidentifier"
                      :swarm-data="plotData"
                      :save-plot="true"
                      swarm-id="proteinscore"
                      :swarm-sel-ids="plotSelIds"
                      :swarm-title="proteinidentifier"
                      swarm-title-prefix="Protein phosphorylation score "
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
  import { mapMutations } from 'vuex'

  import CohortSelect from './partials/CohortSelect.vue'
  import proteinscoreTable from '@/components/tables/ProteinScoresTable.vue'
  import SwarmPlot from '@/components/plots/SwarmPlot.vue'
  import ProteinSelect from '@/components/partials/ProteinSelect.vue'

  import { DataType, IncludeRef, ImputationMode } from '@/constants'
  import { api } from '@/routes.ts'

  export default {
    name: 'ProteinscoreComponent',
    components: {
      proteinscoreTable,
      SwarmPlot,
      CohortSelect,
      ProteinSelect
    },
    data: () => ({
      proteinidentifier: '',
      includeRefChannels: false,
      cohortIndex: 0,
      swarmShow: false,
      loading: false,
      plotData: [],
      url: '',
      lastDataSource: '',
      plotSelIds: [],
      selectedData: []
    }),
    computed: {
      includeRef() {
        return this.includeRefChannels ? IncludeRef.INCLUDE_REF : IncludeRef.EXCLUDE_REF
      }
    },
    watch: {
      cohortIndex: function () {
        this.updateId()
      },
      includeRefChannels: function () {
        this.updateId()
      },
      proteinidentifier: function () {
        this.updateId()
      }
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      updateCohort({ cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      updateProtein({ identifier }) {
        this.proteinidentifier = identifier
      },
      updateId() {
        this.swarmShow = false
        this.plotData = []
        this.plotSelIds = []
        if (this.proteinidentifier.length > 0) {
          this.loading = true
          this.url = api.ABUNDANCE({
            cohort_index: this.cohortIndex,
            level: DataType.PHOSPHO_SCORE,
            identifier: this.proteinidentifier,
            imputation: ImputationMode.NO_IMPUTE,
            include_ref: this.includeRef
          })
        }
      },
      async loadSwarmplot({ dataSource }) {
        if (dataSource.length === 0 || this.lastDataSource === dataSource) return

        this.lastDataSource = dataSource
        const response = await axios.get(dataSource)
        this.swarmShow = true
        this.plotData = response.data
        this.loading = false
      },
      updateSelectedRows(selectedIds, selectedData) {
        this.plotSelIds = []
        selectedData.forEach(rowData => {
          this.plotSelIds.push(rowData.index) // selected indices on the swarm plot
        })
        this.selectedData = selectedData
      }
    }
  }
</script>
<style scoped>
  .scroll {
    overflow-x: scroll;
  }
  .sequence-gene {
    width: 600px;
    background-color: rgb(255, 255, 255);
  }
</style>
