from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

@dataclass
class DocContent:
    anchor_id: str
    plain_text: str

@dataclass
class EmailContent:
    subject: str
    html_body: str
    text_body: str
