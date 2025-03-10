<template>
  <DxDataGrid
    :ref="dataGridRefKey"
    :data-source="dataSource"
    :state-storing="{
      enabled: true,
      type: 'custom',
      customLoad: loadGridState,
      customSave: saveGridState
    }"
    :remote-operations="false"
    :allow-column-reordering="true"
    :allow-column-resizing="true"
    :row-alternation-enabled="true"
    :scrolling="{ useNative: true }"
    :selection="{ mode: 'multiple', allowSelectAll: true}"
    :show-borders="true"
    column-resizing-mode="widget"
    :column-chooser="{ enabled: 'true', mode: 'select' }"
    @cell-prepared="onCellPrepared"
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
    <DxPaging :page-size="10" />
  </DxDataGrid>
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
const dataGridRefKey = 'qc-table-data-grid'

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
      pageSizes: [10, 25, 50, 100],
      allEntities: ['LMS'],
      dataGridRefKey
    }
  },
  computed: {
    dataGrid: function () {
      return this.$refs[dataGridRefKey].instance
    },
    cookieAccepted () {
      return this.$store.state.cookieAccepted
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
  mounted () {
    this.getListModels()
  },
  methods: {
    saveGridState (state) {
      if (this.cookieAccepted) {
        localStorage.setItem('gridStateEntitytable', JSON.stringify(state))
      }
    },
    loadGridState () {
      if (this.cookieAccepted) {
        const savedState = localStorage.getItem('gridStateEntitytable')
        return savedState ? JSON.parse(savedState) : null
      }
    },
    async getListModels () {
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/entityscore/classifiers_list`)
      this.allEntities = response.data
    },
    onSelectionChanged: function (e) {
      this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
    },
    onCellPrepared (e) {
      this.allEntities.forEach(element => {
        const fieldName = element.toString()
        if (e.rowType === 'data') {
          if (e.column.dataField === fieldName && e.data[fieldName] > 0.75) {
            e.cellElement.style.cssText = 'color: white; background-color: red'
          }
          if (e.column.dataField === fieldName && e.data[fieldName] <= 0.75 && e.data[fieldName] > 0.5) {
            e.cellElement.style.cssText = 'color: black; background-color: yellow'
          }
          if (e.column.dataField === fieldName && e.data[fieldName] <= 0.35) {
            e.cellElement.style.cssText = 'color: white; background-color: grey'
          }
        }
      })
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
