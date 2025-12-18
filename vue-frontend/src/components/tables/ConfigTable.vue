<template>
  <DxDataGrid
    :ref="dataGridRefKey"
    :data-source="dataSource"
    :allow-column-resizing="true"
    :scrolling="{ useNative: true }"
    :show-borders="false"
  >
    <DxExport
      :enabled="true"
      :allow-export-selected-data="true"
    />

    <DxPager
      :show-info="true"
      :show-navigation-buttons="true"
    />
    <DxPaging :page-size="10" />
  </DxDataGrid>
</template>
<script>

import {
  DxDataGrid,
  DxPager,
  DxExport,
  DxPaging
} from 'devextreme-vue/data-grid'

import 'devextreme/dist/css/dx.light.css'

const dataGridRefKey = 'qc-table-data-grid'

export default {
  components: {
    DxDataGrid,
    DxExport,
    DxPager,
    DxPaging
  },
  props: {
    dataSource: undefined,
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      pageSizes: [10, 25, 50, 100],
      dataGridRefKey
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[dataGridRefKey].instance
    }
  },
  watch: {
    isLoading () {
      // for some reason this does not work together with :scrolling="{ useNative: true }"
      if (this.isLoading) {
        this.dataGrid.beginCustomLoading()
      } else {
        this.dataGrid.endCustomLoading()
      }
    }
  }
}
</script>

  <style>
  .dx-command-select {
      width: 30px!important;
      min-width: 30px!important;
  }
  </style>
