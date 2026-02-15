-- Simple schema: categories, products, purchases, customers

-- Drop tables in reverse order to avoid foreign key constraints
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  category_id INTEGER REFERENCES categories(id)
);

CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  location TEXT
);

CREATE TABLE purchases (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER REFERENCES customers(id),
  product_id INTEGER REFERENCES products(id),
  unit_price NUMERIC,
  total_price NUMERIC
);

-- seed
INSERT INTO categories (name) VALUES ('Electronics');
INSERT INTO categories (name) VALUES ('Books');

INSERT INTO products (name, category_id) VALUES ('Smartphone', 1);
INSERT INTO products (name, category_id) VALUES ('Laptop', 1);
INSERT INTO products (name, category_id) VALUES ('Novel', 2);

INSERT INTO customers (name, location) VALUES ('Alice Johnson', 'New York');
INSERT INTO customers (name, location) VALUES ('Bob Smith', 'California');
INSERT INTO customers (name, location) VALUES ('Charlie Brown', 'Texas');

INSERT INTO purchases (customer_id, product_id, unit_price, total_price) VALUES (1, 1, 299.99, 299.99);
INSERT INTO purchases (customer_id, product_id, unit_price, total_price) VALUES (2, 2, 999.99, 1999.98);