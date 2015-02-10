from tickee.core import marshalling

dict2list = lambda d: d.items()
list2dict = lambda lis: dict(lis)

def ticketorder_statistics(statistics_dict):
    return list2dict(map(lambda ds: (marshalling.date(ds[0]), ds[1]), dict2list(statistics_dict)))