<template>
  <div>
    <v-main>
      <v-toolbar
        color="white"
      >
        <v-tabs
          v-model="tabIndex"
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
        </v-tabs>
      </v-toolbar>

      <router-view />
    </v-main>
  </div>
</template>

<script>

export default {
  data: () => ({
    imagesrc: require('@/assets/topas_logo.png'),
    items: [
      { label: 'Topas Scores', path: '/topasscores' },
      { label: 'Substrate Phoshphorylation Scores', path: '/kinasescores' },
      { label: 'Protein Phoshphorylation Scores', path: '/proteinscores' },
      { label: 'Z Scores', path: '/zscores' }
    ]
  })
}
</script>
