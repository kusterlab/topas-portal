<template>
  <div>
    <v-btn-toggle
      v-if="showToggle"
      v-model="selectionMethod"
      color="primary"
      mandatory
    >
      <v-btn value="metadata" class="flex-grow-1 px-3"> Metadata </v-btn>
      <v-btn v-if="showTableSelect" value="table" class="px-3"> Table </v-btn>
      <v-btn value="samplelist" class="flex-grow-1 px-3"> List </v-btn>
    </v-btn-toggle>
    <v-autocomplete
      v-if="selectionMethod === 'metadata'"
      v-model="metadataType"
      prepend-icon="mdi-account"
      auto-select-first
      :items="metaDatatypes"
      label="Metadata column"
      @update:model-value="metaDataChanged"
      class="mt-2"
    />
    <v-autocomplete
      v-if="selectionMethod === 'metadata'"
      v-model="metadataValuesSelected"
      prepend-icon="mdi-filter"
      class="mt-4"
      auto-select-first
      multiple
      chips
      :items="metadataTypeFields"
      label="Group of interest"
      @update:model-value="metadataValuesSelectedChanged"
    />
    <v-textarea
      v-if="selectionMethod !== 'metadata'"
      v-model="customGroup"
      clear-icon="mdi-close-circle"
      :placeholder="textareaPlaceholder"
      :readonly="selectionMethod === 'table'"
      clearable
      rows="4"
      @update:model-value="updateSampleIdList"
    />
  </div>
</template>

<script>
  import axios from 'axios'
  import { mapMutations } from 'vuex'

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
      },
      showTableSelect: {
        type: Boolean,
        default: false
      }
    },
    data: () => ({
      selectionMethod: 'metadata',
      metadataType: 'Sample name',
      metadataTypeFields: [],
      metaDatatypes: [],
      metadataValuesSelected: null
    }),
    computed: {
      customGroup: {
        get: function () {
          if (this.sampleIds === null) {
            return ''
          }
          return this.sampleIds.join('\n')
        },
        set: function () {}
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
    mounted() {
      this.updateMetadata()
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      async updateMetadata() {
        if (this.cohortIndex === -1) {
          return
        }
        let response = []
        try {
          response = await axios.get(
            `${import.meta.env.VITE_API_HOST}/${this.cohortIndex}/metadata/fields`
          )
          this.metaDatatypes = response.data
          this.metaDataChanged()
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: 'Error: Probably no meta data exists for this cohort'
          })
        }
      },
      async metaDataChanged() {
        const metadataType = this.metadataType
        this.metadataValuesSelected = null
        let response = []
        try {
          response = await axios.get(
            `${import.meta.env.VITE_API_HOST}/${this.cohortIndex}/metadata/fields/${metadataType}`
          )
          this.metadataTypeFields = response.data
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: `Error: ${error}`
          })
        }
      },
      async metadataValuesSelectedChanged() {
        if (!this.metadataValuesSelected || this.metadataValuesSelected.length === 0) {
          this.updateSampleIds([])
          return
        }

        try {
          const response = await axios.get(
            `${import.meta.env.VITE_API_HOST}/${this.cohortIndex}/metadata/fields/${this.metadataType}/patients/${this.metadataValuesSelected}`
          )
          this.updateSampleIds(response.data)
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: `Error: ${error}`
          })
        }
      },
      updateSampleIdList(sampleIds) {
        if (!sampleIds) {
          sampleIds = ''
        }
        this.updateSampleIds(sampleIds.split('\n'))
      },
      updateSampleIds(sampleIds) {
        if (this.selectionMethod !== 'metadata') {
          this.metadataValuesSelected = null
        }
        this.$emit('update-group', sampleIds)
        this.$emit('update-metadata-type', this.metadataType)
        this.$emit('update-metadata-values-selected', this.metadataValuesSelected)
      }
    }
  }
</script>
