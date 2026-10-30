from pydantic import BaseModel, Field


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
