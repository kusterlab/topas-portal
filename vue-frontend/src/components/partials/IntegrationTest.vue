<template>
  <v-container fluid class="pa-0">
    <v-card variant="flat">
      <v-card-title tag="h1"> Cohort endpoint tests </v-card-title>
      <v-card-text>
        <v-col>
          <v-row>
            <v-col cols="auto">
              <cohort-select @select-cohort="updateCohort" />
            </v-col>
            <v-col cols="auto">
              <sample-select
                :cohort-index="cohortIndex"
                :show-toggle="false"
                :show-table-select="false"
                @update-group="updateSampleGroup"
              />
            </v-col>
            <v-col cols="auto">
              <v-text-field
                v-model="proteinCheck"
                style="width: 100px"
                label="Protein"
              />
            </v-col>
            <v-col cols="auto">
              <v-text-field
                v-model="ppeptideCheck"
                style="width: 100px"
                label="P-peptide"
              />
            </v-col>

            <v-col cols="auto">
              <v-text-field
                v-model="topasCheck"
                style="width: 100px"
                label="Topas"
              />
            </v-col>

            <v-col cols="auto">
              <v-btn color="primary" :loading="loading" class="mb-4 ml-4" @click="checkAll">
                Check All Endpoints
              </v-btn>
            </v-col>
          </v-row>
          <v-row>
            <v-data-table
              :headers="headers"
              :items="results"
              item-value="name"
              :items-per-page="50"
            >
              <template #[`item.status`]="{ item }">
                <v-chip v-if="item.status === 200" color="green" size="small"> ✅ 200 OK </v-chip>
                <v-chip v-else-if="item.status === 'ERR'" color="red" size="small"> ❌ ERR </v-chip>
                <v-chip v-else-if="item.status" color="orange" size="small">
                  ⚠️ {{ item.status }}
                </v-chip>
                <v-chip v-else color="grey" size="small"> ⏳ Checking... </v-chip>
              </template>

              <template #[`item.ms`]="{ item }">
                <span v-if="item.ms">{{ item.ms }} ms</span>
              </template>
            </v-data-table>
          </v-row>
        </v-col>
      </v-card-text>
    </v-card>
    <v-card class="mt-4" variant="flat">
      <v-card-title>Error logs</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="11">
            <v-textarea
              label="Error Logs"
              style="width: 100%"
              variant="filled"
              hide-details
              :model-value="errorLogs"
            />
          </v-col>
          <v-col cols="1">
            <v-btn color="primary" @click="updateErrorLogs">
              <v-icon> mdi-refresh </v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
  import axios from 'axios'
  import { mapGetters, mapState, mapMutations } from 'vuex'
  import CohortSelect from './CohortSelect.vue'
  import SampleSelect from './SampleSelect.vue'
  import { DataType, IncludeRef, IntensityUnit, ImputationMode } from '@/constants'
  import { api } from '@/routes.ts'

  export default {
    name: 'ConfigureUpdate',
    components: {
      CohortSelect,
      SampleSelect
    },
    data: () => ({
      cohortName: '',
      cohortIndex: -1,
      showUpdateCohorts: true,
      logValue: '',
      proteinCheck: 'EGFR',
      ppeptideCheck: 'AAAAAPAS(ph)ED',
      topasCheck: 'AXL',
      selectedSamples: [],
      loading: false,
      headers: [
        { title: 'Endpoint', value: 'name' },
        { title: 'URL', value: 'url' },
        { title: 'Status', value: 'status' },
        { title: 'Time (ms)', value: 'ms' },
        { title: 'Bytes', value: 'bytes' }
      ],
      results: [],
      errorLogs: ''
    }),
    computed: {
      ...mapState({
        all_cohorts: state => state.all_cohorts
      }),
      ...mapGetters({
        hasData: 'hasData'
      })
    },
    mounted() {
      this.updateLog()
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      async updateLog() {
        const response = await axios.get(`${import.meta.env.VITE_API_HOST}/integration/logs`)
        this.logValue = response.data.replace(/topas_separator/g, '\n')
      },
      updateCohort({ cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      updateSampleGroup(sampleIdList) {
        this.selectedSamples = sampleIdList
      },
      async checkAll() {
        this.loading = true
        const testArguments = {
          cohort_index: this.cohortIndex,
          patient: this.selectedSamples[0],
          level: DataType.FULL_PROTEOME,
          patients: this.selectedSamples,
          identifier: this.proteinCheck,
          cnv_type: 'AMPLIFICATION',
          level_2: DataType.TOPAS_RTK_SCORE,
          intensity_unit: IntensityUnit.Z_SCORE,
          patients_list: 'all',
          sample_ids: 'S001,S002',
          data_type: 'rna',
          grp1_ind: this.selectedSamples,
          grp2_ind: 'index',
          y_axis_type: 'fdr',
          taxcode: '9606',
          protein_search: this.proteinCheck,
          link: 'kegg/hsa04010.json',
          grp_ind: this.selectedSamples,
          method: 'gc',
          topas_names: this.topasCheck,
          score_type: 'score',
          categories: 'cat1,cat2',
          topasname: this.topasCheck,
          fieldname: 'code_oncotree',
          field_interest: '40',
          modality: 'rna',
          batchlists: 'b1,b2',
          include_ref: IncludeRef.INCLUDE_REF,
          imputation: ImputationMode.NO_IMPUTE,
          selected_genes_mode: 'all',
          dimensionality_reduction_method: 'ppca',
          use_replicate: 'noreplicate',
          custom_patients: 'all',
          imputation_ratio: '0.9',
          output_format: 'plot'
        }

        const endpoints = [
          { name: 'FAVICON', url: api.FAVICON() },
          { name: 'CONFIG', url: api.CONFIG() },
          { name: 'CONFIG_PATH', url: api.CONFIG_PATH() },
          { name: 'CONFIG_CHECKALL', url: api.CONFIG_CHECKALL() },
          { name: 'COHORT_NAMES', url: api.COHORT_NAMES() },
          { name: 'COLUMN_NAMES', url: api.COLUMN_NAMES() },
          { name: 'PATIENT_REPORT_TABLE', url: api.PATIENT_REPORT_TABLE(testArguments) },
          { name: 'PATIENT_REPORT_TABLE_XLSX', url: api.PATIENT_REPORT_TABLE_XLSX(testArguments) },
          { name: 'ENTITY_STATUS', url: api.ENTITY_STATUS() },
          { name: 'CORRELATION_FPKM_PROTEIN', url: api.CORRELATION_FPKM_PROTEIN(testArguments) },
          { name: 'ONCOKB_CNV', url: api.ONCOKB_CNV(testArguments) },
          { name: 'ANNOTATION_MODALITY', url: api.ANNOTATION_MODALITY(testArguments) },
          { name: 'VENN_PATIENT_COMPARE', url: api.VENN_PATIENT_COMPARE(testArguments) },
          { name: 'VENN_BATCH_COMPARE', url: api.VENN_BATCH_COMPARE(testArguments) },
          { name: 'UPDATE_LOG', url: api.UPDATE_LOG() },
          { name: 'ERROR_LOG', url: api.ERROR_LOG() },
          {
            name: 'PATIENT_CENTRIC_SUMMED_INTENSITY',
            url: api.PATIENT_CENTRIC_SUMMED_INTENSITY(testArguments)
          },
          { name: 'PATIENT_CENTRIC_COUNTS', url: api.PATIENT_CENTRIC_COUNTS(testArguments) },
          { name: 'TOPAS_ANNOTATIONS', url: api.TOPAS_ANNOTATIONS() },
          { name: 'TOPAS_IDS', url: api.TOPAS_IDS(testArguments) },
          { name: 'TOPAS_SUBSCORE', url: api.TOPAS_SUBSCORE(testArguments) },
          { name: 'SAMPLE_ANNOTATION', url: api.SAMPLE_ANNOTATION(testArguments) },
          { name: 'PATIENTS', url: api.PATIENTS(testArguments) },
          {
            name: 'PATIENTS_GENOMICS_ANNOTATIONS',
            url: api.PATIENTS_GENOMICS_ANNOTATIONS(testArguments)
          },
          { name: 'PATIENTS_METADATA', url: api.PATIENTS_METADATA(testArguments) },
          { name: 'PATIENTS_METADATA_FIELDS', url: api.PATIENTS_METADATA_FIELDS(testArguments) },
          {
            name: 'PATIENTS_METADATA_FIELD_VALUES',
            url: api.PATIENTS_METADATA_FIELD_VALUES(testArguments)
          },
          {
            name: 'PATIENTS_BY_FIELD_INTEREST',
            url: api.PATIENTS_BY_FIELD_INTEREST(testArguments)
          },
          { name: 'PATIENTS_ALL_ENTITIES', url: api.PATIENTS_ALL_ENTITIES(testArguments) },
          { name: 'GENOMICS_IDENTIFIER', url: api.GENOMICS_IDENTIFIER(testArguments) },
          { name: 'DENSITY_FPKM', url: api.DENSITY_FPKM(testArguments) },
          { name: 'DENSITY_PROTEIN', url: api.DENSITY_PROTEIN(testArguments) },
          { name: 'ABUNDANCE/PROTEIN', url: api.ABUNDANCE(testArguments) },
          {
            name: 'ABUNDANCE/PSITE',
            url: api.ABUNDANCE({
              ...testArguments,
              level: DataType.PHOSPHO_PROTEOME,
              identifier: this.ppeptideCheck
            })
          },
          {
            name: 'ABUNDANCE/TRANSCRIPTOMICS',
            url: api.ABUNDANCE({ ...testArguments, level: DataType.TRANSCRIPTOMICS })
          },
          {
            name: 'ABUNDANCE/PHOSPHO_SCORE',
            url: api.ABUNDANCE({ ...testArguments, level: DataType.PHOSPHO_SCORE })
          },
          {
            name: 'ABUNDANCE/KINASE_SCORE',
            url: api.ABUNDANCE({
              ...testArguments,
              level: DataType.KINASE_SCORE,
              identifier: 'EGFR(RTK-TOPAS)'
            })
          },
          {
            name: 'ABUNDANCE/TOPAS_RTK_SCORE',
            url: api.ABUNDANCE({
              ...testArguments,
              level: DataType.TOPAS_RTK_SCORE,
              identifier: 'EGFR'
            })
          },
          { name: 'CORRELATION', url: api.CORRELATION(testArguments) },
          { name: 'HEATMAP', url: api.HEATMAP(testArguments) },
          { name: 'DIFFERENTIAL', url: api.DIFFERENTIAL(testArguments) },
          { name: 'PROTEIN_LIST', url: api.PROTEIN_LIST(testArguments) },
          {
            name: 'PROTEIN_LIST/PSITE',
            url: api.PROTEIN_LIST({ ...testArguments, level: DataType.PHOSPHO_PROTEOME })
          },
          { name: 'CANONICAL_PATHWAYS', url: api.CANONICAL_PATHWAYS(testArguments) },
          { name: 'PATHWAY_SKELETONS', url: api.PATHWAY_SKELETONS(testArguments) },
          { name: 'PCA_UMAP', url: api.PCA_UMAP(testArguments) }
          // { name: 'ENRICHMENTS', url: api.ENRICHMENTS(testArguments) }  // too slow and currently not used
        ]

        // Immediately display table
        this.results = endpoints

        // Start fetching each endpoint asynchronously
        endpoints.forEach(async (ep, i) => {
          try {
            const start = performance.now()
            const res = await fetch(ep.url, { method: 'GET' })
            const end = performance.now()

            const buffer = await res.arrayBuffer()
            const byteLength = buffer.byteLength

            // Update this one endpoint in-place
            this.results[i] = {
              ...ep,
              status: res.status,
              ms: Math.round(end - start),
              bytes: byteLength
            }
          } catch (err) {
            this.results[i] = {
              ...ep,
              status: 'ERR',
              ms: null,
              bytes: null
            }
          }
        })

        const response = await axios.get(`${import.meta.env.VITE_API_HOST}/error/logs`)
        this.errorLogs = response.data.replace(/topas_separator/g, '\n')

        this.loading = false
      }
    }
  }
</script>
