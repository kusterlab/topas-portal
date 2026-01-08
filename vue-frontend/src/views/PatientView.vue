<template>
  <v-main>
    <v-tabs>
      <v-tab
        to="/patient-report"
        exact
      >
        Patient report
      </v-tab>
      <v-tab to="/cohort-stats">
        Cohort statistics
      </v-tab>
    </v-tabs>

    <router-view />
  </v-main>
</template>

<script>
export default {
  name: 'PatientView'
}
</script>

<style></style>
