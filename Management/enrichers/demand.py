import itertools

from django.db.models import Count

from Management.models import Sale, DemandStatus, DemandDiff, ReminderStatusType

def set_demand_diff_fields(demands):
    # extract demand ids
    demand_ids = [d.id for d in demands]
    
    # construct a map of demand id to DemandDiff list
    diffs = DemandDiff.objects \
        .filter(demand_id__in=demand_ids) \
        .order_by('demand_id')

    diff_groups = itertools.groupby(diffs, lambda diff: diff.demand_id)

    demand_diff_map = {demand_id:list(demand_diffs) for (demand_id, demand_diffs) in diff_groups}

    diff_type_to_field = {
        u'קבועה': 'fixed_diff',
        u'משתנה': 'var_diff',
        u'בונוס': 'bonus_diff',
        u'קיזוז': 'fee_diff',
        u'התאמה': 'adjust_diff',
    }

    for demand in demands:
        total_diff_amount = 0

        if demand.id in demand_diff_map:
            demand_diffs = demand_diff_map[demand.id]
        else:
            demand_diffs = []

        for diff in demand_diffs:
            total_diff_amount += diff.amount

            if diff.type in diff_type_to_field:
                field_name = diff_type_to_field[diff.type]
                
                # set '*_diff' fields
                setattr(demand, field_name, diff)
        
        # set 'total_amount' field
        demand.total_amount = demand.sales_commission + total_diff_amount

def set_demand_is_fixed(demands):
    # extract demand ids
    demand_ids = [d.id for d in demands]

    # count modified sales for demand
    query = Sale.objects \
        .filter(demand_id__in=demand_ids) \
        .exclude(salehousemod=None, salepricemod=None, salepre=None, salereject=None) \
        .values('demand_id') \
        .annotate(cnt=Count('demand_id'))

    counts_by_demand = {row['demand_id']:row['cnt'] for row in query}

    for demand in demands:
        cnt = counts_by_demand.get(demand.id, 0)
        demand.is_fixed = cnt > 0

def set_demand_last_status(demands):
    # extract demand ids
    demand_ids = [d.id for d in demands]

    statuses = DemandStatus.objects \
        .select_related('type') \
        .filter(demand_id__in=demand_ids) \
        .order_by('demand_id','-date')

    statuses_by_demand = itertools.groupby(statuses, lambda status: status.demand_id)

    # construct a map of (demand_id, last_status)
    last_status_by_demand = {demand_id:next(demand_statuses, None) for (demand_id, demand_statuses) in statuses_by_demand}

    for demand in demands:
        demand.last_status = last_status_by_demand.get(demand.id, None)

def set_demand_open_reminders(demands):
    for demand in demands:
        demand.open_reminders = [r for r in demand.reminders.all()
            if r.statuses.latest().type_id not in (ReminderStatusType.Deleted,ReminderStatusType.Done)]

def set_demand_invoice_payment_fields(demands):
    for demand in demands:
        # sum invoice amounts
        invoice_amounts = [i.amount for i in demand.invoices.all()]
        demand.invoices_amount = sum(invoice_amounts) if len(invoice_amounts) > 0 else None

        # sum invoice offset amounts
        invoice_offset_amounts = [i.offset.amount for i in demand.invoices.all() if i.offset != None]
        demand.invoice_offsets_amount = sum(invoice_offset_amounts) if len(invoice_offset_amounts) > 0 else None

        demand.total_amount_offset = (demand.invoices_amount or 0) + (demand.invoice_offsets_amount or 0)

        # sum payment amounts
        payment_amounts = [p.amount for p in demand.payments.all()]
        demand.payments_amount = sum(payment_amounts) if len(payment_amounts) > 0 else None

        total_amount = demand.total_amount

        demand.diff_invoice = demand.total_amount_offset - total_amount
        demand.diff_invoice_payment = (demand.payments_amount or 0) - demand.total_amount_offset

        demand.is_fully_paid = demand.force_fully_paid or (
            total_amount == demand.total_amount_offset and total_amount == (demand.payments_amount or 0))

def set_demand_sale_fields(
    demands, 
    from_year, from_month, to_year, to_month):
    # extract project ids
    project_ids = [d.project_id for d in demands]

    # get sales for all projects
    all_sales = Sale.objects \
        .contractor_pay_range(from_year, from_month, to_year, to_month) \
        .filter(
            house__building__project_id__in=project_ids,
            commission_include=True, 
            salecancel__isnull=True) \
        .order_by('house__building__project_id', 'contractor_pay_year', 'contractor_pay_month') \
        .select_related('house__building')

    # group sales by (project id, year, month)
    sale_groups = itertools.groupby(
        all_sales, 
        lambda sale: (sale.house.building.project_id, sale.contractor_pay_year, sale.contractor_pay_month))

    sales_map = {map_key: list(sales) for (map_key, sales) in sale_groups}

    for demand in demands:
        map_key = (demand.project_id, demand.year, demand.month)

        sales_list = sales_map.get(map_key, [])

        demand.sales_list = sales_list
        demand.sales_with_discount = [sale for sale in sales_list if sale.discount != None]
        demand.sales_count = len(sales_list)
        demand.sales_total_price = sum([sale.price for sale in sales_list])
        demand.sales_amount = sum([sale.price_final for sale in sales_list])
