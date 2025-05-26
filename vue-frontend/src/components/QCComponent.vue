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
          <cohort-select
            @select-cohort="updateCohort"
          />
          <subcohort-select
            class="mt-4"
            :cohort-index="cohortIndex"
            :sample-ids="customGroup"
            @update-group="updateSampleGroup"
            @update-selection-method="updateSelectionMethodGroup"
          />
          <v-checkbox
            v-if = "!onlyReferenceChannels"
            v-model="includeReplicates"
            label="Include replicates"
            hide-details
            dense
          />
          <v-checkbox
            v-if = "!onlyReferenceChannels"
            v-model="includeReferenceChannels"
            label="Include reference channels"
            hide-details
            dense
          />
          <v-checkbox
            v-model="onlyReferenceChannels"
            label="Only reference channels"
            hide-details
            dense
          />
          <v-text-field
            v-model="imputationRatio"
            class="mt-4"
            label="Min. sample occurrence [%]"
            hint="Only use proteins/p-peptides occurring in >x% of total samples. The remaining missing values are imputed by PPCA."
            persistent-hint
            type="number"
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
          Select plot inputs
        </v-card-title>
        <v-card-text>
          <v-btn-toggle
            v-model="dimReductionMethod"
            color="primary"
            mandatory
            dense
          >
            <v-btn value="ppca">
              PCA
            </v-btn>
            <v-btn value="umap">
              UMAP
            </v-btn>
          </v-btn-toggle>
          <v-select
            v-model="inputDataType"
            prepend-icon="mdi-filter"
            class="input_data_type my-2"
            dense
            outlined
            hide-details
            :items="allInputDataTypes"
            label="Input Type"
            @change="loading=false"
          />
          <v-checkbox
            v-model="geneSubsetActive"
            label="Use custom identifier list"
            hide-details
            dense
          />
          <v-file-input
            v-show="geneSubsetActive"
            v-model="file"
            class="mt-4"
            placeholder="Upload a txt file"
            accept="text/*,.txt"
            hint="one gene name/p-peptide per line"
            persistent-hint
            dense
          />

          <v-select
            v-model="activeMeta"
            prepend-icon="mdi-palette"
            class="metadata mt-4"
            dense
            outlined
            hide-details
            :items="metaData"
            label="Color by Metadata"
            @change="loading=false"
          />
          <v-btn
            class="primary mt-4"
            @click="updatePCA"
          >
            Generate plot
          </v-btn>
        </v-card-text>
      </v-card>
      <v-card
        flat
        class="mt-4"
      >
        <v-card-title
          tag="h1"
        >
          Silhouette Analysis
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="minNumPatients"
            label="Min. #patients per group"
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
              :label="dimReductionMethod.toUpperCase() + ' coordinates'"
              value="afterCluster"
            />
          </v-radio-group>

          <v-btn
            class="primary ma-2"
            :loading="loading"
            @click="updateSilhouette"
          >
            Generate Silhouette
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
        </v-card-text>
      </v-card>
      <v-card
        v-if="silData.length > 0"
        flat
        class="mt-4"
      >
        <v-card-text>
          <v-row>
            <v-col
              sm="12"
              md="5"
              lg="5"
            >
              <silhouetteTable
                v-if="silData.length > 0"
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
import { mapMutations } from 'vuex'

import QcTable from '@/components/tables/QCTable'
import silhouetteTable from '@/components/tables/silhouetteTable'
import QcPlot from '@/components/plots/QCPlot.vue'
import LolipopPlot from './plots/LolipopPlot.vue'
import { DataType } from '@/constants'
import CohortSelect from './partials/CohortSelect.vue'
import SubcohortSelect from './partials/SubcohortSelect.vue'

export default {
  name: 'QCComponent',
  components: {
    QcTable,
    QcPlot,
    LolipopPlot,
    silhouetteTable,
    CohortSelect,
    SubcohortSelect
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
    onlyReferenceChannels: false,
    qcData: [],
    silData: [],
    minNumPatients: 1,
    imputationRatio: 90,
    variance1: 0,
    variance2: 0,
    fixedDomain: [{ min: -1, max: 1 }],
    selIds: [],
    metaData: [],
    silhouetteInputType: 'beforeCluster',
    geneSubsetActive: false,
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
        value: DataType.TOPAS_SCORE
      }
    ],
    inputDataType: DataType.FULL_PROTEOME,
    plotType: 'Intensity',
    dimReductionMethod: 'ppca',
    includeReplicates: true,
    includeReferenceChannels: false,
    allorSelectedgenes: 'all',
    loading: false,
    customGroup: [],
    selectionMethod: [],
    isLoading: false,
    showPlot: false,
    file: null
  }),

  computed: {
  },

  mounted () {
    this.metaComboUpdater()
  },

  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    async updateSilhouette () {
      try {
        this.loading = true
        this.silData = []
        this.showPlot = false
        if (this.activeMeta.toString() !== 'Sample') {
          const dimReductionMethod = this.dimReductionMethod
          const numPatient = parseInt(this.minNumPatients)
          const inputDataType = this.inputDataType
          let referenceChannel = this.includeReferenceChannels ? 'ref' : 'noref'
          referenceChannel = this.onlyReferenceChannels ? 'onlyref' : referenceChannel
          const replicate = this.includeReplicates ? 'replicate' : 'noreplicate'
          const silInputType = this.silhouetteInputType
          this.allorSelectedgenes = 'all' // running with all genes
          if (this.geneSubsetActive && this.file !== null) {
            this.addNotification({
              color: 'info',
              message: 'Submitting file for upload...'
            })
            const formData = new FormData()
            formData.append('file', this.file)
            const response = await axios.post(`${process.env.VUE_APP_API_HOST}/uploadGenes`, formData, {
              headers: {
                'Content-Type': 'multipart/form-data'
              },
              timeout: 5000
            })
            this.addNotification({
              color: 'info',
              message: `${response}`
            })
            this.allorSelectedgenes = 'selected' // running with selected genes
          }
          const customGroup = this.customGroup.length === 0 ? 'all' : this.customGroup
          const allOrselected = this.allorSelectedgenes
          const imputationRatio = this.imputationRatio / 100.0
          const response = await axios.get(`${process.env.VUE_APP_API_HOST}/qc/sil/all/${inputDataType}/${this.cohortIndex}/${dimReductionMethod}/${referenceChannel}/${replicate}/${this.activeMeta}/${numPatient}/${silInputType}/${allOrselected}/${customGroup}/${imputationRatio}`)
          this.silData = response.data
          this.silData.length > 0 ? this.showPlot = true : this.showPlot = false
        } else {
          this.addNotification({
            color: 'warning',
            message: '"Sample" cannot be used as meta data type for silhouette scores.'
          })
        }
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `${error}`
        })
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
        this.addNotification({
          color: 'info',
          message: 'Submitting file for upload...'
        })
        const formData = new FormData()
        formData.append('file', this.file)
        const response = await axios.post(`${process.env.VUE_APP_API_HOST}/uploadGenes`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 5000
        })
        this.addNotification({
          color: 'info',
          message: `${response.data}`
        })
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
      const customGroup = this.customGroup.length === 0 ? 'all' : this.customGroup
      const inputDataType = this.inputDataType
      const dimReductionMethod = this.dimReductionMethod
      let referenceChannel = this.includeReferenceChannels ? 'ref' : 'noref'
      referenceChannel = this.onlyReferenceChannels ? 'onlyref' : referenceChannel
      const allSelected = this.allorSelectedgenes
      const replicate = this.includeReplicates ? 'replicate' : 'noreplicate'
      const imputationRatio = this.imputationRatio / 100.0
      try {
        this.isLoading = true
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/qc/${allSelected}/${inputDataType}/${this.cohortIndex}/${dimReductionMethod}/${referenceChannel}/${replicate}/${customGroup}/${imputationRatio}`)
        this.qcData = response.data.dataFrame
        this.variance1 = response.data.pcVars[0]
        this.variance2 = response.data.pcVars[1]
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `Error while calculating PCA: ${error.response.data}`
        })
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
