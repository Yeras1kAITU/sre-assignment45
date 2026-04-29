-- Initialize database schema and sample data

-- Create users table
CREATE TABLE IF NOT EXISTS users (
                                     id SERIAL PRIMARY KEY,
                                     username VARCHAR(100) UNIQUE NOT NULL,
                                     email VARCHAR(255) UNIQUE NOT NULL,
                                     full_name VARCHAR(255) NOT NULL,
                                     role VARCHAR(50) DEFAULT 'user',
                                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
                                        id SERIAL PRIMARY KEY,
                                        name VARCHAR(255) NOT NULL,
                                        description TEXT,
                                        price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
                                        stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                                        category VARCHAR(100),
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
                                      id SERIAL PRIMARY KEY,
                                      user_id VARCHAR(100) NOT NULL,
                                      items JSONB NOT NULL,
                                      total_amount DECIMAL(10, 2) NOT NULL,
                                      status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
                                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Insert sample users
INSERT INTO users (username, email, full_name, role) VALUES
                                                         ('admin', 'admin@example.com', 'Admin User', 'admin'),
                                                         ('john_doe', 'john@example.com', 'John Doe', 'user'),
                                                         ('jane_smith', 'jane@example.com', 'Jane Smith', 'user'),
                                                         ('bob_wilson', 'bob@example.com', 'Bob Wilson', 'user')
ON CONFLICT (username) DO NOTHING;

-- Insert sample products
INSERT INTO products (name, description, price, stock, category) VALUES
                                                                     ('Laptop Pro X1', 'High-performance laptop with 16GB RAM, 512GB SSD', 1299.99, 50, 'Electronics'),
                                                                     ('Wireless Mouse', 'Ergonomic wireless mouse with long battery life', 29.99, 200, 'Accessories'),
                                                                     ('Mechanical Keyboard', 'RGB mechanical keyboard with Cherry MX switches', 89.99, 150, 'Accessories'),
                                                                     ('USB-C Hub 7-in-1', 'Multi-port USB-C hub with HDMI, USB 3.0, SD card', 49.99, 100, 'Accessories'),
                                                                     ('4K Monitor 27"', '27-inch 4K IPS monitor with HDR support', 449.99, 30, 'Electronics'),
                                                                     ('Noise Cancelling Headphones', 'Premium wireless headphones with ANC', 199.99, 75, 'Audio'),
                                                                     ('Smartphone Stand', 'Adjustable aluminum smartphone stand', 19.99, 300, 'Accessories'),
                                                                     ('External SSD 1TB', 'Portable 1TB external SSD, USB 3.2', 129.99, 60, 'Storage'),
                                                                     ('Webcam HD 1080p', 'Full HD webcam with auto-focus and microphone', 79.99, 90, 'Electronics'),
                                                                     ('Laptop Sleeve', 'Water-resistant laptop sleeve, multiple sizes', 24.99, 150, 'Accessories')
ON CONFLICT DO NOTHING;

-- Insert sample orders
INSERT INTO orders (user_id, items, total_amount, status) VALUES
                                                              (
                                                                  'john_doe',
                                                                  '[{"product_id": 1, "quantity": 1, "price": 1299.99}, {"product_id": 2, "quantity": 1, "price": 29.99}]',
                                                                  1329.98,
                                                                  'completed'
                                                              ),
                                                              (
                                                                  'jane_smith',
                                                                  '[{"product_id": 3, "quantity": 1, "price": 89.99}, {"product_id": 4, "quantity": 2, "price": 49.99}]',
                                                                  189.97,
                                                                  'processing'
                                                              ),
                                                              (
                                                                  'bob_wilson',
                                                                  '[{"product_id": 5, "quantity": 1, "price": 449.99}]',
                                                                  449.99,
                                                                  'pending'
                                                              )
ON CONFLICT DO NOTHING;