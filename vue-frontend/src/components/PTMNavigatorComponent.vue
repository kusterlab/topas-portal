<template>
  <ptm-navigator :backend-api="ptmnavigatorBackend" :ptm-navigator-router="router" />
</template>

<script>
  import ptmNavigatorPrdbApi from '@/plugins/ptmNavigatorApi'
  import { PTMNavigator } from 'ptmnavigator-vue3'
  export default {
    name: 'PTMNavigatorWrapper',
    components: { 'ptm-navigator': PTMNavigator },
    // components: {
    //   'ptm-navigator': () => import('ptmnavigator-vue3').then(m => {
    //     console.log(Object.keys(m))
    //     return m.PTMNavigator
    //   }).catch(e => console.warn(e))
    // },
    data() {
      return {
        ptmnavigatorBackend: ptmNavigatorPrdbApi,
        router: this.$router
      }
    },
    mounted() {
      if (!window.customElements.get('biowc-pathwaygraph')) {
        console.warn('Missing biowc-pathwaygraph - PTM viz may fail')
      }
    }
  }
</script>

<style lang="scss" scoped>
  ::v-deep(button) {
    margin-bottom: 0;
  }
</style>
