def get_or_create(session, model, default_values=False, **kwargs):
    if not default_values:
        default_values = {}    

    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = default_values
        params.update({**kwargs})
        instance = model(**params)
        session.add(instance)
        session.commit()
        return instance, True