MTB_PORTAL_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
include $(MTB_PORTAL_DIR)MakefileShared

dependencies:
	git config --global credential.helper cache

jump: 
	$(DOCKER_CMD) \
		$(IMAGE) bash

# --no-cache
build: dependencies
	docker build -f Dockerfile -t $(IMAGE) . || (exit 1)

run:
	docker run -v /media:/media -p 3834:3834 $(IMAGE)

flask:
	cd flask-backend && poetry run python3 app.py

test_flask:
	cd flask-backend && poetry run python3 app.py test

export_flask_routes:
	cd flask-backend && poetry run python3 routes.py

serve: export_flask_routes
	cd vue-frontend && npm install && npm run serve

lint:
	cd vue-frontend && npx eslint "./**" --fix --ignore-pattern Dockerfile

unittest:
	python3 -m  pytest

all:
	sh dockerize-dev-backend.sh && sh dockerize-dev-frontend.sh

db:
	sh dockerize-dev-backend.sh

frontend:
	sh dockerize-dev-frontend.sh

database_import: zscores_FP_to_db zscores_PP_to_db intensity_FP_to_db intensity_PP_to_db protein_seq_to_db meta_data_to_db sample_annotation_to_db expression_meta_to_db topas_scores_to_db phospho_scores_to_db

zscores_FP_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py  FP_z  all_cohorts

zscores_PP_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py  PP_z  all_cohorts

intensity_FP_to_db:
	sudo docker exec -it $(CONTAINER_ID) python ./importer.py  FP_i  all_cohorts

intensity_PP_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py  PP_i  all_cohorts

protein_seq_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py  protein_to_seq  all_cohorts

meta_data_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py  patient_meta_data  all_cohorts

sample_annotation_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py  sample_annotation_data  all_cohorts

expression_meta_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py  expression_meta_data  all_cohorts

topas_scores_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py topas_scores all_cohorts

phospho_scores_to_db:
	sudo docker exec -it $(CONTAINER_ID) python  ./importer.py phospho_scores all_cohorts

gotobackend:
	sudo docker exec -it $(CONTAINER_ID) /bin/bash 

backup:
	sudo docker exec -t $(POSTGRES_ID) pg_dumpall -c -U topas > dump.sql 

restore:
	cat dump.sql | sudo docker exec -i $(POSTGRES_ID) psql -d  cohort_db -U topas

gotosql:
	psql "sslmode=disable dbname=cohort_db user=topas password=topaswp3 hostaddr=localhost port=5432" 

create_docker_networks:
	(docker network create INTERNAL && docker network create EXTERNAL) || true