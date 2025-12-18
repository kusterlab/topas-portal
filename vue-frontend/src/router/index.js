import Vue from 'vue'
import Router from 'vue-router'
import LandingPage from '@/components/LandingPage.vue'
import AbundanceComponent from '@/components/AbundanceComponent.vue'

import AdminToolsComponent from '@/components/AdminToolsComponent.vue'

import ScoresView from '@/views/ScoresView.vue'
import TopasComponent from '@/components/TopasComponent.vue'
import KinaseComponent from '@/components/KinaseComponent.vue'
import PproteinComponent from '@/components/ProteinScores.vue'
import EntityComponent from '@/components/entitymodelComponent.vue'
import ZscoringComponent from '@/components/ZscoringComponent.vue'

import AnalyticsView from '@/views/AnalyticsView.vue'
import PCAComponent from '@/components/QCComponent.vue'
import CorrelationComponent from '@/components/CorrelationComponent.vue'
import DifferentialComponent from '@/components/DifferentialComponent.vue'
import VennComponent from '@/components/VennComponent.vue'
import HeatmapComponent from '@/components/HeatmapComponent.vue'
import KinobeadsComponent from '@/components/DrugComponent.vue'
import PTMNavigatorComponent from '@/components/PTMNavigatorComponent.vue'

import PatientView from '@/views/PatientView.vue'
import PatientReportComponent from '@/components/PatientReportComponent.vue'
import OverviewComponent from '@/components/OverviewComponent.vue'

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
      component: AnalyticsView,
      redirect: '/correlation',
      children:
        [
          { path: '/correlation', component: CorrelationComponent },
          { path: '/pca', component: PCAComponent },
          { path: '/differential', component: DifferentialComponent },
          { path: '/heatmap', component: HeatmapComponent },
          { path: '/venn', component: VennComponent },
          { path: '/kinobeads', component: KinobeadsComponent },
          { path: '/ptmnavigator', component: PTMNavigatorComponent }
        ]
    },
    {
      path: '/patient',
      component: PatientView,
      redirect: '/patient_report',
      children:
        [
          { path: '/patient_report', component: PatientReportComponent },
          { path: '/cohort_stats', component: OverviewComponent }
        ]
    },
    { path: '/admin-tools', component: AdminToolsComponent }
  ]
})
