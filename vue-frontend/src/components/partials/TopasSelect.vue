<template>
  <div>
    <v-autocomplete
      v-model="selectedTopasIds"
      label="Select kinase"
      class="topas mt-1"
      prepend-icon="mdi-filter"
      auto-select-first
      :items="allTopasIds"
      :multiple="multiple"
      :clearable="multiple"
      :chips="multiple"
      :closable-chips="multiple"
      @update:model-value="updateSelectedTopasIds"
    >
      <template v-if="multiple" #prepend-item>
        <v-list-item v-show="multiple" ripple>
          <v-list-item-action>
            <v-checkbox v-model="allSelected" hide-details @update:model-value="selectAll" />
          </v-list-item-action>
          <v-list-item-title>Select All</v-list-item-title>
        </v-list-item>
        <v-divider v-show="multiple" />
      </template>
    </v-autocomplete>
  </div>
</template>

<script>
  import axios from 'axios'
  import { mapMutations } from 'vuex'
  import { api } from '@/routes.ts'

  export default {
    name: 'TopasSelect',
    props: {
      cohortIndex: {
        type: Number,
        default: -1
      },
      multiple: {
        type: Boolean,
        default: false
      }
    },
    data: () => ({
      selectedTopasIds: [],
      allTopasIds: [],
      dataSource: 'z_score'
    }),
    computed: {
      allSelected: function () {
        return this.selectedTopasIds && this.allTopasIds.length === this.selectedTopasIds.length
      }
    },
    watch: {
      cohortIndex: function () {
        this.topasComboupdater()
      },
      dataSource: function () {
        this.updateSelectedTopasIds()
      }
    },
    mounted() {
      this.topasComboupdater()
    },
    methods: {
      ...mapMutations({
        addNotification: 'notifications/addNotification'
      }),
      async topasComboupdater() {
        // retrieving different topas types RTK or main from the backend
        if (this.cohortIndex < 0) return

        const allTopasIds = []
        try {
          const response = await axios.get(api.TOPAS_IDS({ cohort_index: this.cohortIndex }))

          response.data.forEach(element => {
            if (element.ids !== 'num_identified' && element.ids !== 'num_annotated') {
              allTopasIds.push(element.ids)
            }
          })
        } catch (error) {
          this.addNotification({
            color: 'error',
            message: `An error occurred while processing response data: ${error}`
          })
        }

        this.allTopasIds = allTopasIds
      },
      updateSelectedTopasIds() {
        if (!this.selectedTopasIds || this.selectedTopasIds.length === 0) return
        this.$emit('select-topas', {
          dataSource: this.dataSource,
          identifier: this.selectedTopasIds
        })
      },
      selectAll() {
        if (this.allSelected) {
          this.selectedTopasIds = []
        } else {
          this.selectedTopasIds = this.allTopasIds
        }
        this.updateSelectedTopasIds()
      }
    }
  }
</script>
