<template>
  <DxDataGrid
    :ref="dataGridRefKey"
    :data-source="dataSource"
    :remote-operations="false"
    :allow-column-reordering="true"
    :allow-column-resizing="true"
    :row-alternation-enabled="true"
    :scrolling="{ useNative: true }"
    :selection="{ mode: 'multiple', allowSelectAll: true}"
    :show-borders="true"
    column-resizing-mode="widget"
    :column-chooser="{ enabled: 'true', mode: 'select' }"
    @selection-changed="onSelectionChanged"
  >
    <DxExport
      :enabled="true"
      :allow-export-selected-data="true"
    />
    <DxFilterRow :visible="true" />

    <DxPager
      :allowed-page-sizes="pageSizes"
      :show-page-size-selector="true"
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
  DxPaging,
  DxFilterRow
} from 'devextreme-vue/data-grid'

import 'devextreme/dist/css/dx.light.css'

const dataGridRefKey = 'qc-table-data-grid'

export default {
  components: {
    DxDataGrid,
    DxExport,
    DxPager,
    DxPaging,
    DxFilterRow
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
  },
  methods: {
    onSelectionChanged: function (e) {
      this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
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
