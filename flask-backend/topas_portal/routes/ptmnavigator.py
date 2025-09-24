from .base import ApiBase

class PtmNavigatorApiRoutes(ApiBase):
    CANONICAL_PATHWAYS = "/canonical_pathways/<string:taxcode>?protein_search=<protein_search>"
    PATHWAY_SKELETONS = "/pathway_skeletons/<string:taxcode>?link=<link>"
    ENRICHMENTS = "/cohorts/<int:cohort_index>/enrichments/<string:grp_ind>?method=<method>"
    
