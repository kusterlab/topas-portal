<template>
  <v-container fluid>
    <v-row class="pa-4 bg-grey-lighten-3">
      <v-col sm="12" md="2" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Differential Expression </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <v-checkbox
              v-model="applyMultipleTestingCorrection"
              class="mt-4"
              density="default"
              hide-details
              label="Multiple testing correction (Benjamini-Hochberg)"
            />
            <v-select
              v-model="modality"
              class="input_data_type mb-2 mt-4"
              density="default"
              variant="outlined"
              prepend-icon="mdi-filter"
              hide-details
              :items="allInputDataTypes"
              label="Input Data Type"
            />
            <v-select
              v-model="proteinType"
              class="input_data_type mb-2 mt-4"
              prepend-icon="mdi-palette"
              density="default"
              variant="outlined"
              hide-details
              :items="allProteinnTypes"
              label="Highlight proteins"
              @update:model-value="updateProteinType"
            />
          </v-card-text>
        </v-card>
        <v-card variant="flat" class="mt-4">
          <v-card-title tag="h1"> Select groups </v-card-title>
          <v-card-text>
            <p class="mb-2"> Group1 </p>
            <sample-select
              :cohort-index="cohortIndex"
              :sample-ids="customGroup1"
              :show-table-select="true"
              @update-group="updateSampleGroup1"
              @update-selection-method="updateSelectionMethodGroup1"
            />

            <p class="mt-4 mb-2 d-inline-flex"> Group2 </p>
            <v-checkbox
              v-model="secondGroup"
              hide-details
              density="default"
              class="d-inline-flex ml-2 mt-0"
              label="All - Group1"
            />
            <sample-select
              v-if="!secondGroup"
              :cohort-index="cohortIndex"
              :sample-ids="customGroup2"
              :show-table-select="true"
              @update-group="updateSampleGroup2"
              @update-selection-method="updateSelectionMethodGroup2"
            />

            <v-btn class="ma-2" color="primary" :loading="loading" @click="doTest">
              Perform Analysis
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col sm="12" md="9" lg="10">
        <v-card
          v-show="selectionMethod1 === 'table' || selectionMethod2 === 'table'"
          variant="flat"
          class="mb-4"
        >
          <v-card-text>
            <v-row>
              <v-col v-show="selectionMethod1 === 'table'" sm="12" md="6" lg="6">
                <h2>Group1</h2>
                <patient-select-table
                  :cohort-index="cohortIndex"
                  @onRowSelect="updatemetaSelectedRows1"
                />
              </v-col>
              <v-col v-show="selectionMethod2 === 'table'" sm="12" md="6" lg="6">
                <h2>Group2</h2>
                <patient-select-table
                  :cohort-index="cohortIndex"
                  @onRowSelect="updatemetaSelectedRows2"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        <v-card variant="flat">
          <v-card-text>
            <v-row>
              <v-col sm="12" md="6" lg="6">
                <statistic-table
                  :data-source="statisticData"
                  :selected-protein="selectedDotsInPlot"
                  @onRowSelect="updatestatsSelectedRowsstats"
                />
              </v-col>
              <v-col sm="12" md="6" lg="6">
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
  </v-container>
</template>

<script>
  import axios from 'axios'
  import { mapMutations } from 'vuex'

  import CohortSelect from './partials/CohortSelect.vue'
  import PatientSelectTable from './tables/DifferentialmetaTable.vue'
  import ScatterPlot from './plots/ScatterPlot.vue'
  import StatisticTable from './tables/StatisticsTable.vue'
  import SampleSelect from './partials/SampleSelect.vue'
  import { proteinTypes } from './plots/proteinTypes'

  import { DataType } from '@/constants'
  import { api } from '@/routes.ts'

  export default {
    name: 'TopasComponent',
    components: {
      CohortSelect,
      PatientSelectTable,
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
      cohortIndex: 0,
      proteinsInterest: proteinTypes.PROTEINLIST,
      allProteinnTypes: proteinTypes.CATEGORY,
      proteinType: 'None',
      grp1Index: 'index',
      modality: DataType.TOPAS_RTK_SCORE,
      secondGroup: true,
      grp2Index: 'index',
      applyMultipleTestingCorrection: true,
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
          title: 'TOPAS RTK scores',
          value: DataType.TOPAS_RTK_SCORE
        },
        {
          title: 'Full proteome',
          value: DataType.FULL_PROTEOME
        },
        {
          title: 'Substrate Phosphorylation scores',
          value: DataType.KINASE_SCORE
        },
        {
          title: 'Kinase substrates peptides',
          value: DataType.KINASE_SUBSTRATE
        },
        {
          title: 'Protein Phosphorylation scores',
          value: DataType.PHOSPHO_SCORE
        },
        {
          title: 'Transcriptome (FPKM)',
          value: DataType.TRANSCRIPTOMICS
        },
        {
          title: 'Phospho peptides',
          value: DataType.PHOSPHO_PROTEOME
        }
      ]
    }),
    computed: {
      yAxistype: function () {
        if (this.applyMultipleTestingCorrection) {
          return 'fdr'
        } else {
          return 'p_values'
        }
      }
    },
    watch: {},
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      updateCohort({ dataSource, cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      async doTest() {
        try {
          this.statisticData = null
          this.loading = true

          const grp1 = this.customGroup1
          const yAxistype = this.yAxistype
          let grp2 = this.customGroup2
          if (this.secondGroup) {
            // the second group will be all other patients
            grp2 = 'index'
          }

          const modality = this.modality
          const response = await axios.get(
            api.DIFFERENTIAL({
              cohort_index: this.cohortIndex,
              level: modality,
              grp1_ind: grp1,
              grp2_ind: grp2,
              y_axis_type: yAxistype
            })
          )
          this.statisticData = response.data
          this.loading = false
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: `Error: in performing t-test ${error}`
          })
          this.loading = false
        }
      },

      selectDot(selectedDot) {
        this.selectedDotsInPlot = selectedDot
      },
      updateSampleGroup1(sampleIdList) {
        this.customGroup1 = sampleIdList
      },

      updateSelectionMethodGroup1(selectionMethod) {
        this.selectionMethod1 = selectionMethod
      },

      updateProteinType() {
        this.selectedPvalues = this.proteinsInterest[this.proteinType]
      },

      updateSampleGroup2(sampleIdList) {
        this.customGroup2 = sampleIdList
      },

      updateSelectionMethodGroup2(selectionMethod) {
        this.selectionMethod2 = selectionMethod
      },

      updatestatsSelectedRowsstats(selectedIds, selectedData) {
        const selectedPvalues = []
        if (selectedData.length > 1000) {
          this.addNotification({
            color: 'warning',
            message:
              'You selected more than 1000 rows to color on the plot, this may take some time'
          })
        }
        selectedData.forEach(element => {
          selectedPvalues.push(element.sampleId)
        })
        this.selectedPvalues = selectedPvalues
      },

      updatemetaSelectedRows1(selectedIds, selectedData) {
        this.updatemetaSelectedRows(selectedIds, selectedData, 'grp1')
      },

      updatemetaSelectedRows2(selectedIds, selectedData) {
        this.updatemetaSelectedRows(selectedIds, selectedData, 'grp2')
      },

      updatemetaSelectedRows(selectedIds, selectedData, activeGrp) {
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
