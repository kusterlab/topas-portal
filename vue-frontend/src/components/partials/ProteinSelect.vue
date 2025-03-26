<template>
  <div>
    <v-autocomplete
      v-model="selectedProteins"
      :items="allProteins"
      outlined
      prepend-icon="mdi-filter"
      dense
      hide-details
      auto-select-first
      :multiple="multiple"
      :clearable="multiple"
      :small-chips="multiple"
      :label="label_or_datalayer"
      @change="updateProteins"
    />
  </div>
</template>

<script>
import axios from 'axios'
import { mapMutations } from 'vuex'

export default {
  name: 'ProteinSelect',
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
      default: 'protein'
    },
    multiple: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    selectedProteins: '',
    allProteins: []
  }),
  computed: {
    label_or_datalayer () {
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
      this.loadProteins()
    },
    dataLayer: function () {
      this.loadProteins()
    }
  },

  mounted () {
    this.loadProteins()
  },
  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    async loadProteins () {
      if (this.cohortIndex < 0) return
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/${this.dataLayer}/list`)
        this.allProteins = response.data
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `An error occurred while retrieving the list of proteins for this cohort: ${error}`
        })
        this.allProteins = []
      }
    },
    updateProteins () {
      if (!this.selectedProteins || this.selectedProteins.length === 0) return
      this.$emit('select-protein', { dataSource: this.dataLayer, identifier: this.selectedProteins })
    }
  }
}
</script>
