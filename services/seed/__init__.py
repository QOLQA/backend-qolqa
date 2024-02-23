from random import randint
from faker import Faker
from fastapi import Request
from interfaces.seed import Seed
import uuid

from models.no_sql_db import NoSqlDBForm, SubModel, Collection, Position, NestedCollection

fake = Faker()


class Seed(Seed):
  def documents(self, request: Request, number_models: int):
    for _ in range(number_models):
      collection = NoSqlDBForm(submodels=[])
      num_sub_models = randint(2, 3)
      for _ in range(num_sub_models):
        sub_model = SubModel(documents=[], relations={})
        num_documents = randint(1, 3)
        for _ in range(num_documents):
          document = Collection(
            name=fake.word(),
            id=str(uuid.uuid4()),
            fields={fake.word(): fake.word() for _ in range(3)},
            position=Position(x=fake.random_int(10, 400), y=fake.random_int(10, 400)),
            nested_docs=[]
          )
          num_nested_docs = randint(1, 2)
          
          for _ in range(num_nested_docs):
            nested_doc = NestedCollection(
              name=fake.word(),
              fields={fake.word(): fake.word() for _ in range(2)},
              nested_docs=[]
            )
            document.nested_docs.append(nested_doc)
          sub_model.documents.append(document)
          
        sub_model.relations[sub_model.documents[0].id] = sub_model.documents[len(sub_model.documents) - 1].id
        collection.submodels.append(sub_model)

      request.app.services.models.create(collection)
    return {'msg': 'cool'}

seed = Seed()
