import motor.motor_asyncio
from beanie import init_beanie

from config import BaseConfig
from models import Car, User

settings = BaseConfig()
print(settings.DB_URL)


async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.DB_URL)
    await init_beanie(database=client.carAds, document_models=[User, Car])
