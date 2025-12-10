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

          <topas-select
            v-if="String(inputDataType).startsWith('topas')"
            :cohort-index="cohortIndex"
            :multiple="true"
            @select-topas="updateIdentifier"
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
      <v-card
        flat
      >
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
        flat
        :loading="heatmapIsLoading"
        :disabled="heatmapIsLoading"
      >
        <v-card-text>
          <v-tooltip bottom>
            <template v-slot:activator="{ on, attrs }">
              <v-btn
                class="ma-2"
                color="primary"
                @click="downloadCSV"
                :disabled="!heatmapHasData"
                v-bind="attrs"
                v-on="on"
              >
                <v-icon
                  dark
                >
                  mdi-table-arrow-down
                </v-icon>
              </v-btn>
            </template>
            <span>Download as CSV</span>
          </v-tooltip>
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
import utils from '@/plugins/DownloadUtils'
import CohortSelect from './partials/CohortSelect.vue'
import PatientSelectTable from './tables/DifferentialmetaTable.vue'
import TopasSelect from '@/components/partials/TopasSelect'
import ProteinSelect from '@/components/partials/ProteinSelect'
import SampleSelect from './partials/SampleSelect.vue'
import { Plotly } from 'vue-plotly'
import { DataType } from '@/constants'
import { api } from '@/routes.ts'

export default {
  name: 'HeatmapComponent',
  components: {
    CohortSelect,
    PatientSelectTable,
    TopasSelect,
    ProteinSelect,
    Plotly,
    SampleSelect
  },
  props: {
    minWidth: {
      type: Number,
      default: 400
    },
    cohortChange: {
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
    heatmapIsLoading: false,
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
        text: 'Substrate Phosphorylation scores',
        value: DataType.KINASE_SCORE
      },
      {
        text: 'Kinase substrate abundances',
        value: DataType.KINASE_SUBSTRATE
      },
      {
        text: 'Protein phosphorylation scores',
        value: DataType.PHOSPHO_SCORE
      },
      {
        text: 'Phosphoprotein p-peptides',
        value: DataType.PHOSPHO_SCORE_PSITE
      },
      // {
      //   text: 'TOPAS-CK scores',
      //   value: DataType.TOPAS_CK_SCORE
      // },
      {
        text: 'TOPAS-RTK scores',
        value: DataType.TOPAS_RTK_SCORE
      },
      {
        text: 'TOPAS-RTK subscores (protein expression)',
        value: DataType.TOPAS_PROTEIN
      },
      {
        text: 'TOPAS-RTK subscores (substrate phos. scores)',
        value: DataType.TOPAS_KINASE_SCORE
      },
      {
        text: 'TOPAS-RTK subscores (kinase substrates)',
        value: DataType.TOPAS_KINASE_SUBSTRATE
      },
      {
        text: 'TOPAS-RTK subscores (protein phos. scores)',
        value: DataType.TOPAS_PHOSPHO_SCORE
      },
      {
        text: 'TOPAS-RTK subscores (phosphoprotein p-peptides)',
        value: DataType.TOPAS_PHOSPHO_SCORE_PSITE
      }
    ],
    toImageButtonOptions: {
      format: 'svg', // one of png, svg, jpeg, webp
      filename: 'heatmap'
    }
  }),
  computed: {
    heatmapHasData: function () {
      return this.cohortIndex >= 0 && this.identifier !== null && this.selectedSamples !== null && this.selectedSamples.length > 0
    }
  },
  watch: {
    cohortChange: function () {
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
      if (this.heatmapHasData) {
        this.heatmapIsLoading = true
        const response = await axios.get(api.HEATMAP({
          level: this.inputDataType,
          cohort_index: this.cohortIndex,
          identifier: this.identifier,
          sample_ids: this.selectedSamples,
          output_format: 'plot'
        }))
        this.heatmapIsLoading = false
        this.heatmapData = response.data
        this.componentKey = this.componentKey + 1
      }
    },
    async downloadCSV () {
      const response = await axios.get(api.HEATMAP({
        level: this.inputDataType,
        cohort_index: this.cohortIndex,
        identifier: this.identifier,
        sample_ids: this.selectedSamples,
        output_format: 'table'
      }))
      const heatmapData = response.data
      if (heatmapData.length > 0) {
        utils.downloadCSV(
          utils.jsonToCsvRows(heatmapData),
          `heatmap_${this.inputDataType}`
        )
      }
    }
  }
}
</script>
<style scoped>

</style>
