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
  TUPAC_KINASE_SCORE: 'tupac_kinase',
  TUPAC_KINASE_SUBSTRATE: 'tupac_kinase_substrate',
  TUPAC_IMPORTANT_PHOSPHO: 'important_phosphorylation',
  TUPAC_PHOSPHO_SCORE: 'tupac_phospho',
  TUPAC_PHOSPHO_SCORE_PSITE: 'tupac_phospho_psite',
  TUPAC_PROTEIN: 'tupac_expression',
  TUPAC_SCORE: 'tupac',
  TUPAC_SCORE_RTK: 'tupac_rtk',
  TRANSCRIPTOMICS: 'fpkm',
  TUPAC_SUBSCORE: 'tupac_subscore',
  BIOMARKER: 'biomarker',
  FP_PP: 'FP_PP',
  CUSTOM: 'custom'
})
