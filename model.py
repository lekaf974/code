from dataclasses import dataclass
from typing import Optional, List
from datetime import date


class OutOfStock(Exception):
    pass


@dataclass(frozen=True)
class OrderLine:
    reference: str
    sku: str
    quantity: int


class Batch:
    
    def __init__(self, reference: str, sku: str, quantity: int, eta:Optional[date]):
        self.reference = reference
        self.sku = sku
        self.quantity = quantity
        self.eta = eta
        self.allocations = set()

    def allocate(self, order_line: OrderLine) -> None:
        if self.can_be_allocated(order_line): 
            self.allocations.add(order_line)

    def deallocate(self, order_line: OrderLine) -> None:
        if order_line in self.allocations:
            self.allocations.remove(order_line)

    @property
    def available_quantity(self):
        return self.quantity - self.allocated_quantity

    @property
    def allocated_quantity(self):
        return sum(line.quantity for line in self.allocations)

    def can_be_allocated(self, order_line: OrderLine) -> bool:
        return (self.sku == order_line.sku and 
            self.available_quantity >= order_line.quantity)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    
def allocate(order_line: OrderLine, batches: List[Batch]) -> None:
    try:
        batch = next(
            batch for batch in sorted(batches) if batch.can_be_allocated(order_line)
            )
        batch.allocate(order_line)
        return batch.reference
    except StopIteration:    
        raise OutOfStock(f'Out of stock for sku: {order_line.sku}')

    

