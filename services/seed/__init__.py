from random import randint
from faker import Faker
from fastapi import Request
from interfaces.seed import Seed
import uuid

from models.no_sql_db import NoSqlDBForm, SubModel, Collection, Position, NestedCollection, Relation

fake = Faker()


class Seed(Seed):
  def documents(self, request: Request, number_models: int):
    for _ in range(number_models):
      no_sql_db = NoSqlDBForm(submodels=[], name=fake.word())
      num_sub_models = randint(2, 3)

      for _ in range(num_sub_models):
        sub_model = SubModel(collections=[], relations=None)
        num_collections = randint(2, 4)

        for _ in range(num_collections):
          collection = Collection(
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
              nested_docs=[],
              id=str(uuid.uuid4()),
              cardinality="1..1"
            )
            collection.nested_docs.append(nested_doc)
          sub_model.collections.append(collection)

        sub_model.relations = []
        sub_model.relations.append(Relation(
          id_source=sub_model.collections[0].id,
          id_target=sub_model.collections[len(sub_model.collections) - 1].id,
          cardinality="n..1"
        ))
        no_sql_db.submodels.append(sub_model)

      request.app.services.models.create(no_sql_db)
    return {'msg': 'cool'}

seed = Seed()
