"""
Function Helper Functions
"""

import asyncio
import logging
import secrets

from prisma.enums import FunctionState
from prisma.models import Function, ObjectType
from prisma.types import FunctionCreateInput, ObjectFieldCreateInput

from codex.common.model import (
    FunctionDef,
    ObjectFieldModel,
    ObjectTypeModel,
    create_object_type,
    get_related_types,
    normalize_type,
)

logger = logging.getLogger(__name__)


async def construct_function(
    function: FunctionDef,
    available_types: dict[str, ObjectType],
    import_statements: list[str] | None = None,
) -> FunctionCreateInput:
    if not function.function_template:
        raise ValueError("Function template is required")

    input = FunctionCreateInput(
        functionName=function.name,
        template=function.function_template or "",
        description=function.function_desc,
        state=FunctionState.WRITTEN
        if function.is_implemented
        else FunctionState.DEFINITION,
        rawCode=function.function_code,
        functionCode=function.function_code,
        importStatements=import_statements or [],
    )

    if function.return_type:
        field = ObjectFieldCreateInput(
            name="return",
            description=function.return_desc,
            typeName=normalize_type(function.return_type),
            RelatedTypes={
                "connect": [
                    {"id": type.id}
                    for type in get_related_types(function.return_type, available_types)
                ]
            },
        )
        input["FunctionReturn"] = {"create": field}

    if function.arg_types:
        fields = [
            ObjectFieldCreateInput(
                name=name,
                description=function.arg_descs.get(name, "-"),
                typeName=normalize_type(type),
                RelatedTypes={
                    "connect": [
                        {"id": type.id}
                        for type in get_related_types(type, available_types)
                    ]
                },
            )
            for name, type in function.arg_types
        ]
        input["FunctionArgs"] = {"create": fields}  # type: ignore

    return input


def generate_object_code(obj: ObjectTypeModel) -> str:
    if not obj.name:
        return ""  # Avoid generating an empty object

    # Auto-generate a template for the object, this will not capture any class functions.
    fields = f"\n{' ' * 8}".join(
        [
            f"{field.name}: {field.type} "
            f"{('= '+field.value) if field.value else ''} "
            f"{('# '+field.description) if field.description else ''}"
            for field in obj.Fields or []
        ]
    )

    parent_class = ""
    if obj.is_enum:
        parent_class = "Enum"
    elif obj.is_pydantic:
        parent_class = "BaseModel"

    doc_string = (
        f"""\"\"\"
        {obj.description}
        \"\"\""""
        if obj.description
        else ""
    )

    method_body = ("\n" + " " * 8).join(obj.code.split("\n")) + "\n" if obj.code else ""

    template = f"""
    class {obj.name}({parent_class}):
        {doc_string if doc_string else ""}
        {fields if fields else ""}
        {method_body if method_body else ""}
        {"pass" if not fields and not method_body else ""}
    """
    return "\n".join([line[4:] for line in template.split("\n")]).strip()


def generate_object_template(obj: ObjectType) -> str:
    return generate_object_code(ObjectTypeModel(db_obj=obj))


async def create_auth_functions() -> list[Function]:
    function_defs: list[FunctionDef] = []
    secret_key_str = secrets.token_hex(32)

    # Verify Password
    # def verify_password(plain_password: str, hashed_password: str) -> bool:
    #     return pwd_context.verify(plain_password, hashed_password)
    verify_password = FunctionDef(
        name="verify_password",
        arg_types=[("plain_password", "str"), ("hashed_password", "str")],
        arg_descs={
            "plain_password": "The plain text password.",
            "hashed_password": "The hashed password.",
        },
        return_type="bool",
        return_desc="True if the password matches, False otherwise",
        is_implemented=True,
        function_desc="Verify the plain text password against the hashed password",
        function_code="return pwd_context.verify(plain_password, hashed_password)",
        function_template="""
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    \"\"\"
    Verify the plain text password against the hashed password

    Args:
    plain_password (str): The plain text password.
    hashed_password (str): The hashed password.

    Returns:
    bool: True if the password matches, False otherwise.
    \"\"\"
    return pwd_context.verify(plain_password, hashed_password)
        """,
    )
    function_defs.append(verify_password)

    # Get Password Hash
    # def get_password_hash(password):
    #     return pwd_context.hash(password)
    get_password_hash = FunctionDef(
        name="get_password_hash",
        arg_types=[("password", "str")],
        arg_descs={"password": "The password to hash."},
        return_type="str",
        return_desc="The hashed password.",
        is_implemented=True,
        function_desc="Hash the provided password.",
        function_code="return pwd_context.hash(password)",
        function_template="""
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    \"\"\"
    Hash the provided password.

    Args:
    password (str): The password to hash.

    Returns:
    str: The hashed password.
    \"\"\"
    return pwd_context.hash(password)
        """,
    )
    function_defs.append(get_password_hash)

    # Get User
    # def get_user(username: str)-> prisma.models.User | None:
    #     find the user in prisma db
    #     user = await prisma.models.User.prisma().find_unique(
    #       where={"username": username},
    #     )
    #    return user
    get_user = FunctionDef(
        name="get_user",
        arg_types=[("username", "str")],
        arg_descs={"username": "The username to find."},
        return_type="prisma.models.User | None",
        return_desc="The user if found, None otherwise.",
        is_implemented=True,
        function_desc="Find the user by username.",
        function_code="""
            user = await prisma.models.User.prisma().find_unique(
                where={"username": username},
            )
            return user
        """,
        function_template="""
async def get_user(username: str) -> prisma.models.User | None:
    \"\"\"
    Find the user by username.

    Args:
    username (str): The username to find.

    Returns:
    prisma.models.User | None: The user if found, None otherwise.
    \"\"\"
    user = await prisma.models.User.prisma().find_unique(
        where={"username": username},
    )
    return user
        """,
    )
    function_defs.append(get_user)

    # Authenticate User
    # async def authenticate_user(username: str, password: str):
    #     user = await get_user(username)
    #     if not user:
    #         return False
    #     if not verify_password(password, user.hashed_password):
    #         return False
    #     return user
    authenticate_user = FunctionDef(
        name="authenticate_user",
        arg_types=[("username", "str"), ("password", "str")],
        arg_descs={
            "username": "The username to authenticate.",
            "password": "The password to verify.",
        },
        return_type="prisma.models.User | None",
        return_desc="The user if authenticated, None otherwise.",
        is_implemented=True,
        function_desc="Authenticate the user by username and password.",
        function_code="""
            user = await get_user(username)
            if not user:
                return None
            if not verify_password(password, user.hashed_password):
                return None
            return user
        """,
        function_template="""
async def authenticate_user(username: str, password: str) -> prisma.models.User | None:
    \"\"\"
    Authenticate the user by username and password.

    Args:
    username (str): The username to authenticate.
    password (str): The password to verify.

    Returns:
    prisma.models.User | None: The user if authenticated, None otherwise.
    \"\"\"
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
        """,
    )
    function_defs.append(authenticate_user)

    # Create Access Token
    # def create_access_token(data: dict, expires_delta: timedelta | None = None):
    #     to_encode = data.copy()
    #     if expires_delta:
    #         expire = datetime.now(timezone.utc) + expires_delta
    #     else:
    #         expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    #     to_encode.update({"exp": expire})
    #     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    #     return encoded_jwt
    create_access_token = FunctionDef(
        name="create_access_token",
        arg_types=[("data", "dict"), ("expires_delta", "timedelta | None")],
        arg_descs={
            "data": "The data to encode.",
            "expires_delta": "The expiration time for the token.",
        },
        return_type="str",
        return_desc="The encoded JWT token.",
        is_implemented=True,
        function_desc="Create an access token.",
        function_code=f"""
            SECRET_KEY = "{secret_key_str}"
            ALGORITHM = "HS256"

            to_encode = data.copy()
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            to_encode.update({{"exp": expire}})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt
        """,
        function_template=f"""
SECRET_KEY = "{secret_key_str}"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    \"\"\"
    Create an access token.

    Args:
    data (dict): The data to encode.
    expires_delta (timedelta | None): The expiration time for the token.

    Returns:
    str: The encoded JWT token.
    \"\"\"
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({{"exp": expire}})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
        """,
    )
    function_defs.append(create_access_token)

    # Get Current User
    # async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    #     credentials_exception = HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Could not validate credentials",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    #     try:
    #         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #         username: str = payload.get("sub")
    #         if username is None:
    #             raise credentials_exception
    #         token_data = TokenData(username=username)
    #     except JWTError:
    #         raise credentials_exception
    #     user = await get_user(username=token_data.username)
    #     if user is None:
    #         raise credentials_exception
    #     return user
    get_current_user = FunctionDef(
        name="get_current_user",
        arg_types=[("token", "Annotated[str, Depends(oauth2_scheme)]")],
        arg_descs={"token": "The token to validate."},
        return_type="prisma.models.User | None",
        return_desc="The current user if found, None otherwise.",
        is_implemented=True,
        function_desc="Get the current user from the token.",
        function_code=f"""
            SECRET_KEY = "{secret_key_str}"
            ALGORITHM = "HS256"

            oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={{"WWW-Authenticate": "Bearer"}},
            )
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username is None:
                    raise credentials_exception
                token_data = TokenData(username=username)
            except JWTError:
                raise credentials_exception
            user = await get_user(username=token_data.username)
            if user is None:
                raise credentials_exception
            return user
        """,
        function_template=f"""
SECRET_KEY = "{secret_key_str}"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> prisma.models.User | None:
    \"\"\"
    Get the current user from the token.

    Args:
    token (str): The token to validate.

    Returns:
    prisma.models.User | None: The current user if found, None otherwise.
    \"\"\"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={{"WWW-Authenticate": "Bearer"}},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
        """,
    )
    function_defs.append(get_current_user)

    # Get Current Active User
    # async def get_current_active_user(
    #     current_user: Annotated[User, Depends(get_current_user)],
    # ):
    #     if current_user.disabled:
    #         raise HTTPException(status_code=400, detail="Inactive user")
    #     return current_user
    get_current_active_user = FunctionDef(
        name="get_current_active_user",
        arg_types=[
            ("current_user", "Annotated[prisma.models.User, Depends(get_current_user)]")
        ],
        arg_descs={"current_user": "The current user."},
        return_type="User",
        return_desc="The active user.",
        is_implemented=True,
        function_desc="Get the current active user.",
        function_code="""
            if current_user.disabled:
                raise HTTPException(status_code=400, detail="Inactive user")
            return current_user
        """,
        function_template="""
async def get_current_active_user(current_user: Annotated[prisma.models.User, Depends(get_current_user)]) -> User:
    \"\"\"
    Get the current active user.

    Args:
    current_user (User): The current user.

    Returns:
    User: The active user.
    \"\"\"
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
        """,
    )
    function_defs.append(get_current_active_user)

    # Make Access Token
    # @app.post("/token")
    # async def login_for_access_token(
    #     form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    # ) -> Token:
    #     user = await authenticate_user(form_data.username, form_data.password)
    #     if not user:
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Incorrect username or password",
    #             headers={"WWW-Authenticate": "Bearer"},
    #         )
    #     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    #     access_token = create_access_token(
    #         data={"sub": user.username}, expires_delta=access_token_expires
    #     )
    #     return Token(access_token=access_token, token_type="bearer")
    login_for_access_token = FunctionDef(
        name="login_for_access_token",
        arg_types=[("form_data", "Annotated[OAuth2PasswordRequestForm, Depends()]")],
        arg_descs={"form_data": "The form data."},
        return_type="Token",
        return_desc="The access token.",
        is_implemented=True,
        function_desc="Login for an access token.",
        function_code="""
            ACCESS_TOKEN_EXPIRE_MINUTES = 30

            user = await authenticate_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )
            return Token(access_token=access_token, token_type="bearer")
        """,
        function_template="""
ACCESS_TOKEN_EXPIRE_MINUTES = 30

async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    \"\"\"
    Login for an access token.

    Args:
    form_data (Annotated[OAuth2PasswordRequestForm, Depends()]): The form data.

    Returns:
    Token: The access token.
    \"\"\"
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
        """,
    )
    function_defs.append(login_for_access_token)

    # class Token(BaseModel):
    #     access_token: str
    #     token_type: str

    # class TokenData(BaseModel):
    #     username: str | None = None
    available_objects = await create_object_type(
        object=ObjectTypeModel(
            name="Token",
            description="The access token.",
            is_pydantic=True,
            Fields=[
                ObjectFieldModel(
                    name="access_token",
                    description="The access token.",
                    type="str",
                ),
                ObjectFieldModel(
                    name="token_type",
                    description="The token type.",
                    type="str",
                ),
            ],
        ),
        available_objects={},
    )
    available_objects = await create_object_type(
        object=ObjectTypeModel(
            name="TokenData",
            description="The token data.",
            is_pydantic=True,
            Fields=[
                ObjectFieldModel(
                    name="username",
                    description="The username.",
                    type="str | None",
                    value="None",
                ),
            ],
        ),
        available_objects=available_objects,
    )

    imports = [
        "from datetime import datetime, timedelta, timezone",
        "from typing import Annotated",
        "from fastapi import Depends, FastAPI, HTTPException, status",
        "from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm",
        "from jose import JWTError, jwt",
        "from passlib.context import CryptContext",
        "from pydantic import BaseModel",
    ]

    create_ops = [
        construct_function(
            function=function,
            available_types=available_objects,
            import_statements=imports,
        )
        for function in function_defs
    ]
    # await all functions to be created
    create_params = await asyncio.gather(*create_ops)
    creations = [
        Function.prisma().create(create_param) for create_param in create_params
    ]
    created: list[Function] = await asyncio.gather(*creations)
    return created
