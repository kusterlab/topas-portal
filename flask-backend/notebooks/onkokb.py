import pickle
import pandas as  pd
from pathlib import Path
import re


def load_genomics_table(genomics_path="/media/kusterlab/internal_projects/active/TOPAS/WP31/genomics/genomics_df2portal.csv") -> pd.DataFrame:
    genomics_df = pd.read_csv(Path(genomics_path))
    genomics_df = genomics_df.loc[:, ~genomics_df.columns.str.contains("^Unnamed")]
    return genomics_df
# Open the pickle file in read-binary mode

def load_onkoKB_data(onkoKB_path:str='/media/kusterlab/internal_projects/active/TOPAS/WP31/genomics/onkoKB_library_210825.csv') -> dict:
    df = pd.read_csv(onkoKB_path)
    return df[['gene_pair','annotation']].set_index('gene_pair').to_dict()['annotation']
    


def split_fusion(x):
    if str(x).__contains__(','): 
        x0 = x.split('|')[0]
        x1 = x.split('|')[1].split(',')[0]
        x2 = x.split('|')[1].split(',')[1]
        return [f'{x0}|{x1}',f'{x0}|{x2}']
    else:
        return [x]
    
    
def get_all_fusions_per_NGS(x,fusion_dic,pattern_alteration = r'[A-Z1-9]+\|[A-Z1-9,]+'):
    try:
        all_alteration = x.split('_fusion:')[-1]     
        all_matches = re.finditer(pattern_alteration,all_alteration)
        all_possibilities = [split_fusion(match.group()) for match in all_matches]
        return (';').join([fusion_dic.get(x,x) for x in list(set(sum(all_possibilities,start=[])))])
    except:
        return ''


def get_all_cnvs_per_NGS(x,gene_name,cnv_dic,pattern_alteration = r'AMP|DEL|GAIN|LOSS'):
    onkokb_definitions = {'AMP':'AMPLIFICATION','DEL':'DELETION'}
    try:
        all_alteration = x.split('_snv:')[0]
        all_matches = re.finditer(pattern_alteration,all_alteration)
        all_possibilities = [[match.group()] for match in all_matches]
        res = [f'{gene_name}_{onkokb_definitions.get(x,x)}' for x in list(set(sum(all_possibilities,start=[])))]
        return (';').join([cnv_dic.get(x,x) for x in list(set(res))])
    except:
        return ''
    



def get_all_snv_per_NGS(X,protein_name,snv_dic,pattern_alteration = r'p.[A-Z][0-9]+[A-Z]'):
    """
    This function is the wrapper around the function for extracting the SNVs
    :X: should be like cnv:CNN_snv:C_T_exonic_20_P266S_fusion:n.d        if it is multi they shold be seprated by ;
    """
    try:


        all_alteration = X.split('snv:')[-1].split('fusion:')[0]
        all_matches = re.finditer(pattern_alteration,all_alteration)
        all_possibilities = [match.group() for match in all_matches]

        if len(all_possibilities) > 0:
            res = [f'{protein_name}_{x}' for x in all_possibilities]
            return (';').join([snv_dic.get(x,x) for x in list(set(res))])
        else:
            return ''
    except:
        return ''




    
def add_onkokb_annotation(df,genomics_df,gene_name, fusion_dic,column_name='fusion_onkoKB'):
    try:
        
        sub_df = genomics_df[['Sample name',gene_name]]
        
        if column_name == 'fusion_onkoKB':
            function_to_get = get_all_fusions_per_NGS
            sub_df[column_name] = sub_df[gene_name].apply(lambda x:function_to_get(x,fusion_dic))
            
        if column_name == 'cnv_onkoKB':
            function_to_get = get_all_cnvs_per_NGS
            sub_df[column_name] = sub_df[gene_name].apply(lambda x:function_to_get(x,gene_name,fusion_dic))
            
            
        if column_name == 'snv_onkoKB':
            function_to_get = get_all_snv_per_NGS
            sub_df[column_name] = sub_df[gene_name].apply(lambda x:function_to_get(x,gene_name,fusion_dic))
            
            
            
        return df.merge(sub_df[['Sample name',column_name]],on='Sample name',how='left')
    except:
        return df
    
genomics_df = load_genomics_table()
onkoKB2portal = load_onkoKB_data()
test = genomics_df[['Sample name','EGFR']]
test = add_onkokb_annotation(test,genomics_df,'EGFR',onkoKB2portal,column_name='fusion_onkoKB')
test = add_onkokb_annotation(test,genomics_df,'EGFR',onkoKB2portal,column_name='cnv_onkoKB')
test = add_onkokb_annotation(test,genomics_df,'EGFR',onkoKB2portal,column_name='snv_onkoKB')
test[test['fusion_onkoKB'] != '']