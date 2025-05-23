const state = {
  notifications: []
}

const mutations = {
  addNotification (state, notification) {
    state.notifications.push(notification)
    setTimeout(() => {
      state.notifications.shift()
    }, 10000)
  },
  clearNotifications (state) {
    state.notifications = []
  },
  dismissNotification (state, idx) {
    state.notifications.splice(idx, 1)
  }
}

const getters = {
  hasNotifications (state) {
    return state.notifications.length > 0
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  getters
}
