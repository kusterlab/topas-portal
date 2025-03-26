<template>
  <div>
    <v-tabs
      show-arrows
    >
      <v-tab
        v-for="item in items"
        :key="item.path"
        :to="item.path"
        class="tab-item"
      >
        <v-icon
          left
          class="tab-icon"
        >
          {{ item.icon }}
        </v-icon>
        <span class="tab-text">{{ item.label }}</span>
      </v-tab>
      <v-tab
        v-for="item in customitems"
        v-show="customitemsStatus"
        :key="item.path"
        :to="item.path"
        class="tab-item"
      >
        <v-icon
          left
          class="tab-icon"
        >
          {{ item.icon }}
        </v-icon>
        <span class="tab-text">{{ item.label }}</span>
      </v-tab>
    </v-tabs>

    <router-view />
  </div>
</template>

<script>
import axios from 'axios'
import { mapMutations } from 'vuex'

export default {
  data: () => ({
    imagesrc: require('@/assets/topas_logo.png'),
    items: [
      { label: 'Topas Scores', path: '/topasscores' },
      { label: 'Substrate Phosph. Scores', path: '/kinasescores' },
      { label: 'Protein Phosph. Scores', path: '/proteinscores' },
      { label: 'Subcohort z-scores', path: '/zscores' }
    ],
    customitems: [
      { label: 'Entity Scores', path: '/entityscores' }
    ],
    customitemsStatus: false
  }),
  mounted () {
    this.getEntityscoresstatus()
  },
  methods: {
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
    async getEntityscoresstatus () {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/entityscore/status`)
        this.customitemsStatus = response.data === 1
      } catch (error) {
        this.addNotification({
          color: 'error',
          message: 'Error: No connection to backend'
        })
      }
    }
  }
}
</script>
