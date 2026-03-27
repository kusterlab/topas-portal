// this is an automatically generated file that mirrors the enums in flask-backend/topas_portal/constants.py

export const DataType = Object.freeze({
  FULL_PROTEOME: 'protein',
  FULL_PROTEOME_ANNOTATED: 'protein_annotated',
  FULL_PROTEOME_NUM_PEPTIDES: 'num_peptides',
  PHOSPHO_PROTEOME: 'psite',
  FP_PP: 'FP_PP',
  PHOSPHO_PROTEOME_ANNOTATED: 'psite_annotated',
  PHOSPHO_SCORE: 'phospho_score',
  PHOSPHO_SCORE_PSITE: 'phospho_psite',
  KINASE_SCORE: 'kinase',
  KINASE_SUBSTRATE: 'kinase_substrate',
  TOPAS_KINASE_SCORE: 'topas_kinase',
  TOPAS_KINASE_SUBSTRATE: 'topas_kinase_substrate',
  TOPAS_PHOSPHO_SCORE: 'topas_phospho',
  TOPAS_PHOSPHO_SCORE_PSITE: 'topas_phospho_psite',
  TOPAS_PROTEIN: 'topas_expression',
  TOPAS_RTK_SCORE: 'topas_rtk',
  TOPAS_CK_SCORE: 'topas_ck',
  TOPAS_SUBSCORE: 'topas_subscore',
  BIOMARKER: 'biomarker',
  REPORT_SUMMARY: 'report_summary',
  PATIENT_METADATA: 'patients_df',
  SAMPLE_ANNOTATION: 'sample_annotation_df',
  SEARCH_QC: 'search_qc',
  TRANSCRIPTOMICS: 'fpkm',
  GENOMICS: 'genomics'
})


export const ColumnNames = Object.freeze({
  SAMPLE_NAME: 'Sample name',
  GENE_NAME: 'Gene names'
})


export const ImputationMode = Object.freeze({
  NO_IMPUTE: 'noimpute',
  IMPUTE: 'impute'
})

export const IncludeRef = Object.freeze({
  INCLUDE_REF: 'include_ref',
  EXCLUDE_REF: 'exclude_ref',
  ONLY_REF: 'only_ref'
})

export const IntensityUnit = Object.freeze({
  INTENSITY: 'intensity',
  Z_SCORE: 'z_scored',
  FOLD_CHANGE: 'fc',
  RANK: 'rank',
  BATCH_RANK: 'batchrank',
  SCORE: 'score',
  IDENTIFICATION_METADATA: 'identification_metadata'
})

