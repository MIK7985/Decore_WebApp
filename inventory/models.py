from django.db import models
from django.utils import timezone
from employees.models import Employee
from sites_mgmt.models import WorkSite

class StorageFacility(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_storages', limit_choices_to={'role': 'storage_manager'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('raw_material', 'Raw Material'),
        ('manufactured', 'Manufactured Item'),
        ('tool', 'Tool'),
        ('consumable', 'Consumable'),
    ]
    UNIT_CHOICES = [
        ('Bags', 'Bags'),
        ('Pieces', 'Pieces'),
        ('SqFt', 'SqFt'),
        ('SqM', 'SqM'),
        ('Kg', 'Kg'),
        ('Litre', 'Litre'),
        ('Bundle', 'Bundle'),
        ('Box', 'Box'),
        ('Pack', 'Pack'),
        ('Roll', 'Roll'),
        ('Set', 'Set'),
        ('Feet', 'Feet'),
        ('Metre', 'Metre'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Cost per unit (visible only to admin/managers)")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
from django.core.validators import MinValueValidator

class StorageStock(models.Model):
    storage = models.ForeignKey(StorageFacility, on_delete=models.CASCADE, related_name='stocks')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('storage', 'item')

    def __str__(self):
        return f"{self.item.name} at {self.storage.name}: {self.quantity} {self.item.unit}"

class SiteStock(models.Model):
    site = models.ForeignKey(WorkSite, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('site', 'item')

    def __str__(self):
        return f"{self.item.name} at {self.site.name}: {self.quantity} {self.item.unit}"

class DispatchOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    source_storage = models.ForeignKey(StorageFacility, on_delete=models.PROTECT, related_name='dispatches')
    destination_site = models.ForeignKey(WorkSite, on_delete=models.PROTECT, related_name='deliveries')
    driver = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='deliveries_driven', limit_choices_to={'role': 'driver'})
    vehicle_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    dispatch_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('core.CustomUser', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Dispatch #{self.pk} to {self.destination_site.name}"

class DispatchItem(models.Model):
    dispatch_order = models.ForeignKey(DispatchOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} {self.item.unit} of {self.item.name}"

class MaterialRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Fulfilled'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled')
    ]
    site = models.ForeignKey(WorkSite, on_delete=models.CASCADE, related_name='material_requests')
    requested_by = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='material_requests')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True, blank=True)
    custom_item_name = models.CharField(max_length=200, blank=True, help_text="Used if item is not in catalog")
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    delivered_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        item_display = self.item.name if self.item else self.custom_item_name
        return f"{self.quantity} {item_display} for {self.site.name}"

class DeliveryLog(models.Model):
    driver = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='delivery_logs')
    site = models.ForeignKey(WorkSite, on_delete=models.CASCADE, related_name='deliveries_received')
    source_storage = models.ForeignKey('StorageFacility', on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries_sent', help_text="Where did you pick up these items?")
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Delivery by {self.driver.name} to {self.site.name} on {self.date}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class DeliveryLogItem(models.Model):
    log = models.ForeignKey(DeliveryLog, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} {self.item.unit} of {self.item.name}"

    def get_cost(self):
        return self.quantity * self.item.unit_price
