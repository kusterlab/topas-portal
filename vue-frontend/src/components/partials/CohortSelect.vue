<template>
  <div>
    <v-select
      v-model="diseaseName"
      class="cohort"
      prepend-icon="mdi-database"
      dense
      outlined
      hide-details
      :items="all_diseases"
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
    diseaseName: ''
  }),
  computed: {
    ...mapState({
      all_diseases: state => state.all_diseases
    }),
    ...mapGetters({
      hasData: 'hasData'
    }),
    cookieAccepted () {
      return this.$store.state.cookieAccepted
    },
    cohortIndex: function () {
      return this.all_diseases.indexOf(this.diseaseName)
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
      this.cohortIndex = this.$store.state.cohortIndex
      this.diseaseName = this.$store.state.diseaseName
    },
    updateCohort () {
      if (!this.diseaseName || this.diseaseName.length === 0) return
      this.$emit('select-cohort', { dataSource: this.diseaseName, cohortIndex: this.cohortIndex })
      this.setCohortIndex({ diseaseName: this.diseaseName, cohortIndex: this.cohortIndex })
    }
  }
}
</script>
