<template>
  <DxDataGrid
    :ref="gridRefKey"
    :data-source="dataSource"
    :remote-operations="false"
    :allow-column-reordering="true"
    :allow-column-resizing="true"
    :row-alternation-enabled="true"
    :scrolling="{ useNative: true }"
    :show-borders="true"
    :columns="columns"
    :column-chooser="{ enabled: 'true', mode: 'select' }"
    @content-ready="onGridReady"
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
    <DxPaging :page-size="25" />
  </DxDataGrid>
</template>
<script>

import {
  DxDataGrid,
  DxPager,
  DxPaging,
  DxExport,
  DxFilterRow
} from 'devextreme-vue/data-grid'

import 'devextreme/dist/css/dx.light.css'
const gridRefKey = 'data-grid'
export default {
  components: {
    DxDataGrid,
    DxPager,
    DxPaging,
    DxExport,
    DxFilterRow
  },

  props: {
    dataSource: undefined
  },
  data () {
    return {
      pageSizes: [10, 25, 50, 100],
      gridRefKey,
      columns: [],
      lastColumnKeys: null,
      masterColumns: {
        'Modified sequence group': { width: 300, visible: false },
        'Site positions (PSP)': { width: 300, visible: false },
        PSP_LT_LIT: { width: 50, visible: false },
        PSP_MS_LIT: { width: 50, visible: false },
        'Modified sequence representative': { width: 300 }
      }
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[gridRefKey].instance
    }
  },
  methods: {
    onSelectionChanged: function (e) {
      this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
    },
    onGridReady (e) {
      const ds = e.component.getDataSource()
      const items = ds?.items()
      if (!items?.length) return

      const keys = Object.keys(items[0])
      const keySignature = keys.join('|')

      if (this.lastColumnKeys === keySignature) return

      this.lastColumnKeys = keySignature

      this.columns = keys.map(key => {
        const master = this.masterColumns[key] || {}
        return {
          dataField: key,
          ...master
        }
      })
    }
  }
}
</script>
