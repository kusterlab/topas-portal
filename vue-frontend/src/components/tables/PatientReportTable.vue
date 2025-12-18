<template>
  <div>
    <DxDataGrid
      :ref="dataGridRefName"
      :data-source="dataSource"
      :remote-operations="false"
      :allow-column-reordering="true"
      :allow-column-resizing="true"
      :row-alternation-enabled="true"
      :selection="{ mode: 'multiple', allowSelectAll: true }"
      :show-borders="true"
      column-resizing-mode="widget"
      :columns="topasFields"
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
          location="before"
          locate-in-menu="auto"
          show-text="always"
          widget="dxButton"
          :disabled="patientReportUrl.length === 0"
          :options="downloadReportsButtonOptions"
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
import axios from 'axios'
import { mapMutations, mapState } from 'vuex'

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
    },
    patientReportUrl: {
      type: String,
      default: null
    }
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
      }]
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
          this.dataGrid.clearFilter()
          this.dataGrid.clearSelection()
        }
      }
    },
    downloadReportsButtonOptions () {
      return {
        icon: 'download',
        text: 'Download report(s)',
        onClick: () => {
          this.downloadReports()
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
    ...mapMutations({
      addNotification: 'notifications/addNotification'
    }),
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
    forceFileDownload: function (response, title) {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', title)
      document.body.appendChild(link)
      link.click()
    },
    downloadReports: function () {
      const patientIdentifiers = this.dataGrid.getSelectedRowsData().map(item => item['Sample name'])
      let outputFilename = ''
      if (patientIdentifiers.length === 0) {
        this.addNotification({
          color: 'error',
          message: 'Error: please select one or more patients'
        })
        return
      }
      if (patientIdentifiers.length === 1) {
        outputFilename = patientIdentifiers[0] + '_patient_report.xlsx'
      } else {
        outputFilename = 'patient_reports.zip'
      }
      this.addNotification({
        color: 'info',
        message: 'Downloading patient reports, this may take a while.'
      })
      axios.get(this.patientReportUrl.replace(':patients', patientIdentifiers.join(',')), { responseType: 'arraybuffer' })
        .then((response) => {
          this.forceFileDownload(response, outputFilename)
        })
        .catch((e) => {
          const enc = new TextDecoder()
          this.addNotification({
            color: 'error',
            message: 'Error: ' + enc.decode(e.response.data)
          })
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
