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
        <log-component />
      </v-tab-item>
    </v-tabs-items>
  </v-main>
</template>

<script>
import LogComponent from './LogComponent.vue'
export default {
  name: 'VisualizationComponent',
  components: {
    LogComponent
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
    allPlots: ['Admin Tools'],
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
