<template>
  <div id="container">
    <div :id="swarmId">
      <v-btn
        class="ma-2"
        color="primary"
        @click="reDrawPlot"
      >
        <v-icon
          dark
        >
          mdi-pencil
        </v-icon>
      </v-btn>

      <v-btn
        class="ma-2"
        color="primary"
        @click="resetPlot"
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
        @click="downloadSVG"
      >
        <v-icon
          dark
        >
          mdi-cloud-download
        </v-icon>
      </v-btn>
      <v-row class="dense align-center">
        <v-col
          cols="auto"
          class="p-0"
        >
          <v-text-field
            v-model="patientGroup"
            class="swarmbtn"
            label="Group:"
            placeholder="G1"
          />
        </v-col>
        <v-col
          cols="auto"
          class="p-0"
        >
          <v-text-field
            v-model="ticksIntervals"
            class="tick"
            label="Ticks:"
            placeholder="5"
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col width="20%">
          <v-color-picker
            v-model="colorCode"
            hide-inputs
            hide-canvas
            light
            swatches-max-height="50"
            width="300"
          />
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script>
import utils from '@/plugins/DownloadUtils'

const d3 = require('d3')
export default {
  name: 'SwarmPlot',
  props: {
    swarmData:
     {
       type: Array,
       default: undefined
     },
    savePlot: {
      type: Boolean,
      default: false
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

    drawBoxPlot: {
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
  data: () => ({
    colorCode: '',
    ticksIntervals: 5,
    patientGroup: '',
    LegendY: 40,
    scatterPoints: [],
    legendArray: []
  }),
  watch: {
    swarmData: function () {
      this.initSwarm()
      this.disposeLabels()
    },
    drawBoxPlot: function () {
      this.reDrawPlot()
    }
  },
  mounted () {
    this.initSwarm()
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

    disposeLabels: function () {
      this.patientGroup = ''
      this.LegendY = 40
      this.legendArray = []
      // this.initSwarm()
      // this.rePlot()
    },

    boxPlot: function (dataSet, fieldOfTable, width, yScale, margin, svg) {
      // Box plot display on the back ground
      if (this.drawBoxPlot) {
        const dataBoxplot = []
        dataSet.forEach(element => {
          dataBoxplot.push(element[fieldOfTable])
        })

        const dataSorted = dataBoxplot.sort(d3.ascending)
        const q1 = d3.quantile(dataSorted, 0.25)
        const median = d3.quantile(dataSorted, 0.5)
        // Using IQR for the outliars
        const q3 = d3.quantile(dataSorted, 0.75)
        const interQuantileRange = q3 - q1
        const min = q1 - 1.5 * interQuantileRange
        const max = q1 + 1.5 * interQuantileRange
        const recHeigth = yScale(q1) - yScale(q3)
        const center = (width - (margin.left))

        svg
          .append('line')
          .attr('opacity', 0.7)
          .attr('x1', center - (3 * margin.left))
          .attr('x2', center - (3 * margin.left))
          .attr('y1', yScale(min))
          .attr('y2', yScale(max))
          .attr('stroke', 'black')

        svg
          .append('rect')
          .attr('x', center - (4 * (margin.left) + margin.right))
          .attr('y', yScale(q3))
          .attr('height', recHeigth)
          .attr('width', 2 * (margin.left + margin.right))
          .attr('stroke', 'grey')
          .attr('opacity', 0.4)
          .style('fill', 'grey')
        svg
          .selectAll('toto')
          .data([min, median, max])
          .enter()
          .append('line')
          .attr('opacity', 0.7)
          .attr('x1', center - (4 * (margin.left) + margin.right))
          .attr('x2', center - (2 * (margin.left) - margin.right))
          .attr('y1', function (d) {
            return (yScale(d))
          })
          .attr('y2', function (d) {
            return (yScale(d))
          })
          .attr('stroke', 'grey')
      }
    },
    simulationSwarm: function (dataSet, width, svg, fieldOfTable, yScale, nominalField) {
      const spreadingFactor = dataSet.length > 1 ? 2 : 10
      // const simulationItrations = dataSet.length + 1000
      // const simulationItrations = 100
      const simulation = d3.forceSimulation(dataSet)
        .force('x', d3.forceX((width / 2) + spreadingFactor))
        .force('y', d3.forceY(d => yScale(d[fieldOfTable])).strength(10)) // Increase velocity
        .force('collide', d3.forceCollide(3))
        .alpha(1)
        .stop()

      // for (let i = 0; i < simulationItrations; ++i) {
      for (let i = 0, n = Math.ceil(Math.log(simulation.alphaMin()) / Math.log(1 - simulation.alphaDecay())); i < n; ++i) {
        simulation.tick()
      }
      const namesCircles = svg.selectAll('.names')
        .data(dataSet, function (d) {
          return d[nominalField]
        })
      namesCircles.enter()
        .append('circle')
        .attr('class', 'names')
        .attr('r', (d) => d.sizeR)
        .attr('fill', (d) => (!d.y) ? 'white' : d.colorID)
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

    manualLegendAdd: function (svg) {
      if (this.patientGroup.length > 0 & this.colorCode.length > 0) {
        const legend = {}
        legend.color = this.colorCode
        legend.group = this.patientGroup
        legend.Y = this.LegendY
        this.legendArray.push(legend)
        this.LegendY += 20
        this.legendArray.forEach(element => {
          svg.append('circle').attr('cx', 90).attr('cy', element.Y).attr('r', 6).style('fill', element.color)
          svg.append('text').attr('x', 100).attr('y', element.Y).text(element.group).style('font-size', '15px').attr('alignment-baseline', 'middle')
        })
      }
    },
    selectedDotCall (sel) {
      this.$emit('onDotClick', sel)
    },

    mouseHover: function (pltobj, nominalField, fieldOfTable, tooltip, xLine) {
      const svg = pltobj.svg
      // const y = pltobj.yScale
      const g = svg.append('g')
        .attr('clip-path', 'url(#clip)')
      const that = this
      d3.selectAll('.names')
        .on('mousemove', function (d) {
          tooltip.html(`<strong>${d.target.__data__[nominalField]}</strong><br>
        ${d.target.__data__[fieldOfTable]}`)
            .style('top', (d.pageY - 50) + 'px')
          // .style('left', (d.pageX) + 'px')
            .style('opacity', 0.9)
          xLine.attr('x1', d3.select(this).attr('cx'))
            .attr('y1', d3.select(this).attr('cy'))
            .attr('y2', d3.select(this).attr('cy'))
            .attr('x2', 50)
            .attr('opacity', 1)
        })
        .on('mouseout', function () {
        // console.log(_.target.__data__[fieldOfTable])
          tooltip.style('opacity', 0)
          xLine.attr('opacity', 0)
        })
        .on('click', function (d) { that.selectedDotCall(d.target.__data__[nominalField]) })
        .on('dblclick', function (d) {
          that.selectedDotCall(null)
          g.append('text')
            .attr('x', (that.height / 2) - (that.width / 2) + 4)
            .attr('y', d3.select(this).attr('cy'))
            .style('font', '11px arial')
            .text(d.target.__data__[fieldOfTable].toFixed(2))
        })
    },

    prepFunc: function (svg, margin, yScale) {
      svg.append('g')
        .attr('class', 'y axis')

      svg.append('g').attr('class', 'lines')
      svg.append('g').attr('class', 'selcirc')

      const titlePlot = this.swarmTitlePrefix + ' (' + this.swarmTitle + ')'
      svg.append('text')
      // .attr("class", "y label")
        .attr('transform', 'rotate(-90)')
        .attr('text-anchor', 'middle')
        .attr('x', -this.height / 2)
        .attr('y', 15)
        .text(titlePlot)

      const xLine = svg.append('line')
        .attr('stroke', 'rgb(96,125,139)')
        .attr('stroke-dasharray', '1,2')

      const tooltip = d3.select(`#${this.swarmId}`)
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 1)

      const yAxis = d3.axisRight(yScale)
        .ticks(this.ticksIntervals, '.2f')
        .tickFormat(d3.format(',.2f'))
        .tickSizeInner(0)

      d3.transition(svg).select('.y.axis')
        .attr('transform', 'translate(' + (margin.left) + ',01)')
        .call(yAxis)

      return { tooltip, xLine }
    },
    initaxes: function (width, height, margin, dataSet, fieldOfTable) {
      d3.select(`#${this.swarmId}`).selectAll('svg').remove()
      const svg = d3.select(`#${this.swarmId}`)
        .append('svg')
        .attr('class', 'd3')
        .attr('width', width)
        .attr('height', height)
      this.manualLegendAdd(svg) // adding element of the legends
      const yScale = d3.scaleLinear()
        .range([height - margin.bottom, margin.top])
        .domain(d3.extent(dataSet, function (d) {
          return +d[fieldOfTable]
        }))

      return ({ yScale, svg })
    },
    reDrawPlot: function () {
      const resetPlot = false
      this.rePlot(resetPlot)
    },
    resetPlot () {
      const resetPlot = true
      this.rePlot(resetPlot)
    },
    rePlot: function (resetPlot) {
      const fieldOfTable = this.fieldValues // Data field for the y position values
      const nominalField = this.fieldName // Identifier of the data on the table
      const dataSet = this.scatterPoints
      this.$emit('selectedCells', { colorCode: this.colorCode, selectedPatiens: this.swarmSelIds })
      if (this.swarmSelIds.length > 0) {
        this.swarmSelIds.forEach(element => {
          dataSet[element].colorID = this.colorCode
          dataSet[element].sizeR = 4
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
      const pltobj = this.initaxes(this.width, this.height, this.margin, dataSet, fieldOfTable)
      const svg = pltobj.svg
      const yScale = pltobj.yScale
      this.boxPlot(dataSet, fieldOfTable, this.width, yScale, this.margin, svg) // draw boxplot
      const plotObject = this.prepFunc(svg, this.margin, yScale)
      const tooltip = plotObject.tooltip
      const xLine = plotObject.xLine

      // scatter plot
      const scatterPoints = this.scatterPoints
      svg.append('g')
        .selectAll('dot')
        .data(scatterPoints)
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
          return (!d.y) ? 'white' : d.colorID
        })

      this.mouseHover(pltobj, nominalField, fieldOfTable, tooltip, xLine) // at mouse  hover
      this.patientGroup = ''
    },

    initSwarm: function () {
      const pltobj = this.initaxes(this.width, this.height, this.margin, this.swarmData, this.fieldValues)
      this.boxPlot(this.swarmData, this.fieldValues, this.width, pltobj.yScale, this.margin, pltobj.svg) // draw boxplot
      const plotObject = this.prepFunc(pltobj.svg, this.margin, pltobj.yScale)
      const tooltip = plotObject.tooltip
      const xLine = plotObject.xLine
      this.simulationSwarm(this.swarmData, this.width, pltobj.svg, this.fieldValues, pltobj.yScale, this.fieldName) // 1st simulation of the data on the plot
      this.mouseHover(pltobj, this.fieldName, this.fieldValues, tooltip, xLine) // at mouse hover
    }
  }
}
</script>

<style>

#color-btn {
  background-color: rgb(136, 230, 220);

}

.v-text-field {
  width: 400px;

}
.swarmbtn {
  width: 70px;

}

.tick {
  width: 40px;

}

.tooltip {
  position: absolute;
  font-size: 12px;
  width: auto;
  height: auto;
  pointer-events: none;
  background-color: white;
}
</style>
