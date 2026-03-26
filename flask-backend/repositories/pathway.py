# app/repositories/pathway_repo.py
from pymongo import MongoClient
from typing import List, Optional
from bson import ObjectId
from models.pathway import PathwayModel

class PathwayRepository:
    def __init__(self, client: MongoClient):
        self.collection = None
        if client is not None:
            self.collection = client.db_name.pathways
    
    def create(self, model: PathwayModel) -> PathwayModel:
        doc = model.model_dump(exclude={'id'}, mode="db")
        result = self.collection.insert_one(doc)
        doc['_id'] = str(result.inserted_id)
        return doc
    
    def get_by_id(self, id: str) -> Optional[PathwayModel]:
        doc = self.collection.find_one({'_id': ObjectId(id)})
        return PathwayModel.model_validate(doc) if doc else None

    def get_by_name(self, name: str) -> Optional[PathwayModel]:
        doc = self.collection.find_one({'name': name})
        return PathwayModel.model_validate(doc) if doc else None

    def get_all(self, filters: dict = None) -> List[PathwayModel]:
        cursor = self.collection.find(filters or {})
        docs = list(cursor)
        return [PathwayModel.model_validate(doc) for doc in docs]
    
    def update(self, id: str, model: PathwayModel) -> bool:
        doc = model.model_dump(mode="db")
        result = self.collection.update_one(
            {'_id': ObjectId(id)}, 
            {'$set': doc}
        )
        return result.modified_count > 0