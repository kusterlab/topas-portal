from topas_portal.digest import make_protein2peptide_dataframe


def load_in_silico_digestion(fasta_file):
    return make_protein2peptide_dataframe(fasta_file)
