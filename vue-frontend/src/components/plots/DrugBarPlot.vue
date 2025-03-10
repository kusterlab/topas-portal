<template>
  <div id="barplot" />
</template>
<script>
const d3 = require('d3')
export default {
  name: 'BarPlot',
  props: {
    barplotData: {
      type: Array,
      default: undefined
    },
    barplotMax: {
      type: Number,
      default: undefined
    }
  },
  watch: {
    barplotData: function () {
      this.barPlotfunc()
    }
  },
  mounted () {
    this.barPlotfunc()
  },
  methods: {
    barPlotfunc () {
      const data = this.barplotData

      // set the dimensions and margins of the graph
      const margin = { top: 20, right: 30, bottom: 40, left: 90 }
      const width = 460 - margin.left - margin.right
      const height = 400 - margin.top - margin.bottom

      // append the svg object to the body of the page
      d3.select('#barplot').selectAll('svg').remove()
      const svg = d3.select('#barplot')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .call(d3.zoom().on('zoom', function (event) {
          svg.attr('transform', event.transform)
        }))
        .append('g')
        .attr('transform',
          'translate(' + margin.left + ',' + margin.top + ')')

      // Add X axis
      const x = d3.scaleLinear()
        .domain([0, this.barplotMax])
        .range([0, width])
      svg.append('g')
        .attr('transform', 'translate(0,' + height + ')')
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('transform', 'translate(-10,0)rotate(-45)')
        .style('text-anchor', 'end')

      // Y axis
      const y = d3.scaleBand()
        .range([0, height])
        .domain(data.map(function (d) { return d.Drug }))
        .padding(0.1)
      svg.append('g')
        .call(d3.axisLeft(y))
      /*
      const zoom = d3.zoom()
        .scaleExtent([0.5, 20]) // This control how much you can unzoom (x0.5) and zoom (x20)
        .extent([[0, 0], [width, height]])
        .on('zoom', updateChart(x, y))
      */
      // Bars
      svg.selectAll('myRect')
        .data(data)
        .enter()
        .append('rect')
        .attr('x', x(0))
        .attr('y', function (d) { return y(d.Drug) })
        .attr('width', function (d) { return x(parseInt(d.Kdapp)) })
        .attr('height', y.bandwidth())
        .attr('fill', '#69b3a2')
      /*
      function updateChart (xAxis, yAxis) {
        // recover the new scale
        const newX = d3.event.transform.rescaleX(x)
        const newY = d3.event.transform.rescaleY(y)

        // update axes with these new boundaries
        xAxis.call(d3.axisBottom(newX))
        yAxis.call(d3.axisLeft(newY))
        svg.selectAll('myRect')
          .attr('y', function (d) { return newY(d.Drug) })
          .attr('width', function (d) { return newX(parseInt(d.Kdapp)) })
      }
      */
    }
  }

}

</script>
