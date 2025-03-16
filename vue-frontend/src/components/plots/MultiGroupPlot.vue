<template>
  <div :id="iD">
    <v-btn
      v-if="savePlot & plotData.length > 0"
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
  </div>
</template>

<script>
import utils from '@/plugins/DownloadUtils'
const d3 = require('d3')

export default {
  name: 'MultiGroupPlot',
  props: {
    plotData: {
      type: Array,
      default: undefined
    },
    savePlot: {
      type: Boolean,
      default: true
    },
    showLegends: {
      type: Boolean,
      default: false
    },
    fieldX: {
      type: String,
      default: ''
    },
    iD: {
      type: String,
      default: 'multigroupplot'
    },
    fieldY: {
      type: String,
      default: ''
    },
    title: {
      type: String,
      default: ''
    },
    selectedPatients: {
      type: Array,
      default: undefined
    },
    selectedColor: {
      type: String,
      default: undefined
    }
  },
  data: () => ({
    scatterPoints: [],
    key: 0,
    width: 1500,
    // fieldX: 'basket',
    // fieldY: 'score',
    // title: 'sample',
    height: 500,
    margin: [100, 100, 100, 100]
  }),
  watch: {
    plotData: function () {
      this.key = this.key + 1
      this.drawSwarm('default')
    },
    selectedPatients () {
      if (this.selectedPatients !== null && this.selectedPatients.length > 0) {
        this.drawSwarm('default')
      } else {
        this.drawSwarm('reset')
      }
    }
  },
  mounted () {
  },
  methods: {
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
    drawSwarm (mode) {
      const data = this.plotData
      d3.select(`#${this.iD}`).selectAll('svg').remove()
      const fieldX = this.fieldX //  x
      const fieldY = this.fieldY //  y
      const title = this.title //  tooltip field
      const width = this.width
      const height = this.height
      const margin = this.margin
      const svg = d3
        .select(`#${this.iD}`)
        .append('svg')
        .attr('height', height)
        .attr('width', width)

      const sectors = Array.from(new Set(data.map((d) => d[fieldX]))) // x categories
      const xScale = d3
        .scaleBand()
        .domain(sectors)
        .range([margin[3], width - margin[1]])

      const yScale = d3 // y axis
        .scaleLinear()
        .domain(d3.extent(data.map((d) => +d[fieldY])))
        .range([height - (margin[2] + 10), margin[0] + 50])
      // const color = d3.scaleOrdinal().domain(fieldX).range(d3.schemePaired)
      const sample = this.title
      const selectedPatients = this.selectedPatients
      if (this.selectedPatients !== null && selectedPatients.length > 0) {
        let newpatient = ''
        for (let k = 0; k < selectedPatients.length; k++) {
          newpatient = selectedPatients[k]
          data.forEach(element => {
            if (newpatient === element[sample]) {
              element.color = this.selectedColor
              element.sizeR = 3
            }
          })
        }
      }
      if (mode === 'reset') {
        data.forEach(element => {
          element.color = 'grey'
          element.sizeR = 0.5
        })
      }
      const ySize = d3.extent(data.map((d) => +d[fieldY]))
      const size = d3.scaleSqrt().domain(ySize).range([1, 2])
      const xLine = svg.append('line')
        .attr('stroke', 'rgb(96,125,139)')
        .attr('stroke-dasharray', '1,2')
      svg
        .selectAll('.circ')
        .data(data)
        .enter()
        .append('circle')
        .attr('class', 'circ')
        .attr('stroke', (d) => d.color)
        .attr('fill', (d) => d.color)
        // .attr('fill', (d) => color(d[fieldX]))
        .attr('r', (d) => d.sizeR)
        .attr('cx', (d) => xScale(d[fieldX]))
        .attr('cy', (d) => yScale(d[fieldY]))
      // using the tooltip
      const simulation = d3
        .forceSimulation(data)
        .force(
          'x',
          d3
            .forceX((d) => {
              return xScale(d[fieldX])
            })
            .strength(0.1)
        )
        .force(
          'y',
          d3
            .forceY(function (d) {
              return yScale(d[fieldY])
            })
            .strength(1)
        )
        .force(
          'collide',
          d3.forceCollide((d) => {
            return size(d[fieldY])
          })
        )
        .alpha(1)
        .on('tick', tick)
      function tick () {
        d3.selectAll('.circ')
          .attr('cx', (d) => d.x)
          .attr('cy', (d) => d.y)
      }
      setTimeout(function () {
        simulation.alphaDecay(0.1)
      }, (1000 + this.plotData.length))
      const yAxis = d3.axisRight(yScale)
      svg.append('g')
        .call(yAxis)
      const xAxis = d3.axisBottom(xScale)
      svg.append('g')
        .call(xAxis)
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-.8em')
        .attr('dy', '.15em')
        .attr('transform', 'rotate(-20)')

      const tooltip = d3.select(`#${this.iD}`)
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 1)

      d3.selectAll('.circ').on('mousemove', function (d) {
        tooltip.html(`<strong>${title}: ${d.target.__data__[title]}</strong><br>${fieldY}: ${d.target.__data__[fieldY].toFixed(2)}    ${d.target.__data__[fieldX]}</br>`)
          .style('top', 200 + 'px')
          .style('left', 200 + 'px')
          .style('opacity', 0.9)
        xLine.attr('x1', d3.select(this).attr('cx'))
          .attr('y1', d3.select(this).attr('cy'))
          .attr('y2', d3.select(this).attr('cy'))
          .attr('x2', 0)
          .attr('opacity', 1)
      }).on('mouseout', function () {
        tooltip.style('opacity', 0)
        xLine.attr('opacity', 0)
      })
      // show legends property
      if (this.showLegends) {
        const uniqueIds = []
        const uniqColors = []
        let y = 30
        data.filter(element => {
          let item = element.Sample.split('_')
          item = item[item.length - 1]
          const currColor = element.color
          const isDuplicate = uniqueIds.includes(item)
          if (!isDuplicate) {
            uniqueIds.push(item)
            uniqColors.push(currColor)
            svg.append('circle').attr('cx', width - (width / 6)).attr('cy', y).attr('r', 6).style('fill', currColor)
            svg.append('text').attr('x', width - ((width / 6.5))).attr('y', y).text(item).style('font-size', '15px').attr('alignment-baseline', 'middle')
            y = y + 20
            return true
          }
          return false
        })
      }
    }
  }
}
</script>

<style>
.tooltip {
    position: absolute;
    font-size: 12px;
    width:  auto;
    height: auto;
    pointer-events: none;
    background-color: white;
}
</style>
