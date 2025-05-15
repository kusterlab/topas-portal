import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'
import notifications from './notifications'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    all_cohorts: [],
    loading: false,
    cohortIndex: -1,
    cohortName: '',
    // cookieAccepted: localStorage.getItem('cookieConsent') === 'accepted'   // for now we remove cookies consent, since no user personal data is saved as cookies; remove the bellow line and activate this line incase you need consent in front
    cookieAccepted: true // remove this line and activate the above line to activate consent for cookies
  },
  mutations: {
    ACCEPT_COOKIES (state) {
      state.cookieAccepted = true
    },
    setCohortIndex (state, newValue) {
      state.cohortIndex = newValue.cohortIndex
      state.cohortName = newValue.cohortName
    }
  },
  getters: {
    hasData: state => Object.keys(state.all_cohorts).length > 0
  },

  actions: {
    acceptCookies ({ commit }) {
      localStorage.setItem('cookieConsent', 'accepted')
      commit('ACCEPT_COOKIES')
    },

    async fetchAllCohorts ({ state, rootState }) {
      if (state.loading) {
        return
      }

      state.loading = true
      const response = await axios.get(`${process.env.VUE_APP_API_HOST}/cohort_names`)
      const finalIndex = []

      response.data.forEach(element => {
        finalIndex.push(element)
      })
      state.all_cohorts = finalIndex
      state.loading = false
    }
  },
  modules: {
    notifications
  }

})

export default store
