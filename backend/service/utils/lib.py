from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import ClauseElement

def get_or_create(session, model, defaults=None, **kwargs):
    try:
        query = session.query(model).filter_by(**kwargs)

        instance = query.first()

        if instance:
            return instance, False
        else:
            session.begin(nested=True)
            try:
                params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
                print(params)
                params.update(defaults)
                print(defaults,params)
                instance = model(**params)

                session.add(instance)
                session.commit()

                return instance, True
            except IntegrityError as e:
                session.rollback()
                instance = query.one()

                return instance, False
    except Exception as e:
        raise e