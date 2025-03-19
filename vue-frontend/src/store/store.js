import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    all_diseases: [],
    loading: false,
    cohortIndex: -1,
    diseaseName: '',
    // cookieAccepted: localStorage.getItem('cookieConsent') === 'accepted'   // for now we remove cookies consent, since no user personal data is saved as cookies; remove the bellow line and activate this line incase you need consent in front
    cookieAccepted: true // remove this line and activate the above line to activate consent for cookies
  },
  mutations: {
    ACCEPT_COOKIES (state) {
      state.cookieAccepted = true
    },
    setCohortIndex (state, newValue) {
      state.cohortIndex = newValue.cohortIndex
      state.diseaseName = newValue.diseaseName
    }
  },
  getters: {
    hasData: state => Object.keys(state.all_diseases).length > 0
  },

  actions: {
    acceptCookies ({ commit }) {
      localStorage.setItem('cookieConsent', 'accepted')
      commit('ACCEPT_COOKIES')
    },

    async fetchAllDiseases ({ state, rootState }) {
      if (state.loading) {
        return
      }

      state.loading = true
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/cohort_names`)
      const finalIndex = []

      response.data.forEach(element => {
        finalIndex.push(element)
      })
      state.all_diseases = finalIndex
      state.loading = false
    }
  }
})

export default store
