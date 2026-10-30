from fastapi import FastAPI, HTTPException

from app.models import create_products_table, create_customers_table
from fastapi.middleware.cors import CORSMiddleware
from app.database import get_connection
from app.security import hash_password
from app.schemas import CustomerCreate
from app.schemas import ProductCreate, ProductResponse, ProductUpdate
from app.security import verify_password, create_access_token
from app.schemas import CustomerLogin

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


@app.on_event("startup")
def startup():
    create_products_table()
    create_customers_table()

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
def get_products():

    connection = get_connection()

    products = connection.execute(
        "SELECT * FROM products"
    ).fetchall()

    connection.close()

    return [dict(product) for product in products]

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