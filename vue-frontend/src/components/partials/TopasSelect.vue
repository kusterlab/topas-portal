<template>
  <div>
    <v-autocomplete
      v-model="topasName"
      class="topas mt-1"
      dense
      outlined
      hide-details
      prepend-icon="mdi-filter"
      auto-select-first
      :items="allTopass"
      :multiple="multiple"
      :clearable="multiple"
      :small-chips="multiple"
      :deletable-chips="multiple"
      label="Select kinase"
      @change="updateTopas"
    >
      <template #prepend-item>
        <v-list-item
          v-show="multiple"
          ripple
        >
          <v-list-item-action>
            <v-simple-checkbox
              :value="allSelected"
              :ripple="true"
              @click="selectAll"
            />
          </v-list-item-action>
          <v-list-item-content>
            <v-list-item-title>Select All</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
        <v-divider v-show="multiple" />
      </template>
    </v-autocomplete>
    <v-checkbox
      v-if="scoreType"
      v-model="showTopasRtkOnly"
      class="ml-8"
      label="TOPAS RTKs only"
      hide-details
      dense
    />
    <v-radio-group
      v-if="scoreType"
      v-model="dataSource"
      label="Score type"
    >
      <v-radio
        label="TOPAS Z-scores"
        value="z_score"
      />
      <v-radio
        label="TOPAS raw scores"
        value="topas_score"
      />
    </v-radio-group>
  </div>
</template>

<script>
import axios from 'axios'
import { mapMutations } from 'vuex'

export default {
  name: 'TopasSelect',
  props: {
    scoreType: {
      type: Boolean,
      default: true
    },
    cohortIndex: {
      type: Number,
      default: -1
    },
    multiple: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    topasName: null,
    allTopass: [],
    dataSource: 'z_score',
    showTopasRtkOnly: true
  }),
  computed: {
    allSelected: function () {
      return this.topasName && this.allTopass.length === this.topasName.length
    }
  },
  watch: {
    cohortIndex: function () {
      this.topasComboupdater()
    },
    showTopasRtkOnly: function () {
      this.topasComboupdater()
    },
    dataSource: function () {
      this.updateTopas()
    }
  },
  mounted () {
    this.topasComboupdater()
  },
  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    async topasComboupdater () { // retrieving different topas types RTK or main from the backend
      if (this.cohortIndex < 0) return

      const categories = this.showTopasRtkOnly ? 'RTK' : 'all'
      const topass = []
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/topas/${this.cohortIndex}/topasids/${categories}`)

        response.data.forEach(element => {
          if (element.ids !== 'num_identified' && element.ids !== 'num_annotated') {
            topass.push(element.ids)
          }
        })
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `An error occurred while processing response data: ${error}`
        })
      }

      this.allTopass = topass
    },
    updateTopas () {
      if (!this.topasName || this.topasName.length === 0) return
      this.$emit('select-topas', { dataSource: this.dataSource, identifier: this.topasName })
    },
    selectAll () {
      if (this.allSelected) {
        this.topasName = null
      } else {
        this.topasName = this.allTopass
      }
      this.updateTopas()
    }
  }
}
</script>
