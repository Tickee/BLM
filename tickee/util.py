'''
Created on 13-jun-2011

@author: Kevin Van Wilder <kevin@tick.ee>
'''
from sqlalchemy.sql.expression import ClauseElement
import sqlahelper

Session = sqlahelper.get_session()


def get_or_create(session, model, defaults=None, **kwargs):
    instance = session.Query(model.filter_by(**kwargs)).first()
    if instance:
        return instance, False
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults)
        instance = model(**params)
        session.add(instance)
        return instance, True