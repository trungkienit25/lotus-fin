from typing import List, Optional
from pydantic import BaseModel, Field


class UserPrincipal(BaseModel):
    user_id: str = Field(..., description="Unique Frappe user email or username")
    company: str = Field(..., description="Currently active verified company boundary")
    roles: List[str] = Field(default_factory=list, description="Roles granted in session")
    as_of_date: Optional[str] = Field(default=None, description="Evaluation date boundary")

    def has_role(self, role: str) -> bool:
        return role in self.roles or "System Manager" in self.roles
