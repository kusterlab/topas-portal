<template>
  <div id="barhistplot">
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
  </div>
</template>

<script>
import utils from '@/plugins/DownloadUtils'
import * as d3 from 'd3'

export default {
  name: 'BarhistPlot',
  props: {
    plotData: {
      type: Array,
      default: () => [{ X: 14.3, Y: 11.4, color: 'blue' },
        { X: 22.2, Y: 21.6, color: 'red' },
        { X: 31, Y: 32, color: 'blue', opacity: 0.9 },
        { X: 31, Y: 32, color: 'blue', opacity: 0.9 },
        { X: 38, Y: 32, color: 'blue', opacity: 0.9 },
        { X: 34, Y: 32, color: 'green', opacity: 0.5 },
        { X: 39, Y: 32, color: 'green', opacity: 0.5 },
        { X: 3.5, Y: 50, color: 'red', opacity: 0.7 }]
    },
    savePlot: {
      type: Boolean,
      default: true
    },
    titleVariables: {
      type: Array,
      default: () => [{ name: 'all_genes', color: 'blue' },
        { name: 'selected', color: 'red' },
        { name: 'third', color: 'green' }]
    }
  },
  data: () => ({

  }),
  watch: {
    plotData: function () {
      if (this.plotData.length > 0) {
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
      // Parse the Data
      const data = this.plotData

      // set the dimensions and margins of the graph
      const margin = { top: 30, right: 30, bottom: 70, left: 60 }
      const width = 460 - margin.left - margin.right
      const height = 400 - margin.top - margin.bottom

      d3.select('#barhistplot').selectAll('svg').remove()
      // append the svg object to the body of the page
      const svg = d3.select('#barhistplot')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform',
          'translate(' + margin.left + ',' + margin.top + ')')

      const maxY = d3.max(data, (d) => d.Y)
      const maxX = d3.max(data, (d) => d.X) + 0.05
      const minY = d3.min(data, (d) => d.Y)
      const minX = d3.min(data, (d) => d.X) - 0.05
      // X axis
      const x = d3.scaleLinear()
        .domain([minX, maxX])
        .range([0, width])

      const xAxis = svg.append('g')
        .call(d3.axisBottom(x))
        .attr('transform', 'translate(0,' + height + ')')

      // Add Y axis
      const y = d3.scaleLinear()
        .domain([minY, maxY])
        .range([height, 0])
      const yAxis = svg.append('g')
        .call(d3.axisLeft(y))

      // Add a clipPath: everything out of this area won't be drawn.
      svg.append('defs').append('SVG:clipPath')
        .attr('id', 'clip')
        .append('SVG:rect')
        .attr('width', width)
        .attr('height', height)
        .attr('x', 0)
        .attr('y', 0)

      // Create the scatter variable: where both the circles and the brush take place
      const g = svg.append('g')
        .attr('clip-path', 'url(#clip)')

      // Bars
      g.selectAll('mybar')
        .data(data)
        .enter()
        .append('rect')
        .attr('x', function (d) { return x(d.X) })
        .attr('y', function (d) { return y(d.Y) })
        // .attr('width', 8)
        .attr('width', 8)
        .attr('opacity', function (d) { return d.opacity })
        .attr('height', function (d) { return height - y(d.Y) })
        .style('fill', function (d) { return d.color.toString() })

      const zoom = d3.zoom()
        .scaleExtent([1, 10]) // This control how much you can unzoom (x0.5) and zoom (x20)
        .extent([[0, 0], [width, height]])
        .on('zoom', function (event) {
          const newX = event.transform.rescaleX(x)
          const newY = event.transform.rescaleY(y)
          // update axes with these new boundaries
          xAxis.call(d3.axisBottom(newX))
          yAxis.call(d3.axisLeft(newY))
          // g.selectAll('path')
          g.selectAll('rect')
            .attr('transform', event.transform)
        })

      svg.append('rect')
        .attr('width', width)
        .attr('height', height)
        .style('fill', 'none')
        .style('pointer-events', 'all')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')
        .call(zoom)

      let deltaBetween = 30
      // Handmade legend
      this.titleVariables.forEach(element => {
        svg.append('circle').attr('cx', 300).attr('cy', deltaBetween).attr('r', 3).style('fill', element.color)
        svg.append('text').attr('x', 310).attr('y', deltaBetween).text(element.name).style('font-size', '12px').attr('alignment-baseline', 'middle')
        deltaBetween += 30
      })
      // add the x Axis
      svg
        .append('text')
        .attr(
          'transform',
          'translate(' +
              width / 2 +
              ' ,' +
              (height + margin.top + 30) +
              ')'
        )
        .style('text-anchor', 'middle')
        .text('Intensity/FPKM Range')
      // add the y Axis
      svg
        .append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - height / 2)
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text('Scaled Density')
    }
  }
}
</script>
<style>

</style>
