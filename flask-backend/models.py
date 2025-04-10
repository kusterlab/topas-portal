from peewee import Model, CharField, IntegerField, FloatField, TextField, chunked
import db_settings as db
import pandas as pd
import topas_portal.settings as settings

# add all needed tables as below


class BaseModel(Model):
    class Meta:
        database = db.db


class Cohorts(BaseModel):
    """
    Description of a cohort
    """

    cohort_id = IntegerField()
    cohort_name = CharField()


class Sampleannotation(BaseModel):
    """
    Sample annotation file
    """

    patient_name = CharField()
    value = TextField()
    meta_type = CharField()
    cohort_id = IntegerField()


class Patientmetadata(BaseModel):
    """
    Patients meta_data
    """

    patient_name = CharField()
    value = TextField()
    meta_type = CharField()
    cohort_id = IntegerField()


class Modsequencetoprotein(BaseModel):
    """
    Mapping between the modified sequnce and the protien names
    """

    gene_name = TextField()
    peptide = TextField()
    Proteins = TextField()
    cohort_id = IntegerField()


class Expressionfpzscores(BaseModel):
    """
    Expression data as FP level z_scored
    """

    cohort_id = IntegerField()
    patient_name = CharField()
    protein_name = TextField()
    value = FloatField()


class Expressionfpintensity(BaseModel):
    """
    Expression data as FP level at intensity level
    """

    cohort_id = IntegerField()
    patient_name = CharField()
    protein_name = TextField()
    value = FloatField()


class Phosphoscores(BaseModel):
    """
    Phosphoscores
    """

    cohort_id = IntegerField()
    patient_name = CharField()
    protein_name = TextField()
    value = FloatField()


class Expressionppzscores(BaseModel):
    """
    Expression data as PP level z_scored
    """

    cohort_id = IntegerField()
    patient_name = CharField()
    sequence = TextField()
    value = FloatField()


class Expressionppintensity(BaseModel):
    """
    Expression data as PP level at intensity level
    """

    cohort_id = IntegerField()
    patient_name = CharField()
    sequence = TextField()
    value = FloatField()


class Expressionfpmeta(BaseModel):
    """
    The number of peptides per patient for each protien
    """

    cohort_id = IntegerField()
    patient_name = CharField()
    protein_name = TextField()
    value = IntegerField()


class Topasscoresraw(BaseModel):
    """
    Topas scores of wp3 pipeline
    """

    patient_name = CharField()
    topas_name = TextField()
    value = FloatField()
    cohort_id = IntegerField()


class Topaszscores(BaseModel):
    """
    Topas scores of wp3 pipeline
    """

    patient_name = CharField()
    topas_name = TextField()
    value = FloatField()
    cohort_id = IntegerField()


def chunkwise_insert(df: pd.DataFrame, Obj):
    """
    Chunkwise many insert to the database
    """
    dict_cohorts = df.to_dict("records")
    model = Obj
    with db.db.atomic():
        for batch in chunked(dict_cohorts, settings.CHUNK_SIZE_IMPORT):
            model.insert_many(batch).execute()


# the tables should be registered in the below dictiondary
tables = {
    "cohorts": Cohorts,
    "modsequencetoprotein": Modsequencetoprotein,
    "expressionfpmeta": Expressionfpmeta,
    "patientmetadata": Patientmetadata,
    "sampleannotation": Sampleannotation,
    "expressionfpzscores": Expressionfpzscores,
    "expressionfpintensity": Expressionfpintensity,
    "expressionppzscores": Expressionppzscores,
    "expressionppintensity": Expressionppintensity,
    "phosphoscores": Phosphoscores,
    "topasscoresraw": Topasscoresraw,
    "topaszscores": Topaszscores,
}


def table_create(tableName, tablleClass):
    if db.db.table_exists(tableName) is False:
        db.db.create_tables([tablleClass])


for table in tables.keys():
    table_create(table, tables[table])


# Uncomment the below block to use the tablefunc feature of postgres
# such as the crossstab function
"""
try:
    db.db.execute_sql('create extension tablefunc;')
except:
    pass
"""
