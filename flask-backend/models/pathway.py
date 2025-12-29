from db import mongodb
from pydantic import BaseModel, Field, AliasChoices, ConfigDict, field_validator, field_serializer
from bson import ObjectId
from typing import Any, Dict
import json

class PathwayModel(BaseModel):
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))
    name: str
    type: str = "custom"
    skeleton: str


    model_config = ConfigDict(arbitrary_types_allowed=True, validate_by_name=True, validate_by_alias=True)

    @field_validator('id', mode='before')
    @classmethod
    def parse_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v
    
    @field_validator('skeleton', mode='before')
    @classmethod
    def destringify(cls, v: Any) -> Dict[str, Any]:
        if isinstance(v, str):
            return json.loads(v)
        return v 
    
    @field_serializer('skeleton')
    @classmethod
    def stringify(cls, v: Dict[str, Any], info) -> str:
        if info.mode == "db":
            return json.dumps(v)
        return v
