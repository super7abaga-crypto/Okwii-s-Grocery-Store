import re
from pydantic import BaseModel, Field, field_validator

class ProductCreate(BaseModel):
    name: str = Field(min_length=2)
    description: str = ""
    category: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    image: str = ""


class ProductResponse(ProductCreate):
    id: int

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    description: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    image: str | None = None

class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=2)
    email: str
    password: str = Field(min_length=8)

class CustomerLogin(BaseModel):
    email: str
    password: str

class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    phone_number: str = Field(min_length=7)
    delivery_address: str = Field(min_length=10)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value):
        # Remove spaces, hyphens and brackets
        phone = re.sub(r"[\s\-()]", "", value)

        # Accept Nigerian numbers:
        # 08012345678
        # +2348012345678
        # 2348012345678
        if not re.fullmatch(r"(?:0[789][01]\d{8}|\+234[789][01]\d{8}|234[789][01]\d{8})", phone):
            raise ValueError("Enter a valid Nigerian phone number.")

        return phone

    @field_validator("delivery_address")
    @classmethod
    def validate_delivery_address(cls, value):
        address = value.strip()

        if len(address) < 10:
            raise ValueError("Please enter a complete delivery address.")

        return address


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderResponse(BaseModel):
    id: int
    total: float
    status: str
    payment_method: str
    payment_status: str
    phone_number: str
    delivery_address: str
    items: list[OrderItemResponse]