<template>
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
          Drug Scores
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="diseaseName"
            class="cohort"
            dense
            outlined
            hide-details
            :items="all_diseases"
            label="Cohort / Cell Type"
            @change="updatePatientDrugLists"
          />
          <v-radio-group
            v-model="inputType"
            label="Input type"
            hide-details
            @change="updateId"
          >
            <v-radio
              label="Compare patients (per drug)"
              value="per_drug"
            />
            <v-radio
              label="Compare drugs (per patient)"
              value="per_patient"
            />
          </v-radio-group>
          <v-autocomplete
            v-if="inputType == 'per_drug'"
            v-model="drugidentifier"
            :items="allDrugs"
            outlined
            dense
            label="Select Drug"
            class="mt-4"
            @change="updateId('drug')"
          />
          <v-autocomplete
            v-if="inputType == 'per_drug'"
            v-model="entityIdentifier"
            :items="allEntities"
            outlined
            dense
            chips
            small-chips
            label="Filter by entities"
            multiple
            @change="updateId('drug')"
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
              <drugscore-table
                :data-source="url"
                @onRowSelect="updateSelectedRows"
              />
            </v-col>
            <v-col
              sm="12"
              md="5"
              lg="5"
            >
              <swarm-plot
                v-if="swarmShow"
                :swarm-data="plotData"
                :swarm-title="titleIdentifier"
                swarm-id="drugscore"
                :swarm-sel-ids="selectedIds"
                swarm-title-prefix="Drug_scores"
                field-name="Sample name"
                :draw-box-plot="true"
                field-values="Drug_score"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
import axios from 'axios'
import { mapGetters, mapState } from 'vuex'
import DrugscoreTable from '@/components/tables/DrugscoreTable.vue'
import SwarmPlot from '@/components/plots/SwarmPlot'

export default {
  name: 'DrugscoreComponent',
  components: {
    DrugscoreTable,
    SwarmPlot
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
    drugidentifier: '',
    patientidentifier: '',
    titleIdentifier: '',
    diseaseName: 'sarcoma',
    inputType: 'per_drug',
    entityIdentifier: null,
    swarmShow: false,
    plotData: [],
    allEntities: [],
    url: '',
    allPatients: [],
    allDrugs: [],
    selectedIds: [],
    selectedData: [],
    place_holder: 'Imatinib',
    identifierLbl: 'Drug Name'
  }),
  mounted () {
    this.plotData = []
    this.selectedIds = []
    this.swarmSelIds = []
  },
  computed: {
    ...mapState({
      all_diseases: state => state.all_diseases
    }),
    ...mapGetters({
      hasData: 'hasData'
    })
  },
  methods: {
    updatePatientDrugLists () {
      this.getDrugsList()
      this.getPatientsList()
      this.getEntitiesList()
    },
    async getEntitiesList () {
      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/patients/${cohortIndex}/all_entities`)
      const entities = []
      response.data.forEach(element => {
        entities.push(element.Entity)
      })
      this.allEntities = entities
    },
    async getPatientsList () {
      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/drugscore/${cohortIndex}/patients_list`)
      const patients = []
      response.data.forEach(element => {
        patients.push(element.patients)
      })
      this.allPatients = patients
    },
    async getDrugsList () {
      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/drugscore/${cohortIndex}/drugs_list`)
      const drugs = []
      response.data.forEach(element => {
        drugs.push(element.Drug)
      })
      this.allDrugs = drugs
    },
    updateId (type) {
      this.swarmShow = false
      this.plotData = []
      this.selectedIds = []

      if (type === 'drug' && this.drugidentifier.length > 0) {
        this.titleIdentifier = this.drugidentifier
        this.getDrugScoresForDrug(this.drugidentifier)
        this.getPatientsList()
      }

      if (type === 'patient' && this.patientidentifier.length > 0) {
        this.titleIdentifier = this.patientidentifier
        this.getDrugScoresForPatient(this.patientidentifier)
      }
    },
    async getDrugScoresForDrug (key) {
      this.patientidentifier = ''
      this.plotData = []
      let entities = this.entityIdentifier
      if (!entities || entities.length === 0) {
        entities = 'all'
      }

      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      const query = `${process.env.VUE_APP_API_HOST}/drugscore/${cohortIndex}/drug/${key}/${entities}`
      this.url = query
      const response = await axios.get(query)
      this.swarmShow = true
      this.plotData = response.data
    },

    async getDrugScoresForPatient (key) {
      this.drugidentifier = ''
      this.plotData = []
      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      const query = `${process.env.VUE_APP_API_HOST}/drugscore/${cohortIndex}/patient/${key}`
      this.url = query
      const response = await axios.get(query)
      this.swarmShow = true
      this.plotData = response.data
    },

    updateSelectedRows (selectedIds, selectedData) {
      this.selectedIds = []
      selectedData.forEach((rowData) => {
        this.selectedIds.push(rowData.index) // selected indices on the swarm plot
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
