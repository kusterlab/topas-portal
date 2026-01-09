<template>
  <div>
    <v-autocomplete
      v-model="selectedPhosphopeptides"
      :items="allPhosphopeptides"
      variant="outlined"
      prepend-icon="mdi-filter"
      density="default"
      hide-details
      auto-select-first
      :multiple="multiple"
      :clearable="multiple"
      :chips="multiple"
      :label="label_or_datalayer"
      :loading="allPhosphopeptides.length === 0"
      @update:model-value="updatePhosphopeptides"
    />
  </div>
</template>

<script>
  import axios from 'axios'
  import { mapMutations } from 'vuex'
  import { DataType } from '@/constants'

  export default {
    name: 'PhosphopeptideSelect',
    props: {
      cohortIndex: {
        type: Number,
        default: -1
      },
      label: {
        type: String,
        default: ''
      },
      dataLayer: {
        type: String,
        default: DataType.PHOSPHO_PROTEOME
      },
      multiple: {
        type: Boolean,
        default: false
      }
    },
    data: () => ({
      selectedPhosphopeptides: '',
      allPhosphopeptides: []
    }),
    computed: {
      label_or_datalayer() {
        let label = this.dataLayer
        if (this.label.length > 0) {
          label = this.label
        }
        if (this.multiple) {
          return `Select ${label}s`
        } else {
          return `Select ${label}`
        }
      }
    },
    watch: {
      cohortIndex: function () {
        this.loadPhosphopeptides()
      },
      dataLayer: function () {
        this.loadPhosphopeptides()
      }
    },

    mounted() {
      this.loadPhosphopeptides()
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      async loadPhosphopeptides() {
        if (this.cohortIndex < 0) return
        try {
          const response = await axios.get(
            `${import.meta.env.VITE_API_HOST}/${this.cohortIndex}/${this.dataLayer}/list`
          )
          this.allPhosphopeptides = response.data
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: `An error occurred while retrieving the list of phosphopeptides for this cohort: ${error}`
          })
          this.allPhosphopeptides = []
        }
      },
      updatePhosphopeptides() {
        if (!this.selectedPhosphopeptides || this.selectedPhosphopeptides.length === 0) return
        this.$emit('select-phosphopeptide', {
          dataSource: this.dataLayer,
          identifier: this.selectedPhosphopeptides
        })
      }
    }
  }
</script>
