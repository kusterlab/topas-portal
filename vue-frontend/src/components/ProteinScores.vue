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
            Protein Phosph. Scores
          </v-card-title>
          <v-card-text>
            <cohort-select
              @select-cohort="updateCohort"
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
                  In this tab you can visualize the protein phosphorylation scores to interrogate the relative phosphorylation of proteins based on the abundance of all protein phosphorylation sites.
                </v-expansion-panel-content>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-header class="mb-0">
                  How to use
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  You can select a protein- or sample-centric view. Use the dropdown menu to select a cohort, then apply filters as required to stratify samples. To visualize specific samples in the swarm plot, select samples in the list, pick a name in the field "Group" above the plot, adjust the color and click the blue edit button. Click the circled arrow to come back to default. To export the plot, click the export button on the right handside above the plot.
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
                <proteinscore-table
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
                      v-show="plotData"
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
  </v-app>
</template>
<script>
import axios from 'axios'
import { mapMutations } from 'vuex'

import CohortSelect from './partials/CohortSelect.vue'
import proteinscoreTable from '@/components/tables/ProteinscoreTable.vue'
import SwarmPlot from '@/components/plots/SwarmPlot'
import ProteinSelect from '@/components/partials/ProteinSelect'
import explorerComponent from './partials/scoresComponent.vue'

import { DataType, IncludeRef } from '@/constants'
import { api } from '@/routes.ts'

export default {
  name: 'ProteinscoreComponent',
  components: {
    proteinscoreTable,
    SwarmPlot,
    CohortSelect,
    explorerComponent,
    ProteinSelect
  },
  data: () => ({
    proteinidentifier: '',
    patientidentifier: '',
    cohortIndex: 0,
    inputType: 'per_protein',
    swarmShow: false,
    loading: false,
    plotData: [],
    url: '',
    allPatients: [],
    plotSelIds: [],
    selectedData: [],
    place_holder: 'Imatinib',
    identifierLbl: 'Protein Name'
  }),
  computed: {
    activeCohortIndex () {
      return this.cohortIndex
    }
  },
  watch: {
    activeCohortIndex: function () {
      this.getPatientslist()
    }
  },
  mounted () {
    this.plotData = null
    this.plotSelIds = []
    this.swarmSelIds = []
  },
  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
      this.updateProtein()
    },
    async getPatientslist () {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/proteinscore/${this.cohortIndex}/patients_list`)
        this.allPatients = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `Error: unable to load patients list for this cohort ${error}`
        })
        this.allPatients = []
      }
    },
    updateProtein ({ dataSource, identifier }) {
      this.proteinidentifier = identifier
      this.updateId('protein')
    },
    updateId (type) {
      this.swarmShow = false
      this.plotData = []
      this.plotSelIds = []
      if (this.proteinidentifier.length > 0) {
        this.getProteindata(this.proteinidentifier)
      }
    },
    async getProteindata (key) {
      this.loading = true
      this.patientidentifier = ''
      this.plotData = []
      const query = api.ABUNDANCE({ cohort_index: this.cohortIndex, level: DataType.PHOSPHO_SCORE, identifier: key, imputation: 'noimpute', include_ref: IncludeRef.EXCLUDE_REF })
      this.url = query
      const response = await axios.get(query)
      this.swarmShow = true
      this.plotData = response.data
      this.loading = false
    },
    updateSelectedRows (selectedIds, selectedData) {
      this.plotSelIds = []
      selectedData.forEach((rowData) => {
        this.plotSelIds.push(rowData.index) // selected indices on the swarm plot
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
