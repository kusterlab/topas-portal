<template>
  <div id="container">
    <v-row>
      <v-col
        sm="12"
        md="2"
        lg="2"
      >
        <div id="selectedItems">
          <v-text-field
            v-model="selectedBatch"
            value=""
            label="Selected Group"
            readonly
          />
        </div>
        <div id="uniqSize">
          <v-text-field
            v-model="uniqueSize"
            value=""
            label="# Unique"
            readonly
          />
          <v-text-field
            id="selected-size"
            v-model="selectedSize"
            value=""
            label="# Selected"
            readonly
          />
        </div>
      </v-col>
      <v-col
        sm="12"
        md="3"
        lg="3"
      >
        <div>
          <div id="venn" />
        </div>
      </v-col>
    </v-row>
    <v-row>
      <v-radio-group
        v-model="tableCriteria"
      >
        <v-radio
          label="Show None"
          color="red"
          value="none"
        />
        <v-radio
          label="Show all items in the selected area"
          color="blue"
          value="all"
        />
        <v-radio
          label="Show unique items in the selected area"
          color="green"
          value="uniq"
        />
      </v-radio-group>
    </v-row>
    <v-row>
      <v-btn
        class="ma-2"
        color="primary"
        @click="downloadSVG"
      >
        SVG
        <v-icon
          dark
        >
          mdi-cloud-download
        </v-icon>
      </v-btn>
    </v-row>
    <v-row>
      <v-col
        sm="12"
        md="7"
        lg="7"
      >
        <v-table theme="dark">
          <thead>
            <tr>
              <th class="text-left">
                Search:       <input
                  v-model="search"
                  type="text"
                  label="search"
                  class="search-txt"
                >
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in filteredItems"
              :key="item"
            >
              <td>{{ item }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-col>
    </v-row>
  </div>
</template>

<script>
import memberships from './vennFunctions'
import utils from '@/plugins/DownloadUtils'
// import JsonExcel from 'vue-json-excel'
const venn = require('venn.js')
const d3 = require('d3')
const matrix = require('matrix-js')

export default {
  name: 'VennPlot',
  components: {
  },
  props: {
    vennplotData: {
      // The data should be structured as bellow
      /*
      const plotSet = [
        { sample: 'gene1', group: 'A' },
        { sample: 'gene2', group: 'A' },
        { sample: 'gene2', group: 'B' },
        { sample: 'gene3', group: 'B' },
        { sample: 'gene1', group: 'C' },
        { sample: 'gene3', group: 'C' },
        { sample: 'gene4', group: 'C' }
      ]
      */
      type: Array,
      default: undefined
    }
  },
  data: () => ({
    itemsPerPage: 5,
    headers: [
      {
        title: 'sample',
        align: 'start',
        sortable: true,
        key: 'sample'
      }
    ],
    finalPlotData: [{ sample: 'gene1', group: 'A' }],
    selectedBatch: '',
    selectedProteins: [],
    uniqProteins: [],
    selectedSize: 0,
    uniqueSize: 0,
    search: '',
    tableCriteria: 'none',
    showListIntersect: true,
    showListDiff: true
  }),
  computed: {
    filteredItems () {
      let tempFiltered = this.tableCriteria === 'uniq' ? this.uniqProteins : this.selectedProteins
      tempFiltered = this.tableCriteria === 'none' ? [] : tempFiltered
      return tempFiltered.filter(item => {
        return item.toLowerCase().indexOf(this.search.toLowerCase()) > -1
      })
    }
  },
  watch: {
    vennplotData: function () {
      this.plotVennDiagram()
    }
  },
  methods: {
    downloadSVG () {
      const aPlots = []
      aPlots.push(d3.select(this.$el).select('svg').node())
      if (aPlots.length > 0) {
        utils.downloadSVGs(
          aPlots,
          'overlap Plot',
          false,
          'canvasId',
          []
        )
      }
    },
    // https://github.com/benfred/venn.js
    plotVennDiagram () {
      const that = this
      const plotSet = this.vennplotData
      const uniquegroups = memberships.getUniqList(plotSet)
      const assignedMat = matrix(memberships.getMemFunc(uniquegroups.length))

      // preparation of the plot set
      const finalSet = []
      for (let i = 0; i < assignedMat.size()[0]; i++) {
        const element = {}
        const sett = []
        for (let j = 0; j < assignedMat.size()[1]; j++) {
          if (assignedMat(i, j) === 1) {
            sett.push(uniquegroups[j])
          }
        }
        element.sets = sett
        finalSet.push(element)
      }

      // calculating proteins list and interserction sizse
      finalSet.forEach(element => {
        element.proteins = []
        if (element.sets.length === 1) {
          // only one group
          const indGrp = uniquegroups.indexOf(element.sets[0])
          element.proteins = memberships.getProteinList(plotSet, uniquegroups[indGrp])
        } else {
          // 2 groups
          const indGrp1 = uniquegroups.indexOf(element.sets[0])
          const grpList1 = memberships.getProteinList(plotSet, uniquegroups[indGrp1])
          const indGrp2 = uniquegroups.indexOf(element.sets[1])
          const grpList2 = memberships.getProteinList(plotSet, uniquegroups[indGrp2])
          let interSectList = memberships.getIntersection(grpList1, grpList2)
          // more than two groups
          if (element.sets.length > 2) { // more than 2 venn
            for (let z = 2; z < element.sets.length; z++) {
              const indGrp = uniquegroups.indexOf(element.sets[z])
              const grpList = memberships.getProteinList(plotSet, uniquegroups[indGrp])
              interSectList = memberships.getIntersection(interSectList, grpList)
            }
          }
          element.proteins = interSectList
        }
        element.size = element.proteins.length
      })
      this.finalPlotData = finalSet

      // let sets = this.finalPlotData
      const sets = this.finalPlotData.filter(element => element.size > 0)
      /*
         sets = sets.sort(function(a, b) {
          // Compare the 2 dates
          if (a.size < b.size) return -1;
          if (a.size > b.size) return 1;
          return 0;
        });
        */

      // plot
      const div = d3.select('#venn')
      div.datum(sets).call(venn.VennDiagram())
      // add listeners to all the groups to display tooltip on mouseover
      div.selectAll('g')
        .on('click', function (event, d) {
          venn.sortAreas(div, d)
          // highlight the current path
          console.log(event)
          // console.log(selGrp)
          const selection = d3.select(this).transition('tooltip').duration(400)
          that.selectedBatch = selection._groups[0][0].__data__.sets
          that.selectedProteins = []
          that.uniqProteins = []
          let currentDiff = []
          if (that.showListIntersect) { that.selectedProteins = selection._groups[0][0].__data__.proteins }
          that.uniqueSize = ''
          if (that.selectedBatch.length === 1) {
            currentDiff = selection._groups[0][0].__data__.proteins
            const selGrp = that.selectedBatch.toString()
            for (let p = 0; p < uniquegroups.length; p++) {
              if (uniquegroups[p] !== selGrp) {
                // console.log(uniquegroups[p])
                currentDiff = memberships.getDifference(currentDiff, memberships.getProteinList(plotSet, uniquegroups[p]))
                const uniqueIds = []
                currentDiff.filter(element => {
                  const isDuplicate = uniqueIds.includes(element)
                  if (!isDuplicate) {
                    uniqueIds.push(element)
                    return true
                  }
                  return false
                })
                currentDiff = uniqueIds
              }
            }
            if (that.showListDiff) { that.uniqProteins = currentDiff }
          }
          that.uniqueSize = currentDiff.length
          // console.log(memberships.getIntersection(currentDiff))
          // alert(that.uniqueSize)
          that.selectedSize = selection._groups[0][0].__data__.size
          selection.select('path')
            .style('stroke-width', 3)
            .style('fill-opacity', 0.6)
            .style('stroke-opacity', 1)
        })
        /*
        .on('mouseout', function (d, i) {
          const selection = d3.select(this).transition('tooltip').duration(400)
          selection.select('path')
            .style('stroke-width', 0)
            .style('fill-opacity', 0.25)
            .style('stroke-opacity', 0)
        })
      // console.log(test)
      */
    }

  }

}
</script>

<style>
.search-txt {
  background-color: rgba(219, 181, 181, 0.378);
  padding: 5px;
  width: 250px;
  margin-bottom: 25px;
}
.export-btn {
  background-color: rgba(161, 161, 235, 0.997);
  padding: 5px;
  width: 500px;
  margin-bottom: 25px;
}
#uniqSize
 {
  width: 100px;

}
#selectedItems
 {
  width: 300px;

}
</style>
