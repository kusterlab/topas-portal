<template>
  <DxDataGrid
    :ref="gridRefKey"
    :data-source="dataSource"
    :remote-operations="false"
    :allow-column-reordering="true"
    :row-alternation-enabled="true"
    :show-borders="true"
    :column-chooser="{ enabled: 'true', mode: 'select' }"
  >
    <DxExport
      :enabled="true"
      :allow-export-selected-data="true"
    />

    <DxFilterRow :visible="true" />

    <DxColumn
      data-field="Sample name"
      data-type="string"
      :width="180"
    />

    <DxColumn
      data-field="Entity"
      data-type="string"
      :width="120"
    />

    <DxColumn
      data-field="Batch_No"
      data-type="number"
      :width="60"
    />

    <DxColumn
      data-field="TMT_channel"
      data-type="number"
      :width="60"
    />
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
  DxColumn,
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
    DxColumn,
    DxPager,
    DxPaging,
    DxExport,
    DxFilterRow
  },

  props: {
    dataSource: undefined,
    selectedBatch: {
      type: Number,
      default: null
    }
  },
  data () {
    return {
      pageSizes: [10, 25, 50, 100],
      gridRefKey
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[gridRefKey].instance
    }
  },
  methods: {
    filterByBatch () {
      if (this.selectedBatch !== null) {
        this.dataGrid.filter([
          ['Batch', '=', this.selectedBatch]
        ])
      } else {
        this.dataGrid.filter(null)
      }
    },
    onSelectionChanged: function (e) {
      this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
    }
  }
}
</script>
