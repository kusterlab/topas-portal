<template>
  <v-main>
    <v-tabs
      v-model="tabs"
      show-arrows
    >
      <v-tab
        v-for="item of allPlots"
        :key="item"
        @click="tabChange"
      >
        {{ item }}
      </v-tab>
    </v-tabs>
    <v-tabs-items v-model="tabs">
      <v-tab-item class="tab">
        <patientreport-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <overview-component />
      </v-tab-item>
    </v-tabs-items>
  </v-main>
</template>

<script>
import PatientreportComponent from './PatientReportComponent.vue'
import OverviewComponent from './OverviewComponent.vue'

const d3 = require('d3')
export default {
  name: 'VisualizationComponent',
  components: {
    PatientreportComponent,
    OverviewComponent
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
    allPlots: ['Patient Report', 'Cohort statistics'],
    tabs: null
  }),
  computed: {
  },
  methods: {
    tabChange () {
      //  To Avoid data leakge between different d3 objects, SVGs remove during tab changes
      //  if (this.items[this.tabs] === 'Protein Expression' || this.items[this.tabs] === 'Topas Scores' || this.items[this.tabs] === 'Drug Scores' || this.items[this.tabs] === 'Phosphorylation Scores') {
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

<style></style>
