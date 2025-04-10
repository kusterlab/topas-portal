#!/bin/bash
# USAGE: update_cohort_to_db <cohort_name>
# example: update_cohort_to_db PAN_CANCER

CONTAINER_ID=`sudo docker container ls --all --quiet --filter "name=mtb_portal_mtb_portal_flask_backend_1"`
sudo docker exec -it $CONTAINER_ID python  ./importer.py  FP_z  $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  PP_z  $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  FP_i  $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  PP_i  $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  protein_to_seq  $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  patient_meta_data  $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  sample_annotation_data $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  expression_meta_data  $1
sudo docker exec -it $CONTAINER_ID python  ./importer.py  topas_scores $1
