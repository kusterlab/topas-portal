<template>
  <v-row class="pa-4 grey lighten-3">
    <v-col
      sm="12"
      md="5"
      lg="4"
    >
      <v-card flat>
        <v-card-title
          tag="h1"
        >
          Kinobeads
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="identifierDrug"
            dense
            outlined
            label="Single or multi kinodbeads_Targets"
            placeholder="EGFR_YES1"
            @change="updateDrugId"
          />
          <v-radio-group
            v-model="sortFunction"
          >
            <v-radio
              label="Sort Drugs by Average Kd values of  genes"
              color="red"
              value="mean"
            />
            <v-radio
              label="Sort Drugs by Median Kd of genes"
              color="blue"
              value="median"
            />
            <v-radio
              label="Sort Drugs by their top gene from the above list"
              color="green"
              value="min"
            />
          </v-radio-group>
          <v-flex
            class="box"
            xs2
            sm2
            md2
            lg2
            xl2
          >
            <bar-plot
              v-if="barplotData"
              :barplot-data="barplotData"
              :barplot-max="barplotMaximum"
            />
          </v-flex>
        </v-card-text>
      </v-card>
    </v-col>
    <v-col
      sm="12"
      md="7"
      lg="8"
    >
      <v-card flat>
        <v-card-text>
          <drug-table
            :data-source="drugData"
            @getGenes="yieldGenes"
          />
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
import drugTable from '@/components/tables/DrugTable'
import barPlot from '@/components/plots/DrugBarPlot.vue'
import axios from 'axios'

export default {
  name: 'DrugComponent',
  components: {
    drugTable,
    barPlot
  },
  props: {
    minWidth: {
      type: Number,
      default: 400
    },
    minHeight: {
      type: Number,
      default: 300
    }
  },
  data: () => ({

    identifierDrug: '',
    sortFunction: 'mean',
    barplotData: false,
    barplotMaximum: 5000,
    drugData: `${process.env.VUE_APP_API_HOST}/drugs`

  }),
  watch: {
    sortFunction: function () {
      this.updateDrugId()
    }
  },
  methods: {
    yieldGenes (value) {
      this.barplotData = value.plotData
      this.barplotMaximum = value.maximum
    },
    async updateDrugId () {
      const drugGeneName = this.identifierDrug
      const sortFunction = this.sortFunction
      if (drugGeneName.length === 0) {
        return axios.get(`${process.env.VUE_APP_API_HOST}/drugs`)
          .then(response => {
            this.drugData = response.data
          })
          .catch(error => {
            console.log(error)
          })
      } else {
        return axios.get(`${process.env.VUE_APP_API_HOST}/drug_genes/${sortFunction}/${drugGeneName}`)
          .then(response => {
            // this.drugData=response.data.filter(item => item.Drug == drugName)
            this.drugData = response.data
          })
          .catch(error => {
            console.log(error)
          })
      }
    }
  }

}
</script>
<style scoped>
</style>
