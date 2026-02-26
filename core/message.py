from typing import Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel

MessageRole = Literal["user", "assistant", "system", "tool"]

class Message(BaseModel):
    """消息类"""

    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __init__(self, role: MessageRole, content: str, **kwargs):
        super().__init__(
            role=role,
            content=content,
            timestamp=kwargs.get('timestamp', datetime.now()),
            metadata=kwargs.get('metadata', {})
        )
    
    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"