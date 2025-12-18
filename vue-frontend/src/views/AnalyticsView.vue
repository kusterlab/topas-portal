<template>
  <v-main>
    <v-tabs>
      <v-tab to="/correlation" exact>Correlation</v-tab>
      <v-tab to="/pca" exact>PCA</v-tab>
      <v-tab to="/differential" exact>Differential</v-tab>
      <v-tab to="/heatmap" exact>Heatmap</v-tab>
      <v-tab to="/venn" exact>Venn</v-tab>
      <v-tab to="/kinobeads" exact>Kinobeads</v-tab>
      <v-tab to="/ptmnavigator" exact>PTM Navigator</v-tab>
    </v-tabs>

    <router-view />
  </v-main>
</template>

<script>
export default {
  name: 'AnalyticsComponent'
}
</script>

<style>

</style>
