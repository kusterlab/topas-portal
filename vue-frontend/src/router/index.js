import Vue from 'vue'
import Router from 'vue-router'
import LandingPage from '@/components/LandingPage.vue'
import AbundanceComponent from '@/components/AbundanceComponent.vue'

import PatientComponent from '@/components/PatientComponent.vue'
import AdminToolsComponent from '@/components/AdminToolsComponent.vue'

import ScoresView from '@/views/ScoresView.vue'
import TopasComponent from '@/components/TopasComponent.vue'
import KinaseComponent from '@/components/KinaseComponent.vue'
import PproteinComponent from '@/components/ProteinScores.vue'
import EntityComponent from '@/components/entitymodelComponent.vue'
import ZscoringComponent from '@/components/ZscoringComponent.vue'

import AnalyticsComponent from '@/views/AnalyticsView.vue'
import PCAComponent from '@/components/QCComponent.vue'
import CorrelationComponent from '@/components/CorrelationComponent.vue'
import DifferentialComponent from '@/components/DifferentialComponent.vue'
import VennComponent from '@/components/VennComponent.vue'
import HeatmapComponent from '@/components/HeatmapComponent.vue'
import KinobeadsComponent from '@/components/DrugComponent.vue'
import PTMNavigatorComponent from '@/components/PTMNavigatorComponent.vue'

Vue.use(Router)

export default new Router({
  mode: 'hash',
  base: process.env.NODE_ENV === 'production'
    ? '/master_topas-portal/'
    : '/',
  routes: [
    { path: '/', component: LandingPage },
    { path: '/abundance', component: AbundanceComponent },
    {
      path: '/scores',
      component: ScoresView,
      children:
        [
          { path: '/topasscores', component: TopasComponent },
          { path: '/kinasescores', component: KinaseComponent },
          { path: '/proteinscores', component: PproteinComponent },
          { path: '/entityscores', component: EntityComponent },
          { path: '/zscores', component: ZscoringComponent }
        ]
    },
    {
      path: '/analytics',
      component: AnalyticsComponent,
      redirect: '/correlation',
      children:
        [
          { path: '/correlation', name: 'correlation', component: CorrelationComponent },
          { path: '/pca', name: 'pca', component: PCAComponent },
          { path: '/differential', name: 'differential', component: DifferentialComponent },
          { path: '/heatmap', name: 'heatmap', component: HeatmapComponent },
          { path: '/venn', name: 'venn', component: VennComponent },
          { path: '/kinobeads', name: 'kinobeads', component: KinobeadsComponent },
          { path: '/ptmnavigator', name: 'ptmnavigator', component: PTMNavigatorComponent }
        ]
    },
    { path: '/patient', component: PatientComponent },
    { path: '/admin-tools', component: AdminToolsComponent }
  ]
})
