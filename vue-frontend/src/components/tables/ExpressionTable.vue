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
      :state-storing="{
        enabled: true,
        type: 'custom',
        customLoad: loadGridState,
        customSave: saveGridState
      }"
      :column-auto-width="true"
      :columns="expressionFields"
      :allow-column-resizing="true"
      :allow-column-reordering="true"
      :selection="{ mode: 'multiple', allowSelectAll: true }"
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
      expressionFields: undefined
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[this.dataGridRefName].instance
    },
    cookieAccepted () {
      return this.$store.state.cookieAccepted
    }
  },
  watch: {
    selectedPatient: function () {
      this.filterBySamplename(this.selectedPatient)
    }
  },
  created () {
    this.gettableFields()
  },
  methods: {

    saveGridState (state) {
      if (this.cookieAccepted) {
        localStorage.setItem('gridStateExpression', JSON.stringify(state))
      }
    },
    loadGridState () {
      if (this.cookieAccepted) {
        const savedState = localStorage.getItem('gridStateExpression')
        return savedState ? JSON.parse(savedState) : null
      }
    },
    async gettableFields () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/colnames`)
      const commonField = response.data
      commonField.forEach(element => {
        if (element.visible === 'false') {
          element.visible = false
        }
      })
      this.expressionFields = [...[{
        dataField: 'Sample name',
        dataType: 'string',
        visibleIndex: 0,
        width: '170'
      },
      {
        dataField: 'Rank',
        dataType: 'number',
        width: '50'
      }, {
        dataField: 'Occurrence',
        dataType: 'number',
        width: '50'
      }, {
        dataField: 'FC',
        dataType: 'number',
        format: { type: 'fixedPoint', precision: 2 },
        width: '60'
      }, {
        dataField: 'Z-score',
        dataType: 'number',
        format: { type: 'fixedPoint', precision: 2 },
        width: '70'
      }, {
        dataField: 'Intensity',
        dataType: 'number',
        format: { type: 'fixedPoint', precision: 2 },
        width: '70'
      }, {
        dataField: 'num_pep',
        dataType: 'number',
        width: '40'
      }, {
        dataField: 'genomics_annotations',
        dataType: 'string',
        width: '120'
      }, {
        dataField: 'oncoKB_annotations',
        dataType: 'string',
        width: '120'
      }, {
        dataField: 'confidence_score',
        dataType: 'number',
        format: { type: 'fixedPoint', precision: 2 },
        width: '60'
      }], ...commonField]
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
