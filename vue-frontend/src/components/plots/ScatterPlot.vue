<template>
  <div :id="id">
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
  name: 'ScatterPlot',
  props: {
    savePlot: {
      type: Boolean,
      default: true
    },
    id: {
      type: String,
      default: 'scatterplot'
    },
    addTrendlinte: {
      type: String,
      default: null
    },
    removeOwncolor: {
      type: Boolean,
      default: true
    },
    addStatslinte: {
      type: Boolean,
      default: false
    },
    ownColormethod: {
      type: String,
      default: null
    },
    width: {
      type: Number,
      default: 460
    },
    height: {
      type: Number,
      default: 400
    },
    identifier1: {
      type: String,
      default: ''
    },
    sizeR: {
      type: Number,
      default: 3
    },
    identifier2: {
      type: String,
      default: ''
    },
    omicsTypeX: {
      type: String,
      default: 'Proteomics'
    },
    omicsTypeY: {
      type: String,
      default: 'Proteomics'
    },
    scoreType: {
      type: String,
      default: 'Z-score'
    },
    labelX: {
      type: String,
      default: ''
    },
    labelY: {
      type: String,
      default: ''
    },
    selIds: {
      type: Array,
      default: () => []
    },
    expressions1: {
      type: Array,
      default: () => []
    },
    expressions2: {
      type: Array,
      default: () => []
    },
    ensembleData: {
      type: Array,
      default: () => null
      // if ensemble data is being used no need for the above expression 1 and expression2; then data should be as bellow
      // [
      //  { sampleId: 'EGFR', expression1: 1, expression2: 2 },
      //  { sampleId: 'EGFR', expression1: 2, expression2: 4 },
      //  { sampleId: 'EGFR', expression1: 3, expression2: 6 }
      // ]
    }
  },
  data: () => ({
    expressionsCommon: [],
    selectedDot: ''
  }),
  watch: {
    expressions1: function () {
      this.updateScatterPlot()
    },
    expressions2: function () {
      this.updateScatterPlot()
    },
    selIds: function () {
      this.plotExpression()
    },
    labelX: function () {
      this.updateScatterPlot()
    },
    labelY: function () {
      this.updateScatterPlot()
    },
    ensembleData: function () {
      this.updateScatterPlot()
    },
    ownColormethod: function () {
      this.updateScatterPlot()
    }

  },

  mounted () {
    this.updateScatterPlot()
  },

  methods: {
    selectedDotCall (sel) {
      this.$emit('onDotSelect', sel)
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
    updateScatterPlot () {
      this.expressionsCommon = this.getExpressionInCommonSamples(this.scoreType)
      this.plotExpression()
    },
    getExpressionInCommonSamples: function (scoreType) {
      let expressionsInCommonSamples = []
      if (this.ensembleData) {
        expressionsInCommonSamples = this.ensembleData
      } else {
        const expressionsBySampleId1 = Object.assign({}, ...this.expressions1.map((x) => ({ [x['Sample name']]: x[scoreType] })))
        const expressionsBySampleId2 = Object.assign({}, ...this.expressions2.map((x) => ({ [x['Sample name']]: x[scoreType] })))
        for (const [key, value] of Object.entries(expressionsBySampleId1)) {
          if (key in expressionsBySampleId2) {
            expressionsInCommonSamples.push({
              sampleId: key,
              expression1: value,
              expression2: expressionsBySampleId2[key]
            })
          }
        }
      }
      return expressionsInCommonSamples
    },

    linearRegression: function (y, x) {
      const lr = {}
      const n = y.length
      let sumX = 0
      let sumY = 0
      let sumXy = 0
      let sumXx = 0
      let sumYy = 0

      for (let i = 0; i < y.length; i++) {
        sumX += x[i]
        sumY += y[i]
        sumXy += (x[i] * y[i])
        sumXx += (x[i] * x[i])
        sumYy += (y[i] * y[i])
      }

      lr.slope = (n * sumXy - sumX * sumY) / (n * sumXx - sumX * sumX)
      lr.intercept = (sumY - lr.slope * sumX) / n
      let r2 = Math.pow((n * sumXy - sumX * sumY) / Math.sqrt((n * sumXx - sumX * sumX) * (n * sumYy - sumY * sumY)), 2)
      r2 = Math.sqrt(r2)
      lr.correlation = Math.round(r2 * 100) / 100
      return lr
    },

    plotExpression: function () {
      // set the dimensions and margins of the graph
      const margin = { top: 10, right: 30, bottom: 30, left: 60 }
      const width = this.width - margin.left - margin.right
      const height = this.height - margin.top - margin.bottom
      const that = this

      d3.select(`#${this.id}`).select('svg').remove()

      // append the svg object to the body of the page
      const svg = d3.select(`#${this.id}`)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom + 30)
        .call(d3.zoom().on('zoom', function (event) {
          svg.attr('transform', event.transform)
        }))
        .append('g')
        .attr('transform',
          'translate(' + margin.left + ',' + margin.top + ')')

      // Add X axis
      const minValueX = Math.min(10, Math.min(...this.expressionsCommon.map(d => d.expression1)))
      const maxValueX = Math.max(-10, Math.max(...this.expressionsCommon.map(d => d.expression1)))
      const x = d3.scaleLinear()
        .domain([minValueX, maxValueX])
        .range([0, width])
      svg.append('g')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(x))

      // Add Y axis
      const minValueY = Math.min(10, Math.min(...this.expressionsCommon.map(d => d.expression2)))
      const maxValueY = Math.max(-10, Math.max(...this.expressionsCommon.map(d => d.expression2)))

      // trendline parameters
      const XaxisData = []
      const YaxisData = []
      /*
      Object.entries(this.expressionsCommon).forEach(Element => {
        XaxisData.push(Element[1].expression1)
        YaxisData.push(Element[1].expression2)
      })
      */
      this.expressionsCommon.forEach(element => {
        XaxisData.push(element.expression1)
        YaxisData.push(element.expression2)
        if (this.removeOwncolor) {
          element.ownColor = 'grey'
        }
        let clrDot = 'grey'
        let sizeR = this.sizeR
        for (let s = 0; s < this.selIds.length; s++) {
          if (this.selIds[s] === element.sampleId) {
            element.ownColor = 'red'
            clrDot = 'red'
            sizeR = 4
          }
        }
        element.color = clrDot
        if (this.ownColor) {
          element.ownColor = clrDot
        }
        element.sizeR = sizeR
      })
      let x1 = minValueX
      let x2 = maxValueX
      const equation = this.linearRegression(YaxisData, XaxisData)
      let y1 = (equation.slope * x1) + equation.intercept
      let y2 = (equation.slope * x2) + equation.intercept

      if (y1 < minValueY) {
        // if overflow it updates the two vlaues
        y1 = minValueY
        x1 = (y1 - equation.intercept) / equation.slope
      }

      if (y2 < minValueY) {
        // if overflow it updates the two vlaues
        y2 = minValueY
        x2 = (y2 - equation.intercept) / equation.slope
      }

      const y = d3.scaleLinear()
        .domain([minValueY, maxValueY])
        .range([height, 0])
      svg.append('g')
        .call(d3.axisLeft(y))

      // Add the tooltip container to the vis container
      // it's invisible and its position/contents are defined during mouseover
      const tooltip = d3.select(`#${this.id}`).append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)

      // tooltip mouseover event handler
      const tipMouseover = function (e, d) {
        const html = d.sampleId
        tooltip.html(html)
          .style('left', (d - 20) + 'px')
          .style('top', (d) + 'px')
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
      const g = svg.append('g')
        .attr('clip-path', 'url(#clip)')

      if (this.ownColormethod) {
        svg.append('g')
          .selectAll('dot')
          .data(this.expressionsCommon)
          .enter()
          .append('circle')
          .attr('cx', function (d) {
            return x(d.expression1)
          })
          .attr('cy', function (d) {
            return y(d.expression2)
          })
          .attr('r', function (d) {
            return d.sizeR
          })
          .attr('fill', function (d) {
            return d.ownColor
          })
          .on('mousemove', tipMouseover)
          .on('mouseout', tipMouseout)
          .on('dblclick', function () { that.selectedDotCall(null) })
          .on('click', function (_, d) {
            that.selectedDotCall(d.sampleId)
            g.append('text')
              .attr('x', x(d.expression1))
              .attr('y', y(d.expression2))
              .text(d.sampleId)
          })
      } else {
        svg.append('g')
          .selectAll('dot')
          .data(this.expressionsCommon)
          .enter()
          .append('circle')
          .attr('cx', function (d) {
            return x(d.expression1)
          })
          .attr('cy', function (d) {
            return y(d.expression2)
          })
          .attr('r', function (d) {
            return d.sizeR
          })
          .attr('fill', function (d) {
            return d.color
          })
          .on('mousemove', tipMouseover)
          .on('mouseout', tipMouseout)
          .on('dblclick', function () { that.selectedDotCall(null) })
          .on('click', function (_, d) {
            that.selectedDotCall(d.sampleId)
            g.append('text')
              .attr('x', x(d.expression1))
              .attr('y', y(d.expression2))
              .text(d.sampleId)
          })
      }

      if (this.addTrendlinte) {
      // adding trendline to the plot
        svg
          .append('line')
          .data(this.expressionsCommon)
          .attr('x1', x(x1))
          .attr('x2', x(x2))
          .attr('y1', y(y1))
          .attr('y2', y(y2))
          .attr('stroke', 'black')
      }
      // add the x Axis
      if (this.addStatslinte) {
        svg
          .append('line')
          .attr('opacity', 0.7)
          .attr('y1', 0)
          .attr('y2', y(2))
          .attr('x1', x(1))
          .attr('x2', x(1))
          .attr('stroke', 'blue')
          .attr('stroke-dasharray', '3')

        svg
          .append('line')
          .attr('opacity', 0.7)
          .attr('y1', 0)
          .attr('y2', y(2))
          .attr('x1', x(-1))
          .attr('x2', x(-1))
          .attr('stroke', 'blue')
          .attr('stroke-dasharray', '3')

        // horizontal line
        svg
          .append('line')
          .attr('opacity', 0.7)
          .attr('y1', y(2))
          .attr('y2', y(2))
          .attr('x1', 0)
          .attr('x2', x(-1))
          .attr('stroke', 'blue')
          .attr('stroke-dasharray', '3')

        svg
          .append('line')
          .attr('opacity', 0.7)
          .attr('y1', y(2))
          .attr('y2', y(2))
          .attr('x1', x(1))
          .attr('x2', width)
          .attr('stroke', 'blue')
          .attr('stroke-dasharray', '3')
      }

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
        .text(this.identifier1 + ' ' + this.labelX.replace('Intensity', 'log10 Expression') + '  (' + this.omicsTypeX + ')')

      // add the y Axis
      svg
        .append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - height / 2)
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .text(this.identifier2 + ' ' + this.labelY.replace('Intensity', 'log10 Expression') + '  (' + this.omicsTypeY + ')')

      /*
      let line = d3.line()
        .x((d) => x(d[0]))
        .y((d) => y(d[1]));
      svg
      .append("path")
      .datum(res)
      .attr("class", "line")
      .attr("d", line)
*/
    }
  }
}
</script>
<style>
.tooltip {
  position: absolute;
  font-size: 14px;
  width: auto;
  height: auto;
  pointer-events: none;
  background-color: white;
}
</style>
