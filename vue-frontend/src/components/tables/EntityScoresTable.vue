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
    :selection="{ mode: 'multiple', allowSelectAll: true }"
    :show-borders="true"
    column-resizing-mode="widget"
    :column-chooser="{ enabled: 'true', mode: 'select' }"
    @cell-prepared="onCellPrepared"
    @selection-changed="onSelectionChanged"
  >
    <DxExport :enabled="true" :allow-export-selected-data="true" />
    <DxFilterRow :visible="true" />
    <DxColumn data-field="Sample name" data-type="string" />
    <DxColumn data-field="code_oncotree" data-type="string" />

    <DxColumn
      v-for="entity in allEntities"
      :key="entity"
      :data-field="entity"
      data-type="number"
      :format="{ type: 'fixedPoint', precision: 3 }"
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
  import { DxDataGrid, DxPager, DxExport, DxPaging, DxFilterRow, DxColumn } from 'devextreme-vue/data-grid'

  import 'devextreme/dist/css/dx.light.css'
  import axios from 'axios'
  const dataGridRefKey = 'qc-table-data-grid'

  export default {
    components: {
      DxDataGrid,
      DxExport,
      DxPager,
      DxPaging,
      DxFilterRow,
      DxColumn
    },
    props: {
      dataSource: undefined,
      isLoading: {
        type: Boolean,
        default: false
      }
    },
    data() {
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
      cookieAccepted() {
        return this.$store.state.cookieAccepted
      }
    },
    watch: {
      isLoading() {
        // for some reason this does not work together with :scrolling="{ useNative: true }"
        if (this.isLoading) {
          this.dataGrid?.beginCustomLoading()
        } else {
          this.dataGrid?.endCustomLoading()
        }
      }
    },
    mounted() {
      this.getListModels()
    },
    methods: {
      saveGridState(state) {
        if (this.cookieAccepted) {
          const minimalState = {
            columns: state.columns
          }
          localStorage.setItem('gridStateEntitytable', JSON.stringify(minimalState))
        }
      },
      loadGridState() {
        if (this.cookieAccepted) {
          const savedState = localStorage.getItem('gridStateEntitytable')
          return savedState ? JSON.parse(savedState) : null
        }
      },
      async getListModels() {
        const response = await axios.get(
          `${import.meta.env.VITE_API_HOST}/entityscore/classifiers_list`
        )
        this.allEntities = response.data
      },
      onSelectionChanged: function (e) {
        this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
      },
      onCellPrepared(e) {
        this.allEntities.forEach(element => {
          const fieldName = element.toString()
          if (e.rowType === 'data') {
            if (e.column.dataField === fieldName && e.data[fieldName] > 0.9) {
              e.cellElement.style.cssText = 'color: white; background-color: #06a77d'
            }

            if (
              e.column.dataField === fieldName &&
              e.data[fieldName] <= 0.9 &&
              e.data[fieldName] > 0.5
            ) {
              e.cellElement.style.cssText = 'color: black; background-color: #e8f7ee'
            }

            if (e.column.dataField === fieldName && e.data[fieldName] <= 0.5) {
              e.cellElement.style.cssText = 'color: black; background-color: #E0E0E0'
            }
          }
        })
      }
    }
  }
</script>

<style>
  .dx-command-select {
    width: 30px !important;
    min-width: 30px !important;
  }
</style>
