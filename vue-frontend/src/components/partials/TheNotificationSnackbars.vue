<template>
  <v-snackbar
    location="top right"
    :model-value="hasNotifications"
    color="transparent"
    class="elevation-0 notification-container"
    timeout="-1"
  >
    <v-snackbar
      v-for="(n, i) in notifications"
      :key="i"
      :timeout="n.timeout || -1"
      :color="n.color || 'info'"
      :model-value="true"
      location="right"
      class="notification-item"
      :style="{ 'padding-bottom': 0, 'padding-top': 0 }"
      @update:model-value="dismissNotification(i)"
    >
      {{ n.message }}
      <template #action>
        <v-btn variant="text" class="mt-3" @click="dismissNotification(i)">
          <v-icon start> mdi-close </v-icon>
          Dismiss
        </v-btn>
      </template>
    </v-snackbar>
  </v-snackbar>
</template>

<script>
  import { mapState, mapMutations, mapGetters } from 'vuex'

  export default {
    computed: {
      ...mapState({
        /** @returns {any[]} */
        notifications: state => state.notifications.notifications
      }),
      ...mapGetters({
        hasNotifications: 'notifications/hasNotifications'
      })
    },
    methods: {
      ...mapMutations({
        dismissNotification: 'notifications/dismissNotification'
      })
    }
  }
</script>

<style lang="scss">
  .notification-container {
    & > .v-snack__wrapper > .v-snack__content {
      padding: 0;
    }

    .notification-item:not(.v-snack--absolute) {
      position: initial;
      height: auto;
    }
  }
</style>
