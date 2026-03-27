<template>
  <v-row class="ma-1">
    <v-btn-toggle
      v-model="allPatients"
      color="primary"
      density="compact"
      mandatory
      class="flex-grow-1"
    >
      <v-btn value="cohort" class="mb-0 flex-grow-1"> Full </v-btn>
      <v-btn value="subcohort" class="mb-0 flex-grow-1"> Subcohort </v-btn>
    </v-btn-toggle>
    <v-container v-if="allPatients === 'subcohort'">
      <sample-select
        :cohort-index="cohortIndex"
        :sample-ids="sampleIds"
        :show-table-select="showTableSelect"
        @update-group="updateSampleGroup"
        @update-selection-method="updateSelectionMethodGroup"
      />
    </v-container>
  </v-row>
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
      },
      showTableSelect: {
        type: Boolean,
        default: false
      }
    },
    data: () => ({
      allPatients: 'cohort',
      customGroup: [],
      selectionMethod: 'none'
    }),
    computed: {},
    watch: {
      allPatients: function () {
        this.emitGroup()
        this.emitSelectionMethod()
      }
    },
    mounted() {},
    methods: {
      updateSampleGroup(data) {
        if (this.allPatients === 'cohort') {
          this.customGroup = []
        } else {
          this.customGroup = data
        }
        this.emitGroup()
      },
      updateSelectionMethodGroup(data) {
        if (this.allPatients === 'cohort') {
          this.selectionMethod = 'none'
        } else {
          this.selectionMethod = data
        }
        this.emitSelectionMethod()
      },
      emitGroup() {
        this.$emit('update-group', this.customGroup)
      },
      emitSelectionMethod() {
        this.$emit('update-selection-method', this.selectionMethod)
      }
    }
  }
</script>
