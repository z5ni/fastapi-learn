import asyncio
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
import time


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


# == CORS 미들웨어 설정 ==
# 허용할 origin 목록
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 허용할 origin 목록. ["*"]은 모든 origin 허용
    allow_credentials=True,  # True 시 다른 origin 요청에 쿠키/인증 정보 포함 허용. 단 allow_origins is not ["*"]
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
    ],  # 허용할 HTTP 메서드 목록. ["*"]는 모든 표준 메서드 허용
    allow_headers=["*"],  # 허용할 HTTP 요청 헤더 목록. ["*"]는 모든 헤더 허용
)


# == 미들웨어 ==
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    print(f"[Middleware] Request received {request.method} {request.url.path}")

    response = await call_next(request)  # 다음 처리 단계 호출 및 응답 받기

    process_time = time.time() - start_time

    # 응답 헤더에 커스텀 헤더 추가
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    print(f"[Middleware] Response generated. Process time: {process_time:.4f}")

    return response  # 수정된 응답 반환


# 임시 데이터 저장소
items_db = {}


@app.get("/")
async def read_root():
    await asyncio.sleep(0.5)
    return {"message": "Hello World!"}


# == 의존성 주입 예시 ==
# 공통 파라미터 처리: 여러 엔드포인트에서 공통으로 사용되는 파라미터들을 하나의 함수로 관리
async def get_common_param(q: str | None = None, skip: int = 0, limit: int = 10):
    return {"q": q, "skip": skip, "limit": limit}


# Depends()를 사용해 의존성 주입: 함수의 반환값이 매개변수로 자동 주입됨
@app.get("/items")
async def get_items(common_params: dict = Depends(get_common_param)):
    """Get all items"""
    print(
        f"q: {common_params['q']}, skip: {common_params['skip']}, limit: {common_params['limit']}"
    )
    return {"message": "Item list", "params": common_params}


@app.get("/users")
async def get_users(common_params: dict = Depends(get_common_param)):
    print(
        f"q: {common_params['q']}, skip: {common_params['skip']}, limit: {common_params['limit']}"
    )
    return {"message": "User list", "params": common_params}


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


# == 중첩 의존성 주입 예시 ==
# 1차 의존성: API 키 검증
async def verify_api_key(api_key: str | None = None):
    if api_key != "abc":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )
    return api_key


# 2차 의존성: API 키 검증을 포함한 관리자 권한 검증 (의존성의 의존성)
async def verify_admin_access(api_key: str = Depends(verify_api_key)):
    print(f"admin access (API Key: {api_key})")
    return {"is_admin": True}


# 의존성을 사용한 보안 엔드포인트
@app.get("/secure-data/")
async def get_secure_data(api_key: str = Depends(verify_api_key)):
    # verify_api_key 함수에서 예외 발생 시 실행되지 않음
    print(f"보안 데이터 접근 허용 (API Key: {api_key})")
    return {"message": "This is secure data", "access_api_key": api_key}


@app.get("/admin/")
async def get_admin_data(admin_info: dict = Depends(verify_admin_access)):
    print(f"관리자 데이터 접근 허용 {admin_info}")
    return {"message": "Hello admin", "admin_access": admin_info}


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
