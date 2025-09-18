<template>
  <div>
    <DxDataGrid
      :ref="dataGridRefName"
      :data-source="dataSource"
      :remote-operations="false"
      :allow-column-reordering="true"
      :allow-column-resizing="true"
      :row-alternation-enabled="true"
      :selection="{ mode: 'multiple', allowSelectAll: true}"
      :show-borders="true"
      :scrolling="{ useNative: true }"
      column-resizing-mode="widget"
      :columns="topasFields"
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
      <DxPaging :page-size="15" />
      <DxToolbar>
        <DxItem
          location="before"
          locate-in-menu="auto"
          show-text="always"
          widget="dxButton"
          :options="refreshButtonOptions"
        />
        <DxItem
          name="exportButton"
        />
        <DxItem
          name="columnChooserButton"
        />
      </DxToolbar>
    </DxDataGrid>
  </div>
</template>
<script>

import {
  DxDataGrid,
  DxPager,
  DxExport,
  DxPaging,
  DxFilterRow,
  DxToolbar,
  DxItem
} from 'devextreme-vue/data-grid'

import 'devextreme/dist/css/dx.light.css'
import axios from 'axios'
export default {
  components: {
    DxDataGrid,
    DxExport,
    DxPager,
    DxPaging,
    DxFilterRow,
    DxToolbar,
    DxItem
  },
  props: {
    dataSource: undefined,
    selectedPatient: {
      type: String,
      default: null
    }
  },
  data () {
    return {
      pageSizes: [15, 25, 50, 100],
      dataGridRefName: 'dataGrid',
      commonFields: undefined,
      topasFields: undefined,
      customFields: [
        {
          dataField: 'Sample name',
          dataType: 'string',
          visibleIndex: 0,
          width: '170'
        }, {

          dataField: 'Z-score',
          dataType: 'number',
          format: { type: 'fixedPoint', precision: 2 },
          width: '70'
        }, {

          dataField: 'genomics_annotations',
          dataType: 'string',
          width: '120'
        }, {

          dataField: 'snv',
          dataType: 'string',
          width: '120'

        }, {

          dataField: 'cnv',
          dataType: 'string',
          width: '120'

        }, {

          dataField: 'fusion',
          dataType: 'string',
          width: '120'

        }, {

          dataField: 'fusion_onkoKB',
          dataType: 'string',
          width: '120'

        }, {

          dataField: 'cnv_onkoKB',
          dataType: 'string',
          width: '120'

        }, {

          dataField: 'snv_onkoKB',
          dataType: 'string',
          width: '120'

        }
      ]
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[this.dataGridRefName].instance
    },
    refreshButtonOptions () {
      return {
        icon: 'pulldown',
        text: 'Reset table',
        onClick: () => {
          this.filterBySamplename(null)
          this.dataGrid.clearFilter()
          this.dataGrid.clearSelection()
        }
      }
    }
  },
  watch: {
    selectedPatient: function () {
      this.filterBySamplename(this.selectedPatient)
    }
  },
  created () {
    this.getCommonfield()
  },
  methods: {
    async getCommonfield () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/colnames`)
      const commonField = response.data
      commonField.forEach(element => {
        if (element.visible === 'false') {
          element.visible = false
        }
      })
      this.topasFields = [...this.customFields, ...commonField]
    },
    filterBySamplename (sample) {
      if (sample !== null) {
        this.dataGrid.filter([
          ['Sample name', '=', sample]
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

<style>
.dx-command-select {
    width: 30px!important;
    min-width: 30px!important;
}
</style>
