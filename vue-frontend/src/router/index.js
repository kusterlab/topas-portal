import Vue from 'vue'
import Router from 'vue-router'
import LandingPage from '@/components/LandingPage.vue'

import AnalytesView from '@/views/AnalytesView.vue'
import AbundanceComponent from '@/components/AbundanceComponent.vue'
import AnnotationsComponent from '@/components/AnnotationsComponent.vue'

import ScoresView from '@/views/ScoresView.vue'
import TopasComponent from '@/components/TopasComponent.vue'
import KinaseComponent from '@/components/KinaseScoresComponent.vue'
import PproteinComponent from '@/components/ProteinScoresComponent.vue'
import EntityComponent from '@/components/EntityScoresComponent.vue'
import ZscoringComponent from '@/components/ZscoringComponent.vue'

import AnalyticsView from '@/views/AnalyticsView.vue'
import PCAComponent from '@/components/PCAComponent.vue'
import CorrelationComponent from '@/components/CorrelationComponent.vue'
import DifferentialComponent from '@/components/DifferentialComponent.vue'
import VennComponent from '@/components/VennComponent.vue'
import HeatmapComponent from '@/components/HeatmapComponent.vue'
import KinobeadsComponent from '@/components/DrugComponent.vue'
import PTMNavigatorComponent from '@/components/PTMNavigatorComponent.vue'

import PatientView from '@/views/PatientView.vue'
import PatientReportComponent from '@/components/PatientReportComponent.vue'
import CohortStatsComponent from '@/components/CohortStatsComponent.vue'

import SettingsView from '@/views/SettingsView.vue'
import AdminToolsComponent from '@/components/AdminToolsComponent.vue'

Vue.use(Router)

export default new Router({
  mode: 'hash',
  base: process.env.NODE_ENV === 'production'
    ? '/master_topas-portal/'
    : '/',
  routes: [
    { path: '/', component: LandingPage },
    {
      path: '/analytes',
      component: AnalytesView,
      redirect: '/abundance',
      children:
        [
          { path: '/abundance', component: AbundanceComponent },
          { path: '/annotations', component: AnnotationsComponent }
        ]
    },
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
      redirect: '/patient-report',
      children:
        [
          { path: '/patient-report', component: PatientReportComponent },
          { path: '/cohort-stats', component: CohortStatsComponent }
        ]
    },
    {
      path: '/settings',
      component: SettingsView,
      redirect: '/admin-tools',
      children:
        [
          { path: '/admin-tools', component: AdminToolsComponent }
        ]
    }
  ]
})
