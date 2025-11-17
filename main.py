import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List
from database import create_document

app = FastAPI(title="Mad Over Italian - Event API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Mad Over Italian Event Backend Running"}

# Models for request/response
class TicketRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    quantity: int = Field(1, ge=1, le=10)
    notes: str | None = Field(None, max_length=500)

class TicketResponse(BaseModel):
    success: bool
    order_id: str
    total_amount: float

TICKET_PRICE = 10.0

@app.post("/api/tickets", response_model=TicketResponse)
def create_ticket_purchase(payload: TicketRequest):
    # Calculate total
    total = round(TICKET_PRICE * payload.quantity, 2)

    # Persist to DB
    try:
        order_id = create_document(
            "ticketpurchase",
            {
                "name": payload.name,
                "email": payload.email,
                "quantity": payload.quantity,
                "amount": total,
                "notes": payload.notes,
                "event": "Mad Over Italian Store Opening Tasting",
                "status": "confirmed",
                "currency": "AUD",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return TicketResponse(success=True, order_id=order_id, total_amount=total)

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
