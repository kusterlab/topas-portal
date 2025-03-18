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
          Protein/p-site overlap
        </v-card-title>
        <v-card-text>
          <cohort-select
            @select-cohort="updateCohort"
          />
          <v-select
            v-model="activeBatches"
            :items="allPossibleBatches"
            attach
            chips
            label="Batches/Patients"
            multiple
            @change="loading=false"
          />
          <v-radio-group v-model="phospho">
            <v-radio
              label="Full Proteome"
              color="red"
              value="fp"
            />
            <v-radio
              label="Phospho Proteome"
              color="blue"
              value="pp"
            />
          </v-radio-group>
          <v-radio-group
            v-model="modalityType"
            @change="getBatchlist"
          >
            <v-radio
              label="Batch comparison"
              color="red"
              value="batchcompare"
            />
            <v-radio
              label="Patient comparison"
              color="blue"
              value="patientcompare"
            />
          </v-radio-group>
          <v-btn
            class="ma-2"
            color="primary"
            :loading="loading"
            @click="getvennData"
          >
            Compare
          </v-btn>
        </v-card-text>
      </v-card>
      <v-card flat>
        <v-card-title
          tag="h1"
        >
          File Upload
        </v-card-title>
        <v-card-text>
          <v-tooltip top>
            <template #activator="{ on, attrs }">
              <input
                ref="docreader"
                type="file"
                v-bind="attrs"
                @change="readFile"
                v-on="on"
              >
            </template>
            <span>Upload a comma delimited file with two columns<br>
              - the first column is protein/peptides <br>
              - the second columns is the groups they belong to <br>
              - If a protein belongs to multi groups it should be in separate rows as below <br>
              EGFR, GroupA <br>
              EGFR, GroupB <br>
              - the columns should have headers with any names</span>
          </v-tooltip>
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
              <venn-plot
                :vennplot-data="vennData"
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
import CohortSelect from './partials/CohortSelect.vue'
import VennPlot from '@/components/plots/VennPlot.vue'

export default {
  name: 'VennComponent',
  components: {
    CohortSelect,
    VennPlot
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
    vennData: [],
    phospho: 'fp',
    allPossibleBatches: [],
    activeBatches: [],
    modalityType: 'batchcompare',
    loading: false

  }),
  computed: {
  },
  methods: {
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    async readFile () {
      // parsing a csv file for d3
      this.file = this.$refs.docreader.files[0]
      const csv = await this.file.text()
      const lines = csv.split('\n')
      const result = []
      // var headers=lines[0].split(",");
      const headers = ['sample', 'group']
      for (let i = 1; i < lines.length - 1; i++) {
        const obj = {}
        const currentline = lines[i].split(',')
        obj[headers[0]] = currentline[0]
        obj[headers[1]] = currentline[1]
        result.push(obj)
      }
      this.vennData = result
    },
    async getBatchlist () {
      this.activeBatches = ''
      let response = null
      if (this.modalityType === 'batchcompare') {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/annotation/${this.cohortIndex}/allbatch`)
      } else {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/annotation/${this.cohortIndex}/allpatients`)
      }
      const allPossibleBatches = []
      response.data.forEach(element => {
        allPossibleBatches.push(element.result)
      })
      this.allPossibleBatches = allPossibleBatches
    },
    async getvennData () {
      this.loading = true
      console.log(this.activeBatches)
      let querY = this.activeBatches[0]
      for (let i = 1; i < this.activeBatches.length; i++) {
        querY = querY + '_' + this.activeBatches[i]
      }

      const phospho = this.phospho
      const modalityType = this.modalityType
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/venn/${this.cohortIndex}/${modalityType}/${phospho}/${querY}`)
        this.vennData = response.data
        this.loading = false
      } catch (error) {
        this.loading = false
      }
    }

  }
}
</script>

<style>

.left {
 height: 100%;

}
.right {

  overflow-x: scroll; /* it works! */
}
</style>
