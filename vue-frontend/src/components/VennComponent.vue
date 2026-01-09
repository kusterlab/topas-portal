<template>
  <v-container fluid>
    <v-row class="pa-4 bg-grey-lighten-3">
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Protein/p-site overlap </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <v-btn-toggle
              v-model="dataType"
              class="mt-4"
              density="default"
              @update:model-value="getvennData"
            >
              <v-btn v-for="option in allInputDataTypes" :key="option.value" :value="option.value">
                {{ option.text }}
              </v-btn>
            </v-btn-toggle>
            <v-btn-toggle
              v-model="modalityType"
              density="default"
              hide-details
              @update:model-value="getBatchlist"
            >
              <v-btn value="batchcompare"> Batches </v-btn>
              <v-btn value="patientcompare"> Patients </v-btn>
            </v-btn-toggle>
            <v-select
              v-model="activeBatches"
              :items="allPossibleBatches"
              variant="outlined"
              small-chips
              density="default"
              hide-details
              clearable
              label="Batches/Patients"
              multiple
              @update:model-value="loading = false"
            />
            <v-btn class="mt-2 mb-0" color="primary" :loading="loading" @click="getvennData">
              Plot venn diagram
            </v-btn>
          </v-card-text>
        </v-card>
        <v-card variant="flat" class="mt-4">
          <v-card-title tag="h1"> Custom input </v-card-title>
          <v-card-text>
            <v-tooltip top>
              <template #activator="{ on, attrs }">
                <input v-bind="attrs" ref="docreader" type="file" @change="readFile" v-on="on" />
              </template>
              <span
                >Upload a comma delimited file with two columns<br />
                - a header row with column names: 'item' and 'group'<br />
                - the first column is protein/peptides <br />
                - the second columns is the group they belong to <br />
                - If a protein belongs to multiple groups it should be in separate rows, e.g.:
                <br />
                EGFR, GroupA <br />
                EGFR, GroupB <br />
              </span>
            </v-tooltip>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col sm="12" md="9" lg="10">
        <v-card variant="flat">
          <v-card-text>
            <venn-plot :vennplot-data="vennData" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import axios from 'axios'
  import CohortSelect from './partials/CohortSelect.vue'
  import VennPlot from '@/components/plots/VennPlot.vue'
  import { DataType } from '@/constants'
  import { api } from '@/routes.ts'

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
      dataType: DataType.FULL_PROTEOME,
      allPossibleBatches: [],
      activeBatches: [],
      modalityType: 'batchcompare',
      loading: false,
      allInputDataTypes: [
        {
          title: 'Proteins',
          value: DataType.FULL_PROTEOME
        },
        {
          title: 'P-peptides',
          value: DataType.PHOSPHO_PROTEOME
        }
      ]
    }),
    computed: {},
    watch: {},
    mounted() {
      this.getBatchlist()
    },
    methods: {
      updateCohort({ dataSource, cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      async readFile() {
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
      async getBatchlist() {
        this.activeBatches = ''
        let response = null
        if (this.modalityType === 'batchcompare') {
          response = await axios.get(
            api.ANNOTATION_MODALITY({ cohort_index: this.cohortIndex, modality: 'allbatch' })
          )
        } else {
          response = await axios.get(
            api.ANNOTATION_MODALITY({ cohort_index: this.cohortIndex, modality: 'allpatients' })
          )
        }
        const allPossibleBatches = []
        response.data.forEach(element => {
          allPossibleBatches.push(element.result)
        })
        this.allPossibleBatches = allPossibleBatches
      },
      async getvennData() {
        this.loading = true
        let query = this.activeBatches[0]
        for (let i = 1; i < this.activeBatches.length; i++) {
          query = query + ';' + this.activeBatches[i]
        }
        try {
          let response = null
          if (this.modalityType === 'batchcompare') {
            response = await axios.get(
              api.VENN_BATCH_COMPARE({
                cohort_index: this.cohortIndex,
                level: this.dataType,
                batchlists: query
              })
            )
          } else {
            response = await axios.get(
              api.VENN_PATIENT_COMPARE({
                cohort_index: this.cohortIndex,
                level: this.dataType,
                patients: query
              })
            )
          }
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
