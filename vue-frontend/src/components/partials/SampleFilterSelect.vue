<template>
  <div>
    <v-switch v-model="showRefChannels" label="Show ref channels" density="compact" class="mt-2"/>
    <v-switch v-model="showExcludedChannels" label="Show excluded channels" density="compact" class="mb-4"/>
  </div>
</template>
<script>
  import { SampleFilter } from '@/constants'

  export default {
    name: 'SampleFilterSelect',
    props: {},
    data: () => ({
      showRefChannels: false,
      showExcludedChannels: false
    }),
    computed: {
      sampleFilter() {
        if (this.showRefChannels) {
          if (this.showExcludedChannels) {
            return SampleFilter.ALL
          } else {
            return SampleFilter.PATIENTS_AND_REF
          }
        } else {
          if (this.showExcludedChannels) {
            return SampleFilter.PATIENTS_AND_EXCLUDED
          } else {
            return SampleFilter.ONLY_PATIENTS
          }
        }
      }
    },
    mounted() {
    },
    watch: {
      sampleFilter() {
        this.$emit('update-sample-filter', { sampleFilter: this.sampleFilter })
      }
    }
  }
</script>
