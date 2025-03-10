<template>
  <div>
    <v-btn
      class="ma-2"
      color="primary"
      @click="clearSels"
    >
      <v-icon dark>
        mdi-refresh
      </v-icon>
    </v-btn>
    <DxDataGrid
      :ref="dataGridRefName"
      :data-source="dataSource"
      :remote-operations="false"
      :allow-column-reordering="true"
      :allow-column-resizing="true"
      :columns="qcFields"
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
      <DxPaging :page-size="17" />
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
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      pageSizes: [15, 25, 50, 100],
      dataGridRefName: 'dataGridQC',
      qcFields: [{
        dataField: 'Sample',
        dataType: 'string',
        visibleIndex: 0,
        width: '170'
      }, {
        dataField: 'pc1',
        dataType: 'number',
        visibleIndex: 0,
        width: '80'
      }, {
        dataField: 'pc2',
        dataType: 'number',
        visibleIndex: 0,
        width: '80'
      }]
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[this.dataGridRefName].instance
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
  created () {
    this.getCommonfield()
  },
  methods: {
    clearSels () {
      const dataGrid = this.$refs[this.dataGridRefName].instance
      dataGrid.clearSelection()
    },
    async getCommonfield () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/colnames`)
      const commonField = response.data
      commonField.forEach(element => {
        if (element.visible === 'false') {
          element.visible = false
        }
      })
      this.qcFields = [...this.qcFields, ...commonField]
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
