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
              v-model="diseaseName"
              prepend-icon="mdi-database"
              class="cohort"
              dense
              outlined
              hide-details
              :items="all_diseases"
              label="Cohort / Cell Type"
            />
            <protein-select
              :cohort-index="cohortIndex"
              data-layer="kinase"
              class="mt-4"
              @select-protein="updateKinase"
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
                  In this tab you can visualize Substrate phosphorylation scores to interrogate the activity of protein kinases based on the abundance of kinase substrate phosphorylation sites annotated in Phosphositeplus.
                </v-expansion-panel-content>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-header class="mb-0">
                  How to use
                </v-expansion-panel-header>
                <v-expansion-panel-content>
                  Use the dropdown menu to select a cohort. To visualize specific samples in the swarm plot, select samples in the table, pick a name in the field "Group" above the plot, adjust the color and click the blue edit button. Click the refresh button to reset the swarmplot. To export the plot, click the export button on the right handside above the plot.
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
import ProteinSelect from '@/components/partials/ProteinSelect'
import explorerComponent from './partials/scoresComponent.vue'

export default {
  name: 'KinaseComponent',
  components: {
    kinasescoreTable,
    SwarmPlot,
    explorerComponent,
    ProteinSelect
  },
  data: () => ({
    diseaseName: '',
    selectedData: [],
    singleswarmData: [],
    url: '',
    plotSelIds: [],
    proteinidentifier: '',
    loading: false,
    activeKinases: []
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
  methods: {
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
      const query = `${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/kinase/abundance/${this.activeKinases}/noimpute`
      this.url = query
      const singleSwarm = await axios.get(query)
      this.swarmShow = true
      this.singleswarmData = singleSwarm.data
    }

  }
}
</script>

<style>

</style>
