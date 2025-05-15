<template>
  <div>
    <v-checkbox
      v-model="advancedFilter"
      hide-details
      dense
      label="Advanced table filter"
    />
    <div
      v-show="advancedFilter"
      class="filter-container"
    >
      <DxFilterBuilder
        :value="filter"
        :fields="Drugfields"
        @value-changed="onChangeEvent"
      />
    </div>
    <DxDataGrid
      :data-source="dataSource"
      :filter-value="gridFilterValue"
      :show-borders="true"
      :allow-column-resizing="true"
      :selection="{ mode: 'single', allowSelectAll: false}"
      column-resizing-mode="widget"
      :columns="Drugfields"
      :column-min-width="0"
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

      <DxSorting mode="none" />
      <DxPaging :page-size="10" />
    </DxDataGrid>
  </div>
</template>
<script>
import DxFilterBuilder from 'devextreme-vue/filter-builder'
import 'devextreme/dist/css/dx.light.css'
import {
  DxDataGrid,
  DxPager,
  DxExport,
  DxFilterRow,
  DxSorting,
  DxPaging
} from 'devextreme-vue/data-grid'
const filter = []
const Drugfields = [
  {
    dataField: 'Drug',
    dataType: 'string'
  },
  {
    dataField: 'Kinobeads_TargetGenes',
    dataType: 'string'
  },
  {
    dataField: 'Designated_TargetGenes',
    dataType: 'string'
  },
  {
    dataField: 'Other targets',
    dataType: 'string'
  },
  {
    dataField: 'Clinical Phase',
    dataType: 'string'
  }
]

export default {
  components: {
    DxFilterBuilder,
    DxDataGrid,
    DxPager,
    DxExport,
    DxFilterRow,
    DxSorting,
    DxPaging
  },
  props: {
    dataSource: undefined
  },
  data () {
    return {
      Drugfields,
      filter,
      advancedFilter: false,
      gridFilterValue: filter,
      kino_genes: [],
      pageSizes: [10, 25, 50, 100]
    }
  },
  methods: {
    onSelectionChanged ({ selectedRowsData }) {
      const data = selectedRowsData[0].Kinobeads_TargetGenes
      const array = data.split(',')
      const finalAr = []
      array.forEach(element => (finalAr.push(element.replace('(', '(Kdapp = '))))
      this.kino_genes = finalAr
      let maxim = 0
      const plotData = []
      array.forEach(element => {
        const item = {}
        item.Drug = element.split(' ')[0]
        item.Kdapp = parseInt(element.split(' ')[1].slice(1, -1))
        if (item.Kdapp > maxim) { maxim = item.Kdapp }
        plotData.push(item)
      })
      const allBarData = {}
      allBarData.plotData = plotData
      allBarData.maximum = maxim
      this.$emit('getGenes', allBarData)
    },

    onChangeEvent (e) {
      this.filter = e.component.option('value')
      this.gridFilterValue = this.filter
    }

  }
}

</script>

<style scoped>
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
