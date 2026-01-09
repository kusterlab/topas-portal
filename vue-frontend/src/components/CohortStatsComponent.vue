<template>
  <v-container fluid>
    <v-row class="pa-4 bg-grey-lighten-3">
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Cohort statistics </v-card-title>
          <v-card-text>
            <cohort-select @select-cohort="updateCohort" />
            <v-select
              v-model="activeMeta"
              class="mt-4"
              density="default"
              variant="outlined"
              hide-details
              :items="metaData"
              label="Metadata column"
              prepend-icon="mdi-palette"
              @update:model-value="updateplotaData"
            />
            <v-text-field
              v-model="minNumitems"
              class="mt-4"
              label="Min Items per Group"
              type="number"
              density="default"
              variant="outlined"
              prepend-icon="mdi-counter"
              hide-details
              @update:model-value="updateplotaData"
            />
          </v-card-text>
        </v-card>
        <v-card variant="flat" class="mt-4">
          <v-card-title>Help</v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> Tab info </v-expansion-panel-title>
                <v-expansion-panel-text>
                  In this tab you can visualize metadata and number of detected modifications per
                  type for each cohort.
                </v-expansion-panel-text>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> How to use </v-expansion-panel-title>
                <v-expansion-panel-text>
                  Use the dropdown menus to select a cohort and metadata for visualization. Adjust
                  the minimum items per group to filter the data accordingly.
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Data Visualization Section -->
      <v-col sm="12" md="9" lg="10">
        <v-row>
          <v-col v-if="entityData.data" sm="12" md="5" lg="5">
            <v-card variant="flat">
              <v-card-title>
                {{ activeMeta }}
              </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  :loading="loadingEntity"
                  height="200"
                  width="200"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <VuePlotly
                      v-if="entityData.data"
                      :key="componentKey"
                      :data="entityData.data"
                      :layout="entityData.layout"
                      :to-image-button-options="toImageButtonOptions"
                    />
                  </v-responsive>
                </v-skeleton-loader>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col v-if="modificationData.data" sm="12" md="5" lg="5">
            <v-card variant="flat">
              <v-card-title> Modifications </v-card-title>
              <v-card-text>
                <v-skeleton-loader
                  :loading="loadingEntity"
                  height="200"
                  width="200"
                  type="image, list-item-two-line"
                >
                  <v-responsive>
                    <VuePlotly
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
          </v-col>
        </v-row>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import axios from 'axios'
  import { mapMutations } from 'vuex'

  import CohortSelect from './partials/CohortSelect.vue'
  import { VuePlotly } from 'vue3-plotly'

  export default {
    name: 'OverviewComponent',
    components: {
      CohortSelect,
      VuePlotly
    },
    data: () => ({
      cohortIndex: -1,
      entityData: [],
      modificationData: [],
      selectedSamples: [],
      componentKey: 0,
      loadingEntity: false,
      loadingPhospho: false,
      metaData: [],
      minNumitems: 10,
      activeMeta: 'code_oncotree',
      showPlot: false,
      layout: {
        title: 'plotlyoverview'
      },

      toImageButtonOptions: {
        format: 'svg', // one of png, svg, jpeg, webp
        filename: 'piechart'
      }
    }),
    computed: {
      cookieAccepted() {
        return this.$store.state.cookieAccepted
      }
    },
    watch: {
      cohortIndex() {
        this.updateplotaDataphospho()
      }
    },
    mounted() {
      this.metaComboUpdater()
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      updateCohort({ cohortIndex }) {
        this.cohortIndex = cohortIndex
      },
      acceptCookies() {
        this.$store.dispatch('acceptCookies')
      },
      async metaComboUpdater() {
        // retrieving different meta data to color patients from the backend
        const response = await axios.get(`${import.meta.env.VITE_API_HOST}/overview/meta_types`)
        const finalIndex = []
        response.data.forEach(element => {
          finalIndex.push(element)
        })
        this.metaData = finalIndex
      },
      async updateplotaData() {
        let response
        this.entityData = []
        this.loadingEntity = true
        try {
          response = await axios.get(
            `${import.meta.env.VITE_API_HOST}/overview/entity_count/${this.cohortIndex}/${this.activeMeta}/${this.minNumitems}`
          )
          this.entityData = response.data
          // this.componentKey = this.componentKey + 1
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: `Error: ${error}`
          })
          this.entityData = []
        }
        this.loadingEntity = false
      },
      async updateplotaDataphospho() {
        let response
        this.modificationData = []
        this.loadingPhospho = true
        try {
          response = await axios.get(
            `${import.meta.env.VITE_API_HOST}/overview/mod_seq_type/${this.cohortIndex}`
          )
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
