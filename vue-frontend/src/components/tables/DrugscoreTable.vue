<template>
  <div>
    <DxDataGrid
      :ref="dataGridRefName"
      :data-source="dataSource"
      :remote-operations="false"
      :allow-column-resizing="true"
      :column-auto-width="true"
      :scrolling="{ useNative: true }"
      :selection="{ mode: 'multiple', allowSelectAll: true}"
      :show-borders="true"
      :column-chooser="{ enabled: 'true', mode: 'select' }"
      @selection-changed="onSelectionChanged"
    >
      <DxExport
        :enabled="true"
        :allow-export-selected-data="true"
      />
      <DxFilterRow :visible="true" />

      <DxColumn
        data-field="Sample name"
        data-type="string"
        :width="170"
      />

      <DxColumn
        data-field="is_replicate"
        data-type="string"
        :width="70"
        :visible="false"
      />

      <DxColumn
        data-field="Entity_y"
        data-type="string"
        :width="70"
        :visible="true"
      />

      <DxColumn
        data-field="code_oncotree"
        data-type="string"
        :width="70"
        :visible="true"
      />

      <DxColumn
        data-field="breadcrumb_oncotree"
        data-type="string"
        :width="70"
        :visible="true"
      />

      <DxColumn
        data-field="Drug_score"
        data-type="number"
        :format="{type: 'fixedPoint', precision: 2}"
        :width="80"
      />

      <DxColumn
        data-field="Histologic subtype"
        data-type="string"
        :width="60"
      />
      <DxColumn
        data-field="Histologic subtype, specifications"
        data-type="string"
        :width="60"
      />

      <DxColumn
        data-field="tissue_topology"
        data-type="string"
        :min-width="60"
      />
      <DxColumn
        data-field="Tissue_origin"
        data-type="string"
        :min-width="60"
      />
      <DxColumn
        data-field="tissue_topology_specification"
        data-type="string"
        :min-width="60"
      />
      <DxColumn
        data-field="tissue_primarius"
        data-type="string"
        :min-width="60"
      />

      <DxColumn
        data-field="NGS_FGFR"
        data-type="string"
        :min-width="60"
      />

      <DxColumn
        data-field="NGS_PDGFR"
        data-type="string"
        :min-width="60"
      />

      <DxColumn
        data-field="NGS_ERBB2"
        data-type="string"
        :min-width="60"
      />

      <DxColumn
        data-field="NGS_KIT"
        data-type="string"
        :min-width="60"
      />

      <DxColumn
        data-field="NGS_EGFR"
        data-type="string"
        :min-width="60"
      />

      <DxColumn
        data-field="Sex"
        data-type="string"
        :min-width="60"
      />

      <DxColumn
        data-field="Batch_No"
        data-type="number"
        :width="60"
      />

      <DxColumn
        data-field="comment"
        data-type="string"
        :width="60"
      />

      <DxColumn
        data-field="Tumor cell content"
        data-type="string"
      />
      <DxColumn
        data-field="Timeline"
        data-type="string"
        :width="100"
        :visible="false"
      />
      <DxColumn
        data-field="ICD03 - Morpho"
        data-type="string"
        :min-width="150"
        :visible="false"
      />

      <DxColumn
        data-field="Program"
        data-type="string"
        :width="80"
        :visible="false"
      />

      <DxColumn
        data-field="Tumor/Metastisis"
        data-type="string"
        :visible="false"
      />
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
  DxColumn,
  DxPager,
  DxExport,
  DxPaging,
  DxFilterRow,
  DxToolbar,
  DxItem
} from 'devextreme-vue/data-grid'
import 'devextreme/dist/css/dx.light.css'

export default {
  components: {
    DxDataGrid,
    DxColumn,
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
      dataGridRefName: 'dataGrid'
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
          this.dataGrid.clearFilter()
          this.dataGrid.clearSelection()
        }
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
