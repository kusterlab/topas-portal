// this mirrors the DataType Enum in flask-backend/bin/utils.py

export const DataType = Object.freeze({
  FULL_PROTEOME: 'protein',
  FULL_PROTEOME_ANNOTATED: 'protein_annotated',
  PHOSPHO_PROTEOME: 'psite',
  PHOSPHO_PROTEOME_ANNOTATED: 'psite_annotated',
  PHOSPHO_SCORE: 'phospho_score',
  PHOSPHO_SCORE_PSITE: 'phospho_psite',
  KINASE_SCORE: 'kinase',
  KINASE_SUBSTRATE: 'kinase_substrate',
  TOPAS_KINASE_SCORE: 'topas_kinase',
  TOPAS_KINASE_SUBSTRATE: 'topas_kinase_substrate',
  TOPAS_IMPORTANT_PHOSPHO: 'important_phosphorylation',
  TOPAS_PHOSPHO_SCORE: 'topas_phospho',
  TOPAS_PHOSPHO_SCORE_PSITE: 'topas_phospho_psite',
  TOPAS_PROTEIN: 'topas_expression',
  TOPAS_SCORE: 'topas',
  TOPAS_SCORE_RTK: 'topas_rtk',
  TRANSCRIPTOMICS: 'fpkm',
  TOPAS_SUBSCORE: 'topas_subscore',
  BIOMARKER: 'biomarker',
  FP_PP: 'FP_PP'
})
