<template>
  <v-row class="pa-4 grey lighten-3">
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
    <v-tabs-items v-model="tabs">
      <v-tab-item class="tab">
        <patient-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <drug-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <meta-analysis />
      </v-tab-item>
      <v-tab-item class="tab">
        <log-component />
      </v-tab-item>
    </v-tabs-items>
  </v-row>
</template>

<script>
import PatientComponent from './PatientReportComponent.vue'
import LogComponent from './LogComponent.vue'
import DrugComponent from './DrugComponent.vue'
import metaAnalysis from './OverviewComponent.vue'

export default {
  name: 'VisualizationComponent',
  components: {
    PatientComponent,
    LogComponent,
    metaAnalysis,
    DrugComponent
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
    allPlots: ['Patient reports', 'Kino beads', 'Meta analysis', 'Admin Tools'],
    tabs: null
  }),
  computed: {
  },
  methods: {
    tabChange () {
    //  To Avoid data leakge between different d3 objects, SVGs remove during tab changes
    //  if (this.items[this.tabs] === 'Protein Expression' || this.items[this.tabs] === 'Basket Scores' || this.items[this.tabs] === 'Drug Scores' || this.items[this.tabs] === 'Phosphorylation Scores') {
    //  }
    }
  }
}
</script>

<style>

</style>
