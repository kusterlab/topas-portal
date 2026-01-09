<template>
  <v-main>
    <v-tabs>
      <v-tab to="/correlation" exact> Correlation </v-tab>
      <v-tab to="/pca"> PCA </v-tab>
      <v-tab to="/differential"> Differential </v-tab>
      <v-tab to="/heatmap"> Heatmap </v-tab>
      <v-tab to="/venn"> Venn </v-tab>
      <v-tab to="/kinobeads"> Kinobeads </v-tab>
      <v-tab to="/ptmnavigator"> PTM Navigator </v-tab>
    </v-tabs>

    <router-view />
  </v-main>
</template>

<script>
  export default {
    name: 'AnalyticsView'
  }
</script>

<style></style>
