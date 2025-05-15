<template>
  <div class="datahistclass">
    <v-btn
      v-if="savePlot"
      class="ma-2"
      color="primary"
      @click="downloadSVG"
    >
      <v-icon
        v-if="savePlot"
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
  props: {
    fullChartData: {
      type: Array,
      default: undefined
    },
    filteredChartData: {
      type: Array,
      default: undefined
    },
    savePlot: {
      type: Boolean,
      default: false
    },
    fullTooltip: {
      type: Function,
      default: () => {}
    },
    filteredTooltip: {
      type: Function,
      default: () => {}
    },
    title: {
      type: String,
      default: ''
    },
    xlabel: {
      type: String,
      default: ''
    },
    plotHistogram: {
      type: Boolean,
      default: true
    },
    plotKDE: {
      type: Boolean,
      default: false
    },
    markMedianBar: {
      type: Boolean,
      default: false
    },
    minWidth: {
      type: Number,
      default: 200
    },
    minHeight: {
      type: Number,
      default: 200
    },
    selectedLines: {
      type: Array,
      default: undefined
    },
    minDose: {
      type: Number,
      default: null
    },
    maxDose: {
      type: Number,
      default: null
    },
    doseUnit: {
      type: String,
      default: ''
    },
    margin: {
      type: Object,
      default: function () {
        return { top: 20, right: 10, bottom: 50, left: 50 }
      }
    }
  },
  data: function () {
    return {
      minValue: 0,
      maxValue: 1,
      // xTransformation: this.minusLog10
      xTransformation: this.identity
    }
  },
  watch: {
    fullChartData: function () {
      this.init()
    },
    selectedLines: function (newSelectedLines) {
      this.drawLines(newSelectedLines)
    }
  },
  mounted: function () {
    this.init()
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
    minusLog10 (x) {
      return -Math.log10(x)
    },
    identity (x) {
      return x
    },
    drawPlot: function (data) {
      const sortedData = [...data]
      sortedData.sort()

      this.minValue = Math.min(this.xTransformation(this.minDose), this.xTransformation(sortedData.at(0)))
      this.maxValue = Math.max(this.xTransformation(this.maxDose), this.xTransformation(sortedData.at(-1)))

      let nclass = 25

      // ref: https://bl.ocks.org/d3noob/96b74d0bd6d11427dd797892551a103c

      const width = this.minWidth - this.margin.left - this.margin.right
      const height = this.minHeight - this.margin.top - this.margin.bottom

      // ceil / floor to a multiple of 0.1
      const maxX = Math.ceil(this.maxValue / 0.1) * 0.1
      const minX = Math.floor(this.minValue / 0.1) * 0.1

      // set the ranges
      const x = d3.scaleLinear().domain([minX, maxX]).rangeRound([0, width])
      const y = d3.scaleLinear().range([height, 0])

      const thresholds = x.ticks(nclass - 1)
      // set the parameters for the histogram
      const histogram = d3
        .histogram()
        .value(function (d) {
          return d
        })
        .domain(x.domain())
        .thresholds(thresholds)

      nclass = x.ticks(nclass - 1).length

      // append the svg object to the body of the page
      // append a 'group' element to 'svg'
      // moves the 'group' element to the top left margin
      const svg = d3
        .select(this.$el)
        .append('svg')
        .attr('class', 'HistogramContainer')
        .attr('width', width + this.margin.left + this.margin.right)
        .attr('height', height + this.margin.top + this.margin.bottom + 25)
        .append('g')
        .attr(
          'transform',
          'translate(' + this.margin.left + ',' + this.margin.top + ')'
        )

      if (this.plotHistogram) {
        // group the data for the bars
        const bins = histogram(sortedData)
        const maxFrequency = d3.max(bins, function (d) {
          return d.length
        })
        // Scale the range of the data in the y domain
        y.domain([0, maxFrequency])
        this.drawHistogram(svg, bins, height, x, y)
      }

      if (this.plotKDE) {
        // Kernel density estimate graph
        const bandwidth = ((maxX - minX) / nclass) * 2
        const density = this.kde(
          this.epanechnikov(),
          thresholds,
          data,
          bandwidth
        )
        // Scale the range of the data in the y domain
        const maxDensity = d3.max(density.map(d => d[1]))
        y.domain([0, maxDensity * 1.1])

        if (this.filteredChartData) {
          // Draw full data in grey if filtered data is present
          this.drawKDE(svg, density, x, y, this.fullTooltip, '#9d9d9d', '5 4')

          const densityFiltered = this.kde(
            this.epanechnikov(),
            thresholds,
            // this.filteredChartData.sort(),
            bandwidth
          )

          this.drawKDE(svg, densityFiltered, x, y, this.filteredTooltip)
        } else {
          this.drawKDE(svg, density, x, y)
        }
      }

      // add the x Axis
      svg
        .append('g')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('dy', '-.5em')
        .attr('dx', '1em')
        .attr('transform', 'rotate(90)')
        .style('text-anchor', 'start')

      svg
        .append('text')
        .attr(
          'transform',
          'translate(' +
              width / 2 +
              ' ,' +
              (height + this.margin.top + 50) +
              ')'
        )
        .style('text-anchor', 'middle')
        .text(this.xlabel)

      // add the y Axis
      svg.append('g').call(d3.axisLeft(y))

      svg
        .append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - this.margin.left)
        .attr('x', 0 - height / 2)
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text('Frequency')

      svg.append('g').attr('class', 'lines')

      // title
      svg
        .append('text')
        .attr('class', 'Title')
        .attr('x', width / 2)
        .attr('y', 0)
        .attr('text-anchor', 'middle')
        .text(this.title)

      // colour median bar red
      if (this.markMedianBar) {
        const median = this.getMedian(sortedData)
        const medBarId = this.findMedBar(maxX, minX, nclass, median)

        svg.select('#bar' + medBarId).style('fill', '#C4071B')
      }
    },
    kde: function (kernel, thresholds, data, bandwidth) {
      const binWidth = thresholds[1] - thresholds[0]
      return thresholds.map((t) => [
        t,
        d3.sum(data, function (d) {
          return kernel((t - d) / bandwidth) / bandwidth
        }) * binWidth
      ])
    },
    epanechnikov: function () {
      return function (x) {
        return Math.abs(x) <= 1 ? 0.75 * (1 - x * x) : 0
      }
    },
    drawLines: function (oLines) {
      const width = this.minWidth - this.margin.left - this.margin.right
      const height = this.minHeight - this.margin.top - this.margin.bottom

      // ceil / floor to a multiple of 0.1
      const maxX = Math.ceil(this.maxValue / 0.1) * 0.1
      const minX = Math.floor(this.minValue / 0.1) * 0.1

      const x = d3.scaleLinear().domain([minX, maxX]).rangeRound([0, width])

      const allLines = d3.select(this.$el).select('.lines')

      d3.select(this.$el).selectAll('.selectedLine').remove()
      const lines = allLines.selectAll('line').data(oLines).enter()
      lines
        .append('line')
        .classed('selectedLine', true)
        .attr('x1', (d) => {
          return x(Math.min(Math.max(d.value, this.minValue), this.maxValue))
        })
        .attr('y1', height * 0.05)
        .attr('x2', (d) => {
          return x(Math.min(Math.max(d.value, this.minValue), this.maxValue))
        })
        .attr('y2', height)
        .attr('id', (d) => `selectedLine-${d.curveid}`)
        .style('stroke-width', 2)
        .style('stroke', function (d) {
          return d.color
        })
        .style('stroke-dasharray', function (d) {
          return d.dash
        })
        .style('fill', 'none')

      // Add thicker invisible line for more sensitivity to mouse events
      lines
        .append('line')
        .classed('selectedLine', true)
        .attr('x1', (d) => {
          return x(Math.min(Math.max(d.value, this.minValue), this.maxValue))
        })
        .attr('y1', height * 0.05)
        .attr('x2', (d) => {
          return x(Math.min(Math.max(d.value, this.minValue), this.maxValue))
        })
        .attr('y2', height)
        .style('stroke-width', 10)
        .style('stroke', 'transparent')
        .on('mouseenter', function (e, d) {
          d3.select(`#selectedLine-${d.curveid}`).classed('highlightLines', true)
        })
        .on('mouseout', function (e, d) {
          d3.select(`#selectedLine-${d.curveid}`).classed('highlightLines', false)
        })
        .append('title').text(d => `Num = ${d.value.toPrecision(3)}`)

      lines
        .append('path')
        .classed('selectedLine', true)
        .attr('transform', (d) => {
          return 'translate(' + x(Math.min(Math.max(d.value, this.minValue), this.maxValue)) + ',' + height * 0.25 + ')'
        })
        .style('fill', function (d) {
          return d.color
        })
        .attr('stroke-width', 100)
        .append('title').text(d => `Num = ${d.value.toPrecision(3)}`)
    },
    getMedian: function (valarray) {
      let medval
      if (valarray.length % 2 === 0) {
        // if even
        const val1where = valarray.length / 2
        const val2where = valarray.length / 2 + 1
        const val1 = valarray[val1where]
        const val2 = valarray[val2where]
        medval = (val1 + val2) / 2
      } else {
        const where = (valarray.length + 1) / 2
        medval = valarray[where]
      }
      return medval
    },
    findMedBar: function (maxX, minX, nclass, median) {
      const size = (maxX - minX) / nclass
      let found, i
      for (i = 0; i <= nclass; i++) {
        if (minX + size * i < median && median < minX + size * (i + 1)) {
          found = i
        }
      }
      return found
    },
    init: function () {
      d3.select(this.$el).select('svg').remove()
      const oData = this.fullChartData
      if (typeof oData !== 'undefined' && oData.length > 0) {
        this.drawPlot(oData)
      }
    },

    drawHistogram: function (svg, bins, height, x, y) {
      let i = 0
      // append the bar rectangles to the svg element
      svg
        .selectAll('rect')
        .data(bins)
        .enter()
        .append('rect')
        .attr('class', 'bar')
        .attr('x', 1)
        .attr('transform', function (d) {
          return 'translate(' + x(d.x0) + ',' + y(d.length) + ')'
        })
        .attr('width', function (d) {
          if (x(d.x1) - x(d.x0) > 1) {
            return x(d.x1) - x(d.x0) - 1 // subtract 1 pixel to separate the bins visually
          } else {
            return 0
          }
        })
        .attr('height', function (d) {
          return height - y(d.length)
        })
        .attr('id', function () {
          return 'bar' + i++
        })
        .style('fill', '#CCCCCC') // blue: #0073CF
    },

    drawKDE: function (svg, density, x, y, tooltipText = null, stroke = '#000', dasharray = '1 0') {
      const line = d3
        .line()
        .curve(d3.curveBasis)
        .x(function (d) {
          return x(d[0])
        })
        .y(function (d) {
          return y(d[1])
        })

      svg
        .append('path')
        .datum(density)
        .attr('fill', 'none')
        .attr('stroke', stroke)
        .attr('stroke-dasharray', dasharray)
        .attr('stroke-width', 1.5)
        .attr('stroke-linejoin', 'round')
        .attr('d', line)

      if (tooltipText) {
        svg
          .append('path')
          .datum(density)
          .attr('fill', 'none')
          .attr('stroke', 'transparent')
          .attr('stroke-width', 10)
          .attr('stroke-linejoin', 'round')
          .attr('d', line)
          .append('title')
          .text(tooltipText)
      }
    },

    getSVG: function () {
      return d3.select(this.$el).selectAll('svg').node()
    }
  }
}
</script>

<style>
@import "./GenericHistogram.css.prdb";
</style>
