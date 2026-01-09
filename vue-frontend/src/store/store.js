import { createStore } from 'vuex'
import axios from 'axios'
import notifications from './notifications'

export default createStore({
  state: {
    all_cohorts: [],
    common_fields: [],
    loading: false,
    loading_common_fields: false,
    cohortIndex: -1,
    cohortName: '',
    // cookieAccepted: localStorage.getItem('cookieConsent') === 'accepted'   // for now we remove cookies consent, since no user personal data is saved as cookies; remove the bellow line and activate this line incase you need consent in front
    cookieAccepted: true // remove this line and activate the above line to activate consent for cookies
  },
  mutations: {
    ACCEPT_COOKIES(state) {
      state.cookieAccepted = true
    },
    setCohortIndex(state, newValue) {
      state.cohortIndex = newValue.cohortIndex
      state.cohortName = newValue.cohortName
    }
  },
  getters: {
    hasData: state => Object.keys(state.all_cohorts).length > 0
  },

  actions: {
    acceptCookies({ commit }) {
      localStorage.setItem('cookieConsent', 'accepted')
      commit('ACCEPT_COOKIES')
    },

    async fetchAllCohorts({ state }) {
      if (state.loading) {
        return
      }

      state.loading = true
      const response = await axios.get(`${import.meta.env.VITE_API_HOST}/cohort_names`)
      const finalIndex = []

      response.data.forEach(element => {
        finalIndex.push(element)
      })
      state.all_cohorts = finalIndex
      state.loading = false
    },
    async fetchCommonFields({ state }) {
      if (state.loading_common_fields) {
        return
      }

      state.loading_common_fields = true
      const response = await axios.get(`${import.meta.env.VITE_API_HOST}/colnames`)
      const finalIndex = []
      response.data.forEach(element => {
        if (element.visible === 'false') {
          element.visible = false
        }
        finalIndex.push(element)
      })
      state.common_fields = finalIndex
      state.loading_common_fields = false
    }
  },
  modules: {
    notifications
  }
})
