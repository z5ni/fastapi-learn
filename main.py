from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello World!"}


@app.get("/items")
async def get_items():
    """Get all items"""
    items = ["Item A", "Item B", "Item C", "Item D"]
    return {"items": items}


@app.get("/info")
async def get_info():
    """Get API information"""
    return {"message": "This is an example of FastAPI GET API"}


@app.post("/items")
async def create_item():
    """Create a new item"""
    # TODO: Accept item data from request body
    return {"message": "Item created successfully"}


@app.put("/items/{item_id}")
async def update_item(item_id: int):
    """Update a specific item"""
    # TODO: Use path parameter and request body
    return {"message": f"Item {item_id} updated successfully"}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete a specific item"""
    # TODO: Use path parameter for deletion
    return {"message": f"Item {item_id} deleted successfully"}
