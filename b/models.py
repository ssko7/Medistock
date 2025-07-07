from django.db import models
from decimal import Decimal

# Create your models here.
# 1. Supplier (Distributor)
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=20, blank=True)

# 2. Medicine
class Medicine(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    min_quantity = models.IntegerField(default=0)

# 3. Purchase

class Purchase(models.Model):
    distributor = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=100)
    purchase_date = models.DateField()
    gst=models.DecimalField(max_digits=10, decimal_places=2)
    discount=models.DecimalField(max_digits=10, decimal_places=2)
    sub_total=models.DecimalField(max_digits=10, decimal_places=2)

    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

# 4. Batch (Stock tracker)
class Batch(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='batches')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    batch_code = models.CharField(max_length=100)
    hsn_code = models.CharField(max_length=100, blank=True, null=True)
    strips = models.IntegerField(default=1)
    tablets = models.IntegerField()
    boxes = models.IntegerField(default=1)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_date = models.DateField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=0)  # total bought
    quantity_remaining = models.IntegerField(default=0)  # updated during sale

# 5. Sale (customer transaction)
class Sale(models.Model):
    customer_name = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    refered_doctor = models.CharField(max_length=100, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    sub_total=models.DecimalField(max_digits=10, decimal_places=2)
    gst=models.DecimalField(max_digits=10, decimal_places=2)
    discount=models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2)

# 6. SaleItem (sold per batch)
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_cost(self):
        return self.quantity * (self.batch.cost_price / (self.batch.strips * self.batch.tablets * self.batch.boxes))

    def get_profit(self):
        return (Decimal(self.selling_price) * self.quantity) - self.get_cost()