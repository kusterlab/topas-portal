import Vue from 'vue'
import Router from 'vue-router'
import OverviewComponent from '@/components/LandingPage.vue'
import GeneExpression from '@/components/GeneExpressionComponent.vue'
import AnalyticsComponent from '@/components/AnalyticsComponent.vue'
import PatientComponent from '@/components/PatientComponent.vue'
import OtherComponent from '@/components/OthertoolsComponent.vue'
import KinaseComponent from '@/components/KinaseComponent.vue'
import PproteinComponent from '@/components/ProteinScores.vue'
import TopasComponent from '@/components/BasketComponent.vue'
import EntityComponent from '@/components/entitymodelComponent.vue'
import ZscoringComponent from '@/components/ZscoringComponent.vue'

Vue.use(Router)

export default new Router({
  mode: 'hash',
  base: process.env.NODE_ENV === 'production'
    ? '/master_mtb_portal/'
    : '/',
  routes: [
    { path: '/', component: OverviewComponent },
    { path: '/expression', component: GeneExpression },
    { path: '/topasscores', component: TopasComponent },
    { path: '/analytics', component: AnalyticsComponent },
    { path: '/patient', component: PatientComponent },
    { path: '/other-tools', component: OtherComponent },
    { path: '/kinasescores', component: KinaseComponent },
    { path: '/proteinscores', component: PproteinComponent },
    { path: '/entityscores', component: EntityComponent },
    { path: '/zscores', component: ZscoringComponent }
  ]
})
