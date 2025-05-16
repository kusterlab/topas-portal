<template>
  <div id="container">
    <v-btn
      v-if="savePlot"
      class="ma-2"
      color="primary"
      @click="downloadSVG"
    >
      <v-icon
        dark
      >
        mdi-cloud-download
      </v-icon>
    </v-btn>
    <v-btn
      class="ma-2"
      color="primary"
      @click="resetDotColors"
    >
      <v-icon
        dark
      >
        mdi-refresh
      </v-icon>
    </v-btn>

    <v-btn
      class="ma-2"
      color="primary"
      @click="changetheseSamplescolors"
    >
      <v-icon
        dark
      >
        mdi-pencil
      </v-icon>
    </v-btn>
    <v-row>
      <v-col width="50%">
        <v-color-picker
          v-model="colorCode"
          hide-inputs
          hide-canvas
          light
          swatches-max-height="50"
          width="300"
        />
      </v-col>
      <v-col width="50%">
        <v-text-field
          v-model="patientGroup"
          class="qcbtn"
          label="Group:"
          placeholder="G1"
        />
      </v-col>
    </v-row>
    <v-checkbox
      v-model="showLegend"
      label="Show the legends"
    />

    <div id="qcplot" />
    <canvas
      id="canvasId"
      style="display: none"
    />
  </div>
</template>

<script>
import utils from '@/plugins/DownloadUtils'

const d3 = require('d3')
export default {
  name: 'QcPlot',
  props: {
    savePlot: {
      type: Boolean,
      default: false
    },
    qcSelIds: { // the index of the selected items from table etc.
      type: Array,
      default: undefined
    },
    qcplotData: { // Plot data with pc1,pc2, metadata
      type: Array,
      default: undefined
      /* EXAMPLE any numbers of meta data can be used, pc1 and pc2 are mandataory and should be wihtin the range of -1 to 1
      [{ Sample: 'one', pc1: 0.2, pc2: 0.3, age: 12, meta_data2:'x' },
       { Sample: 'Two', pc1: 0.4, pc2: 0.6, age: 17,meta_data3:'y' },
       { Sample: 'Three', pc1: 0.3, pc2: 0.9, age: 22,meta_data4:'g' }]
      */
    },
    pcVar1: {
      type: Number,
      default: 0
    },
    pcVar2: {
      type: Number,
      default: 0
    },
    qcMeta: {
      type: String,
      default: 'Sample'
    },
    qcType: {
      type: String,
      default: 'ppca'
    }
  },
  data: () => ({
    showLegend: true,
    patientGroup: '',
    colorCode: null,
    finalPlotData: []
  }),
  watch: {

    qcplotData: function () {
      this.finalPlotData = this.qcplotData
      this.finalPlotData.forEach(element => { element.rSize = 50 })
      this.metaAssigner()
      this.plotQc(true)
    },

    showLegend: function () {
      this.plotQc(false)
    },

    qcMeta: function () {
      this.metaAssigner()
      this.plotQc(true)
    }
  },

  mounted () {
  },
  methods: {
    metaAssigner () {
      const typeMeta = this.qcMeta
      this.finalPlotData.forEach(element => {
        element.MetaData = element[typeMeta]
      })
    },
    resetDotColors () {
      this.finalPlotData.forEach(element => {
        element.colorCodes = 'lightgrey'
        element.MetaData = this.patientGroup
        element.shapeCodes = 'symbolCircle'
        element.rSize = 20
      })
      this.plotQc(false)
    },

    changetheseSamplescolors () {
      console.log(this.qcSelIds)
      if (this.qcSelIds.length > 0) {
        this.qcSelIds.forEach(element => {
          this.finalPlotData[element].colorCodes = this.colorCode.hex
          this.finalPlotData[element].MetaData = this.patientGroup
          this.finalPlotData[element].rSize = 50
        })
        console.log(this.finalPlotData)
        // this.finalPlotData = this.finalPlotData.sort((p1, p2) => (p1.colorCodes=='lightgrey' & p2.colorCodes!='lightgrey') ? -1 : (p1.colorCodes!='lightgrey' & p2.colorCodes=='lightgrey') ? 1 : 0);
      }
      this.plotQc(false)
    },

    downloadSVG () {
      const aPlots = []
      aPlots.push(d3.select(this.$el).select('svg').node())
      if (aPlots.length > 0) {
        utils.downloadSVGs(
          aPlots,
          '',
          false,
          'canvasId',
          []
        )
      }
    },

    plotQc (colorShapeAssign) {
      const data = this.finalPlotData
      const shapeSet = [
        'symbolCircle',
        'symbolTriangle',
        'symbolSquare',
        'symbolDiamond',
        'symbolStar',
        'symbolWye',
        'symbolCross'
      ]
      const colorSet = [
        '#2f4f4f',
        '#228b22',
        '#7f0000',
        '#00008b',
        '#ff8c00',
        '#ffff00',
        '#00ff00',
        '#00ffff',
        '#ff00ff',
        '#6495ed',
        '#f5deb3',
        '#ff69b4'
      ]
      if (colorShapeAssign) {
      // getting the unique ids
        const uniqueIds = []
        const metaType = this.qcMeta
        data.filter(element => {
          const isDuplicate = uniqueIds.includes(element[metaType])
          if (!isDuplicate) {
            uniqueIds.push(element[metaType])
            return true
          }
          return false
        })

        let colorInd = 0
        let shapeInd = 0
        // iterating through each unique item and get the index for the color and shape
        for (let i = 0; i < uniqueIds.length; i++) {
          colorInd = colorInd + 1
          if (colorInd >= colorSet.length) {
            colorInd = 0
            shapeInd = shapeInd + 1
          }
          if (shapeInd >= shapeSet.length) {
            shapeInd = 0
          }

          // final assignment
          const activeItem = uniqueIds[i]
          for (let j = 0; j < data.length; j++) {
            data[j].rSize = 40
            if (data[j][metaType] === activeItem) {
              data[j].colorCodes = colorSet[colorInd]
              data[j].shapeCodes = shapeSet[shapeInd]
            }
          }
        }
      } // colorShapeAssign
      let pcVar1 = 'PC1  (' + this.pcVar1 + ')'
      let pcVar2 = 'PC2  (' + this.pcVar2 + ')'

      if (this.qcType !== 'ppca') {
        pcVar1 = 'Umap1'
        pcVar2 = 'Umap2'
      }

      // const pcVar1 = 'PC1'
      // const pcVar2 = 'PC2'

      // set the dimensions and margins of the graph

      const margin = { top: 10, right: 30, bottom: 40, left: 60 }
      const width = 640 - margin.left - margin.right
      const height = 600 - margin.top - margin.bottom
      // append the svg object to the body of the page

      d3.select('#qcplot').selectAll('svg').remove()
      const svg = d3.select('#qcplot')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform',
          'translate(' + margin.left + ',' + margin.top + ')')

      let maxX = -1000
      let maxY = -1000
      let minX = 1000
      let minY = 1000

      data.forEach(element => {
        if (element.pc1 > maxX) maxX = element.pc1
        if (element.pc2 > maxY) maxY = element.pc2
        if (element.pc1 < minX) minX = element.pc1
        if (element.pc2 < minY) minY = element.pc2
      })

      // legends testing

      // let legendX = minX
      const legendY = maxY
      // const maxMinDiffX = maxX - minX
      // const maxMinDiffY = maxY - minY

      maxX = maxX + 0.5
      // maxY = maxY
      // minX = minX
      // minY = minY

      // Add X axis
      minX = -1
      maxX = 1
      minY = -1
      maxY = 1
      const x = d3.scaleLinear()
        .domain([minX, maxX])
        .range([0, width])

      const xAxis = svg.append('g')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(x))

      // Add Y axis
      const y = d3.scaleLinear()
        .domain([minY, maxY])
        .range([height, 0])

      const yAxis = svg.append('g')
        .call(d3.axisLeft(y))

      // add tool tip
      const tooltip = d3.select('#qcplot').append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)

      // tooltip mouseover event handler
      const tipMouseover = function (e, d) {
        const html = d.Sample + ', ' + d.MetaData
        tooltip.html(html)
          .style('left', (e.pagex) + 'px')
          .style('top', (e.pageY - 50) + 'px')
          .transition()
          .duration(200) // ms
          .style('opacity', 0.9) // started as 0!
      }

      // tooltip mouseout event handler
      const tipMouseout = function () {
        tooltip.transition()
          .duration(300) // ms
          .style('opacity', 0) // don't care about position!
      }

      svg
        .append('text')
        .attr(
          'transform',
          'translate(' +
            width / 2 +
            ' ,' +
            (height + margin.top + 20) +
            ')'
        )
        .style('text-anchor', 'middle')
        .text(pcVar1)

      // add the y Axis
      svg
        .append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - (margin.left - 15))
        .attr('x', 0 - height / 2)
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text(pcVar2)

      const symbol = d3.symbol()

      // Add a clipPath: everything out of this area won't be drawn.
      svg.append('defs').append('SVG:clipPath')
        .attr('id', 'clip')
        .append('SVG:rect')
        .attr('width', width)
        .attr('height', height)
        .attr('x', 0)
        .attr('y', 0)

      // Add dots
      const g = svg.append('g')
        .attr('clip-path', 'url(#clip)')

      const clickCirc = function (e, d) {
        if (e.ctrlKey) {
          g.append('text')
            .attr('x', x(d.pc1))
            .attr('y', y(d.pc2))
          // .style('fill', d.colorCodes.toString())
            .text(d.Sample)
        } else {
          g.append('text')
            .attr('x', x(d.pc1))
            .attr('y', y(d.pc2))
          // .style('fill', d.colorCodes.toString())
            .text(d.MetaData)
        }
      }

      g.selectAll('.dots')
        .data(data)
        .enter()
        .append('path')
        .attr('d', symbol.type(function (d) { return d3[d.shapeCodes.toString()] }))
        .attr('d', symbol.size(function (d) { return parseInt(d.rSize) }))
        .attr('transform', d => `translate(${x(d.pc1)},${y(d.pc2)})`)
        .style('fill', function (d) { return d.colorCodes.toString() })
        .on('mousemove', tipMouseover)
        .on('mouseout', tipMouseout)
        .on('click', clickCirc)

      if (this.showLegend) {
        // legends adding to the plot
        const legData = data
        const xpos = width - 60
        // the parameters for the legends dots on the plot
        // let xx= legendX - 1000
        let yy = legendY // the starting point of the legends in the plot
        const delta = 0.04 // the space between the legends

        legData.forEach(element => {
          // element.px = xx
          element.id = element.colorCodes + element.shapeCodes // to get the unique list for the legends
        })
        const uniqueIds = []
        const unique = legData.filter(element => {
          const isDuplicate = uniqueIds.includes(element.id)
          if (!isDuplicate) {
            element.py = yy
            yy = yy - delta
            uniqueIds.push(element.id)
            return true
          }
          return false
        })

        const legendThreshold = 48 // the maximum number of legends to show to prevent over flow
        if (unique.length > legendThreshold) {
          for (let ind = legendThreshold; ind < unique.length; ind++) {
            unique.splice(ind)
          }
        }

        const legs = svg.selectAll('.dots')
          .data(unique)
          .enter()
          .append('path')
        legs.attr('d', symbol.type(function (d) { return d3[d.shapeCodes.toString()] }))
          .attr('transform', d => `translate(${xpos},${y(d.py)})`)
          .style('fill', function (d) {
            return d.colorCodes.toString()
          })

        unique.forEach(element => {
          svg.append('text')
            .attr('x', xpos + 25)
            .attr('y', y(element.py))
            .text(element.MetaData)
            .style('font-size', '14px')
            .attr('alignment-baseline', 'middle')
        })
      } // legends check box

      const zoomed = d3.zoom()
        .scaleExtent([0, 5]) // This control how much you can unzoom (x0.5) and zoom (x20)
        .extent([[0, 0], [width, height]])
        .on('zoom', function (event) {
          const newX = event.transform.rescaleX(x)
          const newY = event.transform.rescaleY(y)
          // update axes with these new boundaries
          xAxis.call(d3.axisBottom(newX))
          yAxis.call(d3.axisLeft(newY))
          g.selectAll('path')
            .attr('transform', d => `translate(${newX(d.pc1)},${newY(d.pc2)})`)
        })

      svg
        .call(zoomed)
    } //  method end

  }

}
</script>

<style>
.qcbtn {
  width: 70px;

}
</style>
