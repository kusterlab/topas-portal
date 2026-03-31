import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
  },
  defaults: {
    global: {
      density: 'comfortable',
      hideDetails: true
    },
    VCard: {
      density: 'default'
    },
    VCardTitle: {
      density: 'default'
    },
    VCardText: {
      density: 'default'
    },
    VSelect: {
      variant: 'outlined'
    },
    VAutocomplete: {
      variant: 'outlined'
    },
    VTextField: {
      variant: 'outlined'
    },
    VBtnToggle: {
      density: 'compact',
      variant: 'outlined',
      divided: true
    },
    VBtn: {
      density: 'default'
    },
    VCheckbox: {
      color: 'primary'
    },
    VSwitch: {
      color: 'primary'
    }
  }
})
