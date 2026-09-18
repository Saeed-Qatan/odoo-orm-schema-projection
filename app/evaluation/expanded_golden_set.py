"""Golden expectations for the synthetic expanded source only."""

EXPANDED_GOLDEN_SET = [
    {
        'query': 'sales product quantity',
        'expected_models': ['sale.order', 'sale.order.line', 'product.product', 'product.template'],
        'expected_fields': {
            'sale.order': ['sale_order_line_ids'],
            'sale.order.line': ['product_id', 'product_uom_qty'],
            'product.product': ['product_tmpl_id'],
            'product.template': ['name'],
        },
        'expected_paths': [['sale.order', 'sale.order.line', 'product.product', 'product.template']],
        'max_extra_fields': 0,
    },
    {
        'query': 'sales customer total',
        'expected_models': ['sale.order', 'res.partner'],
        'expected_fields': {'sale.order': ['partner_id', 'amount_total'], 'res.partner': ['name']},
        'max_extra_fields': 0,
    },
    {
        'query': 'sales status',
        'expected_models': ['sale.order'],
        'expected_fields': {'sale.order': ['state']},
        'max_extra_fields': 0,
    },
    {
        'query': 'sales customer',
        'expected_models': ['sale.order', 'res.partner'],
        'expected_fields': {'sale.order': ['partner_id'], 'res.partner': ['name']},
        'max_extra_fields': 0,
    },
    {
        'query': 'sales product',
        'expected_models': ['sale.order', 'sale.order.line', 'product.product', 'product.template'],
        'expected_fields': {
            'sale.order': ['sale_order_line_ids'],
            'sale.order.line': ['product_id'],
            'product.product': ['product_tmpl_id'],
            'product.template': ['name'],
        },
        'max_extra_fields': 0,
    },
]

EXPANDED_GOLDEN_SET.append({
    'query': 'أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية',
    'expected_models': ['sale.order', 'sale.order.line', 'res.partner', 'product.product', 'product.template'],
    'expected_fields': {
        'sale.order': ['sale_order_line_ids', 'partner_id', 'date_order', 'user_id'],
        'sale.order.line': ['product_id', 'product_uom_qty'],
        'res.partner': ['name'],
        'product.product': ['product_tmpl_id'],
        'product.template': ['name'],
    },
    'max_extra_fields': 0,
})

EXPANDED_GOLDEN_SET.extend([
    {
        'query': 'sales customer country',
        'expected_models': ['sale.order', 'res.partner', 'res.country'],
        'expected_fields': {
            'sale.order': ['partner_id'], 'res.partner': ['name', 'country_id'], 'res.country': ['name'],
        },
        'max_extra_fields': 0,
    },
    {
        'query': 'sales region',
        'expected_models': ['sale.order', 'res.partner', 'res.country.state'],
        'expected_fields': {
            'sale.order': ['partner_id'], 'res.partner': ['state_id'], 'res.country.state': ['name'],
        },
        'max_extra_fields': 0,
    },
    {
        'query': 'sales company',
        'expected_models': ['sale.order', 'res.company'],
        'expected_fields': {'sale.order': ['company_id'], 'res.company': ['name']},
        'max_extra_fields': 0,
    },
    {
        'query': 'sales currency',
        'expected_models': ['sale.order', 'res.currency'],
        'expected_fields': {'sale.order': ['currency_id'], 'res.currency': ['name']},
        'max_extra_fields': 0,
    },
    {
        'query': 'sales category',
        'options': {'max_depth': 4},
        'expected_models': ['sale.order', 'sale.order.line', 'product.product', 'product.template', 'product.category'],
        'expected_fields': {
            'sale.order': ['sale_order_line_ids'], 'sale.order.line': ['product_id'],
            'product.product': ['product_tmpl_id'], 'product.template': ['categ_id'], 'product.category': ['name'],
        },
        'max_extra_fields': 0,
    },
    {
        'query': 'sales salesperson',
        'expected_models': ['sale.order', 'res.users', 'res.partner'],
        'expected_fields': {'sale.order': ['user_id'], 'res.users': ['partner_id'], 'res.partner': ['name']},
        'expected_paths': [['sale.order', 'res.users', 'res.partner']],
        'max_extra_fields': 0,
    },
    {
        'query': 'sales customer country salesperson',
        'expected_models': ['sale.order', 'res.users', 'res.partner', 'res.country'],
        'expected_fields': {
            'sale.order': ['partner_id', 'user_id'], 'res.users': ['partner_id'],
            'res.partner': ['name', 'country_id'], 'res.country': ['name'],
        },
        'max_extra_fields': 0,
    },
    {
        'query': 'أعطني المبيعات مع اسم العميل وبلد العميل واسم المندوب',
        'expected_models': ['sale.order', 'res.users', 'res.partner', 'res.country'],
        'expected_fields': {
            'sale.order': ['partner_id', 'user_id'], 'res.users': ['partner_id'],
            'res.partner': ['name', 'country_id'], 'res.country': ['name'],
        },
        'max_extra_fields': 0,
    },
])
