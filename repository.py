import abc
import model


class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError



class SqlRepository(AbstractRepository):

    def __init__(self, session):
        self.session = session

    def add(self, batch):
        batch_id = self._add_batch({'reference': batch.reference, 'sku': batch.sku, '_purchased_quantity': batch._purchased_quantity, 'eta': batch.eta})
        if len(batch._allocations) > 0:
            orderline_ids = self._add_order_lines(batch._allocations)
            self._add_allocations(batch_id, orderline_ids)

    def get(self, reference) -> model.Batch:
        retrieved_batch = self._get_batch(reference)
        orderlines = self._get_batch_allocated_orderline(retrieved_batch[0])
        batch = model.Batch(*retrieved_batch[1:])
        for line in orderlines:
            batch.allocate(line)
        return batch

    def _get_batch_allocated_orderline(self, batchid):
        result =  list(self.session.execute(
            'SELECT order_lines.orderid, order_lines.sku, order_lines.qty'
            ' FROM order_lines'
            ' JOIN allocations ON allocations.orderline_id = order_lines.id'
            ' JOIN batches ON allocations.batch_id = batches.id'
            ' WHERE batches.id = :batchid',
            dict(batchid=batchid)
        ))
        return [model.OrderLine(**line) for line in result]


    def _get_batch(self, reference):
        return self.session.execute("select * from batches where reference=:reference", {'reference':reference}).first()

    def _add_batch(self, batch_data):
        result = self.session.execute('INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES (:reference, :sku, :_purchased_quantity, :eta)', batch_data)
        return result.lastrowid

    def _add_order_lines(self, allocations):
        orderline_ids = []
        for line in allocations:
            values = {"sku": line.sku, "qty": line.qty, "orderid": line.orderid}
            result = self.session.execute('INSERT INTO order_lines (sku, qty, orderid) VALUES (:sku, :qty, :orderid)', values)
            orderline_ids.append(result.lastrowid)
        return orderline_ids

    def _add_allocations(self, batch_id, orderline_ids):
        for orderline_id in orderline_ids:
            self.session.execute('INSERT INTO allocations (orderline_id, batch_id) VALUES (:orderline_id, :batch_id)', {"orderline_id": orderline_id, "batch_id": batch_id})
