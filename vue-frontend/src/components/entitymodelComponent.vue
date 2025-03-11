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
          <v-select
            v-model="diseaseName"
            prepend-icon="mdi-database"
            class="cohort"
            dense
            outlined
            hide-details
            :items="all_diseases"
            label="Cohort / Cell Type"
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
import { mapGetters, mapState } from 'vuex'
import entityscoreTable from '@/components/tables/entityscoreTable'
import explorerComponent from './partials/scoresComponent.vue'

export default {
  name: 'EntityComponent',
  components: {
    entityscoreTable,
    explorerComponent
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
    // loading: false,
    scores: [],
    jsonUrl: ''

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

  methods: {
    getScores () {
      this.jsonUrl = `${process.env.VUE_APP_API_HOST}/entityscore/${this.cohortIndex}`
    }
  }
}
</script>
