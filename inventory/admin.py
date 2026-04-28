from django.contrib import admin
from .models import StorageFacility, Item, StorageStock, SiteStock, DispatchOrder, DispatchItem

class StorageStockInline(admin.TabularInline):
    model = StorageStock
    extra = 1

@admin.register(StorageFacility)
class StorageFacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'manager', 'created_at')
    inlines = [StorageStockInline]

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(StorageStock)
class StorageStockAdmin(admin.ModelAdmin):
    list_display = ('item', 'storage', 'quantity', 'last_updated')
    list_filter = ('storage', 'item__category')

@admin.register(SiteStock)
class SiteStockAdmin(admin.ModelAdmin):
    list_display = ('item', 'site', 'quantity', 'last_updated')
    list_filter = ('site', 'item__category')

class DispatchItemInline(admin.TabularInline):
    model = DispatchItem
    extra = 1

@admin.register(DispatchOrder)
class DispatchOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_storage', 'destination_site', 'driver', 'status', 'dispatch_date')
    list_filter = ('status', 'source_storage', 'destination_site')
    inlines = [DispatchItemInline]
