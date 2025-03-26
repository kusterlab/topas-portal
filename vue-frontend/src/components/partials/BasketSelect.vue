<template>
  <div>
    <v-autocomplete
      v-model="basketName"
      class="basket mt-1"
      dense
      outlined
      hide-details
      prepend-icon="mdi-filter"
      auto-select-first
      :items="allBaskets"
      :multiple="multiple"
      :clearable="multiple"
      :small-chips="multiple"
      :deletable-chips="multiple"
      label="Select kinase"
      @change="updateBasket"
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
        value="basket_score"
      />
    </v-radio-group>
  </div>
</template>

<script>
import axios from 'axios'
import { mapMutations } from 'vuex'

export default {
  name: 'BasketSelect',
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
    basketName: null,
    allBaskets: [],
    dataSource: 'z_score',
    showTopasRtkOnly: true
  }),
  computed: {
    allSelected: function () {
      return this.basketName && this.allBaskets.length === this.basketName.length
    }
  },
  watch: {
    cohortIndex: function () {
      this.basketComboupdater()
    },
    showTopasRtkOnly: function () {
      this.basketComboupdater()
    },
    dataSource: function () {
      this.updateBasket()
    }
  },
  mounted () {
    this.basketComboupdater()
  },
  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    async basketComboupdater () { // retrieving different basket types RTK or main from the backend
      if (this.cohortIndex < 0) return

      const categories = this.showTopasRtkOnly ? 'RTK' : 'all'
      const baskets = []
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/basket/${this.cohortIndex}/basketids/${categories}`)

        response.data.forEach(element => {
          if (element.ids !== 'num_identified' && element.ids !== 'num_annotated') {
            baskets.push(element.ids)
          }
        })
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: `An error occurred while processing response data: ${error}`
        })
      }

      this.allBaskets = baskets
    },
    updateBasket () {
      if (!this.basketName || this.basketName.length === 0) return
      this.$emit('select-basket', { dataSource: this.dataSource, identifier: this.basketName })
    },
    selectAll () {
      if (this.allSelected) {
        this.basketName = null
      } else {
        this.basketName = this.allBaskets
      }
      this.updateBasket()
    }
  }
}
</script>
