<template>
  <ptm-navigator
    :backend-api="ptmnavigatorBackend"
    :ptm-navigator-router="router"
  />
</template>

<script>
import { PTMNavigator } from 'ptmnavigator'
import ptmNavigatorPrdbApi from '@/plugins/ptmNavigatorApi'

export default {
  name: 'PTMNavigatorWrapper',
  components: {
    'ptm-navigator': PTMNavigator
  },
  data () {
    return {
      ptmnavigatorBackend: ptmNavigatorPrdbApi,
      router: this.$router
    }
  }
}
</script>
