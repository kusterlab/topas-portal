<template>
  <div
    v-if="plotData"
    :id="plotId"
    class="circularbarchart"
  >
    <v-btn
      v-if="savePlot"
      class="ma-2 float-left"
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
import * as d3 from 'd3'

export default {
  name: 'CircularbarPlot',
  props: {
    plotId: {
      type: String,
      default: 'loliPop'
    },
    savePlot: {
      type: Boolean,
      default: true
    },
    patientName: {
      type: String,
      default: ''
    },
    showLegends: {
      type: Boolean,
      default: true
    },
    plotData: {
      type: Array,
      default: () => []
    },
    defaultData: {
      type: Array,
      default: () => [{
        label: 'Toblerone',
        value: 1,
        type: 'A',
        color: 'red'
      },
      {
        label: 'Snickers',
        value: 2,
        type: 'A',
        color: 'red'
      },
      {
        label: 'Jawbreakers',
        value: 6,
        color: 'red'
      },
      {
        label: 'Gummi Worms',
        value: 3,
        type: 'B',
        color: 'blue'
      },
      {
        label: 'new',
        value: 1,
        type: 'B',
        color: 'red'
      }
      ]
    }
  },
  data: () => ({
    key: 0
  }),
  watch: {
    plotData: function () {
      if (this.plotData.length > 0) {
        this.key = this.key + 1
        this.plotExpression()
      }
    }
  },
  mounted () {
    this.plotExpression()
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
    plotExpression: function () {
      const data = this.plotData
      // negative values will be put to zero to avoid a mess in the circular plot
      for (let i = 0; i < data.length; i++) { data[i].new_value = data[i].value > 0 ? data[i].value : 0 }
      const color = d3.scaleOrdinal()
        .range(data.map(function (d) { return d.color }))

      // set the dimensions and margins of the graph
      const margin = { top: 30, right: 30, bottom: 70, left: 60 }
      const width = 460 - margin.left - margin.right
      const height = 400 - margin.top - margin.bottom
      const innerRadius = 90
      const outerRadius = Math.min(width, height) / 2// the outerRadius goes from the middle of the SVG area to the border
      const maxDomain = Math.max(...data.map(function (d) { return d.new_value }))
      // append the svg object
      d3.select(`#${this.plotId}`).selectAll('svg').remove()
      const svg = d3.select(`#${this.plotId}`)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        // .call(d3.zoom().on('zoom', function (event) {
        //   svg.attr('transform', event.transform)
        // }))
        .append('g')
        .attr('transform', 'translate(' + (width / 2 + margin.left) + ',' + (height / 2 + margin.top) + ')')

      // Scales
      const x = d3.scaleBand()
        .range([0, 2 * Math.PI]) // X axis goes from 0 to 2pi = all around the circle. If I stop at 1Pi, it will be around a half circle
        .align(0) // This does nothing
        .domain(data.map(function (d) { return d.label })) // The domain of the X axis is the list of states.

      const y = d3.scaleRadial()
        .range([innerRadius, outerRadius]) // Domain will be define later.
        .domain([0, maxDomain]) // Domain of Y is from 0 to the max seen in the data

      const tooltip = d3.select(`#${this.plotId}`).append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)
      // tooltip mouseover event handler
      const tipMouseover = function (_, d) {
        const html = 'Basket: ' + d.label + '  ' + 'Score: ' + d.new_value.toFixed(2)
        tooltip.html(html)
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

      // Add the bars
      svg.append('g')
        .selectAll('path')
        .data(data)
        .enter()
        .append('path')
        .attr('fill', function (d, i) {
          return color(i)
        })
        .attr('d', d3.arc() // imagine your doing a part of a donut plot
          .innerRadius(innerRadius)
          .outerRadius(function (d) { return y(d.new_value) })
          .startAngle(function (d) { return x(d.label) })
          .endAngle(function (d) { return x(d.label) + x.bandwidth() })
          .padAngle(0.01)
          .padRadius(innerRadius))
        .on('mousemove', tipMouseover)
        .on('mouseout', tipMouseout)

      // Add the labels
      svg.append('g')
        .selectAll('g')
        .data(data)
        .enter()
        .append('g')
        .attr('text-anchor', function (d) { return (x(d.label) + x.bandwidth() / 2 + Math.PI) % (2 * Math.PI) < Math.PI ? 'end' : 'start' })
        .attr('transform', function (d) { return 'rotate(' + ((x(d.label) + x.bandwidth() / 2) * 180 / Math.PI - 90) + ')' + 'translate(' + (y(d.new_value) + 10) + ',0)' })
        .append('text')
        .attr('id', 'circleBasicTooltip')
        .text(function (d) { return (d.label) })
        .attr('transform', function (d) { return (x(d.label) + x.bandwidth() / 2 + Math.PI) % (2 * Math.PI) < Math.PI ? 'rotate(180)' : 'rotate(0)' })
        .style('font-size', '11px')
        .attr('alignment-baseline', 'middle')

      svg.append('text')
        .attr('x', (width / 42))
        .attr('y', 0 - (margin.top / 2))
        .attr('text-anchor', 'middle')
        .style('font-size', '10px')
        .style('text-decoration', 'underline')
        .text(this.patientName)
      if (this.showLegends) {
        const uniqueIds = []
        const unique = data.filter(element => {
          const isDuplicate = uniqueIds.includes(element.type)
          if (!isDuplicate) {
            uniqueIds.push(element.type)
            return true
          }
          return false
        })
        let py = 10
        unique.forEach(element => {
          svg.append('text').attr('x', this.width - 170).attr('y', py).text(element.type).style('font-size', '8px')
          svg.append('circle').attr('cx', this.width - 200).attr('cy', py).attr('r', 3).style('fill', element.color)
          py = py + 10
        })
      }
    }
  }
}
</script>
<style>

</style>
