from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: list[str] = []


app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello World!"}


@app.get("/items")
async def get_items():
    """Get all items"""
    items = ["Item A", "Item B", "Item C", "Item D"]
    return {"items": items}


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get item"""
    return {"item_id": item_id}


@app.get("/items/typed/{item_id}")
async def get_item_typed(item_id: int):
    """
    Type hint demonstration
    - Auto validation: Returns 422 Unprocessable Entity on type mismatch
    - Auto conversion: Automatically converts and passes the correct type
    """
    return {"item_id": item_id, "type": str(type(item_id))}


# Specific paths must be declared before dynamic paths
@app.get("/users/me")
async def get_current_user():
    return {"user": "me"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}


# Query parameters: function arguments not in path become query params
# Default values for optional query parameters
@app.get("/items-query")
async def get_items_with_query(skip: int = 0, limit: int = 10):
    """Get items with pagination query parameters"""
    return {"query_params": {"skip": skip, "limit": limit}}


# Optional query parameters: using Optional or | None
@app.get("/items-optional")
async def get_items_optional(q: Optional[str] = None):
    """Get items with optional search query"""
    result = {"items": [{"item_id": 1}, {"item_id": 2}]}
    if q:
        result.update({"q": q})
    return result


# Required query parameters: no default value makes it required
@app.get("/items-required")
async def get_items_required(price: float, is_offer: bool | None = None):
    """Get items with required price parameter"""
    return {"required_params": {"price": price, "is_offer": is_offer}}


@app.get("/users/{user_id}/orders")
async def get_user_orders(user_id: int, status: Optional[str] = None):
    """Get user orders with optional status filter"""
    result = {"user_id": user_id, "orders": [{"order_id": 1}, {"order_id": 2}]}
    if status:
        result.update({"status": status})
    return result


@app.post("/items")
async def create_item(item: Item):
    """Create a new item"""
    name = item.name
    price = item.price
    description = item.description if item.description else ""

    # Pydantic V2: 모델 객체를 딕셔너리로 변환하기 위해 model_dump 사용
    item_dict = item.model_dump()

    return {"message": f"Item {name} created successfully", "data": item_dict}


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    """Update a specific item"""

    print(f"path param: {item_id}")
    print(f"request body: {item.model_dump()}")

    if q:
        print(f"query param: {q}")

    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"query_param": q})

    return result


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete a specific item"""
    # TODO: Use path parameter for deletion
    return {"message": f"Item {item_id} deleted successfully"}
