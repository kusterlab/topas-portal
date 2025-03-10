import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    all_diseases: [],
    loading: false,
    cookieAccepted: localStorage.getItem('cookieConsent') === 'accepted'
  },
  mutations: {
    ACCEPT_COOKIES (state) {
      state.cookieAccepted = true
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
