<template>
  <v-main>
    <v-tabs>
      <v-tab to="/admin-tools" exact>Admin tools</v-tab>
    </v-tabs>

    <router-view />
  </v-main>
</template>

<script>
export default {
  name: 'SettingsView'
}
</script>

<style>

</style>
