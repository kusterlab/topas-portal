<template>
  <v-main>
    <v-tabs>
      <v-tab to="/patient_report" exact>Patient report</v-tab>
      <v-tab to="/cohort_stats">Cohort statistics</v-tab>
    </v-tabs>

    <router-view />
  </v-main>
</template>

<script>
export default {
  name: 'PatientComponent'
}
</script>

<style></style>
