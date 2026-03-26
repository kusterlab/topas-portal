<template>
  <v-container class="bg-grey-lighten-3" fluid>
    <v-row>
      <v-col sm="12" md="3" lg="2">
        <v-card variant="flat">
          <v-card-title tag="h1"> Kinase inhibitors </v-card-title>
          <v-card-text>
            <v-text-field
              v-model="identifierDrug"
              density="default"
              persistent-hint
              variant="outlined"
              hint="Use semicolons (;) for multiple targets"
              label="Kinase(s) to target"
              placeholder="EGFR;ERBB2"
            />
            <v-select
              v-model="sortFunction"
              class="mt-2"
              prepend-icon="mdi-sort"
              :items="sortFunctions"
              label="Sort by"
              hide-details
              variant="outlined"
              density="default"
            />
          </v-card-text>
        </v-card>
        <!-- Collapsible Help Box -->
        <v-card variant="flat" class="mt-4">
          <v-card-title>Help</v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> Tab info </v-expansion-panel-title>
                <v-expansion-panel-text>
                  In this tab you can find candidate kinase inhibitors for a list of kinases you
                  want to target based on Kinobeads experiments (Klaeger et al. 2017, Science).
                </v-expansion-panel-text>
              </v-expansion-panel>
              <v-expansion-panel>
                <v-expansion-panel-title class="mb-0"> How to use </v-expansion-panel-title>
                <v-expansion-panel-text>
                  Input one or multiple kinases to target. The table will give you a list of drugs
                  that target all kinases of your input list. The table will be sorted with the most
                  potent drug for your target on top. If you provide multiple kinases, you can
                  choose to sort by the average, median or minimum Kd of your chosen targets. You
                  can put additional filters on the table using the advanced filter box above the
                  table.
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col sm="12" md="9" lg="10">
        <v-card variant="flat">
          <v-card-text>
            <v-container fluid>
              <v-row>
                <v-col sm="12" md="6" lg="6">
                  <drug-table :data-source="drugData" @getGenes="yieldGenes" />
                </v-col>
                <v-col sm="12" md="2" lg="2">
                  <v-data-table
                    v-if="barplotData"
                    :sort-by="[{ key: 'Kdapp', order: 'asc' }]"
                    :headers="tableHeaders"
                    :items="barplotData"
                    :page="tablePage"
                    :items-per-page="10"
                    :search="searchTarget"
                    :hide-default-footer="true"
                    density="default"
                  >
                    <template #top>
                      <v-text-field
                        v-model="searchTarget"
                        label="Search target"
                        prepend-icon="mdi-magnify"
                        class="mb-2"
                        hide-details
                      />
                    </template>
                    <template #footer>
                      <v-pagination
                        v-model="tablePage"
                        class="hide-numbers float-right"
                        :length="Math.floor(barplotData.length / 10) + 1"
                      />
                      <div class="float-right mt-3 mr-1">
                        page {{ tablePage }} / {{ Math.floor(barplotData.length / 10) + 1 }}
                      </div>
                    </template>
                  </v-data-table>
                </v-col>
                <v-col sm="12" md="4" lg="4">
                  <bar-plot
                    v-if="barplotData"
                    :barplot-data="barplotData"
                    :barplot-max="barplotMaximum"
                  />
                </v-col>
              </v-row>
            </v-container>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
  import drugTable from '@/components/tables/DrugTable.vue'
  import barPlot from '@/components/plots/DrugBarPlot.vue'

  export default {
    name: 'DrugComponent',
    components: {
      drugTable,
      barPlot
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
      identifierDrug: '',
      sortFunction: 'mean',
      sortFunctions: [
        {
          title: 'Average Kd value',
          value: 'mean'
        },
        {
          title: 'Median Kd value',
          value: 'median'
        },
        {
          title: 'Min Kd value',
          value: 'min'
        }
      ],
      tableHeaders: [
        { title: 'Target', value: 'Drug' },
        { title: 'Kdapp', value: 'Kdapp' }
      ],
      searchTarget: '',
      tablePage: 1,
      barplotData: false,
      barplotMaximum: 5000
    }),
    computed: {
      drugData: function () {
        const drugGeneName = this.identifierDrug
        const sortFunction = this.sortFunction
        if (drugGeneName.length === 0) {
          return `${import.meta.env.VITE_API_HOST}/drugs`
        } else {
          return `${import.meta.env.VITE_API_HOST}/drug_genes/${sortFunction}/${drugGeneName}`
        }
      }
    },
    watch: {},
    methods: {
      yieldGenes(value) {
        this.barplotData = value.plotData
        this.barplotMaximum = value.maximum
      }
    }
  }
</script>
<style scoped>
  ::v-deep(.v-pagination__item) {
    display: none;
  }
  ::v-deep(.v-pagination__more) {
    display: none;
  }
  ::v-deep(.v-pagination__navigation) {
    display: flex; /* Keep arrows visible */
  }
</style>
