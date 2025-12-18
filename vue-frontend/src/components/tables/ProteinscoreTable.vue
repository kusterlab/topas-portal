<template>
  <div>
    <DxDataGrid
      :ref="dataGridRefName"
      :data-source="dataSource"
      :remote-operations="false"
      :allow-column-resizing="true"
      :column-auto-width="true"
      :columns="phosphorylationFields"
      :scrolling="{ useNative: true }"
      :selection="{ mode: 'multiple', allowSelectAll: true}"
      :show-borders="true"
      :column-chooser="{ enabled: 'true', mode: 'select' }"
      @selection-changed="onSelectionChanged"
      @content-ready="onTableReady"
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
    dataSource: undefined
  },
  data () {
    return {
      pageSizes: [10, 25, 50, 100],
      dataGridRefName: 'dataGrid',
      customFields: [{
        dataField: 'Sample name',
        dataType: 'string',
        visibleIndex: 0,
        width: '170'
      }, {
        dataField: 'Z-score',
        caption: 'Phosphorylation_score',
        format: { type: 'fixedPoint', precision: 2 },
        dataType: 'number',
        visibleIndex: 0,
        width: '80'
      }, {

        dataField: 'genomics_annotations',
        dataType: 'string',
        width: '120'
      }, {

        dataField: 'oncoKB_annotations',
        dataType: 'string',
        width: '120'
      }]
    }
  },
  computed: {
    ...mapState({
      common_fields: state => state.common_fields
    }),
    phosphorylationFields () {
      return [...this.customFields, ...this.common_fields]
    },
    refreshButtonOptions () {
      return {
        icon: 'pulldown',
        text: 'Reset table',
        onClick: () => {
          this.$refs[this.dataGridRefName].instance.clearSelection()
        }
      }
    }
  },
  methods: {
    onSelectionChanged: function (e) {
      this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
    },
    onTableReady () {
      this.$emit('table-ready', { dataSource: this.dataSource })
    }
  }
}
</script>

<style>
#grid {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.selected-data {
  margin-top: 20px;
  padding: 20px;
  background-color: rgba(191, 191, 191, 0.15);
}

.selected-data .caption {
  font-weight: bold;
  font-size: 115%;
  margin-right: 4px;
}

</style>
