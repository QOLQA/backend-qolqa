"""
User repository for MongoDB
Handles CRUD operations for users
"""
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from models.user import UserInDB, UserCreate, UserUpdate
from auth.password import get_password_hash
from interfaces.repository import Repository
from utils.errors import Duplicate, Missing
from utils.mongo import get_object_id


class UserRepository(Repository[UserInDB, UserCreate, UserUpdate]):
    """Repository for user CRUD operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database['users']
    
    async def get_by_id(self, user_id: str | ObjectId) -> UserInDB:
        """Get user by ID"""
        object_id = await get_object_id(user_id)
        user_data = await self.collection.find_one({'_id': object_id})
        
        if not user_data:
            raise Missing(msg=f'User with id {user_id} not found')
        
        return UserInDB(**user_data)
    
    async def get_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        user_data = await self.collection.find_one({'username': username.lower()})
        
        if not user_data:
            return None
        
        return UserInDB(**user_data)
    
    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        user_data = await self.collection.find_one({'email': email.lower()})
        
        if not user_data:
            return None
        
        return UserInDB(**user_data)
    
    async def add(self, user_create: UserCreate) -> UserInDB:
        """Create a new user"""
        # Check if username already exists
        existing_user = await self.get_by_username(user_create.username)
        if existing_user:
            raise Duplicate(msg=f'Username {user_create.username} already exists')
        
        # Check if email already exists
        existing_email = await self.get_by_email(user_create.email)
        if existing_email:
            raise Duplicate(msg=f'Email {user_create.email} already exists')
        
        # Hash password
        hashed_password = get_password_hash(user_create.password)
        
        # Create user document
        user_dict = user_create.model_dump(exclude={'password'})
        user_dict['hashed_password'] = hashed_password
        user_dict['username'] = user_dict['username'].lower()
        user_dict['email'] = user_dict['email'].lower()
        
        # Insert into database
        result = await self.collection.insert_one(user_dict)
        
        # Return created user
        return await self.get_by_id(result.inserted_id)
    
    async def get_all(self) -> List[UserInDB]:
        """Get all users"""
        cursor = self.collection.find({})
        users = await cursor.to_list(length=None)
        return [UserInDB(**u) for u in users]

    async def update(self, user_id: str | ObjectId, update_data: dict) -> UserInDB:
        """Update user information"""
        object_id = await get_object_id(user_id)
        
        # Verify user exists
        await self.get_by_id(object_id)
        
        # Update user
        await self.collection.update_one(
            {'_id': object_id},
            {'$set': update_data}
        )
        
        return await self.get_by_id(object_id)
    
    async def delete(self, user_id: str | ObjectId) -> None:
        """Delete a user"""
        object_id = await get_object_id(user_id)
        
        # Verify user exists
        await self.get_by_id(object_id)
        
        # Delete user
        await self.collection.delete_one({'_id': object_id})
