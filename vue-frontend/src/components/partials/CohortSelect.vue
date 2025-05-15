<template>
  <div>
    <v-select
      v-model="cohortName"
      class="cohort"
      prepend-icon="mdi-database"
      dense
      outlined
      hide-details
      :items="all_cohorts"
      label="Cohort"
      @change="updateCohort"
    />
  </div>
</template>
<script>
import { mapGetters, mapState } from 'vuex'
export default {
  name: 'CohortSelect',
  props: {
  },
  data: () => ({
    cohortName: ''
  }),
  computed: {
    ...mapState({
      all_cohorts: state => state.all_cohorts
    }),
    ...mapGetters({
      hasData: 'hasData'
    }),
    cookieAccepted () {
      return this.$store.state.cookieAccepted
    },
    cohortIndex: function () {
      return this.all_cohorts.indexOf(this.cohortName)
    }
  },
  mounted () {
    this.loadDefaultCohort()
    this.updateCohort()
  },
  methods: {
    setCohortIndex (newValue) {
      this.$store.commit('setCohortIndex', newValue)
    },
    loadDefaultCohort () {
      this.cohortName = this.$store.state.cohortName
    },
    updateCohort () {
      if (!this.cohortName || this.cohortName.length === 0) return
      this.$emit('select-cohort', { dataSource: this.cohortName, cohortIndex: this.cohortIndex })
      this.setCohortIndex({ cohortName: this.cohortName, cohortIndex: this.cohortIndex })
    }
  }
}
</script>
