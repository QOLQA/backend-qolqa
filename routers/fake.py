from random import randint

from faker import Faker

from fastapi import APIRouter, Request
from models.Model import Model, SubModel, Document, NestedDoc, Position

router = APIRouter()
fake = Faker()

@router.post('')
async def create_fake_models() -> Model:
    fake_model = Model(submodels=[])
    
    num_submodels = randint(2, 3)
    
    # numero de submodelos
    for _ in range(num_submodels):
        fake_submodel = SubModel(
            documents=[],
            relations={}
        )
        
        # numero de documentos x submodelo
        num_documents = randint(1, 3)
        
        for _ in range(num_documents):
            fake_document = Document(
                name=fake.word(),
                fields={fake.word(): fake.word() for _ in range(3)},
                position=Position(x=fake.random_int(10, 400), y=fake.random_int(10, 400)),
                nested_docs=[]
            )
            fake_submodel.documents.append(fake_document)
        fake_model.submodels.append(fake_submodel)
            
    return fake_model
    
    




