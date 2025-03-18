<template>
  <div>
    <v-btn-toggle
      v-if="showToggle"
      v-model="selectionMethod"
      color="primary"
      mandatory
      dense
      class="mb-0"
    >
      <v-btn value="metadata">
        Metadata
      </v-btn>
      <v-btn value="table">
        Table
      </v-btn>
      <v-btn value="samplelist">
        List
      </v-btn>
    </v-btn-toggle>
    <v-autocomplete
      v-if="selectionMethod === 'metadata'"
      v-model="activeMeta"
      prepend-icon="mdi-account"
      dense
      outlined
      hide-details
      auto-select-first
      :items="metaDatatypes"
      label="Metadata column"
      @change="metaDataChanged"
    />
    <v-autocomplete
      v-if="selectionMethod === 'metadata'"
      v-model="fieldOfInterest"
      prepend-icon="mdi-filter"
      class="mt-4"
      dense
      small-chips
      outlined
      hide-details
      auto-select-first
      :multiple="true"
      :items="activemetaFields"
      label="Group of interest"
      @change="fieldOfInterestChanged"
    />
    <v-textarea
      v-if="selectionMethod !== 'metadata'"
      v-model="customGroup"
      clear-icon="mdi-close-circle"
      :placeholder="textareaPlaceholder"
      :readonly="selectionMethod === 'table'"
      clearable
      outlined
      hide-details
      height="120"
      @change="updateSampleIdList"
    />
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SampleSelect',
  props: {
    cohortIndex: {
      type: Number,
      default: -1
    },
    sampleIds: {
      type: Array,
      default: () => []
    },
    showToggle: {
      type: Boolean,
      default: true
    }
  },
  data: () => ({
    selectionMethod: 'metadata',
    activeMeta: 'Sample name',
    activemetaFields: [],
    metaDatatypes: [],
    fieldOfInterest: null
  }),
  computed: {
    customGroup: {
      get: function () {
        if (this.sampleIds === null) {
          return ''
        }
        return this.sampleIds.join('\n')
      },
      set: function (newValue) {
      }
    },
    textareaPlaceholder: function () {
      if (this.selectionMethod === 'table') {
        return 'select patients in table'
      } else {
        return 'one patient per line'
      }
    }
  },
  watch: {
    cohortIndex: async function () {
      this.updateMetadata()
    },
    selectionMethod: function () {
      // toggle visibility of the sample selection table in the parent component
      this.$emit('update-selection-method', this.selectionMethod)
    }
  },
  mounted () {
    this.updateMetadata()
  },
  methods: {
    async updateMetadata () {
      if (this.cohortIndex === -1) {
        return
      }
      let response = []
      try {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/metadata/fields`)
        this.metaDatatypes = response.data
        this.metaDataChanged()
      } catch (error) {
        alert('Error: Probably no meta data exists for this cohort')
        console.error(error)
      }
    },
    async metaDataChanged () {
      const activeMeta = this.activeMeta
      this.fieldOfInterest = null
      let response = []
      try {
        response = await axios.get(`${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/metadata/fields/${activeMeta}`)
        this.activemetaFields = response.data
      } catch (error) {
        alert(`Error:${error}`)
        console.error(`Error: ${error}`)
      }
    },
    async fieldOfInterestChanged () {
      if (!this.fieldOfInterest || this.fieldOfInterest.length === 0) {
        this.updateSampleIds([])
        return
      }

      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/${this.cohortIndex}/metadata/fields/${this.activeMeta}/patients/${this.fieldOfInterest}`)
        this.updateSampleIds(response.data)
      } catch (error) {
        alert(`Error:${error}`)
        console.error(`Error: ${error}`)
      }
    },
    updateSampleIdList (sampleIds) {
      if (!sampleIds) {
        sampleIds = ''
      }
      this.updateSampleIds(sampleIds.split('\n'))
    },
    updateSampleIds (sampleIds) {
      if (this.selectionMethod !== 'metadata') {
        this.fieldOfInterest = null
      }
      this.$emit('update-group', sampleIds)
      this.$emit('update-field', this.fieldOfInterest)
      this.$emit('update-meta', this.activeMeta)
      // this will return both the sample names and the meta data types
    }
  }
}
</script>
