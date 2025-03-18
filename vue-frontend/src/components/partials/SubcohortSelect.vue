<template>
  <div>
    <v-btn-toggle
      v-model="allPatients"
      color="primary"
      mandatory
      hide-details
      dense
      class="mt-4"
    >
      <v-btn
        value="cohort"
        class="mb-0"
        tile
      >
        Full cohort
      </v-btn>
      <v-btn
        value="subcohort"
        class="mb-0"
        tile
      >
        Subcohort
      </v-btn>
    </v-btn-toggle>
    <v-card
      v-if="allPatients === 'subcohort'"
    >
      <v-card-text class="pa-3">
        <sample-select
          :cohort-index="cohortIndex"
          :sample-ids="sampleIds"
          @update-group="updateSampleGroup"
          @update-selection-method="updateSelectionMethodGroup"
        />
      </v-card-text>
    </v-card>
  </div>
</template>
<script>
import SampleSelect from './SampleSelect.vue'

export default {
  name: 'SubcohortSelect',
  components: {
    SampleSelect
  },
  props: {
    cohortIndex: {
      type: Number,
      default: -1
    },
    sampleIds: {
      type: Array,
      default: () => []
    }
  },
  data: () => ({
    allPatients: 'cohort',
    customGroup: [],
    selectionMethod: 'none'
  }),
  computed: {
  },
  watch: {
    allPatients: function () {
      this.emitGroup()
      this.emitSelectionMethod()
    }
  },
  mounted () {
  },
  methods: {
    updateSampleGroup (data) {
      if (this.allPatients === 'cohort') {
        this.customGroup = []
      } else {
        this.customGroup = data
      }
      this.emitGroup()
    },
    updateSelectionMethodGroup (data) {
      if (this.allPatients === 'cohort') {
        this.selectionMethod = 'none'
      } else {
        this.selectionMethod = data
      }
      this.emitSelectionMethod()
    },
    emitGroup () {
      this.$emit('update-group', this.customGroup)
    },
    emitSelectionMethod () {
      this.$emit('update-selection-method', this.selectionMethod)
    }
  }
}
</script>
