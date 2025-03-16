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
          <v-combobox
            v-model="diseaseName"
            prepend-icon="mdi-database"
            class="cohort"
            dense
            outlined
            hide-details
            :items="all_diseases"
            label="Cohort"
          />

          <p class="mt-4 mb-2">
            Sample selection
          </p>
          <sample-select
            :cohort-index="cohortIndex"
            :sample-ids="selectedSamples"
            @update-group="updateSampleGroup"
            @update-selection-method="updateSelectionMethod"
          />
          <v-select
            v-model="inputDataType"
            class="input_data_type mb-2 mt-8"
            prepend-icon="mdi-filter"
            dense
            outlined
            hide-details
            :items="allInputDataTypes"
            label="Input Data Type"
            @change="updateHeatmap"
          />

          <basket-select
            v-if="String(inputDataType).startsWith('tupac')"
            :cohort-index="all_diseases.indexOf(diseaseName)"
            :score-type="false"
            :multiple="true"
            @select-basket="updateIdentifier"
          />
          <protein-select
            v-if="!String(inputDataType).startsWith('tupac')"
            :cohort-index="all_diseases.indexOf(diseaseName)"
            :multiple="true"
            :data-layer="inputDataType"
            class="mt-4"
            @select-protein="updateIdentifier"
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
              v-show="selectionMethod === 'table'"
              sm="12"
              md="5"
              lg="5"
            >
              <patient-table
                :cohort-index="cohortIndex"
                @onRowSelect="updateSelectedSamples"
              />
            </v-col>
            <v-col
              sm="12"
              md="7"
              lg="7"
            >
              <Plotly
                v-if="heatmapData.data"
                :data="heatmapData.data"
                :layout="heatmapData.layout"
                :to-image-button-options="toImageButtonOptions"
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
import BasketSelect from '@/components/partials/BasketSelect'
import ProteinSelect from '@/components/partials/ProteinSelect'
import SampleSelect from './partials/SampleSelect.vue'
import { Plotly } from 'vue-plotly'
import { DataType } from '@/constants'

export default {
  name: 'HeatmapComponent',
  components: {
    PatientTable,
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
    heatmapData: [],
    selectedSamples: [],
    selectionMethod: 'metadata',
    componentKey: 0,
    diseaseName: null,
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
        value: DataType.TUPAC_SCORE
      },
      {
        text: 'TOPAS subscores (protein expression)',
        value: DataType.TUPAC_PROTEIN
      },
      {
        text: 'TOPAS subscores (kinase activity)',
        value: DataType.TUPAC_KINASE_SCORE
      },
      {
        text: 'TOPAS subscores (kinsase substrate)',
        value: DataType.TUPAC_KINASE_SUBSTRATE
      },
      {
        text: 'TOPAS subscores (protein phosphorylation scores)',
        value: DataType.TUPAC_PHOSPHO_SCORE
      },
      {
        text: 'TOPAS subscores  (p-sites)',
        value: DataType.TUPAC_PHOSPHO_SCORE_PSITE
      }
    ],
    toImageButtonOptions: {
      format: 'svg', // one of png, svg, jpeg, webp
      filename: 'heatmap'
    }
  }),
  watch: {
    diseaseChange: function () {
      this.getPatientsData()
    }
  },
  mounted () {
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
      if (this.cohortIndex >= 0 && this.identifier !== null && this.selectedSamples !== null) {
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
