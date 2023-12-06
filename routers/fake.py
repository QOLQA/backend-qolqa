from random import randint
import uuid

from faker import Faker

from fastapi import APIRouter, Request
from models.Model import Model, SubModel, Document, NestedDoc, Position

router = APIRouter()
fake = Faker()

@router.post('')
async def create_fake_models(
    request: Request,
    num_models: int = 10,
):
    
    for _ in range(num_models):
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
                    id=str(uuid.uuid4()),
                    fields={fake.word(): fake.word() for _ in range(3)},
                    position=Position(x=fake.random_int(10, 400), y=fake.random_int(10, 400)),
                    nested_docs=[]
                )
                
                num_nested_docs = randint(1, 2)
                
                for _ in range(num_nested_docs):
                    fake_nested_doc = NestedDoc(
                        name=fake.word(),
                        fields={fake.word(): fake.word() for _ in range(2)},
                        nested_docs=[]
                    )
                    
                    fake_document.nested_docs.append(fake_nested_doc)
                    
                fake_submodel.documents.append(fake_document)
                
            # relaciones
            fake_submodel.relations[fake_submodel.documents[0].id] = fake_submodel.documents[len(fake_submodel.documents) - 1].id
                
            fake_model.submodels.append(fake_submodel)
        
        request.app.database.create(fake_model)    
        
            
    return {'message': 'creado falsos creados correctamente!'}
    
    




