<template>
  <DxDataGrid
    :ref="gridRefKey"
    :key="componentKey"
    :data-source="dataSource"
    :remote-operations="false"
    :selection="{ mode: 'multiple', allowSelectAll: true}"
    :show-borders="true"
    :columns="correlationFields"
    :column-chooser="{ enabled: 'true', mode: 'select' }"
    :allow-column-resizing="true"
    @selection-changed="onSelectionChanged"
  >
    <DxFilterRow :visible="true" />
    <DxExport
      :enabled="true"
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
  DxPager,
  DxPaging,
  DxExport,
  DxFilterRow
} from 'devextreme-vue/data-grid'
import 'devextreme/dist/css/dx.light.css'
import { mapState } from 'vuex'

export default {
  components: {
    DxDataGrid,
    DxPager,
    DxExport,
    DxPaging,
    DxFilterRow
  },
  props: {
    dataSource: undefined,
    selectedPatient: {
      type: String,
      default: null
    },
    xAxis: {
      type: String,
      default: 'xAxis'
    },
    yAxis: {
      type: String,
      default: 'yAxis'
    }
  },
  data () {
    return {
      pageSizes: [10, 25, 50, 100],
      componentKey: 0,
      dataGridRefName: 'dataGrid',
      customFields: [{
        dataField: 'Sample name',
        dataType: 'string',
        visibleIndex: 0,
        width: '170'
      }, {
        dataField: 'xValue',
        caption: this.xAxis,
        dataType: 'number',
        format: { type: 'fixedPoint', precision: 2 },
        width: '70'
      }, {
        dataField: 'yValue',
        caption: this.yAxis,
        dataType: 'number',
        format: { type: 'fixedPoint', precision: 2 },
        width: '70'
      }]
    }
  },
  computed: {
    ...mapState({
      common_fields: state => state.common_fields
    }),
    correlationFields () {
      return [...this.customFields, ...this.common_fields]
    },
    dataGrid: function () {
      return this.$refs[this.dataGridRefName].instance
    }
  },
  watch: {
    selectedPatient: function () {
      this.filterBySamplename()
    }
  },
  methods: {
    filterBySamplename () {
      if (this.selectedPatient !== null) {
        this.dataGrid.filter([
          ['Sample name', '=', this.selectedPatient]
        ])
      } else {
        this.dataGrid.filter(null)
      }
    },
    reset: function () {
      // this.componentKey += 1
    },
    onSelectionChanged: function (e) {
      this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
    }
  }
}
</script>
