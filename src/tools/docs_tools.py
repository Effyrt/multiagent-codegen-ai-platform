"""
Documentation Tools

Tools for querying framework documentation and examples.
"""

import logging
from typing import Dict, Any, Optional

from .base_tool import BaseTool, ToolParameter

logger = logging.getLogger(__name__)


class DocsLookupTool(BaseTool):
    """
    Query official framework documentation
    
    Retrieves relevant documentation sections for frameworks
    and libraries.
    """
    
    name = "query_framework_docs"
    description = "Get official documentation for frameworks and common patterns"
    parameters = [
        ToolParameter(
            name="framework",
            type="string",
            description="Framework name (fastapi, flask, django, express)",
            required=True,
            enum=["fastapi", "flask", "django", "express", "react", "vue"]
        ),
        ToolParameter(
            name="topic",
            type="string",
            description="Topic or pattern to look up (e.g., 'authentication', 'database', 'routing')",
            required=True
        )
    ]
    
    async def execute(self, framework: str, topic: str) -> Dict[str, Any]:
        """
        Query framework documentation
        
        Args:
            framework: Framework name
            topic: Topic to look up
            
        Returns:
            Documentation content and reference URL
        """
        
        self.logger.info(f"Looking up {framework} docs for: {topic}")
        
        # Mock documentation responses
        # In production, this would query actual documentation APIs or scraped content
        
        docs_database = {
            "fastapi": {
                "authentication": {
                    "content": """
# FastAPI Authentication

FastAPI uses OAuth2 with Password (and hashing), Bearer with JWT tokens.

## Basic Setup:
```python
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    return {"access_token": user.username, "token_type": "bearer"}
```

## Protected Routes:
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Decode and validate token
    return user
```
                    """.strip(),
                    "url": "https://fastapi.tiangolo.com/tutorial/security/",
                    "sections": ["OAuth2", "JWT Tokens", "Dependencies"]
                },
                "database": {
                    "content": """
# FastAPI with Databases

Use SQLAlchemy ORM for database operations.

## Setup:
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
```

## Dependency:
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
                    """.strip(),
                    "url": "https://fastapi.tiangolo.com/tutorial/sql-databases/",
                    "sections": ["SQLAlchemy", "Models", "CRUD Operations"]
                },
                "routing": {
                    "content": """
# FastAPI Routing

Define routes using decorators.

```python
from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def list_items():
    return {"items": []}

@router.post("/")
async def create_item(item: Item):
    return item

@router.get("/{item_id}")
async def get_item(item_id: int):
    return {"item_id": item_id}
```
                    """.strip(),
                    "url": "https://fastapi.tiangolo.com/tutorial/bigger-applications/",
                    "sections": ["APIRouter", "Path Operations", "Tags"]
                }
            },
            "flask": {
                "authentication": {
                    "content": """
# Flask Authentication

Use Flask-Login for session management.

```python
from flask_login import LoginManager, login_user, logout_user

login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return redirect('/dashboard')
```
                    """.strip(),
                    "url": "https://flask-login.readthedocs.io/",
                    "sections": ["Flask-Login", "Sessions", "User Loader"]
                }
            },
            "express": {
                "authentication": {
                    "content": """
# Express.js Authentication

Use Passport.js for authentication.

```javascript
const passport = require('passport');
const LocalStrategy = require('passport-local').Strategy;

passport.use(new LocalStrategy(
  (username, password, done) => {
    User.findOne({ username }, (err, user) => {
      if (!user) return done(null, false);
      if (!user.validPassword(password)) return done(null, false);
      return done(null, user);
    });
  }
));

app.post('/login', passport.authenticate('local'), (req, res) => {
  res.json({ success: true });
});
```
                    """.strip(),
                    "url": "http://www.passportjs.org/docs/",
                    "sections": ["Passport.js", "Strategies", "Sessions"]
                }
            }
        }
        
        # Get docs for framework and topic
        framework_docs = docs_database.get(framework, {})
        topic_docs = framework_docs.get(topic.lower())
        
        if not topic_docs:
            # Return generic not found message
            return {
                "found": False,
                "framework": framework,
                "topic": topic,
                "message": f"Documentation for '{topic}' in {framework} not found in cache",
                "suggestion": f"Check official {framework} documentation",
                "url": self._get_framework_url(framework)
            }
        
        return {
            "found": True,
            "framework": framework,
            "topic": topic,
            "content": topic_docs["content"],
            "url": topic_docs["url"],
            "sections": topic_docs.get("sections", []),
            "related_topics": list(framework_docs.keys())
        }
    
    def _get_framework_url(self, framework: str) -> str:
        """Get base URL for framework documentation"""
        urls = {
            "fastapi": "https://fastapi.tiangolo.com/",
            "flask": "https://flask.palletsprojects.com/",
            "django": "https://docs.djangoproject.com/",
            "express": "https://expressjs.com/",
            "react": "https://reactjs.org/docs/",
            "vue": "https://vuejs.org/guide/"
        }
        return urls.get(framework, f"https://www.google.com/search?q={framework}+documentation")
