from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    create_products_table,
    create_customers_table,
    create_orders_table,
    create_order_items_table,
    add_order_phone_column
)

from app.database import get_connection

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

from app.schemas import (
    CustomerCreate,
    CustomerLogin,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    OrderCreate,
    OrderResponse
)

app = FastAPI(title="Okwii's Grocery Store API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8001",
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBearer()


def get_current_customer(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    customer_id = decode_access_token(token)

    if customer_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired login token."
        )

    connection = get_connection()

    customer = connection.execute(
        "SELECT id, full_name, email FROM customers WHERE id = ?",
        (customer_id,)
    ).fetchone()

    connection.close()

    if customer is None:
        raise HTTPException(
            status_code=401,
            detail="Customer account not found."
        )

    return dict(customer)

@app.on_event("startup")
def startup():
    create_products_table()
    create_customers_table()
    create_orders_table()
    create_order_items_table()
    add_order_phone_column()

@app.get("/")
def home():
    return {
        "message": "Welcome to Okwii's Grocery Store API"
    }

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate):

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO products
        (name, description, category, price, stock, image)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            product.name,
            product.description,
            product.category,
            product.price,
            product.stock,
            product.image
        )
    )

    connection.commit()

    product_id = cursor.lastrowid

    connection.close()

    return {
        "id": product_id,
        **product.model_dump()
    }

@app.get("/products", response_model=list[ProductResponse])
def get_products(
    search: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None
):

    connection = get_connection()

    query = "SELECT * FROM products WHERE 1=1"
    parameters = []

    if search:
        query += " AND name LIKE ?"
        parameters.append(f"%{search}%")

    if category:
        query += " AND category = ?"
        parameters.append(category)

    if min_price is not None:
        query += " AND price >= ?"
        parameters.append(min_price)

    if max_price is not None:
        query += " AND price <= ?"
        parameters.append(max_price)

    products = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return [dict(product) for product in products]

@app.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate):

    connection = get_connection()

    existing_product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if existing_product is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    updates = product.model_dump(exclude_unset=True)

    if not updates:
        connection.close()
        raise HTTPException(
            status_code=400,
            detail="No update information provided"
        )

    fields = ", ".join(
        f"{field} = ?" for field in updates
    )

    values = list(updates.values())
    values.append(product_id)

    connection.execute(
        f"UPDATE products SET {fields} WHERE id = ?",
        values
    )

    connection.commit()

    updated_product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    connection.close()

    return dict(updated_product)

@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    connection = get_connection()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if product is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    connection.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    connection.commit()
    connection.close()

    return {
        "message": "Product deleted successfully"
    }

@app.post("/register")
def register_customer(customer: CustomerCreate):

    connection = get_connection()

    existing_customer = connection.execute(
        "SELECT * FROM customers WHERE email = ?",
        (customer.email.lower(),)
    ).fetchone()

    if existing_customer:
        connection.close()

        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    hashed_password = hash_password(customer.password)

    connection.execute(
        """
        INSERT INTO customers (full_name, email, password)
        VALUES (?, ?, ?)
        """,
        (
            customer.full_name,
            customer.email.lower(),
            hashed_password
        )
    )

    connection.commit()
    connection.close()

    return {
        "message": "Account created successfully!"
    }

@app.post("/login")
def login_customer(customer: CustomerLogin):

    connection = get_connection()

    existing_customer = connection.execute(
        "SELECT * FROM customers WHERE email = ?",
        (customer.email.lower(),)
    ).fetchone()

    connection.close()

    if existing_customer is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    if not verify_password(
        customer.password,
        existing_customer["password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    token = create_access_token(existing_customer["id"])

    return {
        "message": "Login successful!",
        "access_token": token,
        "token_type": "bearer",
        "customer": {
            "id": existing_customer["id"],
            "full_name": existing_customer["full_name"],
            "email": existing_customer["email"]
        }
    }

@app.post("/orders", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    current_customer: dict = Depends(get_current_customer)
):
    connection = get_connection()

    try:
        # Start a transaction and lock writes while checking stock.
        connection.execute("BEGIN IMMEDIATE")

        # Combine repeated product IDs into one quantity.
        quantities = {}

        for item in order.items:
            quantities[item.product_id] = (
                quantities.get(item.product_id, 0) + item.quantity
            )

        total = 0
        order_items = []

        # Check products and calculate prices using the database.
        for product_id, quantity in quantities.items():

            product = connection.execute(
                "SELECT * FROM products WHERE id = ?",
                (product_id,)
            ).fetchone()

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {product_id} was not found."
                )

            if product["stock"] < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for {product['name']}."
                )

            unit_price = product["price"]
            subtotal = unit_price * quantity

            total += subtotal

            order_items.append({
                "product_id": product_id,
                "product_name": product["name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal
            })

        # Save the main order.
        cursor = connection.execute(
            """
            INSERT INTO orders (
                customer_id,
                total,
                status,
                payment_method,
                payment_status,
                delivery_address,
                phone_number
            )
            VALUES (?, ?, 'pending', 'cash', 'pending', ?, ?)
            """,
            (
                current_customer["id"],
                total,
                order.delivery_address,
                order.phone_number
            )
        )

        order_id = cursor.lastrowid

        # Save individual order items and reduce stock.
        for item in order_items:

            connection.execute(
                """
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    quantity,
                    unit_price
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    order_id,
                    item["product_id"],
                    item["quantity"],
                    item["unit_price"]
                )
            )

            connection.execute(
                """
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
                """,
                (
                    item["quantity"],
                    item["product_id"]
                )
            )

        connection.commit()

        return {
            "id": order_id,
            "total": total,
            "status": "pending",
            "payment_method": "cash",
            "payment_status": "pending",
            "phone_number": order.phone_number,
            "delivery_address": order.delivery_address,
            "items": order_items
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

@app.get("/orders/my", response_model=list[OrderResponse])
def get_my_orders(
    current_customer: dict = Depends(get_current_customer)
):
    connection = get_connection()

    try:
        orders = connection.execute(
            """
            SELECT *
            FROM orders
            WHERE customer_id = ?
            ORDER BY created_at DESC
            """,
            (current_customer["id"],)
        ).fetchall()

        customer_orders = []

        for order in orders:

            items = connection.execute(
                """
                SELECT
                    order_items.product_id,
                    products.name AS product_name,
                    order_items.quantity,
                    order_items.unit_price,
                    (order_items.quantity * order_items.unit_price) AS subtotal
                FROM order_items
                JOIN products
                    ON order_items.product_id = products.id
                WHERE order_items.order_id = ?
                """,
                (order["id"],)
            ).fetchall()

            customer_orders.append({
                "id": order["id"],
                "total": order["total"],
                "status": order["status"],
                "payment_method": order["payment_method"],
                "payment_status": order["payment_status"],
                "phone_number": order["phone_number"],
                "delivery_address": order["delivery_address"],
                "items": [dict(item) for item in items]
            })

        return customer_orders

    finally:
        connection.close()