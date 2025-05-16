<template>
  <v-app>
    <explorer-component />
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
            Entity scores
          </v-card-title>
          <cohort-select
              @select-cohort="updateCohort"
            />
          <v-btn
            class="ma-2"
            color="primary"
            @click="getScores"
          >
            Predict Scores
          </v-btn>
        </v-card>
        <!-- Collapsible Help Box -->
        <v-card
          elevation="2"
          class="pa-4 mt-4"
        >
          <v-expansion-panels>
            <v-expansion-panel>
              <v-expansion-panel-header>
                More info?
              </v-expansion-panel-header>
              <v-expansion-panel-content>
                <p class="text-body-2">
                  In this tab you can interrogate the probability of samples matching pre-defined entities based on the expression of up to 100 proteins per entity. Use the dropdown menu to select a cohort and enter the sample of interest into the list. Matching probability is evaluated between 0 (low probability) to 1 (high probability).
                </p>
              </v-expansion-panel-content>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card>
      </v-col>
      <v-col
        sm="12"
        md="9"
        lg="10"
      >
        <entityscore-table
          :data-source="jsonUrl"
        />
      </v-col>
    </v-row>
  </v-app>
</template>

<script>
// import axios from 'axios'
import CohortSelect from './partials/CohortSelect.vue'
import entityscoreTable from '@/components/tables/entityscoreTable'
import explorerComponent from './partials/scoresComponent.vue'

export default {
  name: 'EntityComponent',
  components: {
    entityscoreTable,
    explorerComponent,
    CohortSelect
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
    scores: [],
    jsonUrl: ''

  }),
  computed: {
    activeCohortIndex () {
      return this.cohortIndex
    }
  },

  methods: {
    updateCohort ({ dataSource, cohortIndex }) {
      this.cohortIndex = cohortIndex
    },
    getScores () {
      this.jsonUrl = `${process.env.VUE_APP_API_HOST}/entityscore/${this.cohortIndex}`
    }
  }
}
</script>
