<template>
  <DxDataGrid
    :data-source="dataSource"
    :remote-operations="false"
    :row-alternation-enabled="true"
    :selection="{ mode: 'single'}"
    :show-borders="true"
    :allow-column-resizing="true"
    :scrolling="{ useNative: true }"
    :column-chooser="{ enabled: 'true', mode: 'select' }"
    @selection-changed="onSelectionChanged"
  >
    <DxFilterRow :visible="true" />
    <DxExport
      :enabled="true"
    />

    <DxColumn
      data-field="index"
      data-type="string"
      caption="Gene / Modified sequence"
      :width="400"
    />
    <DxColumn
      data-field="rank"
      data-type="number"
      :min-width="50"
    />
    <DxColumn
      data-field="num_patients"
      data-type="number"
      caption="#patients"
      :min-width="75"
    />
    <DxColumn
      data-field="p-value"
      data-type="number"
      :format="formatThreeSignificant"
      :min-width="80"
    />
    <DxColumn
      data-field="FDR"
      data-type="number"
      :format="formatThreeSignificant"
      :min-width="80"
    />
    <DxColumn
      data-field="correlation"
      data-type="number"
      :format="formatThreeSignificant"
      :min-width="85"
    />
    <DxColumn
      v-if="correlationInputType == 'basket_score'"
      data-field="weight"
      data-type="number"
      caption="Basket weight"
      :min-width="50"
    />
    <DxColumn
      v-if="correlationType == 'psite'"
      data-field="Gene names"
      data-type="string"
      :min-width="100"
    />
    <DxColumn
      v-if="correlationType == 'psite'"
      data-field="PSP Kinases"
      data-type="string"
      :min-width="100"
    />
    <DxColumn
      v-if="correlationType == 'psite'"
      data-field="Site positions identified (MQ)"
      data-type="string"
      caption="PSP Site"
      :min-width="130"
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

export default {
  components: {
    DxDataGrid,
    DxColumn,
    DxPager,
    DxExport,
    DxPaging,
    DxFilterRow
  },
  props: {
    dataSource: undefined,
    correlationInputType: {
      type: String,
      default: ''
    },
    correlationType: {
      type: String,
      default: ''
    }
  },
  data () {
    return {
      pageSizes: [10, 25, 50, 100]
    }
  },
  methods: {
    onSelectionChanged: function (e) {
      this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
    },
    formatThreeSignificant: function (value) {
      if (Math.abs(value) < 1e-3) {
        return value.toExponential(2)
      } else {
        return value.toFixed(3)
      }
    }
  }
}
</script>
