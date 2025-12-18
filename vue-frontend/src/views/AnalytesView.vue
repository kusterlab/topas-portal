<template>
  <v-main>
    <v-tabs>
      <v-tab to="/abundance" exact>Abundance</v-tab>
      <v-tab to="/annotations">Annotations</v-tab>
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
