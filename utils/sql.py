from utils.errors import Format

async def get_integer_id(id: str | int):
    try:
        return int(id)
    except (TypeError):
        raise Format(msg=f'The id: {id} is not a valid integer Id.')
    