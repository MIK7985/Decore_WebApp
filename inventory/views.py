from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StorageFacility, Item, StorageStock, MaterialRequest, DeliveryLog, DeliveryLogItem
from .forms import StorageFacilityForm, ItemForm, AddStockForm, MaterialRequestForm, DeliveryLogForm, DeliveryLogItemForm, DeliveryLogItemFormSet
from django.forms import inlineformset_factory
from django.db.models import Sum

def sync_material_requests(site, item):
    """Self-healing function to accurately sync material requests based on all deliveries"""
    total_delivered = DeliveryLogItem.objects.filter(log__site=site, item=item).aggregate(Sum('quantity'))['quantity__sum'] or 0
    requests = MaterialRequest.objects.filter(site=site, item=item).exclude(status='cancelled').order_by('created_at')
    
    remaining = total_delivered
    for req in requests:
        req.delivered_quantity = min(remaining, req.quantity)
        if req.delivered_quantity >= req.quantity:
            req.status = 'fulfilled'
        elif req.delivered_quantity > 0:
            req.status = 'partial'
        else:
            req.status = 'pending'
        req.save()
        remaining -= req.delivered_quantity
        if remaining <= 0:
            remaining = 0

@login_required
def storage_list(request):
    if not (request.user.can_manage or request.user.role == 'storage_manager' or request.user.role == 'driver'):
        messages.error(request, "You do not have permission to view storages.")
        return redirect('dashboard')
    
    if request.user.role == 'storage_manager' and not request.user.can_manage:
        storages = StorageFacility.objects.filter(manager=request.user.employee).order_by('-created_at')
    else:
        storages = StorageFacility.objects.all().order_by('-created_at')
    
    # Pre-calculate totals for the view
    for storage in storages:
        storage.total_items_types = storage.stocks.count()
    
    context = {'storages': storages}
    return render(request, 'inventory/storage_list.html', context)

@login_required
def storage_add(request):
    if not request.user.can_manage:
        messages.error(request, "You do not have permission to add storages.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = StorageFacilityForm(request.POST)
        if form.is_valid():
            storage = form.save()
            messages.success(request, f"Storage '{storage.name}' created successfully.")
            return redirect('storage_list')
    else:
        form = StorageFacilityForm()
        
    return render(request, 'inventory/storage_form.html', {'form': form, 'title': 'Add New Storage Space'})

@login_required
def storage_detail(request, pk):
    storage = get_object_or_404(StorageFacility, pk=pk)
    
    # Restrict to admin, superuser, storage manager, or driver
    is_driver = request.user.role == 'driver'
    if not (request.user.can_manage or is_driver or (request.user.employee and storage.manager == request.user.employee)):
        messages.error(request, "You do not have permission to view this storage facility.")
        return redirect('storage_list')
        
    stocks = storage.stocks.all().select_related('item').order_by('item__category', 'item__name')
    
    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            item = form.cleaned_data['item']
            qty_to_add = form.cleaned_data['quantity_to_add']
            
            # Get or create the stock record for this storage
            stock, created = StorageStock.objects.get_or_create(storage=storage, item=item)
            
            # Check for negative result
            new_qty = stock.quantity + qty_to_add
            if new_qty < 0:
                messages.error(request, f"Cannot remove {abs(qty_to_add)} {item.unit} of {item.name}. Only {stock.quantity} available in stock.")
            else:
                stock.quantity = new_qty
                stock.save()
                messages.success(request, f"Successfully updated stock for {item.name}.")
            
            return redirect('storage_detail', pk=storage.pk)
    else:
        form = AddStockForm()
        
    context = {
        'storage': storage,
        'stocks': stocks,
        'form': form,
        'is_driver': is_driver,
    }
    return render(request, 'inventory/storage_detail.html', context)

@login_required
def storage_edit(request, pk):
    if not request.user.can_manage:
        messages.error(request, "You do not have permission to edit storages.")
        return redirect('storage_list')
        
    storage = get_object_or_404(StorageFacility, pk=pk)
    if request.method == 'POST':
        form = StorageFacilityForm(request.POST, instance=storage)
        if form.is_valid():
            form.save()
            messages.success(request, f"Storage '{storage.name}' updated successfully.")
            return redirect('storage_list')
    else:
        form = StorageFacilityForm(instance=storage)
        
    return render(request, 'inventory/storage_form.html', {'form': form, 'title': 'Edit Storage Space'})

@login_required
def item_list(request):
    if not (request.user.can_manage or request.user.role == 'storage_manager'):
        messages.error(request, "You do not have permission to view items.")
        return redirect('dashboard')
    
    items = Item.objects.all().order_by('category', 'name')
    return render(request, 'inventory/item_list.html', {'items': items})

@login_required
def item_add(request):
    if not (request.user.can_manage or request.user.role == 'storage_manager'):
        messages.error(request, "You do not have permission to add items.")
        return redirect('item_list')
        
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Item '{item.name}' added to catalog.")
            
            # Check if this request came from the storage_detail page
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            return redirect('item_list')
    else:
        form = ItemForm()
        
    return render(request, 'inventory/storage_form.html', {
        'form': form, 
        'title': 'Add New Item to Catalog',
        'back_url_name': 'item_list'
    })

@login_required
def item_edit(request, pk):
    if not (request.user.can_manage or request.user.role == 'storage_manager'):
        messages.error(request, "You do not have permission to edit items.")
        return redirect('item_list')
        
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{item.name}' updated successfully.")
            return redirect('item_list')
    else:
        form = ItemForm(instance=item)
        
    return render(request, 'inventory/storage_form.html', {
        'form': form, 
        'title': f'Edit {item.name}',
        'back_url_name': 'item_list'
    })

@login_required
def item_delete(request, pk):
    if not request.user.can_manage:
        messages.error(request, "You do not have permission to delete items.")
        return redirect('item_list')
        
    item = get_object_or_404(Item, pk=pk)
    
    # Check if item is used in any stock or requests
    is_used = item.storagestock_set.exists() or item.sitestock_set.exists() or item.materialrequest_set.exists() or item.deliverylogitem_set.exists()
    
    if request.method == 'POST':
        if is_used:
            messages.error(request, f"Cannot delete '{item.name}' because it is currently in use (in stock or requests).")
        else:
            item_name = item.name
            item.delete()
            messages.success(request, f"Item '{item_name}' deleted successfully.")
        return redirect('item_list')
        
    # Render a simple confirmation page
    return render(request, 'core/confirm_delete.html', {
        'object': item,
        'title': 'Delete Item',
        'message': f"Are you sure you want to delete the item '{item.name}'? This cannot be undone.",
        'cancel_url': 'item_list'
    })

@login_required
def material_request_list(request):
    # Form processing for main_worker
    if request.method == 'POST' and request.user.role == 'main_worker':
        form = MaterialRequestForm(request.POST, employee=request.user.employee)
        if form.is_valid():
            req = form.save(commit=False)
            req.requested_by = request.user.employee
            req.save()
            messages.success(request, f"Request for {req.quantity} {req.item.name if req.item else req.custom_item_name} submitted.")
            return redirect('material_request_list')
        else:
            messages.error(request, "Error submitting request. Please check the form.")
    
    # Initialize empty form for main_worker
    form = None
    if request.user.role == 'main_worker':
        form = MaterialRequestForm(employee=request.user.employee)

    # Querying the requests list
    if request.user.role in ['driver', 'storage_manager'] or request.user.can_manage:
        requests_qs = MaterialRequest.objects.all()
        # For drivers/admins/storage managers, let them filter by any site
        from sites_mgmt.models import WorkSite
        sites = WorkSite.objects.filter(status='active').order_by('name')
    elif request.user.role == 'main_worker' and request.user.employee:
        requests_qs = MaterialRequest.objects.filter(requested_by=request.user.employee)
        # For main workers, let them filter only by their assigned sites
        from sites_mgmt.models import WorkSite
        active_site_ids = request.user.employee.assignments.filter(is_active=True).values_list('site_id', flat=True)
        sites = WorkSite.objects.filter(id__in=active_site_ids)
    else:
        messages.error(request, "You do not have permission to view material requests.")
        return redirect('dashboard')
        
    # Apply filters
    site_filter = request.GET.get('site')
    date_filter = request.GET.get('date')
    
    if site_filter:
        requests_qs = requests_qs.filter(site_id=site_filter)
    if date_filter:
        requests_qs = requests_qs.filter(created_at__date=date_filter)
        
    requests = requests_qs.order_by('-created_at')
        
    return render(request, 'inventory/material_request_list.html', {
        'requests': requests,
        'form': form,
        'sites': sites,
        'current_site': site_filter,
        'current_date': date_filter
    })

@login_required
def material_request_update_status(request, pk):
    if request.user.role not in ['driver', 'storage_manager'] and not request.user.can_manage:
        messages.error(request, "You do not have permission to update request status.")
        return redirect('material_request_list')
        
    from django.shortcuts import get_object_or_404
    req = get_object_or_404(MaterialRequest, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(MaterialRequest.STATUS_CHOICES).keys():
            req.status = new_status
            req.save()
            messages.success(request, f"Request for {req.item.name if req.item else req.custom_item_name} marked as {req.get_status_display()}.")
        else:
            messages.error(request, "Invalid status.")
            
    return redirect('material_request_list')

@login_required
def delivery_log_list(request):
    if request.user.role not in ['driver'] and not request.user.can_manage:
        messages.error(request, "You do not have permission to view delivery logs.")
        return redirect('dashboard')
        
    if request.user.role == 'driver':
        logs = DeliveryLog.objects.filter(driver=request.user.employee).order_by('-date', '-created_at')
    else:
        logs = DeliveryLog.objects.all().order_by('-date', '-created_at')
        
    site_id = request.GET.get('site')
    date_filter = request.GET.get('date')
    
    if site_id:
        logs = logs.filter(site_id=site_id)
    if date_filter:
        logs = logs.filter(date=date_filter)
        
    from sites_mgmt.models import WorkSite
    sites = WorkSite.objects.filter(status='active')
        
    return render(request, 'inventory/delivery_log_list.html', {
        'logs': logs,
        'sites': sites,
        'current_site': site_id,
        'current_date': date_filter
    })

@login_required
def delivery_log_create(request):
    if request.user.role != 'driver':
        messages.error(request, "Only drivers can create delivery logs.")
        return redirect('dashboard')
        
    DeliveryItemFormSet = inlineformset_factory(
        DeliveryLog, DeliveryLogItem, 
        form=DeliveryLogItemForm,
        formset=DeliveryLogItemFormSet,
        extra=5, can_delete=False
    )
    
    if request.method == 'POST':
        form = DeliveryLogForm(request.POST)
        formset = DeliveryItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            # Check if at least one item has quantity
            has_items = False
            for inline_form in formset:
                if inline_form.cleaned_data and not inline_form.cleaned_data.get('DELETE', False):
                    has_items = True
                    break
            
            if not has_items:
                messages.error(request, "You must include at least one item in the delivery log.")
            else:
                # --- STOCK VALIDATION ---
                insufficient_stock = []
                source_storage = form.cleaned_data.get('source_storage')
                
                if source_storage:
                    for inline_form in formset:
                        if inline_form.cleaned_data and not inline_form.cleaned_data.get('DELETE', False):
                            item = inline_form.cleaned_data.get('item')
                            qty = inline_form.cleaned_data.get('quantity')
                            if item and qty:
                                stock = StorageStock.objects.filter(storage=source_storage, item=item).first()
                                current_qty = stock.quantity if stock else 0
                                if current_qty < qty:
                                    insufficient_stock.append(f"{item.name} (Available: {current_qty})")
                
                if insufficient_stock:
                    messages.error(request, f"Insufficient stock in {source_storage.name} for: {', '.join(insufficient_stock)}")
                    # Return to form with error messages
                    return render(request, 'inventory/delivery_log_form.html', {
                        'form': form,
                        'formset': formset
                    })
                
                # Proceed with save if stock is sufficient
                log = form.save(commit=False)
                log.driver = request.user.employee
                log.save()
                
                # Process each item manually for automations
                formset.save(commit=False) # Populates deleted_objects if any
                
                # Combine duplicates
                combined_items = {}
                for inline_form in formset:
                    if not inline_form.cleaned_data or inline_form.cleaned_data.get('DELETE', False):
                        continue
                    
                    delivery_item = inline_form.instance
                    delivery_item.log = log
                    
                    if delivery_item.item_id in combined_items:
                        combined_items[delivery_item.item_id].quantity += delivery_item.quantity
                    else:
                        combined_items[delivery_item.item_id] = delivery_item
                
                for delivery_item in combined_items.values():
                    delivery_item.save()
                    
                    # Automation 1: Deduct from Storage Inventory
                    if log.source_storage:
                        stock, created = StorageStock.objects.get_or_create(
                            storage=log.source_storage, item=delivery_item.item
                        )
                        stock.quantity -= delivery_item.quantity
                        stock.save()
                        
                    # Automation 2: Auto-Fulfill Pending Material Requests
                    sync_material_requests(log.site, delivery_item.item)
                
                messages.success(request, f"Delivery to {log.site.name} recorded successfully. Inventory & Requests automatically updated.")
                return redirect('delivery_log_list')
    else:
        form = DeliveryLogForm()
        formset = DeliveryItemFormSet()
        
    return render(request, 'inventory/delivery_log_form.html', {
        'form': form,
        'formset': formset
    })

@login_required
def delivery_log_edit(request, pk):
    log = get_object_or_404(DeliveryLog, pk=pk)
    if request.user.role != 'driver' and not request.user.can_manage:
        messages.error(request, "Permission denied.")
        return redirect('delivery_log_list')
        
    DeliveryItemFormSet = inlineformset_factory(
        DeliveryLog, DeliveryLogItem, 
        form=DeliveryLogItemForm,
        formset=DeliveryLogItemFormSet,
        extra=1, can_delete=True
    )
    
    old_items = {item.id: item.quantity for item in log.items.all()}
    old_source = log.source_storage
    
    if request.method == 'POST':
        form = DeliveryLogForm(request.POST, instance=log)
        formset = DeliveryItemFormSet(request.POST, instance=log)
        if form.is_valid() and formset.is_valid():
            has_items = False
            for inline_form in formset:
                if inline_form.cleaned_data and not inline_form.cleaned_data.get('DELETE', False):
                    has_items = True
                    break
            
            if not has_items:
                messages.error(request, "You must include at least one item.")
            else:
                old_site = log.site
                items_to_sync = set()
                
                updated_log = form.save()
                instances = formset.save(commit=False)
                
                # Handle deleted items
                for obj in formset.deleted_objects:
                    items_to_sync.add(obj.item)
                    if old_source:
                        stock = StorageStock.objects.filter(storage=old_source, item=obj.item).first()
                        if stock:
                            stock.quantity += obj.quantity
                            stock.save()
                    obj.delete()
                    
                # Handle edited/new items by combining duplicates
                combined_instances = {}
                for inline_form in formset:
                    if not inline_form.cleaned_data or inline_form.cleaned_data.get('DELETE', False):
                        continue
                        
                    instance = inline_form.instance
                    instance.log = updated_log
                    
                    if instance.item_id in combined_instances:
                        combined_instances[instance.item_id].quantity += instance.quantity
                        if instance.pk:
                            # Revert old stock before deleting this duplicate row
                            if old_source and instance.pk in old_items:
                                stock = StorageStock.objects.filter(storage=old_source, item=instance.item).first()
                                if stock:
                                    stock.quantity += old_items[instance.pk]
                                    stock.save()
                            instance.delete()
                    else:
                        combined_instances[instance.item_id] = instance
                
                for instance in combined_instances.values():
                    diff = instance.quantity
                    if instance.pk and instance.pk in old_items:
                        diff = instance.quantity - old_items[instance.pk]
                        
                    instance.save()
                    
                    if updated_log.source_storage:
                        stock, _ = StorageStock.objects.get_or_create(storage=updated_log.source_storage, item=instance.item)
                        stock.quantity -= diff
                        stock.save()
                        
                    items_to_sync.add(instance.item)
                
                # Sync material requests for all affected items at both old and new sites
                for item in items_to_sync:
                    sync_material_requests(old_site, item)
                    if updated_log.site != old_site:
                        sync_material_requests(updated_log.site, item)
                
                messages.success(request, "Delivery updated successfully.")
                return redirect('delivery_log_list')
    else:
        form = DeliveryLogForm(instance=log)
        formset = DeliveryItemFormSet(instance=log)
        
    return render(request, 'inventory/delivery_log_form.html', {
        'form': form,
        'formset': formset,
        'is_edit': True
    })

