<template>
  <v-card class="pa-0 bg-grey-lighten-4" max-width="430">
    <v-card-title> Highlight selected samples </v-card-title>
    <v-row dense>
      <v-col>
        <v-text-field class="px-4" density="compact" v-model="groupLabel" label="Label" placeholder="G1" max-width="200"/>
      </v-col>
      <v-col>
        <v-color-picker elevation="0" v-model="colorCode" hide-inputs hide-canvas max-width="200" mode="rgb" class="bg-grey-lighten-4" />
      </v-col>
      <v-col>
        <v-btn color="primary" @click="handleRedraw" class="mx-2">
          <v-icon> mdi-pencil </v-icon>
        </v-btn>
      </v-col>
    </v-row>
  </v-card>
</template>

<script>
  export default {
    name: 'HighlightSelection',
    data: () => ({
      groupLabel: '',
      colorCode: '#ff0000'
    }),

    methods: {
      handleRedraw() {
        this.$emit('highlight-selection', {
          groupLabel: this.groupLabel,
          colorCode: this.colorCode,
        })
      },
    }
  }
</script>
