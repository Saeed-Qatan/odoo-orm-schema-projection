CREATE TABLE res_partner (
    id integer PRIMARY KEY,
    name character varying NOT NULL,
    email character varying,
    phone character varying,
    customer_rank integer,
    supplier_rank integer
);

CREATE TABLE product_product (
    id integer PRIMARY KEY,
    name character varying NOT NULL,
    default_code character varying
);

CREATE TABLE sale_order (
    id integer PRIMARY KEY,
    name character varying NOT NULL,
    date_order timestamp without time zone,
    partner_id integer NOT NULL,
    user_id integer,
    amount_total numeric,
    state character varying,
    CONSTRAINT sale_order_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES res_partner(id)
);

CREATE TABLE sale_order_line (
    id integer PRIMARY KEY,
    order_id integer NOT NULL,
    product_id integer,
    product_uom_qty numeric,
    price_unit numeric,
    CONSTRAINT sale_order_line_order_id_fkey FOREIGN KEY (order_id) REFERENCES sale_order(id),
    CONSTRAINT sale_order_line_product_id_fkey FOREIGN KEY (product_id) REFERENCES product_product(id)
);
