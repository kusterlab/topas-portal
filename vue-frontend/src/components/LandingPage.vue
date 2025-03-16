<template>
  <v-container fluid>
    <v-row class="pa-4 grey lighten-3">
      <v-col
        sm="12"
        md="9"
        lg="9"
      >
        <v-row class="pa-0 home-hero light lighten-4">
          <v-col cols="12">
            <div class="home-hero__banner d-flex align-left justify-left py-1">
              <v-container>
                <h1 class="display-2 font-weight-bold black--text text-left mb-4">
                  Welcome to the TOPAS Portal
                </h1>
                <p class="text-h6 black--text text-left mb-6">
                  A multi-omics resource for precision oncology. Explore data and tools for proteomics, transcriptomics, and genomics.
                </p>
              </v-container>
            </div>
          </v-col>
        </v-row>
        <v-row>
          <v-col
            sm="3"
            md="3"
            lg="3"
          >
            <v-card
              :to="topasactivityPath"
              outlined
            >
              <v-card-title
                class="text-h6 font-weight-bold"
              >
                TOPAS scores
              </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  height="200"
                  width="100%"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <v-img
                      :src="require('@/assets/topas_scores.png')"
                      alt="Entity Image"
                      height="200"
                      contain
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col
            sm="3"
            md="3"
            lg="3"
          >
            <v-card
              :to="kinasectivityPath"
              outlined
            >
              <v-card-title
                class="text-h6 font-weight-bold"
              >
                Kinase activity
              </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  height="200"
                  width="100%"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <v-img
                      :src="require('@/assets/kinase_score.png')"
                      alt="Entity Image"
                      height="200"
                      contain
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col
            sm="3"
            md="3"
            lg="3"
          >
            <v-card
              :to="cohortAnalysis"
              outlined
            >
              <v-card-title
                class="text-h6 font-weight-bold"
              >
                Cohort Analysis
              </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  height="200"
                  width="100%"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <v-img
                      :src="require('@/assets/volcano.png')"
                      alt="Entity Image"
                      height="200"
                      contain
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col
            sm="3"
            md="3"
            lg="3"
          >
            <v-card
              :to="patientReport"
              outlined
            >
              <v-card-title
                class="text-h6 font-weight-bold"
              >
                Patient Report
              </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  height="200"
                  width="100%"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <v-img
                      :src="require('@/assets/patient_report.png')"
                      alt="Entity Image"
                      height="200"
                      contain
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>
    <div>
      <div
        v-if="!cookieAccepted"
        class="cookie-banner"
      >
        This page uses cookies to save table preferences.
        <button @click="acceptCookies">
          Accept
        </button>
      </div>
    </div>
  </v-container>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

export default {
  name: 'LandingComponent',
  data: () => ({
    topasactivityPath: '/topasscores',
    kinasectivityPath: '/kinasescores',
    cohortAnalysis: '/analytics',
    patientReport: '/patient',
    componentKey: 0,
    loadingEntity: false,
    loadingPhospho: false,
    metaData: [],
    minNumitems: 10,
    activeMeta: 'code_oncotree',
    diseaseName: null,
    showPlot: false,
    layout: {
      title: 'plotlyoverview'
    },

    toImageButtonOptions: {
      format: 'svg', // one of png, svg, jpeg, webp
      filename: 'piechart'
    }
  }),
  watch: {
  },
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
    cohortIndex: function () {
      return this.all_diseases.indexOf(this.diseaseName)
    },
    cookieAccepted () {
      return this.$store.state.cookieAccepted
    }
  },
  methods: {
    acceptCookies () {
      this.$store.dispatch('acceptCookies')
    }
  }
}
</script>
<style lang="scss">
.home-hero__container {
  min-height: 10vh;
}
.home-hero__content {
  width: 90vw;
  max-width: 960px;
  overflow: hidden;
}

.v-card__title {
  word-break: normal;
}
.cookie-banner {
  position: fixed;
  bottom: 0;
  width: 100%;
  height: 10%;
  background: #333;
  color: #fff;
  text-align: center;
  padding: 15px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.cookie-banner button {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 4px;
}

.cookie-banner button:hover {
  background-color: #45a049;
}
</style>
