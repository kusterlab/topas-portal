<template>
  <v-row class="pa-4 grey lighten-3">
    <v-col
      sm="4"
      md="3"
      lg="3"
    >
      <v-tabs
        v-model="tabs"
      >
        <v-tab
          v-for="item of allPlots"
          :key="item"
          @click="tabChange"
        >
          {{ item }}
        </v-tab>
      </v-tabs>
    </v-col>
    <v-col
      sm="4"
      md="10"
      lg="10"
    >
      <v-tabs-items v-model="tabs">
        <v-tab-item class="tab">
          <patientreport-component />
        </v-tab-item>
        <v-tab-item class="tab">
          <overview-component />
        </v-tab-item>
      </v-tabs-items>
    </v-col>
  </v-row>
</template>

<script>
import PatientreportComponent from './PatientReportComponent.vue'
import overviewComponent from './OverviewComponent.vue'

const d3 = require('d3')
export default {
  name: 'VisualizationComponent',
  components: {
    PatientreportComponent,
    overviewComponent
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
    allPlots: ['Patient Report', 'Meta analysis'],
    tabs: null
  }),
  computed: {
  },
  methods: {
    tabChange () {
    //  To Avoid data leakge between different d3 objects, SVGs remove during tab changes
    //  if (this.items[this.tabs] === 'Protein Expression' || this.items[this.tabs] === 'Basket Scores' || this.items[this.tabs] === 'Drug Scores' || this.items[this.tabs] === 'Phosphorylation Scores') {
      d3.selectAll('svg').remove()
      d3.selectAll('.names').remove()
      d3.selectAll('dot').remove()
      d3.selectAll('circle').remove()
      d3.selectAll('line').remove()
      d3.selectAll('rect').remove()
      d3.selectAll('toto').remove()
      d3.selectAll('g').remove()
    //  }
    }
  }
}
</script>

<style>

</style>
