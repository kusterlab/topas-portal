<template>
  <div
    v-if="plotData"
    :id="lollipopId"
    class="lollipopchart"
  >
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
  name: 'LolipopPlot',
  props: {
    // this is the id of the plot
    lollipopId: {
      type: String,
      default: 'loliPop'
    },
    savePlot: {
      type: Boolean,
      default: true
    },
    // title for the plot
    loliTitle: {
      type: String,
      default: 'loliPop'
    },
    // upper and lower limit of the plot with two lines
    vline: {
      type: Number,
      default: null
    },
    showLegends: {
      type: Boolean,
      default: null
    },
    // if true the plot will be positive in both up and dowon direction to show two modalities
    overlappingY: {
      type: Boolean,
      default: null
    },
    // if true it will be lolipop else barplot
    loliMode: {
      type: Boolean,
      default: null
    },
    completeTooltip: {
      type: Boolean,
      default: null
    },
    width: {
      type: Number,
      default: 600
    },
    height: {
      type: Number,
      default: 400
    },
    loliradian: {
      type: Number,
      default: 5
    },
    fixedDomain: {
      type: Array,
      default: () => [{
        min: -5,
        max: 5
      }]
    },
    plotData: {
      type: Array,
      // the data should be arranged as bellow
      default: () => [{
        label: 'EGFR',
        value: 1,
        type: 'A',
        color: 'red'
      },
      {
        label: 'EGFR',
        value: -1,
        type: 'A',
        color: 'blue'
      },
      {
        label: 'new',
        value: -2,
        type: 'B',
        color: 'blue'
      },
      {
        label: 'new',
        value: 1.5,
        type: 'B',
        color: 'red'
      }
      ]
    }
  },
  data: () => ({
  }),
  watch: {
    plotData: function () {
      if (this.plotData.length > 0) {
        this.plotExpression()
        this.draw = true
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
      const color = d3.scaleOrdinal()
        .range(data.map(function (d) { return d.color }))
      // set the dimensions and margins of the graph
      const margin = { top: 70, right: 150, bottom: 30, left: 60 }
      const width = this.width - margin.left - margin.right
      const height = this.height - margin.top - margin.bottom
      let maxDomain = Math.max(...data.map(function (d) { return d.value }))
      let minDomain = Math.min(...data.map(function (d) { return d.value }))
      if (this.fixedDomain) {
        minDomain = this.fixedDomain[0].min
        maxDomain = this.fixedDomain[0].max
      }
      const xx = d3.scaleBand()
        .range([0, width])
        .padding(0.9)

      const y = d3.scaleLinear()
        .range([height, minDomain])

      xx.domain(data.map(function (d) {
        return d.label
      }))

      y.domain([minDomain, maxDomain])
      d3.select(`#${this.lollipopId}`).selectAll('svg').remove()
      const svg = d3.select(`#${this.lollipopId}`)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        // .call(d3.zoom().on('zoom', function (event) {
        //   svg.attr('transform', event.transform)
        // }))
        .append('g')
        .attr('class', 'lollipopchart')
        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')

      const tooltip = d3.select(`#${this.lollipopId}`).append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)
      // tooltip mouseover event handler
      const tipMouseover = function (_, d) {
        tooltip.html(this.completeTooltip ? (d.label + '_Score: ' + d.value.toFixed(2) + '_' + d.type) : d.label)
          .transition()
          .duration(200) // ms
          .style('bottom', margin.top + margin.left + 'px')
          .style('opacity', 0.9) // started as 0!
      }

      // tooltip mouseout event handler
      const tipMouseout = function () {
        tooltip.transition()
          .duration(300) // ms
          .style('opacity', 0) // don't care about position!
      }
      const lollipop = svg.append('g').attr('class', 'lollipop')

      const bars = lollipop
        .append('g')
        .attr('class', 'bars')

      bars.selectAll('.bar')
        .data(data)
        .enter().append('rect')
        .attr('class', 'bar')
        .attr('fill', 'grey')
        .attr('fill', function (d, i) {
          return color(i)
        })
        .attr('x', function (d) {
          return xx(d.label)
        })
        .attr('width', xx.bandwidth())
        .attr('y', height)
        .transition()
        .duration(1500)
        .attr('y', function (d) {
          return d.value > 0 ? y(d.value) : y(0)
        })
        .attr('height', function (d) {
          return d.value > 0 ? y(0) - y(d.value) : y(d.value) - y(0)
        })
      if (this.loliMode) {
        const lolliradian = this.loliradian

        const circles = lollipop
          .append('g')
          .attr('class', 'circles')

        circles.selectAll('circle')
          .data(data)
          .enter()
          .append('circle')
          .attr('cx', function (d) {
            return (xx(d.label) + xx.bandwidth() / 2)
          })
          .attr('cy', height)
          .attr('r', xx.bandwidth() / 2)
          .attr('fill', 'white')
          .attr('stroke-width', 5)
          .attr('stroke', 'grey')
          .attr('stroke', function (d, i) {
            return color(i)
          })
          .transition()
          .duration(1500)
          .attr('cy', function (d) {
            return y(d.value)
          })
          .on('end', function () {
            d3.select(this)
              .transition()
              .duration(500)
              .attr('r', lolliradian)
          })
      }
      lollipop.append('g')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisTop(xx))
        .selectAll('text')
        .style('text-anchor', 'end')
        .attr('dx', '-1.1em')
        .attr('dy', '+1em')
        .attr('transform', 'rotate(-90)')

      if (this.overlappingY) {
        lollipop.append('g')
          .call(d3.axisLeft(y))
          .selectAll('text')
          .text(function (d) {
            return (d > 0 ? d : -d)
          })
      } else {
        lollipop.append('g')
          .call(d3.axisLeft(y))
      }

      svg.selectAll('circle')
        .data(data)
        .on('mousemove', tipMouseover)
        .on('mouseout', tipMouseout)
      /*
      const yScale = d3.scaleLinear()
        .range([height, minDomain])
        .domain(d3.extent(data, function (d) {
          return +d.value
        }))
      */
      if (this.vline && (this.vline < maxDomain)) {
        svg
          .append('line')
          .attr('opacity', 0.7)
          .attr('y1', y(this.vline))
          .attr('y2', y(this.vline))
          .attr('x1', 0)
          .attr('x2', width)
          .attr('stroke', 'blue')
          .attr('stroke-dasharray', '2')
        /*
        svg
          .append('line')
          .attr('opacity', 0.7)
          .attr('y1', y(this.vline * -1))
          .attr('y2', y(this.vline * -1))
          .attr('x1', 0)
          .attr('x2', width)
          .attr('stroke', 'blue')
          .attr('stroke-dasharray', '2')
        */
      }

      svg
        .append('line')
        .attr('opacity', 0.7)
        .attr('y1', y(0))
        .attr('y2', y(0))
        .attr('x1', 0)
        .attr('x2', width)
        .attr('stroke', 'black')
      /*
      data.forEach(element => {
        element.id = element.type + element.color // to get the unique list for the legends
      })
      */
      const titlePlot = this.loliTitle
      svg.append('text')
      // .attr("class", "y label")
        .attr('transform', 'rotate(-90)')
        .attr('text-anchor', 'middle')
        .attr('x', -height / 2)
        .attr('y', -40)
        .text(titlePlot)
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
        let py = 30
        unique.forEach(element => {
          svg.append('text').attr('x', this.width - 140).attr('y', py).text(element.type).style('font-size', '16px')
          svg.append('circle').attr('cx', this.width - 150).attr('cy', py).attr('r', 6).style('fill', element.color)
          py = py + 20
        })
      }
    }
  }

}
</script>
<style>

</style>
