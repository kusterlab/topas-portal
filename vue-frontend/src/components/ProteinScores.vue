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
            Protein Phosphorylation Scores
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
              @change="getPatientslist"
            />
            <v-radio-group
              v-model="inputType"
              label="Input type"
              hide-details
              @change="updateId"
            >
              <v-radio
                label="Compare patients (per phosphoprotein)"
                value="per_protein"
              />
              <v-radio
                label="Compare phosphoproteins (per patient)"
                value="per_patient"
              />
            </v-radio-group>
            <protein-select
              v-if="inputType == 'per_protein'"
              :cohort-index="cohortIndex"
              data-layer="phospho_score"
              class="mt-4"
              @select-protein="updateProtein"
            />
            <v-autocomplete
              v-if="inputType == 'per_patient'"
              v-model="patientidentifier"
              :items="allPatients"
              outlined
              dense
              label="Select Patient"
              class="mt-4"
              @change="updateId('patient')"
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
                More info
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <p class="text-body-2">
                  In this tab you can visualize distribution of Protein Phosphorylation scores for a single protein across all patients/samples.
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
import { mapGetters, mapState } from 'vuex'
import proteinscoreTable from '@/components/tables/ProteinscoreTable.vue'
import SwarmPlot from '@/components/plots/SwarmPlot'
import ProteinSelect from '@/components/partials/ProteinSelect'
import explorerComponent from './partials/scoresComponent.vue'
export default {
  name: 'ProteinscoreComponent',
  components: {
    proteinscoreTable,
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
    proteinidentifier: '',
    patientidentifier: '',
    diseaseName: 'sarcoma',
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
  mounted () {
    this.plotData = null
    this.plotSelIds = []
    this.swarmSelIds = []
  },
  computed: {
    ...mapState({
      all_diseases: state => state.all_diseases
    }),
    ...mapGetters({
      hasData: 'hasData'
    }),
    cohortIndex: function () {
      return this.all_diseases.indexOf(this.diseaseName)
    }
  },
  methods: {
    async getPatientslist () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/proteinscore/${this.cohortIndex}/patients_list`)
      this.allPatients = response.data
    },
    updateProtein ({ dataSource, identifier }) {
      this.proteinidentifier = identifier
      this.updateId('protein')
    },
    updateId (type) {
      this.swarmShow = false
      this.plotData = []
      this.plotSelIds = []
      if (type === 'protein' && this.proteinidentifier.length > 0) {
        this.getProteindata(this.proteinidentifier)
        this.getPatientslist()
      }

      if (type === 'patient' && this.patientidentifier.length > 0) {
        this.getpatientdata(this.patientidentifier)
      }
    },
    async getProteindata (key) {
      this.loading = true
      this.patientidentifier = ''
      this.plotData = []
      const query = `${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/phospho_score/abundance/${key}/noimpute`
      this.url = query
      const response = await axios.get(query)
      this.swarmShow = true
      this.plotData = response.data
      this.loading = false
    },

    async getpatientdata (key) {
      this.proteinidentifier = ''
      this.plotData = []
      const query = `${process.env.VUE_APP_API_HOST}/proteinscore/${this.cohortIndex}/patient/${key}`
      this.url = query
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
