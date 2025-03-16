<template>
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
          Differential Expression
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="diseaseName"
            class="cohort"
            prepend-icon="mdi-database"
            dense
            outlined
            hide-details
            :items="all_diseases"
            label="Cohort"
          />

          <p class="mt-4 mb-2">
            Group1
          </p>
          <sample-select
            :cohort-index="cohortIndex"
            prepend-icon="mdi-account"
            :sample-ids="customGroup1"
            @update-group="updateSampleGroup1"
            @update-selection-method="updateSelectionMethodGroup1"
          />

          <p class="mt-4 mb-2 d-inline-flex">
            Group2
          </p>
          <v-checkbox
            v-model="secondGroup"
            hide-details
            dense
            class="d-inline-flex ml-2 mt-0"
            label="All - Group1"
          />
          <sample-select
            v-if="!secondGroup"
            :cohort-index="cohortIndex"
            :sample-ids="customGroup2"
            @update-group="updateSampleGroup2"
            @update-selection-method="updateSelectionMethodGroup2"
          />

          <v-select
            v-model="modality"
            class="input_data_type mb-2 mt-4"
            dense
            outlined
            prepend-icon="mdi-filter"
            hide-details
            :items="allInputDataTypes"
            label="Input Data Type"
            @change="updateHeatmap"
          />
          <v-select
            v-model="proteinType"
            class="input_data_type mb-2 mt-4"
            prepend-icon="mdi-palette"
            dense
            outlined
            hide-details
            :items="allProtienTypes"
            label="Category"
            @change="updateProteinType"
          />
          <v-radio-group
            v-model="yAxistype"
          >
            <v-radio
              label="Multiple testing correction (BH)"
              color="red"
              value="fdr"
            />
            <v-radio
              label="No Multiple testing correction"
              color="blue"
              value="p_values"
            />
          </v-radio-group>

          <v-btn
            class="ma-2"
            color="primary"
            :loading="loading"
            @click="doTest"
          >
            Perform Analysis
          </v-btn>
        </v-card-text>
      </v-card>
    </v-col>
    <v-col
      sm="12"
      md="8"
      lg="6"
    >
      <v-card flat>
        <v-card-text>
          <v-row>
            <v-col
              v-show="selectionMethod1 === 'table'"
              sm="8"
              md="6"
              lg="4"
            >
              <h2>Group1</h2>
              <patient-table
                :cohort-index="cohortIndex"
                @onRowSelect="updatemetaSelectedRows1"
              />
            </v-col>
            <v-col
              v-show="selectionMethod2 === 'table'"
              sm="8"
              md="6"
              lg="4"
            >
              <h2>Group2</h2>
              <patient-table
                :cohort-index="cohortIndex"
                @onRowSelect="updatemetaSelectedRows2"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col
              sm="8"
              md="6"
              lg="4"
            >
              <statistic-table
                :data-source="statisticData"
                :selected-protein="selectedDotsInPlot"
                @onRowSelect="updatestatsSelectedRowsstats"
              />
            </v-col>
            <v-col
              sm="4"
              md="6"
              lg="4"
            >
              <scatter-plot
                id="differentialPlot"
                :save-plot="true"
                identifier1="Fold Change"
                identifier2="-log"
                :size-r="1"
                :omics-type-x="modality"
                :add-statslinte="true"
                :width="600"
                :height="600"
                own-colormethod="true"
                :omics-type-y="yAxistype"
                score-type=""
                label-x=""
                label-y=""
                :sel-ids="selectedPvalues"
                :ensemble-data="statisticData"
                @onDotSelect="selectDot"
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
import PatientTable from './tables/DifferentialmetaTable.vue'
import ScatterPlot from './plots/ScatterPlot.vue'
import StatisticTable from './tables/StatisticsTable.vue'
import SampleSelect from './partials/SampleSelect.vue'
import { DataType } from '@/constants'
import { proteinTypes } from './plots/proteinTypes'

export default {
  name: 'BasketComponent',
  components: {
    PatientTable,
    StatisticTable,
    ScatterPlot,
    SampleSelect
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
    diseaseName: '',
    proteinsInterest: proteinTypes.PROTEINLIST,
    allProtienTypes: proteinTypes.CATEGORY,
    proteinType: 'None',
    grp1Index: 'index',
    modality: DataType.TUPAC_SCORE_RTK,
    secondGroup: true,
    grp2Index: 'index',
    yAxistype: 'fdr',
    selectionMethod1: 'metadata',
    selectionMethod2: 'metadata',
    selectedPvalues: [],
    selectedDotsInPlot: '',
    customGroup1: null,
    customGroup2: null,
    statisticData: null,
    loading: false,
    allInputDataTypes: [
      {
        text: 'TOPAS scores (RTK)',
        value: DataType.TUPAC_SCORE_RTK
      },
      {
        text: 'TOPAS scores',
        value: DataType.TUPAC_SCORE
      },
      {
        text: 'Full proteome',
        value: DataType.FULL_PROTEOME
      },
      {
        text: 'Substrate Phosphorylation scores',
        value: DataType.KINASE_SCORE
      },
      {
        text: 'Kinase substrates peptides',
        value: DataType.KINASE_SUBSTRATE
      },
      {
        text: 'Protein Phosphorylation scores',
        value: DataType.PHOSPHO_SCORE
      },
      {
        text: 'Transcriptome (FPKM)',
        value: DataType.TRANSCRIPTOMICS
      },
      {
        text: 'Phospho peptides',
        value: DataType.PHOSPHO_PROTEOME
      }
    ]
  }),
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
  watch: {

  },
  methods: {
    async doTest () {
      try {
        this.statisticData = null
        this.loading = true

        const grp1 = this.customGroup1
        const yAxistype = this.yAxistype
        let grp2 = this.customGroup2
        if (this.secondGroup) { // the second group will be all other patients
          grp2 = 'index'
        }
        console.log(`This the first group: ${grp1}`)
        console.log(`This is the second group: ${grp2}`)

        const modality = this.modality
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/differential/${this.cohortIndex}/${modality}/${grp1}/${grp2}/${yAxistype}`)
        this.statisticData = response.data
        this.loading = false
      } catch (error) {
        alert(`Error: in Performing t_test,${error}`)
        this.loading = false
        console.error(error)
      }
    },

    selectDot (selectedDot) {
      this.selectedDotsInPlot = selectedDot
    },
    updateSampleGroup1 (sampleIdList) {
      this.customGroup1 = sampleIdList
    },

    updateSelectionMethodGroup1 (selectionMethod) {
      this.selectionMethod1 = selectionMethod
    },

    updateProteinType () {
      this.selectedPvalues = this.proteinsInterest[this.proteinType]
    },

    updateSampleGroup2 (sampleIdList) {
      this.customGroup2 = sampleIdList
    },

    updateSelectionMethodGroup2 (selectionMethod) {
      this.selectionMethod2 = selectionMethod
    },

    updatestatsSelectedRowsstats (selectedIds, selectedData) {
      const selectedPvalues = []
      if (selectedData.length > 1000) {
        alert('you selected more than 1000 rows to color on plot; it takes time')
      }
      selectedData.forEach(element => {
        selectedPvalues.push(element.sampleId)
      })
      this.selectedPvalues = selectedPvalues
      console.log(this.selectedPvalues)
    },

    updatemetaSelectedRows1 (selectedIds, selectedData) {
      this.updatemetaSelectedRows(selectedIds, selectedData, 'grp1')
    },

    updatemetaSelectedRows2 (selectedIds, selectedData) {
      this.updatemetaSelectedRows(selectedIds, selectedData, 'grp2')
    },

    updatemetaSelectedRows (selectedIds, selectedData, activeGrp) {
      this.selectedData = selectedData
      const selectedPatients = []
      this.selectedData.forEach(element => {
        selectedPatients.push(element['Sample name'])
      })
      if (activeGrp === 'grp1') {
        this.customGroup1 = selectedPatients
      } else {
        this.customGroup2 = selectedPatients
      }
    }
  }
}
</script>
