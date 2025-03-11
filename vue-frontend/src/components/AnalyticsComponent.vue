<template>
  <v-row class="pa-4 grey lighten-3">
    <v-tabs
      v-model="tabs"
    >
      <v-tab
        v-for="item of allScores"
        :key="item"
        @click="tabChange"
      >
        {{ item }}
      </v-tab>
    </v-tabs>
    <v-tabs-items v-model="tabs">
      <v-tab-item class="tab">
        <correlation-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <pca-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <differential-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <heatmap-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <venn-component />
      </v-tab-item>
      <v-tab-item class="tab">
        <kinobeads-component />
      </v-tab-item>
    </v-tabs-items>
  </v-row>
</template>

<script>
import PcaComponent from './QCComponent.vue'
import CorrelationComponent from './CorrelationComponent.vue'
import DifferentialComponent from './DifferentialComponent.vue'
import VennComponent from './VennComponent.vue'
import HeatmapComponent from './HeatmapComponent.vue'
import KinobeadsComponent from './DrugComponent.vue'

const d3 = require('d3')
export default {
  name: 'ScoreComponent',
  components: {
    PcaComponent,
    CorrelationComponent,
    VennComponent,
    HeatmapComponent,
    DifferentialComponent,
    KinobeadsComponent
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
    scoreType: 'Correlation Analysis',
    allScores: ['Correlation', 'PCA/UMAP', 'Diff. Expression', 'Heatmap plots', 'Venn diagrams', 'Kino Beads'],
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
