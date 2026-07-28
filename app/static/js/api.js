function formatErrorDetail(detail) {
    // FastAPI validation errors (422) come back as an array of objects like:
    // { loc: ["body", "password"], msg: "String should have at least 4 characters", type: "..." }
    if (Array.isArray(detail)) {
        return detail
            .map((d) => {
                if (d && typeof d === 'object') {
                    const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : '';
                    return field ? `${field}: ${d.msg}` : d.msg;
                }
                return String(d);
            })
            .join(' | ');
    }
    if (detail && typeof detail === 'object') {
        return detail.msg || JSON.stringify(detail);
    }
    return detail;
}

// Product prices are stored in USD; display them consistently in Indian rupees.
const USD_TO_INR = 83;
function formatINR(value) {
    const amount = (Number(value) || 0) * USD_TO_INR;
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(amount);
}
 
async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options,
    });
 
    const body = await response.text();
    let data;
 
    try {
        data = body ? JSON.parse(body) : null;
    } catch (error) {
        data = body;
    }
 
    if (!response.ok) {
        const message =
            (data && formatErrorDetail(data.detail)) ||
            (data && data.message) ||
            body ||
            'Request failed';
        throw new Error(message);
    }
 
    return data;
}
 
async function registerUser(payload) {
    return requestJson('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}
 
async function loginUser(payload) {
    return requestJson('/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}
 
async function fetchProducts(search = '') {
    const params = new URLSearchParams();
    if (search) {
        params.set('search', search);
    }
    const url = `/products${params.toString() ? `?${params.toString()}` : ''}`;
    return requestJson(url);
}
 
async function fetchProductsByCategory(category, search = '') {
    const params = new URLSearchParams();
    if (category) {
        params.set('category', category);
    }
    if (search) {
        params.set('search', search);
    }
    const url = `/products${params.toString() ? `?${params.toString()}` : ''}`;
    return requestJson(url);
}
 
async function fetchCart() {
    return requestJson('/cart/');
}
 
async function addToCart(payload) {
    return requestJson('/cart/add', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}
 
async function removeCartItem(cartId) {
    return requestJson(`/cart/remove/${cartId}`, {
        method: 'DELETE',
    });
}
 
async function fetchCartCount() {
    const items = await fetchCart();
    return Array.isArray(items)
        ? items.reduce((sum, item) => sum + (Number(item?.quantity) || 0), 0)
        : 0;
}
 
async function createOrder(payload) {
    return requestJson('/orders/create', {
        method: 'POST',
        body: JSON.stringify(payload),
    });
}
 
async function fetchOrders() {
    return requestJson('/orders/');
}
 
async function fetchOrderDetail(orderId) {
    return requestJson(`/orders/${orderId}`);
}
 












