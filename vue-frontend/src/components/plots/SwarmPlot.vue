<template>
  <v-container class="pa-0 mt-2" :id="swarmId">
    <v-row dense>
      <v-col>
        <v-btn color="primary" @click="redrawPlot(true)" class="mx-2">
          <v-icon> mdi-refresh </v-icon>
        </v-btn>
        <v-btn v-if="savePlot" color="primary" @click="downloadSVG" class="mx-2">
          <v-icon> mdi-cloud-download </v-icon>
        </v-btn>
      </v-col>
      <v-col>
        <v-number-input inset density="compact" control-variant="split" v-model="ticksIntervals" variant="outlined" label="desired y-ticks" :step="1" max-width="150"/>
      </v-col>
    </v-row>
    <v-row dense>
      <v-col>
        <highlight-selection @highlight-selection="highlightSelection" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import utils from '@/plugins/DownloadUtils'
import HighlightSelection from '@/components/partials/HighlightSelection.vue'

import * as d3 from 'd3'
export default {
  name: 'SwarmPlot',
  components: {
    HighlightSelection
  },
  props: {
    swarmData: {
      type: Array,
      default: undefined
    },
    savePlot: {
      type: Boolean,
      default: true
    },
    swarmSelIds: {
      type: Array,
      default: undefined
    },
    swarmId: {
      type: String,
      default: 'SwarmPlot'
    },
    swarmTitle: {
      type: String,
      default: undefined
    },
    swarmTitlePrefix: {
      type: String,
      default: undefined
    },
    drawSwarmPlot: {
      type: Boolean,
      default: true
    },
    drawStripPlot: {
      type: Boolean,
      default: false
    },
    drawBoxPlot: {
      type: Boolean,
      default: false
    },
    drawViolinPlot: {
      type: Boolean,
      default: false
    },
    margin: {
      type: Object,
      default: function () {
        return { top: 10, right: 0, bottom: 10, left: 50 }
      }
    },
    height: {
      type: Number,
      default: 500
    },
    width: {
      type: Number,
      default: 400
    },
    fieldName: {
      type: String,
      default: undefined
    },
    fieldValues: {
      type: String,
      default: undefined
    }
  },
  data() {
    return {
      colorCode: '#ff0000',
      ticksIntervals: 5,
      patientGroup: '',
      LegendY: 40,
      scatterPoints: [],
      legendArray: []
    }
  },
  watch: {
    swarmData: function () {
      this.initSwarm()
      this.disposeLabels()
    },
    fieldValues: function () {
      this.initSwarm()
    },
    drawBoxPlot: function () {
      this.redrawPlot()
    }
  },
  mounted() {
    this.initSwarm()
  },

  methods: {
    downloadSVG() {
      const aPlots = []
      aPlots.push(d3.select(this.$el).select('svg').node())
      if (aPlots.length > 0) {
        utils.downloadSVGs(aPlots, '', false, 'canvasId', [])
      }
    },

    disposeLabels: function () {
      this.patientGroup = ''
      this.LegendY = 40
      this.legendArray = []
    },

    highlightSelection({ groupLabel, colorCode }) {
      // Handle the redraw event from the child component
      this.patientGroup = groupLabel
      this.colorCode = colorCode
      this.redrawPlot()
    },

    boxPlot: function (dataSet, fieldOfTable, width, yScale, margin, svg) {
      if (!this.drawBoxPlot) return

      // Box plot in the background
      const dataBoxplot = []
      dataSet.forEach(element => {
        dataBoxplot.push(element[fieldOfTable])
      })
      const dataSorted = dataBoxplot.sort(d3.ascending)
      const q1 = d3.quantile(dataSorted, 0.25)
      const median = d3.quantile(dataSorted, 0.5)
      const q3 = d3.quantile(dataSorted, 0.75)
      
      // Using IQR to determine outliers
      const interQuantileRange = q3 - q1
      const min = q1 - 1.5 * interQuantileRange
      const max = q1 + 1.5 * interQuantileRange
      const recHeigth = yScale(q1) - yScale(q3)
      var boxWidth = (width - margin.left - margin.right) / 2
      if (this.drawViolinPlot) boxWidth /= 5

      svg
        .append('line')
        .attr('opacity', 0.7)
        .attr('x1', width / 2)
        .attr('x2', width / 2)
        .attr('y1', yScale(min))
        .attr('y2', yScale(max))
        .attr('stroke', 'black')

      svg
        .append('rect')
        .attr('x', width / 2 - boxWidth / 2)
        .attr('y', yScale(q3))
        .attr('height', recHeigth)
        .attr('width', boxWidth)
        .attr('stroke', 'grey')
        .attr('opacity', 0.4)
        .style('fill', 'grey')
      svg
        .selectAll('toto')
        .data([min, median, max])
        .enter()
        .append('line')
        .attr('opacity', 0.7)
        .attr('x1', width / 2 - boxWidth / 2)
        .attr('x2', width / 2 + boxWidth / 2)
        .attr('y1', function (d) {
          return yScale(d)
        })
        .attr('y2', function (d) {
          return yScale(d)
        })
        .attr('stroke', 'grey')
    },
    /**
     * Adapted from https://d3-graph-gallery.com/graph/violin_basicHist.html
     */
    violinPlot: function (dataSet, fieldOfTable, width, yScale, margin, svg) {
      if (!this.drawViolinPlot) return

      // Box plot in the background
      const dataViolinPlot = []
      dataSet.forEach(element => {
        dataViolinPlot.push(element[fieldOfTable])
      })
      var histogram = d3.histogram()
        .domain(yScale.domain())
        .thresholds(yScale.ticks(20)) // Important: how many bins approx are going to be made? It is the 'resolution' of the violin plot
        .value(d => d)
      
      var bins = histogram(dataViolinPlot)
      const boxWidth = (width - margin.left - margin.right) / 2

      var maxNum = d3.max(bins, a => a.length)

      var xNum = d3.scaleLinear()
        .range([0, boxWidth])
        .domain([-maxNum, maxNum])

      svg
        .append("g")
          .attr("transform", function(d){ return("translate(" + (width / 2 - boxWidth / 2) + " ,0)") } )
        .append("path")
          .datum(bins)
          .style("stroke", "none")
          .attr('opacity', 0.4)
          .style("fill", "grey")
          .attr("d", d3.area()
            .x0(function(d){ return(xNum(-d.length)) } )
            .x1(function(d){ return(xNum(d.length)) } )
            .y(function(d){ return(yScale(d.x0)) } )
            .curve(d3.curveCatmullRom)    // This makes the line smoother to give the violin appearance. Try d3.curveStep to see the difference
          )
    },
    simulationSwarm: function (dataSet, width, svg, fieldOfTable, yScale, margin, nominalField) {
      const spreadingFactor = dataSet.length > 1 ? 2 : 10

      // Initialize positions before simulation starts
      dataSet.forEach(d => {
        d.x = width / 2
        d.y = yScale(d[fieldOfTable])
      })

      // const simulationItrations = dataSet.length + 1000
      // const simulationItrations = 100
      if (this.drawSwarmPlot) {
        const simulation = d3
          .forceSimulation(dataSet)
          .force('x', d3.forceX(width / 2 + spreadingFactor))
          .force('y', d3.forceY(d => yScale(d[fieldOfTable])).strength(10)) // Increase velocity
          .force('collide', d3.forceCollide(3))
          .alpha(0.3)
          .stop()

        // for (let i = 0; i < simulationItrations; ++i) {
        for (
          let i = 0,
          n = Math.ceil(Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay()));
          i < n;
          ++i
        ) {
          simulation.tick()
        }
      } else if (this.drawStripPlot) {
        const random = this.mulberry32(42)  // use pseudo random numbers for reproducibility

        const boxWidth = (width - margin.left - margin.right) / 2
        dataSet.forEach(d => {
          d.x = d.x + (random()-0.5)*boxWidth
        })
      }
      const namesCircles = svg.selectAll('.names').data(dataSet, function (d) {
        return d[nominalField]
      })
      namesCircles
        .enter()
        .append('circle')
        .attr('class', 'names')
        .attr('r', d => d.sizeR)
        .attr('fill', d => (!d.y ? 'white' : d.colorID))
        .merge(namesCircles)
        .transition()
        .duration(1)
        .attr('cx', function (d) {
          return d.x
        })
        .attr('cy', function (d) {
          return d.y
        })
      const scatterData = []
      d3.selectAll('.names')._groups[0].forEach(element => {
        const point = {}
        point[fieldOfTable] = element.__data__[fieldOfTable]
        point[nominalField] = element.__data__[nominalField]
        point.colorID = element.__data__.colorID
        point.sizeR = element.__data__.sizeR
        point.x = element.__data__.x
        point.y = element.__data__.y
        scatterData.push(point)
      })
      this.scatterPoints = scatterData
    },
    mulberry32: function (seed) {
      return function() {
        seed |= 0; // Ensure seed is an integer
        seed = seed + 0x6D2B79F5 | 0;
        let t = Math.imul(seed ^ seed >>> 15, seed | 1);
        t = t + Math.imul(t ^ t >>> 7, t | 61) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296; // Return a float in [0, 1)
      };
    },
    addLegend: function (svg) {
      if (this.patientGroup && this.colorCode) {
        const legend = {}
        legend.color = this.colorCode
        legend.group = this.patientGroup
        legend.Y = this.LegendY
        this.legendArray.push(legend)
        this.LegendY += 20
      }
      if (this.legendArray.length > 0) {
        this.legendArray.forEach(element => {
          svg
            .append('circle')
            .attr('cx', 90)
            .attr('cy', element.Y)
            .attr('r', 6)
            .style('fill', element.color)
          svg
            .append('text')
            .attr('x', 100)
            .attr('y', element.Y)
            .text(element.group)
            .style('font-size', '15px')
            .attr('alignment-baseline', 'middle')
        })
      }
    },
    selectedDotCall(sel) {
      this.$emit('onDotClick', sel)
    },

    mouseHover: function (pltobj, nominalField, fieldOfTable, tooltip, xLine) {
      const svg = pltobj.svg
      // const y = pltobj.yScale
      const g = svg.append('g').attr('clip-path', 'url(#clip)')
      const that = this
      d3.selectAll('.names')
        .on('mousemove', function (d) {
          tooltip
            .html(
              `<strong>${d.target.__data__[nominalField]}</strong><br>
        ${d.target.__data__[fieldOfTable]}`
            )
            .style('top', d.pageY - 50 + 'px')
            // .style('left', (d.pageX) + 'px')
            .style('opacity', 0.9)
          xLine
            .attr('x1', d3.select(this).attr('cx'))
            .attr('y1', d3.select(this).attr('cy'))
            .attr('y2', d3.select(this).attr('cy'))
            .attr('x2', 50)
            .attr('opacity', 1)
        })
        .on('mouseout', function () {
          tooltip.style('opacity', 0)
          xLine.attr('opacity', 0)
        })
        .on('click', function (d) {
          that.selectedDotCall(d.target.__data__[nominalField])
        })
        .on('dblclick', function (d) {
          that.selectedDotCall(null)
          g.append('text')
            .attr('x', that.height / 2 - that.width / 2 + 4)
            .attr('y', d3.select(this).attr('cy'))
            .style('font', '11px arial')
            .text(d.target.__data__[fieldOfTable].toFixed(2))
        })
    },

    prepareAxisAndTooltip: function (svg, margin, yScale) {
      svg.append('g').attr('class', 'y axis')
      svg.append('g').attr('class', 'lines')

      const ylabel = this.swarmTitlePrefix + ' (' + this.swarmTitle + ')'
      svg
        .append('text')
        // .attr("class", "y label")
        .attr('transform', 'rotate(-90)')
        .attr('text-anchor', 'middle')
        .attr('x', -this.height / 2)
        .attr('y', 15)
        .text(ylabel)

      const xLine = svg
        .append('line')
        .attr('stroke', 'rgb(96,125,139)')
        .attr('stroke-dasharray', '1,2')

      const tooltip = d3
        .select(`#${this.swarmId}`)
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 1)

      const yAxis = d3
        .axisRight(yScale)
        .ticks(this.ticksIntervals, '.2f')
        .tickFormat(d3.format(',.2f'))
        .tickSizeInner(0)

      d3.transition(svg)
        .select('.y.axis')
        .attr('transform', 'translate(' + margin.left + ',01)')
        .call(yAxis)

      return { tooltip, xLine }
    },
    initAxes: function (width, height, margin, dataSet, fieldOfTable) {
      d3.select(`#${this.swarmId}`).selectAll('svg').remove()
      const svg = d3
        .select(`#${this.swarmId}`)
        .append('svg')
        .attr('class', 'd3')
        .attr('width', width)
        .attr('height', height)
      this.addLegend(svg) // adding element of the legends
      const yScale = d3
        .scaleLinear()
        .range([height - margin.bottom, margin.top])
        .domain(
          d3.extent(dataSet, function (d) {
            return +d[fieldOfTable]
          })
        )

      return { yScale, svg }
    },
    /**
     * Draw all elements from plot from scratch but reuse swarm coordinates
     * @param {Boolean} resetPlot - remove highlights from all points
     */
    redrawPlot: function (resetPlot = false) {
      const fieldOfTable = this.fieldValues // Data field for the y position values
      const nominalField = this.fieldName // Identifier of the data on the table
      const dataSet = this.scatterPoints
      this.$emit('selectedCells', {
        colorCode: this.colorCode,
        selectedSamples: this.swarmSelIds
      })
      if (this.swarmSelIds.length > 0) {
        this.swarmSelIds.forEach(element => {
          if (element < dataSet.length) {
            dataSet[element].colorID = this.colorCode
            dataSet[element].sizeR = 4
          }
        })
      }

      if (resetPlot) {
        this.disposeLabels()
        for (let i = 0; i < dataSet.length; i++) {
          dataSet[i].colorID = 'grey'
          dataSet[i].sizeR = 2
        }
      }

      this.scatterPoints = dataSet // using scatter points instead of simulation
      const pltobj = this.initAxes(this.width, this.height, this.margin, dataSet, fieldOfTable)
      const svg = pltobj.svg
      const yScale = pltobj.yScale
      this.violinPlot(dataSet, fieldOfTable, this.width, yScale, this.margin, svg) // draw boxplot
      this.boxPlot(dataSet, fieldOfTable, this.width, yScale, this.margin, svg) // draw boxplot
      const plotObject = this.prepareAxisAndTooltip(svg, this.margin, yScale)
      const tooltip = plotObject.tooltip
      const xLine = plotObject.xLine

      // scatter plot
      svg
        .append('g')
        .selectAll('dot')
        .data(this.scatterPoints)
        .enter()
        .append('circle')
        .attr('class', 'names')
        .attr('cx', function (d) {
          return d.x
        })
        .attr('cy', function (d) {
          return d.y
        })
        .attr('r', function (d) {
          return d.sizeR
        })
        .style('fill', function (d) {
          return !d.y ? 'white' : d.colorID
        })

      this.mouseHover(pltobj, nominalField, fieldOfTable, tooltip, xLine)
      this.patientGroup = ''
    },

    initSwarm: function () {
      if (this.swarmData.length === 0) return

      this.disposeLabels()
      const swarmDataFiltered = this.swarmData.filter(
        d => typeof d[this.fieldValues] === 'number'
      )
      const pltobj = this.initAxes(
        this.width,
        this.height,
        this.margin,
        swarmDataFiltered,
        this.fieldValues
      )
      this.violinPlot(
        swarmDataFiltered,
        this.fieldValues,
        this.width,
        pltobj.yScale,
        this.margin,
        pltobj.svg
      ) // draw violinplot
      this.boxPlot(
        swarmDataFiltered,
        this.fieldValues,
        this.width,
        pltobj.yScale,
        this.margin,
        pltobj.svg
      ) // draw boxplot
      const plotObject = this.prepareAxisAndTooltip(pltobj.svg, this.margin, pltobj.yScale)
      const tooltip = plotObject.tooltip
      const xLine = plotObject.xLine
      this.simulationSwarm(
        swarmDataFiltered,
        this.width,
        pltobj.svg,
        this.fieldValues,
        pltobj.yScale,
        this.margin,
        this.fieldName
      ) // 1st simulation of the data on the plot
      this.mouseHover(pltobj, this.fieldName, this.fieldValues, tooltip, xLine) // at mouse hover
    }
  }
}
</script>

<style>
#color-btn {
  background-color: rgb(136, 230, 220);
}

/* .v-text-field {
  width: 400px;

} */
.tooltip {
  position: absolute;
  font-size: 12px;
  width: auto;
  height: auto;
  pointer-events: none;
  background-color: white;
}

.v-color-picker__controls {
  padding: 0px;
}
</style>
