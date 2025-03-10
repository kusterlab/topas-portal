<template>
  <div>
    <v-col
      sm="4"
      lg="4"
      md="4"
    >
      <v-text-field
        v-model="cohortName"
        style="width:1000px;"
        label="New Cohort"
      />
    </v-col>
    <v-col
      sm="4"
      lg="4"
      md="4"
    >
      <v-btn
        @click="addCohort"
      >
        Adding cohort name to config file
      </v-btn>
    </v-col>
    <ConfigUpdate
      :update-mode="false"
      :cohort-name="addedcohortName"
    />
  </div>
</template>

<script>
import axios from 'axios'
import ConfigUpdate from './ConfigUpdate.vue'
export default {
  name: 'AddCohort',
  components: {
    ConfigUpdate
  },
  data: () => ({
    cohortName: '',
    addedcohortName: ''
  }),
  methods: {
    async addCohort () {
      await axios.get(`${process.env.VUE_APP_API_HOST}/addcohort/${this.cohortName}`)
      alert('Added - You should update the path and upload the cohort')
      this.addedcohortName = this.cohortName
    }
  }
}
</script>
