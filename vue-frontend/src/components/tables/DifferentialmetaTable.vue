<template>
  <div>
    <v-text-field
      label="Gene for genomics annotation"
      placeholder="EGFR"
      class="mt-2"
      @change="updatePatientTable"
    />

    <v-checkbox
      v-model="advancedFilter"
      label="Advanced table filter"
    />
    <div v-show="advancedFilter" class="filter-container">
      <DxFilterBuilder
        :value="filter"
        :fields="differentialFields"
        @value-changed="onChangeEvent"
      />
    </div>

    <DxDataGrid
      :ref="dataGridRefName"
      :data-source="dataSource"
      :remote-operations="false"
      :filter-value="gridFilterValue"
      :column-auto-width="true"
      :columns="differentialFields"
      :allow-column-resizing="true"
      :selection="{ mode: 'multiple', allowSelectAll: true }"
      :show-borders="true"
      :scrolling="{ useNative: true }"
      :column-chooser="{ enabled: 'true', mode: 'select' }"
      @selection-changed="onSelectionChanged"
    >
      <DxExport :enabled="true" :allow-export-selected-data="true" />
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
        <DxItem name="exportButton" />
        <DxItem name="columnChooserButton" />
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
  import DxFilterBuilder from 'devextreme-vue/filter-builder'

  const filter = []
  export default {
    components: {
      DxDataGrid,
      DxFilterBuilder,
      DxExport,
      DxPager,
      DxPaging,
      DxFilterRow,
      DxToolbar,
      DxItem
    },
    props: {
      cohortIndex: {
        type: Number,
        default: -1
      }
    },
    data() {
      return {
        filter,
        advancedFilter: false,
        genomicAlterationsGene: null,
        genomicAlterationsGene2: null,
        gridFilterValue: filter,
        pageSizes: [10, 25, 50],
        dataGridRefName: 'dataGrid',
        previousDataSource: '',
        customFields: [
          {
            dataField: 'Sample name',
            dataType: 'string',
            visibleIndex: 0,
            width: '170'
          },
          {
            dataField: 'genomics_annotations',
            dataType: 'string',
            width: '120'
          },
          {
            dataField: 'oncoKB_annotations',
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
      differentialFields() {
        return [...this.customFields, ...this.common_fields]
      },
      dataSource: function () {
        if (this.cohortIndex === -1) {
          return
        }
        return `${import.meta.env.VITE_API_HOST}/${this.cohortIndex}/patients/genomics_annotations/${this.genomicAlterationsGene}`
      },
      dataGrid: function () {
        return this.$refs[this.dataGridRefName]?.instance
      },
      refreshButtonOptions() {
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
      cohortIndex: async function () {
        this.updatePatientTable(this.genomicAlterationsGene)
      }
    },
    methods: {
      updatePatientTable(genomicAlterationsGene) {
        // do not use v-model because that triggers rerendering while typing
        this.genomicAlterationsGene = genomicAlterationsGene
      },
      onChangeEvent(e) {
        this.filter = e.component.option('value')
        this.gridFilterValue = this.filter
      },
      onSelectionChanged: function (e) {
        this.$emit('onRowSelect', e.selectedRowKeys, e.selectedRowsData)
      }
    }
  }
</script>

<style scoped>
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

  .filter-container {
    background-color: rgba(191, 191, 191, 0.15);
    padding: 5px;
    width: 500px;
  }

  .dx-filterbuilder {
    padding: 10px;
  }

  .dx-button {
    margin: 10px;
    float: right;
  }

  .dx-filterbuilder .dx-numberbox {
    width: 80px;
  }
</style>
