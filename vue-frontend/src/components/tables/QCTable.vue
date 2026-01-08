<template>
  <div>
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
import { mapState } from 'vuex'

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
    isLoading: {
      type: Boolean,
      default: false
    }
  },
  data () {
    return {
      pageSizes: [15, 25, 50, 100],
      dataGridRefName: 'dataGridQC',
      customFields: [{
        dataField: 'Sample',
        dataType: 'string',
        visibleIndex: 0,
        width: '170'
      }, {
        dataField: 'pc1',
        dataType: 'number',
        visibleIndex: 0,
        format: { type: 'fixedPoint', precision: 2 },
        width: '60'
      }, {
        dataField: 'pc2',
        dataType: 'number',
        visibleIndex: 0,
        format: { type: 'fixedPoint', precision: 2 },
        width: '60'
      }]
    }
  },
  computed: {
    ...mapState({
      common_fields: state => state.common_fields
    }),
    qcFields () {
      return [...this.customFields, ...this.common_fields]
    },
    dataGrid: function () {
      return this.$refs[this.dataGridRefName]?.instance
    },
    refreshButtonOptions () {
      return {
        icon: 'pulldown',
        text: 'Reset table',
        onClick: () => {
          this.dataGrid?.clearFilter()
          this.dataGrid?.clearSelection()
        }
      }
    }
  },
  watch: {
    isLoading () {
      // for some reason this does not work together with :scrolling="{ useNative: true }"
      if (this.isLoading) {
        this.dataGrid?.beginCustomLoading()
      } else {
        this.dataGrid?.endCustomLoading()
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
