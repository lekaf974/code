from datetime import date, timedelta
import pytest
import uuid
from model import OrderLine, Batch, allocate


today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def create_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch(uuid.uuid4(), sku, batch_qty, eta=today),
        OrderLine(uuid.uuid4(), sku, line_qty)
    )

def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = create_batch_and_line('CHAIR-MYO', 20, 10)

    allocate(line, [batch])
    assert batch.available_quantity == (batch.quantity - line.quantity)

def test_can_allocate_if_available_greater_than_required():
    batch, line = create_batch_and_line('CHAIR-MYO', 20, 10)

    allocate(line, [batch])
    assert batch.available_quantity == (batch.quantity - line.quantity)

def test_cannot_allocate_if_available_smaller_than_required():
    batch, line = create_batch_and_line('CHAIR-MYO', 20, 40)

    batch.allocate(line)
    assert batch.available_quantity == batch.quantity

def test_can_allocate_if_available_equal_to_required():
    batch, line = create_batch_and_line('CHAIR-MYO', 20, 20)

    allocate(line, [batch])
    assert batch.available_quantity == (batch.quantity - line.quantity)

def test_allocation_is_idempotent():
    batch, line = create_batch_and_line('CHAIR-MYO', 20, 20)

    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == (batch.quantity - line.quantity)

def test_can_deallocate_allocated_line():
    batch, line = create_batch_and_line('CHAIR-MYO', 20, 20)

    allocate(line, [batch])
    assert batch.available_quantity == (batch.quantity - line.quantity)

    batch.deallocate(line)
    assert batch.available_quantity == batch.quantity

def test_can_not_deallocate_none_allocated_line():
    batch, line = create_batch_and_line('CHAIR-MYO', 20, 20)

    batch.deallocate(line)
    assert batch.available_quantity == batch.quantity

def test_cannot_allocate_if_skus_not_match():
    batch = Batch(uuid.uuid4(), 'batch-sku', 20, eta=today)
    line = OrderLine(uuid.uuid4(), 'line-sku', 5)

    batch.allocate(line)
    assert batch.available_quantity == batch.quantity

def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = Batch(uuid.uuid4(), 'batch-sku', 20, eta=None)
    shipment_batch = Batch(uuid.uuid4(), 'batch-sku', 40, eta=tomorrow)
    line = OrderLine(uuid.uuid4(), 'batch-sku', 5)

    allocate(line, [in_stock_batch, shipment_batch])
    assert in_stock_batch.available_quantity == (in_stock_batch.quantity - line.quantity)
    assert shipment_batch.available_quantity == shipment_batch.quantity

def test_prefers_earlier_batches():
    earliest_batch = Batch(uuid.uuid4(), 'batch-sku', 20, eta=None)
    medium_batch = Batch(uuid.uuid4(), 'batch-sku', 20, eta=tomorrow)
    latest_batch = Batch(uuid.uuid4(), 'batch-sku', 20, eta=later)
    line = OrderLine(uuid.uuid4(), 'batch-sku', 5)

    allocate(line, [earliest_batch, medium_batch, latest_batch])
    assert earliest_batch.available_quantity == (earliest_batch.quantity - line.quantity)
    assert medium_batch.available_quantity == medium_batch.quantity
    assert latest_batch.available_quantity == latest_batch.quantity

