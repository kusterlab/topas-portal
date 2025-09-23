import axios from 'axios'
import { api } from '@/routes.ts'
import { DataType } from '@/constants'

const INTERNAL_HOST = process.env.VUE_APP_API_HOST

const ptmnApi = {
  getBackendName () {
    return 'Internal'
  },

  async getOrganisms () {
    return [{ taxcode: 9606, name: 'Homo sapiens' }]
  },

  getDefaultSessionId () {
    return 'TOPASXPLATFORMXXTOPASXPLATFORMXX'
  },

  async refreshSessionId (uuid) {
    return 'TOPASXPLATFORMXXTOPASXPLATFORMXX'
  },

  async getUserDatasetList (sessionId) {
    return []
  },

  async loadUserDatasets (sessionId, userDatasets) {
    return {
      ptmInputList: [],
      proteinInputList: []
    }
  },

  async getInternalProjects () {
    const names = (await axios
      .get(`${INTERNAL_HOST}/cohort_names`)
    ).data.map((el, i) => ({ projectId: i, projectName: el }))

    return names
  },

  async getInternalDatasetsForProject (projectId) {
    return (await axios
      .get(`${INTERNAL_HOST}/${projectId}/patients`)
    ).data.map((el) => ({ datasetId: el['Sample name'], datasetName: el['Sample name'], datasetType: 'FoldChange', taxcode: 9606, omics: 'Phosphorylation', projectId }))
  },

  async loadInternalDatasets (selectedDatasets) {
    const patientIds = selectedDatasets.map(el => el.datasetName)
    const projectId = selectedDatasets[0].projectId
    const [proteinInputList, ptmInputList] = await Promise.all([
      Promise.all(patientIds.map(id => fetchAndFormatProteins(projectId, id))).then(res => res.flat()),
      Promise.all(patientIds.map(id => fetchAndFormatPtms(projectId, id))).then(res => res.flat())
    ])
    return {
      ptmInputList,
      proteinInputList
    }
  },

  async getCanonicalPathwayList (taxcode) {
    return (await axios.get(api.CANONICAL_PATHWAYS({ taxcode, protein_search: '' }))).data
  },

  async getCustomPathwayList (uuid) {
    return []
  },

  async getPathwaySkeleton (taxcode, canonicalPathwayLink) {
    return (await axios.get(api.PATHWAY_SKELETONS({ taxcode, link: canonicalPathwayLink }))).data
  },

  async storeCustomPathway (skeleton, uuid, customPathwayName, currentlyEditedPathwayId) {
    return {}
  },

  async getFilteredPathwayIds (searchStrings, taxcode) {
    return (await axios.get(api.CANONICAL_PATHWAYS({ taxcode, protein_search: searchStrings }))).data
  },

  async getEnrichmentTypes () {
    return [
      {
        name: 'TOPAS',
        short: 'topas',
        enrichmentTypeId: 1,
        applicableOmics: ['Phosphorylation'],
        enrichmentClass: 'KinaseActivity',
        tooltipHtml: 'It uses the substrate phosphorylation scores from TOPAS backend.',
        stringColumns: ['Kinase'],
        sortColumn: '-log10 transformed p-value',
        sortDesc: true,
        kaiDetails: {
          kinaseColname: 'Kinase',
          scoreColnamePrefix: 'Mean difference',
          significanceColnamePrefix: '-log10 transformed p-value',
          higherScoreIsStrongerEnrichment: true,
          hasDirection: true,
          directionFromSignificance: false,
          isAlreadyLogTransformed: true
        }
      }
    ]
  },

  async loadUserEnrichmentResults (sessionId, userDatasetIds, enrichmentTypeId) {
    return []
  },

  async loadInternalDatabaseEnrichmentResults (projectId, datasetId) {
    const kinaseResults = await fetchKinaseResults(projectId, datasetId)
    return {
      [datasetId]: [
        {
          enrichmentType: 'TOPAS',
          enrichmentJSON: JSON.stringify(kinaseResults)
        }
      ]
    }
  },

  async loadCurveData (curveIds, isUserDataMode) {
    return []
  },

  getCustomDataUploadComponent () {
    return 'analyticsCustomDataUpload'
  }
}

export default ptmnApi

/*
* Helper functions that are not exported
* */

async function fetchAndFormatProteins (projectId, datasetId) {
  const data = (await axios.get(api.DIFFERENTIAL({ cohort_index: projectId, level: DataType.FULL_PROTEOME, grp1_ind: datasetId, grp2_ind: 'index', y_axis_type: 'p_values' }))).data

  return data.map(el => ({
    geneNames: [el['Gene Names']],
    regulation: el.up_down,
    uniprotAccs: [],
    details: {
      'Experiment Name': datasetId,
      'Experiment ID': datasetId,
      'Mean difference': el.expression1,
      '-log10 transformed p-value': el.expression2
    }
  }))
}

async function fetchAndFormatPtms (projectId, datasetId) {
  const data = (await axios.get(api.DIFFERENTIAL({ cohort_index: projectId, level: DataType.PHOSPHO_PROTEOME, grp1_ind: datasetId, grp2_ind: 'index', y_axis_type: 'p_values' }))).data

  return data.map(el => ({
    geneNames: [el.Genes.split(';')].flat(),
    regulation: el.up_down,
    uniprotAccs: [],
    details: {
      'Experiment Name': datasetId,
      'Experiment ID': datasetId,
      'Mean difference': el.expression1,
      '-log10 transformed p-value': el.expression2
    }
  }))
}

async function fetchKinaseResults (projectId, datasetId) {
  const data = (await axios.get(api.DIFFERENTIAL({ cohort_index: projectId, level: DataType.KINASE_SCORE, grp1_ind: datasetId, grp2_ind: 'index', y_axis_type: 'p_values' }))).data
  return data.map(el => ({
    Kinase: el['Gene Names'],
    'Mean difference': el.expression1,
    '-log10 transformed p-value': el.expression2
  }))
}
