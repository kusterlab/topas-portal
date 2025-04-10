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
          Heatmap
        </v-card-title>
        <v-card-text>
          <cohort-select
            @select-cohort="updateCohort"
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
          Select samples
        </v-card-title>
        <v-card-text>
          <sample-select
            :cohort-index="cohortIndex"
            :show-table-select="true"
            :sample-ids="selectedSamples"
            @update-group="updateSampleGroup"
            @update-selection-method="updateSelectionMethod"
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
          Select data
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="inputDataType"
            class="input_data_type mb-2"
            prepend-icon="mdi-filter"
            dense
            outlined
            hide-details
            :items="allInputDataTypes"
            label="Input Data Type"
            @change="updateHeatmap"
          />

          <basket-select
            v-if="String(inputDataType).startsWith('topas')"
            :cohort-index="cohortIndex"
            :score-type="false"
            :multiple="true"
            @select-basket="updateIdentifier"
          />
          <protein-select
            v-if="!String(inputDataType).startsWith('topas')"
            :cohort-index="cohortIndex"
            :multiple="true"
            :data-layer="inputDataType"
            class="mt-4"
            @select-protein="updateIdentifier"
          />
        </v-card-text>
      </v-card>
    </v-col>
    <v-col
      v-show="selectionMethod === 'table'"
      sm="12"
      md="4"
      lg="4"
    >
      <v-card flat>
        <v-card-text>
          <patient-select-table
            :cohort-index="cohortIndex"
            @onRowSelect="updateSelectedSamples"
          />
        </v-card-text>
      </v-card>
    </v-col>
    <v-col
      sm="12"
      md="5"
      lg="6"
    >
      <v-card
        v-if="heatmapData.data"
        flat
      >
        <v-card-text>
          <Plotly
            :data="heatmapData.data"
            :layout="heatmapData.layout"
            :to-image-button-options="toImageButtonOptions"
          />
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
<script>
import axios from 'axios'
import CohortSelect from './partials/CohortSelect.vue'
import PatientSelectTable from './tables/DifferentialmetaTable.vue'
import BasketSelect from '@/components/partials/BasketSelect'
import ProteinSelect from '@/components/partials/ProteinSelect'
import SampleSelect from './partials/SampleSelect.vue'
import { Plotly } from 'vue-plotly'
import { DataType } from '@/constants'

export default {
  name: 'HeatmapComponent',
  components: {
    CohortSelect,
    PatientSelectTable,
    BasketSelect,
    ProteinSelect,
    Plotly,
    SampleSelect
  },
  props: {
    minWidth: {
      type: Number,
      default: 400
    },
    diseaseChange: {
      type: Boolean,
      default: false
    },
    minHeight: {
      type: Number,
      default: 300
    }
  },
  data: () => ({
    cohortIndex: 0,
    heatmapData: [],
    selectedSamples: [],
    selectionMethod: 'metadata',
    componentKey: 0,
    inputDataType: DataType.FULL_PROTEOME,
    identifier: null,
    showPlot: false,
    layout: {
      title: 'plotlyHeatMap'
    },
    allInputDataTypes: [
      {
        text: 'Full proteome',
        value: DataType.FULL_PROTEOME
      },
      // {
      //   text: 'Phosphopeptides abundance',
      //   value: DataType.PHOSPHO_PROTEOME
      // },
      {
        text: 'Kinase scores',
        value: DataType.KINASE_SCORE
      },
      {
        text: 'Substrate Phosphrylation scores',
        value: DataType.KINASE_SUBSTRATE
      },
      {
        text: 'Protein Phosphorylation scores ',
        value: DataType.PHOSPHO_SCORE
      },
      {
        text: 'Phosphoproteins p-sites',
        value: DataType.PHOSPHO_SCORE_PSITE
      },
      {
        text: 'TOPAS scores',
        value: DataType.TOPAS_SCORE
      },
      {
        text: 'TOPAS subscores (protein expression)',
        value: DataType.TOPAS_PROTEIN
      },
      {
        text: 'TOPAS subscores (kinase activity)',
        value: DataType.TOPAS_KINASE_SCORE
      },
      {
        text: 'TOPAS subscores (kinsase substrate)',
        value: DataType.TOPAS_KINASE_SUBSTRATE
      },
      {
        text: 'TOPAS subscores (protein phosphorylation scores)',
        value: DataType.TOPAS_PHOSPHO_SCORE
      },
      {
        text: 'TOPAS subscores  (p-sites)',
        value: DataType.TOPAS_PHOSPHO_SCORE_PSITE
      }
    ],
    toImageButtonOptions: {
      format: 'svg', // one of png, svg, jpeg, webp
      filename: 'heatmap'
    }
  }),
  computed: {
  },
  watch: {
    diseaseChange: function () {
      this.getPatientsData()
    }
  },
  mounted () {
  },
  methods: {
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    updateIdentifier ({ dataSource, identifier }) {
      this.identifier = identifier
      this.updateHeatmap()
    },
    updateSampleGroup (sampleIdList) {
      this.selectedSamples = sampleIdList
      this.updateHeatmap()
    },
    updateSelectionMethod (selectionMethod) {
      this.selectionMethod = selectionMethod
    },
    updateSelectedSamples (selectedIds, selectedData) {
      this.selectedData = selectedData
      const selectedPatients = []
      this.selectedData.forEach(element => {
        selectedPatients.push(element['Sample name'])
      })
      this.selectedSamples = selectedPatients
      this.updateHeatmap()
    },
    async updateHeatmap () {
      if (this.cohortIndex >= 0 && this.identifier !== null && this.selectedSamples !== null && this.selectedSamples.length > 0) {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/batcheffect/${this.inputDataType}/${this.cohortIndex}/${this.identifier}/${this.selectedSamples}/plot`)
        this.showPlot = true
        this.heatmapData = response.data
        this.patientData = `${process.env.VUE_APP_API_HOST}/batcheffect/${this.inputDataType}/${this.cohortIndex}/${this.identifier}/${this.selectedSamples}/meta`
        this.componentKey = this.componentKey + 1
      }
    }
  }
}
</script>
<style scoped>

</style>
