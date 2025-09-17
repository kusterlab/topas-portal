import axios from 'axios'

const INTERNAL_HOST = process.env.VUE_APP_API_HOST

const api = {
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
    return {}
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
    return (await axios.get(`${INTERNAL_HOST}/canonical_pathways/${taxcode}`)).data
  },

  async getCustomPathwayList (uuid) {
    return []
  },

  async getPathwaySkeleton (taxcode, canonicalPathwayLink) {
    return (await axios.get(
      `${INTERNAL_HOST}/pathway_skeletons/${taxcode}`,
      {
        params: {
          link: canonicalPathwayLink
        }
      })
    ).data
  },

  async storeCustomPathway (skeleton, uuid, customPathwayName, currentlyEditedPathwayId) {
    return {}
  },

  async getFilteredPathwayIds (searchStrings, taxcode) {
    return (await axios.get(
      `${INTERNAL_HOST}/canonical_pathways/${taxcode}`,
      {
        params: {
          protein_search: searchStrings
        }
      }
    )).data
  },

  async getEnrichmentTypes () {
    return [
      {
        name: 'Motif Enrichment',
        short: 'motif',
        enrichmentTypeId: 1,
        applicableOmics: ['Phosphorylation'],
        enrichmentClass: 'KinaseActivity'
      },
      {
        name: 'GCR-PEA',
        short: 'gcr',
        enrichmentTypeId: 2,
        applicableOmics: ['Phosphorylation', 'Protein', 'Other'],
        enrichmentClass: 'Pathway'
      }
    ]
  },

  async loadUserEnrichmentResults (sessionId, userDatasetIds, enrichmentTypeId) {
    return []
  },

  async loadInternalDatabaseEnrichmentResults (datasetId) {
    const gcrResults = (await axios.get(`${INTERNAL_HOST}/0/enrichments/${datasetId}`,
      {
        params: {
          method: 'gcr'
        }
      }
    )).data
    const kinaseResults = await fetchKinaseResults(0, datasetId)
    return {
      [datasetId]: [
        {
          enrichmentType: 'Motif Enrichment',
          enrichmentJSON: JSON.stringify(kinaseResults)
        },
        {
          enrichmentType: 'GCR-PEA',
          enrichmentJSON: JSON.stringify(gcrResults)
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

export default api

/*
* Helper functions that are not exported
* */

async function fetchAndFormatProteins (projectId, datasetId) {
  const data = (await axios.get(`${INTERNAL_HOST}/differential/${projectId}/protein/${datasetId}/index/p_values`)).data

  return data.map(el => ({
    geneNames: [el['Gene Names']],
    regulation: el.up_down,
    uniprotAccs: [],
    details: {
      'Experiment Name': datasetId,
      'Experiment ID': datasetId,
      'Fold Change': el.expression1,
      '-log(p-value)': el.expression2
    }
  }))
}

async function fetchAndFormatPtms (projectId, patientId) {
  const data = (await axios.get(`${INTERNAL_HOST}/differential/${projectId}/psite/${patientId}/index/p_values`)).data

  return data.map(el => ({
    geneNames: [el.Genes.split(';')].flat(),
    regulation: el.up_down,
    uniprotAccs: [],
    details: {
      'Experiment Name': patientId,
      'Experiment ID': patientId,
      'Fold Change': el.expression1,
      '-log(p-value)': el.expression2
    }
  }))
}

async function fetchKinaseResults (projectId, datasetId) {
  const kinaseActivities = (await axios.get(`${INTERNAL_HOST}/differential/${projectId}/kinase/${datasetId}/index/p_values`)).data
  return kinaseActivities.map(el => ({
    Kinase: el['Gene Names'],
    'Log2 Enrichment': el.expression1,
    '-Log10 p_value adjusted': el.expression2
  }))
}
