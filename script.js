let products = [];
async function loadProducts() {

    const container =
        document.getElementById("product-container");

    container.innerHTML = "<p>Loading products...</p>";

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/products"
        );

        if (!response.ok) {
            throw new Error("Unable to load products.");
        }

        products = await response.json();

        displayProducts(products);

    } catch (error) {

        console.error("Product loading error:", error);

        container.innerHTML =
            "<p>Unable to load products. Please try again.</p>";
    }
}

let cart = [];


/* =========================
   DISPLAY PRODUCTS
========================= */

function displayProducts(productList) {

    const container =
        document.getElementById("product-container");

    container.innerHTML = "";

    productList.forEach(product => {

        const card = document.createElement("div");

        card.className = "product-card";

        card.innerHTML = `
            <img
                src="images/${product.image}"
                alt="${product.name}"
                onerror="this.src='https://via.placeholder.com/400x300?text=${encodeURIComponent(product.name)}'"
            >

            <div class="product-info">

                <h3>${product.name}</h3>

                <p>${product.description}</p>

                <span class="price">
                    ₦${product.price.toLocaleString()}
                </span>

                <button
                    class="add-button"
                    onclick="addToCart(${product.id})"
                >
                    Add to Cart
                </button>

            </div>
        `;

        container.appendChild(card);
    });
}


/* =========================
   FILTER PRODUCTS
========================= */

function filterProducts(category) {

    if (category === "all") {

        displayProducts(products);

        return;
    }

    const filtered =
        products.filter(
            product => product.category === category
        );

    displayProducts(filtered);
}


/* =========================
   SEARCH
========================= */

function searchProducts() {

    const search =
        document
            .getElementById("search-input")
            .value
            .toLowerCase();

    const results =
        products.filter(product =>
            product.name
                .toLowerCase()
                .includes(search)
        );

    displayProducts(results);
}


/* =========================
   CART
========================= */


function showCartToast(productName) {
    let toast = document.getElementById("cart-toast");

    // Create the notification the first time it is needed.
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "cart-toast";
        toast.className = "cart-toast";

        toast.innerHTML = `
            <span class="cart-toast-icon">✓</span>
            <div class="cart-toast-message">
                <strong>Added to your cart</strong>
                <span id="cart-toast-text"></span>
            </div>
        `;

        document.body.appendChild(toast);
    }

    document.getElementById("cart-toast-text").textContent =
        productName + " has been added successfully.";

    // Make the notification slide into view.
    toast.classList.add("show");

    // Clear the previous timer if another product is added.
    clearTimeout(window.cartToastTimer);

    // Hide the notification after 2.5 seconds.
    window.cartToastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}

function addToCart(productId) {

    const product =
        products.find(product =>
            product.id === productId
        );

    cart.push(product);

    updateCart();

    showCartToast(product.name);
}


function updateCart() {

    const cartCount =
        document.getElementById("cart-count");

    cartCount.textContent = cart.length;

    const cartItems =
        document.getElementById("cart-items");

    const cartTotal =
        document.getElementById("cart-total");

    if (cart.length === 0) {

        cartItems.innerHTML =
            "<p>Your cart is empty.</p>";

        cartTotal.textContent = "0";

        return;
    }

    let total = 0;

    cartItems.innerHTML = "";

    cart.forEach((product, index) => {

        total += product.price;

        const item =
            document.createElement("div");

        item.className = "cart-item";

        item.innerHTML = `
            <span>
                ${product.name}
            </span>

            <span>
                ₦${product.price.toLocaleString()}

                <button
                    onclick="removeFromCart(${index})"
                >
                    Remove
                </button>
            </span>
        `;

        cartItems.appendChild(item);
    });

    cartTotal.textContent =
        total.toLocaleString();
}


function removeFromCart(index) {

    cart.splice(index, 1);

    updateCart();
}


function openCart() {

    const modal =
        document.getElementById("cart-modal");

    modal.style.display = "flex";

    updateCart();
}


function closeCart() {

    const modal =
        document.getElementById("cart-modal");

    modal.style.display = "none";
}


/* =========================
   START WEBSITE
========================= */

loadProducts();
// ================================
// CUSTOMER AUTHENTICATION
// ================================

const API_URL = "http://127.0.0.1:8000";

function openAuth(formType) {
    const modal = document.getElementById("auth-modal");

    document.getElementById("login-form").style.display =
        formType === "login" ? "block" : "none";

    document.getElementById("register-form").style.display =
        formType === "register" ? "block" : "none";

    document.getElementById("auth-message").textContent = "";

    modal.style.display = "flex";
}


function closeAuth() {
    document.getElementById("auth-modal").style.display = "none";
}


// CUSTOMER REGISTRATION

async function registerCustomer(event) {
    event.preventDefault();

    const fullName =
        document.getElementById("register-name").value.trim();

    const email =
        document.getElementById("register-email").value.trim();

    const password =
        document.getElementById("register-password").value;

    const message =
        document.getElementById("auth-message");

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                full_name: fullName,
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed.");
        }

        message.textContent = "Account created successfully! You can now log in.";

        message.style.color = "green";

        document.querySelector("#register-form form").reset();

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";
    }
}


// CUSTOMER LOGIN

async function loginCustomer(event) {
    event.preventDefault();

    const email =
        document.getElementById("login-email").value.trim();

    const password =
        document.getElementById("login-password").value;

    const message =
        document.getElementById("auth-message");

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed.");
        }

        localStorage.setItem("ogs_token", data.access_token);

        localStorage.setItem(
            "ogs_customer",
            JSON.stringify(data.customer)
        );

        message.textContent = "Login successful!";
        message.style.color = "green";

        updateCustomerNavigation();

        document.querySelector("#login-form form").reset();

        setTimeout(closeAuth, 1000);

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "red";
    }
}


// UPDATE NAVIGATION AFTER LOGIN

function updateCustomerNavigation() {
    const customerData = localStorage.getItem("ogs_customer");

    if (!customerData) {
        return;
    }

    const customer = JSON.parse(customerData);

    document.getElementById("login-button").style.display = "none";

    document.getElementById("register-button").style.display = "none";

    const customerName =
        document.getElementById("customer-name");

    customerName.textContent = `Welcome, ${customer.full_name}`;

    customerName.style.display = "inline";

    document.getElementById("logout-button").style.display = "inline-block";
}


// CUSTOMER LOGOUT

function logoutCustomer() {
    localStorage.removeItem("ogs_token");

    localStorage.removeItem("ogs_customer");

    document.getElementById("login-button").style.display = "inline-block";

    document.getElementById("register-button").style.display = "inline-block";

    document.getElementById("customer-name").style.display = "none";

    document.getElementById("logout-button").style.display = "none";

    alert("You have logged out successfully.");
}


// RESTORE CUSTOMER SESSION WHEN WEBSITE OPENS

updateCustomerNavigation();