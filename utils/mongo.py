from bson import ObjectId, errors

from utils.errors import Format

async def get_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (errors.InvalidId, TypeError):
        raise Format(msg=f'The _id: {id} is not a valid ObjectId.')
    