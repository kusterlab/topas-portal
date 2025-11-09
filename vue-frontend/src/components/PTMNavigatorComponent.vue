<template>
  <ptm-navigator
    :backend-api="ptmnavigatorBackend"
    :ptm-navigator-router="router"
  />
</template>

<script>
import ptmNavigatorPrdbApi from '@/plugins/ptmNavigatorApi'

export default {
  name: 'PTMNavigatorWrapper',
  components: {
    'ptm-navigator': () => import('ptmnavigator').then(m => m.PTMNavigator)
  },
  data () {
    return {
      ptmnavigatorBackend: ptmNavigatorPrdbApi,
      router: this.$router
    }
  }
}
</script>

<style lang="scss" scoped>
::v-deep(button) {
  margin-bottom: 0;
}
</style>
