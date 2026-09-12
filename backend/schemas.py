from pydantic import BaseModel, Field

class ApplianceCreate(BaseModel):
    name: str = Field(min_length=1)
    wattage: int = Field(gt=0)
    priority: int = Field(gt=0)

class ApplianceResponse(BaseModel):
    id: int
    name: str
    wattage: int
    priority: int
    state: str

class StateResponse(BaseModel):
    appliances: list[ApplianceResponse]
    current_load: int
    remaining_capacity: int        