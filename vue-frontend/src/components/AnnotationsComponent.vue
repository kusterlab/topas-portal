<template>
  <v-container fluid>
    <v-row class="pa-4 bg-grey-lighten-3">
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Protein/p-site annotations </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <v-radio-group v-model="mode" label="Input type" hide-details class="mt-4">
              <v-radio
                v-for="(label, value) in radioOptions"
                :key="value"
                :label="label"
                :value="value"
              />
            </v-radio-group>
          </v-card-text>
        </v-card>
        <v-card variant="flat" class="mt-4">
          <v-card-title>Help</v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> Tab info </v-expansion-panel-title>
                <v-expansion-panel-text>
                  In this tab you can search and filter for annotations of proteins and p-peptides.
                </v-expansion-panel-text>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> How to use </v-expansion-panel-title>
                <v-expansion-panel-text>
                  Use the dropdown menus to select a cohort and the radio buttons to select an
                  analyte type.
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Annotation Table Section -->
      <v-col sm="12" md="9" lg="10">
        <v-card variant="flat">
          <v-card-text>
            <patient-scores-table :data-source="annotationUrl" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import { mapMutations } from 'vuex'
  import AnalyteAnnotationsTable from '@/components/tables/AnalyteAnnotationsTable.vue'
  import CohortSelect from './partials/CohortSelect.vue'
  import { DataType } from '@/constants'
  import { api } from '@/routes.ts'

  export default {
    name: 'OverviewComponent',
    components: {
      CohortSelect,
      PatientScoresTable: AnalyteAnnotationsTable
    },
    data: () => ({
      cohortIndex: -1,
      mode: DataType.FULL_PROTEOME,
      radioOptions: {
        [DataType.FULL_PROTEOME]: 'Protein',
        [DataType.PHOSPHO_PROTEOME]: 'Phosphopeptide'
      }
    }),
    computed: {
      annotationUrl() {
        if (this.cohortIndex < 0) return
        return api.ANALYTES_ANNOTATION_TABLE({ cohort_index: this.cohortIndex, level: this.mode })
      }
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      updateCohort({ dataSource, cohortIndex }) {
        this.cohortIndex = cohortIndex
      }
    }
  }
</script>
<style lang="scss"></style>
