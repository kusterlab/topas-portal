# TOPAS Portal

The TOPAS portal allows exploration of proteome and phospho-proteome profiles of patients processed with our clinical-proteomics pipeline from LC/MS data. 
In addition, other omics modalities such as transcriptomics and genomics can be integrated for analysis and comparisons.

This app is deployed at https://topas-portal.kusterlab.org/

## Configuration

The following variables are required to be set in your user's `~/.bashrc` or as part of a CI/CD pipeline:
```
export DB_PASSWORD=<your password>
export CONFIG_FILE_PATH=<path to your portal config file>
```

The `DB_PASSWORD` you can choose yourself and is needed to login to the admin tools panel in the portal.

The `CONFIG_FILE_PATH` is a `json` file with the following format:
```
{
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
    "pspRegulatoryFile": "Regulatory_sites",
    "oncokb_api_token": ""
}
```

- `basket_annotation_path`: path to an Excel file with the following columns:
    ```
    'GROUP'        : '(R)TK', 'SIGNALING', 'OTHER'
    'TOPAS_SCORE'  : e.g. 'KIT', 'PDGFRA', 'PDGFRB', 'FGFR1', 'FGFR4', 'FGFR2', 'FGFR3'
    'TOPAS_SUBSCORE'    : e.g. 'KIT', 'PDGFRA', 'PDGFRB', 'Ligand', 'FGFR1', 'FGFR4', 'FGFR2'
    'LEVEL'        : 'phosphorylation', 'expression', 'kinase activity'
    'SCORING RULE' : 'highest protein phosphorylation score ,  'highest z-score', 'highest kinase score'highest z-score'
    'WEIGHT'       : e.g.  2. ,  nan,  0.5,  3. , -1. , -0.5,  0. 
    'GENE NAME'    : e.g. 'KIT', 'PDGFRA', 'PDGFRB', ..., 'FBLN2', 'ITGA5', 'COL3A1'
    'Site positions (MQ identified - PSP)' : e.g. 'P09619_Y751', 'P11362_Y654', 'P11362_Y653'
    'Kinase'       : e.g. 'AXL;CSK;Chk1;Fyn;Lck;PDGFRA;PDGFRB;PKACA;Src'
    'MODIFIED SEQUENCE' : e.g. '_LLLATpYARPPR_', '_EPPPpYQEPRPR_', 
    'Literature' : optional
    'Comment'    : optional
    ```

- `drug_annotation_path`: path to an Excel file with the following columns:
    ```      
    "Drug"
    "Kinobeads Target List"
    "Designated targets"
    "Other targets"
    "Clinical Phase"
    ```

- `report_directory`: dictionary of `cohort_name -> path to a pipeline results folder` (https://github.com/kusterlab/topas-pipeline).

- `sample_annotation_path` : dictionary of `cohort_name -> path to csv file` with the following columns. Replicates should each get their own row. 
    ```
    Sample name
    Batch Name
    TMT Channel
    QC
    is_reference
    ```

- `FP` and `PP`: dictionary of `cohort_name -> value`, where value is `1` (available) or `0` (unavailable)

- `patient_annotation_path`: dictionary of `cohort_name -> excel file with meta data`.
The column 'Sample name' is mandatory and has to corresponds to the same record in `sample_annotation_path`. Additional columns containing metadata can be added freely.
Replicates of the same sample should not be repeated in this file.

- `meta_data_columns_config`: path to json file with additional metadata columns in `patient_annotation_path` with the following format:
    ```
    {
        "front_end_col_names": [
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
        ]
    }
    ```

## Installation

### Option 1: Deploy on server (recommended)

1. ssh into the server
2. clone this repo:
    ```
    git clone https://github.com/kusterlab/topas-portal.git`
    cd topas-portal
    ```
3. export password and path to config file (see above):
    ```
    export DB_PASSWORD=<your password>
    export CONFIG_FILE_PATH=<path to your portal config file>
    ```
4. deploy backend and frontend
    ```
    make db            # this should deploy the backend and postgres database as two different containers
    make frontend      # this should deploy the frontend as a separate container
    ```
5. Open the portal at http://localhost:8080. To upload cohort data, go to `Other tools -> Admin tools` and press the `Reload all cohorts` button at the bottom of the page.

Check the `Makefile` for additional functionalities.


### Option 2: deploy without docker

1. clone this repo:
    ```
    git clone https://github.com/kusterlab/topas-portal.git`
    cd topas-portal
    ```
2. install and activate a conda env on python 3.9.12:
    ```
    conda create --name portal python=3.9.12
    conda activate portal
    ```
3. install the dependencies:
    - option 1: using poetry (recommended) 
        ```
        pip install poetry==1.8.3
        cd flask_backend
        poetry install
        ```
    - option 2: using pip (not recommended)
        ```
        pip install -r flask-backend/requirements.txt
        ```
4. export password and path to config file (see above) and deploy the backend in debug mode:
    ```
    DB_PASSWORD=<your password> CONFIG_FILE_PATH=<path to your portal config file> make test_flask
    ```
5. Check that the backend is running by opening http://localhost:3832/config in your browser. Your config file should be displayed.
6. Open a new shell and deploy the frontend by running:
    ```
    VUE_APP_API_HOST=http://localhost:3832 make serve
    ```
7. Open the portal at http://localhost:8080. To upload cohort data, go to `Other tools -> Admin tools` and press the `Reload all cohorts` button at the bottom of the page.


### Option 3: deploy with docker

1. clone this repo:
    ```
    git clone https://github.com/kusterlab/topas-portal.git`
    cd topas-portal
    ```
2. Run docker-compose to start the backend:
    ```
    make create_docker_networks
    docker-compose -f docker-compose-backend.local.yml build
    docker-compose -f docker-compose-backend.local.yml up -d
    ```
3. The backend is available at http://localhost:3832 (to test, try http://localhost:3832/config)
    - in the debug mode the config file which is used by default can be found at flask-backend/config_mtb_portal_mintest.json
    - in the production mode the config file path is in settings.py
4. Deploy the frontend:
    ```
    cd vue-frontend
    sudo docker build --build-arg NODE_ENV=development --build-arg VUE_APP_API_HOST=http://$(hostname -I | awk '{print $1}'):3832 -t topas-portal:dev . 
    sudo docker run -d --name mtb_portal_frontend -it -p 3834:3834 --rm topas-portal:dev
    ```
5. Open the portal at http://localhost:3834. To upload cohort data, go to `Other tools -> Admin tools` and press the `Reload all cohorts` button at the bottom of the page.

### Option 4: Run with PostgreSQL as database backend

If you have a lot of data and not enough memory, consider switching to PostgreSQL as the database backend:

1. Set `DATABASE_MODE = True` in `settings.py`.
2. Start a local backend with docker (see above), this creates and starts a PostgreSQL database docker.
3. Import the data into the postgreSQL database (this takes 5-10 minutes for a small cohort):
   ```
   make database_import
   ```
4. Deploy the frontend (see above)


## Common development issues

- DataGrid tables show "Unexpected server response" error: probably NaN values in the flask response. Replace NaNs with empty strings should solve it.
- The frontend of the portal uses eslint which can lead to vue complaining about improper linting. Run `make lint` to fix these errors.