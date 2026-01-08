<template>
  <div>
    <v-checkbox
      v-model="savePlot"
      label="Plot export"
      @update:model-value="changeSaveplot"
    />
  </div>
</template>

<script>
export default {
  name: 'PlotsSaveStatus', // the status of the plots export
  data: () => ({
    savePlot: false
  }),

  methods: {
    changeSaveplot () {
      this.$emit('status', { status: this.savePlot })
    }
  }
}
</script>
