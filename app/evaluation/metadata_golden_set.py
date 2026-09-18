METADATA_GOLDEN_SET = [
    {
        "query": "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية",
        "expected_models": ["sale.order", "sale.order.line", "res.partner", "product.product", "product.template"],
        "expected_fields": {
            "sale.order": ["sale_order_line_ids", "partner_id", "date_order", "user_id"],
            "sale.order.line": ["product_id", "product_uom_qty"],
            "res.partner": ["name"],
            "product.product": ["product_tmpl_id"],
            "product.template": ["name"],
        },
        "max_extra_fields": 0,
    },
    {
        "query": "اعرض اسم العميل وإجمالي أمر البيع",
        "expected_models": ["sale.order", "res.partner"],
        "expected_fields": {"sale.order": ["partner_id", "amount_total"], "res.partner": ["name"]},
        "max_extra_fields": 0,
    },
    {
        "query": "أعطني المبيعات مع اسم العميل وبلد العميل واسم المندو",
        "expected_models": ["sale.order", "res.users", "res.partner", "res.country"],
        "expected_fields": {
            "sale.order": ["partner_id", "user_id"],
            "res.users": ["partner_id"],
            "res.partner": ["name", "country_id"],
            "res.country": ["name"],
        },
        "max_extra_fields": 0,
    },
]


