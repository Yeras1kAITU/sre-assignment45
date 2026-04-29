// API Configuration
const API_URL = 'http://localhost:8080';

// Navigation
function showSection(section) {
    // Hide all sections
    document.querySelectorAll('main section').forEach(s => {
        s.style.display = 'none';
        s.classList.remove('active');
    });

    // Show selected section
    const sectionElement = document.getElementById(`${section}-section`);
    if (sectionElement) {
        sectionElement.style.display = 'block';
        sectionElement.classList.add('active');
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    event.target.classList.add('active');

    // Load section data
    switch(section) {
        case 'products':
            loadProducts();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'chat':
            initChat();
            break;
        case 'status':
            loadSystemStatus();
            break;
    }
}

// Products
async function loadProducts() {
    try {
        const response = await fetch(`${API_URL}/api/products`);
        const data = await response.json();
        const productsList = document.getElementById('products-list');

        if (data.products && data.products.length > 0) {
            productsList.innerHTML = data.products.map(p => `
                <div class="card">
                    <h3>${p.name}</h3>
                    <p>${p.description || 'No description'}</p>
                    <p><strong>Price:</strong> $${parseFloat(p.price).toFixed(2)}</p>
                    <p><strong>Stock:</strong> ${p.stock} units</p>
                    <p><strong>Category:</strong> ${p.category}</p>
                    <p><small>Product ID: ${p.id}</small></p>
                </div>
            `).join('');
        } else {
            productsList.innerHTML = '<p>No products available</p>';
        }
    } catch (error) {
        console.error('Error loading products:', error);
        document.getElementById('products-list').innerHTML = `
            <div class="card down">
                <h3>Error Loading Products</h3>
                <p>Could not connect to Product Service</p>
                <p><small>${error.message}</small></p>
            </div>
        `;
    }
}

// Orders
function addOrderItem() {
    const orderItems = document.getElementById('order-items');
    const newItem = document.createElement('div');
    newItem.className = 'order-item';
    newItem.innerHTML = `
        <input type="number" class="product-id" placeholder="Product ID" required>
        <input type="number" class="quantity" placeholder="Quantity" required min="1">
    `;
    orderItems.appendChild(newItem);
}

document.getElementById('order-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const userId = document.getElementById('user-id').value;
    if (!userId) {
        alert('Please enter a User ID');
        return;
    }

    const items = [];
    const itemElements = document.querySelectorAll('.order-item');

    itemElements.forEach(item => {
        const productId = item.querySelector('.product-id').value;
        const quantity = item.querySelector('.quantity').value;

        if (productId && quantity) {
            items.push({
                product_id: parseInt(productId),
                quantity: parseInt(quantity),
                price: 0 // Price would be fetched from product service in production
            });
        }
    });

    if (items.length === 0) {
        alert('Please add at least one item to the order');
        return;
    }

    const orderData = {
        user_id: userId,
        items: items,
        total_amount: 0 // Would be calculated based on actual prices
    };

    try {
        const response = await fetch(`${API_URL}/api/orders`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });

        if (response.ok) {
            const data = await response.json();
            alert(`✅ Order created successfully!\nOrder ID: ${data.order_id}`);
            loadOrders();
        } else {
            const error = await response.json();
            alert(`❌ Failed to create order: ${error.detail || 'Unknown error'}`);
        }
    } catch (error) {
        alert(`❌ Failed to create order. Order Service might be down.\nError: ${error.message}`);
        console.error('Order creation error:', error);
    }
});

async function loadOrders() {
    try {
        const response = await fetch(`${API_URL}/api/orders`);
        const data = await response.json();
        const ordersList = document.getElementById('orders-list');

        if (data.orders && data.orders.length > 0) {
            ordersList.innerHTML = data.orders.map(o => `
                <div class="card">
                    <p><strong>Order ID:</strong> ${o.id}</p>
                    <p><strong>User:</strong> ${o.user_id}</p>
                    <p><strong>Status:</strong> 
                        <span class="status-indicator ${o.status === 'completed' ? 'status-healthy' : 'status-degraded'}"></span>
                        ${o.status}
                    </p>
                    <p><strong>Total:</strong> $${parseFloat(o.total_amount).toFixed(2)}</p>
                    <p><strong>Items:</strong> ${typeof o.items === 'string' ? JSON.parse(o.items).length : o.items.length}</p>
                    <p><small>Created: ${new Date(o.created_at).toLocaleString()}</small></p>
                </div>
            `).join('');
        } else {
            ordersList.innerHTML = '<p>No orders found</p>';
        }
    } catch (error) {
        console.error('Error loading orders:', error);
        document.getElementById('orders-list').innerHTML = `
            <div class="card down">
                <h3>Error Loading Orders</h3>
                <p>Could not connect to Order Service</p>
                <p><small>${error.message}</small></p>
            </div>
        `;
    }
}

// Chat
let ws = null;
let chatInitialized = false;

function initChat() {
    if (chatInitialized) return;
    chatInitialized = true;

    const username = document.getElementById('chat-username').value || 'Anonymous';

    try {
        ws = new WebSocket(`ws://localhost:8080/ws/${username}`);

        ws.onopen = () => {
            console.log('WebSocket connected');
            addSystemMessage('Connected to chat server');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'history') {
                data.messages.forEach(msg => {
                    if (msg.type === 'system') {
                        addSystemMessage(msg.message);
                    } else {
                        addChatMessage(msg);
                    }
                });
            } else if (data.type === 'system') {
                addSystemMessage(data.message);
            } else if (data.type === 'message') {
                addChatMessage(data);
            }
        };

        ws.onclose = () => {
            addSystemMessage('Disconnected from chat server');
            chatInitialized = false;
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            addSystemMessage('Error connecting to chat server');
            chatInitialized = false;
        };
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        addSystemMessage('Failed to connect to chat service');
        chatInitialized = false;
    }
}

function addChatMessage(data) {
    const messages = document.getElementById('chat-messages');
    const messageElement = document.createElement('p');
    messageElement.innerHTML = `
        <strong>${data.username}:</strong> ${data.message}
        <br><small>${new Date(data.timestamp).toLocaleTimeString()}</small>
    `;
    messages.appendChild(messageElement);
    messages.scrollTop = messages.scrollHeight;
}

function addSystemMessage(message) {
    const messages = document.getElementById('chat-messages');
    const messageElement = document.createElement('p');
    messageElement.style.color = '#667eea';
    messageElement.style.fontStyle = 'italic';
    messageElement.textContent = `[System] ${message}`;
    messages.appendChild(messageElement);
    messages.scrollTop = messages.scrollHeight;
}

function sendMessage() {
    const message = document.getElementById('chat-message').value;
    if (!message.trim()) return;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(message);
        document.getElementById('chat-message').value = '';
    } else {
        alert('Not connected to chat server. Please wait for connection or refresh.');
    }
}

// Allow sending message with Enter key
document.getElementById('chat-message').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// System Status
async function loadSystemStatus() {
    const services = [
        { name: 'auth', display: 'Authentication Service' },
        { name: 'product', display: 'Product Service' },
        { name: 'order', display: 'Order Service' },
        { name: 'user', display: 'User Service' },
        { name: 'chat', display: 'Chat Service' }
    ];

    const statusDiv = document.getElementById('services-status');
    statusDiv.innerHTML = '<p>Loading system status...</p>';

    let statusHTML = '';

    for (const service of services) {
        try {
            const response = await fetch(`${API_URL}/api/${service.name}/health`);
            const data = await response.json();

            const statusClass = data.status === 'healthy' ? 'healthy' : 'degraded';
            const indicatorClass = data.status === 'healthy' ? 'status-healthy' : 'status-degraded';

            statusHTML += `
                <div class="card ${statusClass}">
                    <h3>
                        <span class="status-indicator ${indicatorClass}"></span>
                        ${service.display}
                    </h3>
                    <p><strong>Status:</strong> ${data.status}</p>
                    <p><strong>Database:</strong> ${data.database || 'N/A'}</p>
                    <p><small>${new Date(data.timestamp).toLocaleString()}</small></p>
                </div>
            `;
        } catch (error) {
            statusHTML += `
                <div class="card down">
                    <h3>
                        <span class="status-indicator status-down"></span>
                        ${service.display}
                    </h3>
                    <p><strong>Status:</strong> DOWN</p>
                    <p><small>Service unreachable</small></p>
                </div>
            `;
        }
    }

    statusDiv.innerHTML = statusHTML;
}

// Auto-load products on page load
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
});

// Auto-refresh system status every 30 seconds when visible
let statusRefreshInterval;
const observer = new MutationObserver(() => {
    const statusSection = document.getElementById('status-section');
    if (statusSection.style.display !== 'none') {
        if (!statusRefreshInterval) {
            statusRefreshInterval = setInterval(loadSystemStatus, 30000);
        }
    } else {
        if (statusRefreshInterval) {
            clearInterval(statusRefreshInterval);
            statusRefreshInterval = null;
        }
    }
});

observer.observe(document.getElementById('status-section'), {
    attributes: true,
    attributeFilter: ['style']
});