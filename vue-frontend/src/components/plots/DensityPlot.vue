<template>
  <div id="densityplot">
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
const d3 = require('d3')

export default {
  name: 'DensityPlot',
  props: {
    plotData: {
      /* IT COMPUTES THE COUNTS ON THE FLY GOOD FOR SMALL DATASETS WITH 2 TYPES
        this.densityData = [
          { type: 'variable 1', value: 2 },
          { type: 'variable 1', value: 2 },
          { type: 'variable 1', value: 1 },
          { type: 'variable 2', value: 3 },
          { type: 'variable 2', value: 3 },
          { type: 'variable 2', value: 4 },
          { type: 'variable 2', value: 5 },
          { type: 'variable 2', value: 6 },
          { type: 'variable 2', value: 7 }
        ]
        */
      type: Array,
      default: () => []
    },
    savePlot: {
      type: Boolean,
      default: false
    },
    variableA: {
      type: String,
      default: 'variable A'
    },
    variableB: {
      type: String,
      default: 'variable B'
    }
  },
  data: () => ({

  }),
  watch: {
    plotData: function () {
      this.plotExpression()
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
          'Density Plot',
          false,
          'canvasId',
          []
        )
      }
    },
    plotExpression: function () {
      // set the dimensions and margins of the graph
      const margin = { top: 30, right: 30, bottom: 30, left: 50 }
      const width = 460 - margin.left - margin.right
      const height = 400 - margin.top - margin.bottom

      // append the svg object to the body of the page
      d3.select('#densityplot').selectAll('svg').remove()
      const svg = d3.select('#densityplot')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform',
          'translate(' + margin.left + ',' + margin.top + ')')
      const data = this.plotData
      console.log(data)
      // add the x Axis
      const x = d3.scaleLinear()
        .domain([-10, 15])
        .range([0, width])
      svg.append('g')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(x))

      // add the y Axis
      const y = d3.scaleLinear()
        .range([height, 0])
        .domain([0, 0.12])
      svg.append('g')
        .call(d3.axisLeft(y))

      // Compute kernel density estimation
      const kde = kernelDensityEstimator(kernelEpanechnikov(7), x.ticks(60))
      const density1 = kde(data
        .filter(function (d) { return d.type === 'variable 1' })
        .map(function (d) { return d.value }))
      const density2 = kde(data
        .filter(function (d) { return d.type === 'variable 2' })
        .map(function (d) { return d.value }))

      // Plot the area
      svg.append('path')
        .attr('class', 'mypath')
        .datum(density1)
        .attr('fill', '#69b3a2')
        .attr('opacity', '.6')
        .attr('stroke', '#000')
        .attr('stroke-width', 1)
        .attr('stroke-linejoin', 'round')
        .attr('d', d3.line()
          .curve(d3.curveBasis)
          .x(function (d) { return x(d[0]) })
          .y(function (d) { return y(d[1]) })
        )

      // Plot the area
      svg.append('path')
        .attr('class', 'mypath')
        .datum(density2)
        .attr('fill', '#404080')
        .attr('opacity', '.6')
        .attr('stroke', '#000')
        .attr('stroke-width', 1)
        .attr('stroke-linejoin', 'round')
        .attr('d', d3.line()
          .curve(d3.curveBasis)
          .x(function (d) { return x(d[0]) })
          .y(function (d) { return y(d[1]) })
        )
      // })

      // Handmade legend
      svg.append('circle').attr('cx', 300).attr('cy', 30).attr('r', 6).style('fill', '#69b3a2')
      svg.append('circle').attr('cx', 300).attr('cy', 60).attr('r', 6).style('fill', '#404080')
      svg.append('text').attr('x', 320).attr('y', 30).text(this.variableA).style('font-size', '15px').attr('alignment-baseline', 'middle')
      svg.append('text').attr('x', 320).attr('y', 60).text(this.variableB).style('font-size', '15px').attr('alignment-baseline', 'middle')

      // Function to compute density
      function kernelDensityEstimator (kernel, X) {
        return function (V) {
          return X.map(function (x) {
            return [x, d3.mean(V, function (v) { return kernel(x - v) })]
          })
        }
      }
      function kernelEpanechnikov (k) {
        return function (v) {
          return Math.abs(v /= k) <= 1 ? 0.75 * (1 - v * v) / k : 0
        }
      }
    }
  }
}
</script>
<style>

</style>
