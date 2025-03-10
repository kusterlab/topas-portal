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
      :label="label"
      @change="updateProteins"
    />
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ProteinSelect',
  props: {
    cohortIndex: {
      type: Number,
      default: -1
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
    label () {
      if (this.multiple) {
        return `Select ${this.dataLayer}s`
      } else {
        return `Select ${this.dataLayer}`
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
    async loadProteins () {
      if (this.cohortIndex < 0) return
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/${this.dataLayer}/list`)
      this.allProteins = response.data
    },
    updateProteins () {
      if (!this.selectedProteins || this.selectedProteins.length === 0) return
      this.$emit('select-protein', { dataSource: this.dataLayer, identifier: this.selectedProteins })
    }
  }
}
</script>
