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
import axios from 'axios'
import 'devextreme/dist/css/dx.light.css'
const gridRefKey = 'data-grid'

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
      gridRefKey,
      commonFileds: undefined,
      correlationFields: [{
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
    dataGrid: function () {
      return this.$refs[gridRefKey].instance
    }
  },
  watch: {
    selectedPatient: function () {
      this.filterBySamplename()
    }
  },
  created () {
    this.getCommonField()
  },
  methods: {
    async getCommonField () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/colnames`)
      const commonField = response.data
      commonField.forEach(element => {
        if (element.visible === 'false') {
          element.visible = false
        }
      })
      this.correlationFields = [...this.correlationFields, ...commonField]
    },
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
