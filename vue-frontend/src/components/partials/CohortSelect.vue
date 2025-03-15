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
              label="Cohort / Cell Type"
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
  watch: {
    diseaseName: function () {
      return this.loaddefaultCohort()
    }
  },
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
    this.loaddefaultCohort()
  },
  methods: {
    savedefaultCohort (state) {
      if (this.cookieAccepted) {
        localStorage.setItem('defaultCohort', JSON.stringify(state))
      }
    },
    loaddefaultCohort () {
      if (this.cookieAccepted) {
        const savedState = localStorage.getItem('defaultCohort')
        this.diseaseName = savedState ? JSON.parse(savedState) : ''
      }
    },
    updateCohort () {
      if (!this.diseaseName || this.diseaseName.length === 0) return
      this.savedefaultCohort(this.diseaseName)
      this.$emit('select-cohort', { dataSource: this.diseaseName, cohortIndex: this.cohortIndex })
    }
  }
}
</script>
