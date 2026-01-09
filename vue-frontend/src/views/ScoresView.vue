<template>
  <div>
    <v-tabs show-arrows>
      <v-tab
        v-for="(item, index) in allTabs"
        :key="item.path"
        :to="item.path"
        :exact="index === 0"
        :text="item.label"
      />
      <!-- <v-tab
        v-for="item in customitems"
        v-show="customitemsStatus"
        :key="item.path"
        :to="item.path"
        :text="item.label"
      /> -->
    </v-tabs>

    <router-view />
  </div>
</template>

<script>
  import axios from 'axios'
  import { mapMutations } from 'vuex'

  export default {
    data: () => ({
      items: [
        { label: 'Topas Scores', path: '/topasscores' },
        { label: 'Substrate Phosph. Scores', path: '/kinasescores' },
        { label: 'Protein Phosph. Scores', path: '/proteinscores' },
        { label: 'Subcohort z-scores', path: '/zscores' }
      ],
      customitems: [{ label: 'Entity Scores', path: '/entityscores' }],
      customitemsStatus: false
    }),
    computed: {
      allTabs() {
        return [...this.items, ...(this.customitemsStatus ? this.customitems : [])]
      }
    },
    mounted() {
      this.getEntityscoresstatus()
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      async getEntityscoresstatus() {
        try {
          const response = await axios.get(`${import.meta.env.VITE_API_HOST}/entityscore/status`)
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
