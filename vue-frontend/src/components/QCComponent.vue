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
          PCA/UMAP plots
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="diseaseName"
            prepend-icon="mdi-database"
            class="cohort"
            dense
            outlined
            :items="all_diseases"
            label="Cohort"
          />
          <v-select
            v-model="inputDataType"
            prepend-icon="mdi-filter"
            class="input_data_type mb-2"
            dense
            outlined
            hide-details
            :items="allInputDataTypes"
            label="Input Data Type"
            @change="loading=false"
          />

          <v-checkbox
            v-model="includeReplicates"
            label="Include replicates"
            hide-details
            dense
          />
          <v-checkbox
            v-model="includeReferenceChannels"
            label="Include reference channels"
            hide-details
            dense
          />
          <v-checkbox
            v-model="geneSubsetActive"
            label="Select Genes/Psites (Upload a text file )"
            hide-details
            dense
          />

          <v-card
            v-if="geneSubsetActive"
            class="grey lighten-3 mt-1"
          >
            <v-card-text>
              <v-file-input
                v-model="file"
                placeholder="Upload a txt file"
                accept="text/*,.txt"
                hint="one gene name/Psite per line"
                persistent-hint
                dense
              />
            </v-card-text>
          </v-card>
          <v-text-field
            v-model="imputationRatio"
            label="Minimum Samples Occurence for imputation"
            hide-details
            type="number"
          />
          <v-checkbox
            v-model="allPatients"
            label="All Patients"
          />
          <sample-select
            v-if="!allPatients"
            :cohort-index="cohortIndex"
            :sample-ids="customGroup"
            @update-group="updateSampleGroup"
            @update-selection-method="updateSelectionMethodGroup"
          />
          <v-btn-toggle
            v-model="dimReductionMethod"
            color="primary"
            mandatory
            class="mt-4 mb-6"
          >
            <v-btn value="ppca">
              PCA
            </v-btn>
            <v-btn value="umap">
              UMAP
            </v-btn>
          </v-btn-toggle>

          <v-select
            v-model="activeMeta"
            prepend-icon="mdi-palette"
            class="metadata mb-4"
            dense
            outlined
            hide-details
            :items="metaData"
            label="Color by Metadata"
            @change="loading=false"
          />

          <v-btn
            class="primary ma-2"
            @click="updatePCA"
          >
            Generate PCA/UMAP plot
          </v-btn>
        </v-card-text>
      </v-card>
      <v-card flat>
        <v-card-title
          tag="h1"
        >
          Silhouette Analysis
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="minNumPatients"
            label="Min Number patients in each group"
            hide-details
            type="number"
          />
          <v-radio-group
            v-model="silhouetteInputType"
            label="Input type"
            dense
          >
            <v-radio
              label="Raw data"
              value="beforeCluster"
            />

            <v-radio
              :label="dimReductionMethod"
              value="afterCluster"
            />
          </v-radio-group>

          <v-btn
            class="primary ma-2"
            :loading="loading"
            @click="updateSilhouette"
          >
            Generate Silhouette plot
          </v-btn>
        </v-card-text>
      </v-card>
    </v-col>
    <v-col
      sm="12"
      md="10"
      lg="10"
    >
      <v-card flat>
        <v-card-text>
          <v-row>
            <v-col
              sm="12"
              md="5"
              lg="5"
            >
              <qc-table
                :data-source="qcData"
                :is-loading="isLoading"
                @onRowSelect="updateSelectedRows"
              />
            </v-col>
            <v-col
              sm="12"
              md="3"
              lg="3"
            >
              <qc-plot
                v-if="activeMeta"
                :save-plot="true"
                :qc-type="dimReductionMethod"
                :qc-meta="activeMeta"
                :qc-sel-ids="selIds"
                :qcplot-data="qcData"
                :pc-var1="variance1"
                :pc-var2="variance2"
              />
            </v-col>
          </v-row>
          <v-row>
            <v-col
              sm="12"
              md="5"
              lg="5"
            >
              <silhouetteTable
                :data-source="silData"
              />
            </v-col>
            <v-col
              sm="12"
              md="5"
              lg="5"
            >
              <lolipop-plot
                v-if="showPlot"
                lollipop-id="silPlot"
                loli-title="Silhouette Scores"
                :fixed-domain="fixedDomain"
                :plot-data="silData"
                :loli-mode="true"
                :loliradian="1"
                complete-tooltip="true"
                show-legends="true"
                width="1400"
                height="400"
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
import QcTable from '@/components/tables/QCTable'
import silhouetteTable from '@/components/tables/silhouetteTable'
import QcPlot from '@/components/plots/QCPlot.vue'
import LolipopPlot from './plots/LolipopPlot.vue'
import { DataType } from '@/constants'
import SampleSelect from './partials/SampleSelect.vue'

export default {
  name: 'QCComponent',
  components: {
    QcTable,
    QcPlot,
    LolipopPlot,
    silhouetteTable,
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
    qcData: [],
    silData: [],
    allPatients: true,
    minNumPatients: 1,
    imputationRatio: 0.9,
    variance1: 0,
    variance2: 0,
    fixedDomain: [{ min: -1, max: 1 }],
    selIds: [],
    metaData: [],
    silhouetteInputType: 'beforeCluster',
    activeMeta: 'code_oncotree',
    allInputDataTypes: [
      {
        text: 'Full proteome',
        value: DataType.FULL_PROTEOME
      },
      {
        text: 'Phosphopeptides',
        value: DataType.PHOSPHO_PROTEOME
      },
      {
        text: 'Full proteome + Phosphopeptides',
        value: DataType.FP_PP
      },
      {
        text: 'Full proteome (annotated only)',
        value: DataType.FULL_PROTEOME_ANNOTATED
      },
      {
        text: 'Phosphopeptides (annotated only)',
        value: DataType.PHOSPHO_PROTEOME_ANNOTATED
      },
      {
        text: 'Protein Phosphorylation scores',
        value: DataType.PHOSPHO_SCORE
      },
      {
        text: 'Substrate Phosphorylation scores',
        value: DataType.KINASE_SCORE
      },
      {
        text: 'TOPAS scores',
        value: DataType.TUPAC_SCORE
      }
    ],
    inputDataType: DataType.FULL_PROTEOME,
    diseaseName: 'sarcoma',
    plotType: 'Intensity',
    dimReductionMethod: 'ppca',
    includeReplicates: true,
    includeReferenceChannels: false,
    geneSubsetActive: false,
    allorSelectedgenes: 'all',
    loading: false,
    customGroup: [],
    selectionMethod: [],
    isLoading: false,
    showPlot: false,
    file: null
  }),

  mounted () {
    this.metaComboUpdater()
  },

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
    async updateSilhouette () {
      try {
        this.loading = true
        this.silData = []
        this.showPlot = false
        if (this.activeMeta.toString() !== 'Sample') {
          const dimReductionMethod = this.dimReductionMethod
          const numPatient = parseInt(this.minNumPatients)
          const inputDataType = this.inputDataType
          const referenceChannel = this.includeReferenceChannels ? 'ref' : 'noref'
          const replicate = this.includeReplicates ? 'replicate' : 'noreplicate'
          const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
          const silInputType = this.silhouetteInputType
          this.allorSelectedgenes = 'all' // running with all genes
          if (this.geneSubsetActive && this.file !== null) {
            console.log('Submitting file for upload...')
            const formData = new FormData()
            formData.append('file', this.file)
            const response = await axios.post(`${process.env.VUE_APP_API_HOST}/uploadGenes`, formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              },
              timeout: 5000
            })
            console.log(response)
            this.allorSelectedgenes = 'selected' // running with selected genes
          }
          const customGroup = this.allPatients ? 'all' : this.customGroup
          const allOrselected = this.allorSelectedgenes
          const imputationRatio = this.imputationRatio
          const response = await axios.get(`${process.env.VUE_APP_API_HOST}/qc/sil/all/${inputDataType}/${cohortIndex}/${dimReductionMethod}/${referenceChannel}/${replicate}/${this.activeMeta}/${numPatient}/${silInputType}/${allOrselected}/${customGroup}/${imputationRatio}`)
          this.silData = response.data
          this.silData.length > 0 ? this.showPlot = true : this.showPlot = false
        } else {
          alert('"Sample" cannot be used as meta data type for silhouette scores.')
        }
      } catch (error) {
        alert(error)
      }
      this.loading = false
    },

    updateSampleGroup (sampleIdList) {
      this.customGroup = sampleIdList
    },

    updateSelectionMethodGroup (selectionMethod) {
      this.selectionMethod = selectionMethod
    },

    async updatePCA () {
      this.allorSelectedgenes = 'all' // running with all genes
      if (this.geneSubsetActive && this.file !== null) {
        console.log('Submitting file for upload...')
        const formData = new FormData()
        formData.append('file', this.file)
        const response = await axios.post(`${process.env.VUE_APP_API_HOST}/uploadGenes`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 5000
        })
        console.log(response)
        this.allorSelectedgenes = 'selected' // running with selected genes
      }
      this.getqcData()
    },

    async metaComboUpdater () { // retrieving different meta data to color patients from the backend
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/qc/metadata`)
      const finalIndex = []
      response.data.forEach(element => {
        finalIndex.push(element)
      })

      this.metaData = finalIndex
    },

    async getqcData () {
      const customGroup = this.allPatients ? 'all' : this.customGroup
      const inputDataType = this.inputDataType
      const dimReductionMethod = this.dimReductionMethod
      const referenceChannel = this.includeReferenceChannels ? 'ref' : 'noref'
      const allSelected = this.allorSelectedgenes
      const replicate = this.includeReplicates ? 'replicate' : 'noreplicate'
      const cohortIndex = this.all_diseases.indexOf(this.diseaseName)
      const imputationRatio = this.imputationRatio
      try {
        this.isLoading = true
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/qc/${allSelected}/${inputDataType}/${cohortIndex}/${dimReductionMethod}/${referenceChannel}/${replicate}/${customGroup}/${imputationRatio}`)
        this.qcData = response.data.dataFrame
        this.variance1 = response.data.pcVars[0]
        this.variance2 = response.data.pcVars[1]
      } catch (error) {
        alert(`Error while calculating PCA: ${error.response.data}`)
      } finally {
        this.isLoading = false
      }
    },

    updateSelectedRows (selectedIds, selectedData) { // for customized coloring of the samples if needed
      this.selIds = []
      selectedData.forEach((rowData) => {
        this.selIds.push(rowData.index) // selected indices
      })
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
