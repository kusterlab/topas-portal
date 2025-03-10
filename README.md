# MTB Portal
TOPAS portal is to explore proteome and phospho-proteome profiles of patients processed with our clinical-proteomics piepline from LC/MS data. In addition it is possible to integrate other omics modalities such as Transcriptomics and Genomics for analysis and comparisons.

In this tab you can visualize meta dtata and number of detected modifications per type for each cohort.

Use the dropdown menus to select a cohort and metadata for visualization. Adjust the minimum items per group to filter the data accordingly.
This app is deployed at https://topas-portal.kusterlab.org/

## The bellow variables should be either set as variables in .bashrc or handled in CI/CD pipeline
```
EXPORT DB_PASSWORD=<your passwords>
EXPORT PORTAL_CONFIG_FILE=<the path to the config file of the portal>
```


## the bellow params need to be in the config file of the portal 
```{
    "local_http": "http://localhost:3832",
    "basket_annotation_path": "TOPAS_SCORING_4th gen_5th gen 231212.xlsx",
    "drug_annotation_path": "Drug_List.xlsx",
    "patient_annotation_path": {
        "INFORM": "METADATA.xlsx"
    },
    "report_directory": {
        "INFORM": "TOPAS_pipeline_results"
    },
    "sample_annotation_path": {
        "INFORM": "sample_annotation.csv"
    },
    "FP": {
        "INFORM": 1
    },
    "PP": {
        "INFORM": 1
    },
    "transcriptomics_path_z_scored": "fpkms.csv",
    "transcriptomics_path_not_z_scored": "un_normalized_fpkms.csv",
    "genomics_path": "genomics_df2portal.csv",
    "oncokb_path": "onkokb2portal.csv",
    "meta_data_columns_config": "meta_columns_config.json",
    "pspFastaFile": "Phosphosite_seq.fasta",
    "pspAnnotationFile": "Phosphorylation_site_dataset",
    "pspRegulatoryFile": "Regulatory_sites"
}
```
basket_annotation_path : an excel file with the bellow columns

```
'GROUP'        : '(R)TK', 'SIGNALING', 'OTHER'
'BASKET'       : i.e 'KIT', 'PDGFRA', 'PDGFRB', 'FGFR1', 'FGFR4', 'FGFR2', 'FGFR3'
'SUBBASKET'    : i.e 'KIT', 'PDGFRA', 'PDGFRB', 'Ligand', 'FGFR1', 'FGFR4', 'FGFR2'
'LEVEL'        : i.e 'phosphorylation', 'expression', 'kinase activity'
'SCORING RULE' : i.e 'highest protein phosphorylation score ,  'highest z-score', 'highest kinase score'highest z-score'
'WEIGHT'       : i.e  2. ,  nan,  0.5,  3. , -1. , -0.5,  0. 
'GENE NAME'    : i.e 'KIT', 'PDGFRA', 'PDGFRB', ..., 'FBLN2', 'ITGA5', 'COL3A1'
'Site positions (MQ identified - PSP)' : i.e 'P09619_Y751', 'P11362_Y654', 'P11362_Y653'
'Kinase'       : 'AXL;CSK;Chk1;Fyn;Lck;PDGFRA;PDGFRB;PKACA;Src'
'MODIFIED SEQUENCE' : i.e  '_LLLATpYARPPR_', '_EPPPpYQEPRPR_', 
'Literature' : optional
'Comment'    : optional
```


drug_annotation_path : path to excel file with the bellow columns
```      
   "Drug"
   "Kinobeads Target List"
   "Designated targets"
   "Other targets"
   "Clinical Phase"
```
"report_directory" : for each cohort path to the results from the topas_pipeline

"sample_annotation_path" : for each cohort path to csv file with the bellow columns replicates should be as new rows 
```
Sample name
Batch Name
TMT Channel
QC
is_reference
```
FP and PP : 1 or 0 value for each cohort if the FP (full proteome) or PP (Phospho proteomics) data exist for that specific cohort

"patient_annotation_path" : for each cohort excel file with meta data 
the column 'Sample name' should exist which corresponds to the same record in sample annotation 
the information for the replicates are not needed 

'meta_data_columns_config' : path to json file with Meta data columns.  
json file should be formatted as bellow:
```
{"front_end_col_names": [
    {
        "dataField": "case_submitter_id",
        "dataType": "string",
        "width": "70",
        "visible": "false"
    },
        {
        "dataField": "ethnicity",
        "dataType": "string",
        "width": "70",
        "visible": "false"
    },
    {
        "dataField": "gender",
        "dataType": "string",
        "width": "70",
        "visible": "false"
    },
]}
```
## installation of backend locally without docker
- first clone the portal from the repo 
- To run the flask server:
- first install and activate a conda env on python 3.9.12 by:

```
conda create --name portal python=3.9.12
conda activate portal
```


## using poetry (recommended) 
```
- cat flask-backend/poetry.lock |grep lock|grep version  # to get the lock version of poetry
- pip install poetry==`cat flask-backend/poetry.lock |grep lock|grep version|awk -F = {'print $2'}|sed 's/"//g'|tr -d ' '|tr -d ''`
- poetry --version # to ensure the version is satisfied
- cd flask_backend
- poetry install

```
or

##  without poetry (not recommended)

```
pip install -r flask-backend/requirements.txt
```
To deploy backend on debug mode:

```
make test_flask # to run the portal on Debug mode
```
- To test the backend:
open   http://localhost:3832/config          in your browser, if the config file is shown everything is fine



# To run the vue server without docker (you must use another shell):

```
cd vue-frontend
npm install
npm run serve
```

Then access the app at http://localhost:8080
This should open the portal, to upload the cohorts use the admin tools on Other tools tab

## Run backend locally with docker

```
make create_docker_networks
docker-compose -f docker-compose-backend.local.yml build
docker-compose -f docker-compose-backend.local.yml up -d
```

The backend is available at http://localhost:3832 (to test, try http://localhost:3832/config)
- in the debug mode the config file which is used by default can be found at flask-backend/config_mtb_portal_mintest.json
- in the production mode the config file path is in settings.py

### Run with PostgreSQL support in the backend

1. Set `DATABASE_MODE = True` in `settings.py`.
2. Start a local backend with docker as above, this creates and starts a PostgreSQL database docker.
3. Import the data into the postgreSQL database (this takes 5-10 minutes for a small cohort):
   ```
   make database_import
   ```



### deploying on Test server

- On a server the portal can also be deployed without using CI pipeline
- ssh to server
- git clone the repository and cd to the repository folder
- export password and path to config file as explained above
```
make db            # this should deploy the backend and postgres database as two different containers
make frontend      # this should deploy the frontend as a separate container
```
- check the make file for more functionalities including linting, import to database etc.

### stopping the container 
ssh to the server

```
sudo docker stop `sudo docker ps|grep "mtb_portal/backend"|awk {'print $1'}`
```




## Common bugs

- DataGrid tables show "Unexpected server response" error: probably NaN values in the flask response. Replace NaNs with empty strings should solve it.
- Since the frontend of the poral is using the eslint if any changes of the vue code lead to error you can use
```
make lint
```
will fix the problem