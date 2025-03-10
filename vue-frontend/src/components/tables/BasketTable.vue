<template>
  <div>
    <v-btn
      class="ma-2"
      color="primary"
      @click="clearSels"
    >
      <v-icon
        dark
      >
        mdi-refresh
      </v-icon>
    </v-btn>
    <DxDataGrid
      :ref="dataGridRefName"
      :data-source="dataSource"
      :remote-operations="false"
      :allow-column-reordering="true"
      :allow-column-resizing="true"
      :row-alternation-enabled="true"
      :selection="{ mode: 'multiple', allowSelectAll: true}"
      :show-borders="true"
      column-resizing-mode="widget"
      :columns="tupacFields"
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
    </DxDataGrid>
  </div>
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
import axios from 'axios'
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
      tupacFields: undefined,
      customFields: [{
        dataField: 'Sample name',
        dataType: 'string',
        visibleIndex: 0,
        width: '170'
      }, {

        dataField: 'Z-score',
        dataType: 'number',
        width: '100'
      }, {

        dataField: 'genomics_annotations',
        dataType: 'string',
        width: '120'
      }, {

        dataField: 'oncoKB_annotations',
        dataType: 'string',
        width: '120'
      }
      ]
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[this.dataGridRefName].instance
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
      this.tupacFields = [...this.customFields, ...commonField]
    },
    filterBySamplename (sample) {
      const dataGrid = this.$refs[this.dataGridRefName].instance
      if (sample !== null) {
        dataGrid.filter([
          ['Sample name', '=', sample]
        ])
      } else {
        dataGrid.filter(null)
      }
    },
    clearSels () {
      this.filterBySamplename(null)
      const dataGrid = this.$refs[this.dataGridRefName].instance
      dataGrid.clearSelection()
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
