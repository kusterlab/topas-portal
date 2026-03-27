from flask import Blueprint, jsonify, request
from topas_portal import settings, differential_expression as differential_test
from topas_portal.data_type import DataType
from routes import PtmNavigatorApiRoutes
from db import cohorts_db, mongodb
from repositories.pathway import PathwayRepository
from models.pathway import PathwayModel
import requests
import json



ptmnavigator_page = Blueprint(
    "ptmnavigator_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

pathway_repo = PathwayRepository(mongodb)

@ptmnavigator_page.route(PtmNavigatorApiRoutes.CANONICAL_PATHWAYS.path)
def get_canonical_pathways(
    taxcode: int
):
    search_query = request.args.get("protein_search")
    try:
        if search_query:
            response = requests.get(
                f"{settings.PRDB_HOST}/proteomicsdb/logic/pathwaycentric/getPathwaysByProteinSearchString.xsjs/", 
                params = { "taxcode": taxcode, "searchStrings": search_query } 
            )
        else:
            response = requests.get(f"{settings.PRDB_HOST}/proteomicsdb/logic/pathwaycentric/getAllPathways.xsjs/", params={"taxcode": taxcode})
        response.raise_for_status()

        return jsonify(response.json())
    except requests.exceptions.RequestException as e :
        return jsonify({"error": str(e)}), 500

@ptmnavigator_page.route(PtmNavigatorApiRoutes.PATHWAY_SKELETONS.path)
def get_pathway_skeletons(
    taxcode: int
):
    link = request.args["link"]
    try:
        response = requests.get(f"{settings.PRDB_HOST}/proteomicsdb/logic/pathwaycentric/pathway_skeletons/json/{taxcode}/{link}")
        response.raise_for_status()

        return jsonify(response.json())
    except requests.exceptions.RequestException as e :
        return jsonify({"error": str(e)}), 500

@ptmnavigator_page.route(PtmNavigatorApiRoutes.ENRICHMENTS.path)
def get_enrichments(cohort_index: str, grp_ind: str):
    method = request.args["method"]
    try:
        t_test_df = differential_test.get_data_for_t_test(
            cohorts_db,
            cohort_index,
            grp_ind,
            "index",
            DataType.FULL_PROTEOME,
            "p_values",
        )
        data_list = []

        for _, row in t_test_df.iterrows():
            genes = row["Gene Names"].split(";")
            for g in genes:
                data_list.append({
                    "id": g,
                    "Experiment01": row["expression1"]
                })
        form_data = {
            "organism": "hsa",
            "dataset_name": grp_ind,
            "data": json.dumps(data_list)
        }

        response = requests.post(f"{settings.ENRICHMENT_SERVER_HOST}/ssgsea/{method}", data=form_data)
        response.raise_for_status()

        return jsonify(response.json())
    except requests.exceptions.RequestException as e :
        return jsonify({"error": str(e)}), 500

@ptmnavigator_page.post(PtmNavigatorApiRoutes.CUSTOM_PATHWAYS)
def store_custom_pathway():
    request_body = request.get_json(force=True)
    id = request_body.get("id", None)
    name = request_body["name"]
    skeleton = request_body["skeleton"]

    try:
        existing = pathway_repo.get_by_id(id) if id is not None else None

        if existing:
            existing.skeleton = skeleton
            pathway_repo.update(existing)
            return jsonify({"id": id}), 200
        else:
            created_id = pathway_repo.create(PathwayModel.model_validate({
                "skeleton": skeleton,
                "name": name
            }))

            return jsonify({"id": created_id}), 201
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@ptmnavigator_page.get(PtmNavigatorApiRoutes.CUSTOM_PATHWAYS)
def get_custom_pathways():
    results = pathway_repo.get_all()
    return jsonify([r.model_dump() for r in results]), 200


