from typing import Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, HTTPException


class Item(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=50,
        title="Item Name",  # 문서화를 위한 제목
        description="The name of the item (3 to 50 chars)",  # 문서화를 위한 설명
        examples=["Gaming Keyboard"],  # 문서화를 위한 예시
    )
    description: str | None = Field(
        default=None,  # 기본값 설정
        max_length=300,
        title="Item Description",
        description="Optional description of the item (max 300 chars)",
    )
    price: float = Field(
        gt=0,  # greater than
        le=100000.0,  # less than or equal to
        title="Price",
        description="The price of the item (must be positive and <= 100,000)",
    )
    tax: float | None = Field(
        default=None,
        gt=0,
        title="Tax",
        description="Optional tax amount (must be positive)",
    )
    code: str | None = Field(
        default=None,
        pattern="^code-\\d{3}$",  # 정규식 사용
        title="Code",
        description="Optional Code",
    )
    tags: list[str] = Field(
        default=[],
        # min_length=1,
        max_length=5,
        title="Tags",
        description="List of tags for the item (up to 5 tags)",
    )

    # 커스텀 유효성 검사
    # @field_validator를 사용해 특정 필드에 대한 커스텀 검증 로직 추가
    @field_validator("name")
    @classmethod  # 클래스 메서드로 정의 필요
    def name_must_not_contain_admin(cls, v: str):
        if "admin" in v.lower():
            raise ValueError("Item name cannot contain 'admin'")
        return v.title()


app = FastAPI()

# 임시 데이터 저장소
items_db = {}


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
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, **items_db[item_id]}


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


@app.post("/items", status_code=201)  # 성공 시 201 Created return
async def create_item(item: Item):
    """Create a new item"""
    item_id = len(items_db) + 1
    items_db[item_id] = item.model_dump()  # Pydantic 모델을 dict로 변환

    print(f"Item Created: ID={item_id}, Data={items_db[item_id]}")
    return {"item_id": item_id, **items_db[item_id]}


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
