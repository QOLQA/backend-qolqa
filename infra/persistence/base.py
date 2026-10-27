from typing import Any, Annotated, Callable, ClassVar

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict
from pydantic_core import core_schema

class _ObjectIdPydanticAnnotation:

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(input_value: str) -> ObjectId:
            return ObjectId(input_value)

        return core_schema.union_schema(
            [
                # check if it's an instance first before doing any further work
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ],
            serialization=core_schema.to_string_ser_schema(),
        )

PyObjectId = Annotated[
    ObjectId, _ObjectIdPydanticAnnotation
]

class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(alias="_id")

    model_config = ConfigDict(
        json_encoders={ObjectId: str},
        populate_by_name=True,
        # Serializar usando alias por defecto para que el frontend reciba _id
        json_schema_serialization_defaults_required=True,
    )


class SQLBaseModel(BaseModel):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
