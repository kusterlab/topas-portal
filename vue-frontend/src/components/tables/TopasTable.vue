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
    selectedPatient: {
      type: String,
      default: null
    }
  },
  data () {
    return {
      pageSizes: [15, 25, 50, 100],
      dataGridRefName: 'dataGrid',
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
    ...mapState({
      common_fields: state => state.common_fields
    }),
    topasFields () {
      return [...this.customFields, ...this.common_fields]
    },
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
  methods: {
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
    },
    onTableReady () {
      this.$emit('table-ready', { dataSource: this.dataSource })
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
