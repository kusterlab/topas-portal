<template>
  <div>
    <v-col
      sm="12"
      md="12"
      lg="12"
    >
      <v-row class="pa-4">
        <v-col
          sm="12"
          md="6"
          lg="6"
        >
          <v-card
            elevation="2"
            class="pa-4"
          >
            <v-card-title
              tag="h2"
              class="text-h6 font-weight-bold mb-3"
            >
              Options
            </v-card-title>
            <v-card-text>
              <v-combobox
                v-model="diseaseName"
                dense
                outlined
                hide-details
                :items="all_diseases"
                label="Cohort / Cell Type"
                prepend-icon="mdi-database"
                @change="allUpdate"
              />
            </v-card-text>
            <v-card-text>
              <v-row class="mb-4">
                <v-col cols="12">
                  <v-select
                    v-model="activeMeta"
                    dense
                    outlined
                    hide-details
                    :items="metaData"
                    label="Color by Metadata"
                    prepend-icon="mdi-palette"
                    @change="updateplotaData"
                  />
                </v-col>
              </v-row>
              <v-row class="mb-4">
                <v-col cols="12">
                  <v-text-field
                    v-model="minNumitems"
                    label="Min Items per Group"
                    type="number"
                    dense
                    outlined
                    prepend-icon="mdi-counter"
                    hide-details
                    @change="updateplotaData"
                  />
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
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
                    In this tab you can visualize meta dtata and number of detected modifications per type for each cohort.
                  </p>
                  <p class="text-body-2">
                    Use the dropdown menus to select a cohort and metadata for visualization. Adjust the minimum items per group to filter the data accordingly.
                  </p>
                </v-expansion-panel-content>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card>
        </v-col>

        <!-- Data Visualization Section -->
        <v-col
          sm="12"
          md="6"
          lg="6"
        >
          <v-row>
            <v-col cols="12">
              <v-card-title
                v-if="entityData.data"
                class="text-h6 font-weight-bold"
              >
                Entity Data
              </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  :loading="loadingEntity"
                  height="200"
                  width="200"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <Plotly
                      v-if="entityData.data"
                      :key="componentKey"
                      :data="entityData.data"
                      :layout="entityData.layout"
                      :to-image-button-options="toImageButtonOptions"
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-card-text>
            </v-col>
          </v-row>
          <v-row>
            <v-card flat>
              <v-card-title
                v-if="modificationData.data"
                class="text-h6 font-weight-bold"
              >
                Modification Data
              </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  :loading="loadingEntity"
                  height="200"
                  width="200"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <Plotly
                      v-if="modificationData.data"
                      :key="componentKey"
                      :data="modificationData.data"
                      :layout="modificationData.layout"
                      :to-image-button-options="toImageButtonOptions"
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-card-text>
            </v-card>
          </v-row>
        </v-col>
      </v-row>
    </v-col>
  </div>
</template>

<script>
import axios from 'axios'
import { mapGetters, mapState } from 'vuex'
import { Plotly } from 'vue-plotly'

export default {
  name: 'OverviewComponent',
  components: {
    Plotly
  },
  data: () => ({
    entityData: [],
    topasactivityPath: '/topasscores',
    kinasectivityPath: '/kinasescores',
    modificationData: [],
    selectedSamples: [],
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
    },
    allUpdate () {
      this.updateplotaData()
      this.updateplotaDataphospho()
    },
    async metaComboUpdater () { // retrieving different meta data to color patients from the backend
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/overview/meta_types`)
      const finalIndex = []
      response.data.forEach(element => {
        finalIndex.push(element)
      })
      this.metaData = finalIndex
    },
    async updateplotaData () {
      let response
      this.entityData = []
      this.loadingEntity = true
      try {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/overview/entity_count/${this.cohortIndex}/${this.activeMeta}/${this.minNumitems}`)
        this.entityData = response.data
        // this.componentKey = this.componentKey + 1
      } catch (error) {
        console.log(error)
        this.entityData = []
      }
      this.loadingEntity = false
    },
    async updateplotaDataphospho () {
      let response
      this.modificationData = []
      this.loadingPhospho = true
      try {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/overview/mod_seq_type/${this.cohortIndex}`)
        this.modificationData = response.data
        // this.componentKey = this.componentKey + 1
        this.loadingPhospho = false
      } catch (error) {
        this.modificationData = []
        this.loadingPhospho = false
      }
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
