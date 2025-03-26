<template>
  <div>
    <v-snackbar
      v-model="snackbar"
      :timeout="3000"
      color="error"
    >
      {{ errorMessage }}
    </v-snackbar>
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

export default {
  data: () => ({
    snackbar: false,
    errorMessage: '',
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
    async getEntityscoresstatus () {
      try {
        const response = await axios.get(`${process.env.VUE_APP_API_HOST}/entityscore/status`)
        this.customitemsStatus = response.data === 1
      } catch (error) {
        this.errorMessage = 'Error: No connection to backend'
        this.snackbar = true
      }
    }
  }
}
</script>
