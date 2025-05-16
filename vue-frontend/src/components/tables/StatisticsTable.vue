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
      :ref="gridRefKey"
      :data-source="dataSource"
      :remote-operations="false"
      :allow-column-resizing="true"
      :selection="{ mode: 'multiple', allowSelectAll: true}"
      :show-borders="true"
      :scrolling="{ useNative: true }"
      :column-chooser="{ enabled: 'true', mode: 'select' }"
      @selection-changed="onSelectionChanged"
    >
      <DxExport
        :enabled="true"
        :allow-export-selected-data="true"
      />
      <DxFilterRow :visible="true" />

      <DxColumn
        data-field="Gene Names"
        data-type="string"
        :width="100"
      />
      <DxColumn
        data-field="t_statistics"
        data-type="number"
        :format="formatThreeSignificant"
        :width="60"
        :visible="false"
      />
      <DxColumn
        data-field="p_values"
        data-type="number"
        caption="p-val"
        :format="formatThreeSignificant"
        :width="60"
        :visible="true"
      />
      <DxColumn
        data-field="fdr"
        data-type="number"
        caption="FDR"
        :format="formatThreeSignificant"
        :width="60"
      />
      <DxColumn
        data-field="expression1"
        data-type="number"
        caption="Fold change"
        :format="formatThreeSignificant"
        :width="70"
        :visible="true"
      />
      <DxColumn
        data-field="means_group1"
        data-type="number"
        :format="formatThreeSignificant"
        :width="70"
        :visible="false"
      />
      <DxColumn
        data-field="means_group2"
        data-type="number"
        :format="formatThreeSignificant"
        :width="70"
        :visible="false"
      />
      <DxColumn
        data-field="num_samples_groups_interest"
        data-type="number"
        caption="#samples group1"
        :width="50"
        :visible="true"
      />
      <DxColumn
        data-field="num_sample_other_groups"
        data-type="number"
        caption="#samples group2"
        :width="50"
      />
      <DxColumn
        data-field="up_down"
        data-type="string"
        caption="Regulation"
        :width="60"
        :visible="true"
      />
      <DxColumn
        data-field="Site positions identified (MQ)"
        data-type="string"
        caption="MQ site Localization"
        :width="60"
        :visible="true"
      />
      <DxColumn
        data-field="Genes"
        data-type="string"
        caption="Protein Name"
        :width="60"
        :visible="true"
      />
      <DxColumn
        data-field="PSP Kinases"
        data-type="string"
        caption="PSP Kinase"
        :width="60"
        :visible="true"
      />
      <DxPager
        :allowed-page-sizes="pageSizes"
        :show-page-size-selector="true"
        :show-info="true"
        :show-navigation-buttons="true"
      />
      <DxPaging :page-size="10" />
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
  DxFilterRow
} from 'devextreme-vue/data-grid'
import 'devextreme/dist/css/dx.light.css'

export default {
  components: {
    DxDataGrid,
    DxColumn,
    DxExport,
    DxPager,
    DxPaging,
    DxFilterRow
  },
  props: {
    dataSource: undefined,
    selectedProtein: {
      type: String,
      default: null
    }
  },
  data () {
    return {
      pageSizes: [10, 25, 50, 100],
      gridRefKey: 'data-grid'
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[this.gridRefKey].instance
    }
  },
  watch: {
    selectedProtein: function () {
      this.filterBySamplename()
    }
  },
  methods: {
    filterBySamplename () {
      if (this.selectedProtein !== null) {
        this.dataGrid.filter([
          ['Gene Names', '=', this.selectedProtein]
        ])
      } else {
        this.dataGrid.filter(null)
      }
    },

    clearSels () {
      this.dataGrid.filter(null)
      const dataGrid = this.$refs[this.gridRefKey].instance
      dataGrid.clearSelection()
    },

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
