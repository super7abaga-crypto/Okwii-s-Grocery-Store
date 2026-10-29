const products = [
    {
        id: 1,
        name: "Premium Rice",
        category: "food",
        price: 45000,
        description: "Quality Nigerian rice for everyday meals.",
        image: "images/rice.jpg"
    },

    {
        id: 2,
        name: "Cooking Oil",
        category: "food",
        price: 12000,
        description: "Premium vegetable cooking oil.",
        image: "images/oil.jpg"
    },

    {
        id: 3,
        name: "Soft Drink",
        category: "drinks",
        price: 800,
        description: "Refreshing chilled soft drink.",
        image: "images/drink.jpg"
    },

    {
        id: 4,
        name: "Biscuits",
        category: "snacks",
        price: 1000,
        description: "Crunchy biscuits for a quick snack.",
        image: "images/biscuits.jpg"
    },

    {
        id: 5,
        name: "Spaghetti",
        category: "food",
        price: 1500,
        description: "Quality spaghetti for delicious meals.",
        image: "images/spaghetti.jpg"
    },

    {
        id: 6,
        name: "Laundry Detergent",
        category: "household",
        price: 3500,
        description: "Effective detergent for clean clothes.",
        image: "images/detergent.jpg"
    }
];


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
                src="${product.image}"
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

displayProducts(products);