import axios from 'axios'
import { api } from '@/routes.ts'
import { DataType } from '@/constants'

const INTERNAL_HOST = process.env.VUE_APP_API_HOST

const ptmnApi = {
  getBackendName () {
    return 'Cohort'
  },

  async getOrganisms () {
    return [{ taxcode: 9606, name: 'Homo sapiens' }]
  },

  getDefaultSessionId () {
    return 'ABCDEF0123456789ABCDEF0123456789'
  },

  async refreshSessionId (uuid) {
    return 'ABCDEF0123456789ABCDEF0123456789'
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

  async getCustomPathwayList (_) {
    return (await axios.get(api.CUSTOM_PATHWAYS())).data.map(item => ({
      pathwayId: item.id,
      pathwayName: item.name,
      pathwayJSON: item.skeleton
    }))
  },

  async getPathwaySkeleton (taxcode, canonicalPathwayLink) {
    return (await axios.get(api.PATHWAY_SKELETONS({ taxcode, link: canonicalPathwayLink }))).data
  },

  async storeCustomPathway (skeleton, _, customPathwayName, currentlyEditedPathwayId) {
    return (await axios.post(
      api.CUSTOM_PATHWAYS(),
      {
        id: currentlyEditedPathwayId?._id,
        name: customPathwayName,
        skeleton: JSON.stringify(skeleton)
      }
    )).data.id
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
        tooltipHtml: 'Use the substrate phosphorylation scores from TOPAS backend.',
        stringColumns: ['Kinase'],
        sortColumn: 'Score',
        sortDesc: true,
        kaiDetails: {
          kinaseColname: 'Kinase',
          scoreColnamePrefix: 'Score',
          significanceColnamePrefix: 'adj p-val',
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
  const data = (await axios.get(api.PATIENT_REPORT_TABLE({ cohort_index: projectId, patient: datasetId, level: DataType.FULL_PROTEOME }))).data

  return data.map(el => ({
    geneNames: [el['Gene names'].split(';')].flat(),
    regulation: el['Z-score'] > 1.5
      ? 'up'
      : el['Z-score'] < -1.5
        ? 'down'
        : 'not',
    uniprotAccs: [],
    details: {
      'Experiment Name': datasetId,
      'Sample name': datasetId,
      'Z-score': el['Z-score'],
      'Fold change': el.FC,
      Intensity: el.Intensity,
      Rank: `${el.Rank} of ${el.Occurrence}`,
      'Identification metadata': el['Identification metadata']
    }
  }))
}

async function fetchAndFormatPtms (projectId, datasetId) {
  const data = (await axios.get(api.PATIENT_REPORT_TABLE({ cohort_index: projectId, patient: datasetId, level: DataType.PHOSPHO_PROTEOME }))).data

  return data.map(el => ({
    geneNames: [el['Gene names'].split(';')].flat(),
    regulation: el['Z-score'] > 1.5
      ? 'up'
      : el['Z-score'] < -1.5
        ? 'down'
        : 'not',
    uniprotAccs: [],
    details: {
      'Sample name': datasetId,
      'Modified sequence': el['Modified sequence'],
      'Site position': el['Site positions (MQ identified - PSP)'],
      'Upstream kinases (PSP)': el['Kinases (PSP)'],
      'Z-score': el['Z-score'],
      'Fold change': el.FC,
      Intensity: el.Intensity,
      Rank: `${el.Rank} of ${el.Occurrence}`,
      'Identification metadata': el['Identification metadata']
    }
  }))
}

async function fetchKinaseResults (projectId, datasetId) {
  const data = (await axios.get(api.PATIENT_REPORT_TABLE({ cohort_index: projectId, patient: datasetId, level: DataType.TOPAS_CK_SCORE }))).data
  return data.map(el => ({
    Kinase: el['Gene Names'],
    [`Score (${datasetId})`]: el['Z-score'],
    [`adj p-val (${datasetId})`]: el['Z-score']
  }))
}
