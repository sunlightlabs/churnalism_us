# -*- coding: utf-8 -*-

def batched_results(qry, batch_size=10000):
    max_pk = qry.order_by('-pk')[0].pk
    if max_pk is None:
        return

    pk = None
    while True:
        batch_qry = (qry.filter(pk__gt=pk)
                     if pk is not None
                     else qry)
        for row in batch_qry.filter(pk__lte=max_pk)[:batch_size]:
            yield row
            pk = row.pk
            if pk >= max_pk:
                return


