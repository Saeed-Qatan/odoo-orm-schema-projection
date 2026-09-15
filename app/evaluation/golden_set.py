GOLDEN_SET = [
    {
        "query": "أعطني مبيعات أحمد في أغسطس مع اسم العميل والمنتج والكمية",
        "expected_models": ["sale.order", "res.partner", "sale.order.line", "product.product"],
        "expected_fields": {
            "sale.order": ["date_order", "partner_id"],
            "res.partner": ["name"],
            "sale.order.line": ["product_id", "product_uom_qty"],
            "product.product": ["name"],
        },
        "max_extra_fields": 8,
    },
    {
        "query": "اعرض اسم العميل وإجمالي أمر البيع",
        "expected_models": ["sale.order", "res.partner"],
        "expected_fields": {
            "sale.order": ["partner_id", "amount_total"],
            "res.partner": ["name"],
        },
        "max_extra_fields": 5,
    },
]
