from fastapi import APIRouter, File, UploadFile, HTTPException
from abc import ABC, abstractmethod

class BaseModel(ABC):
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()
        self.load_model()

    @abstractmethod
    def load_model(self):
        pass

    @abstractmethod
    async def predict(self, file: UploadFile):
        pass

    def setup_routes(self):
        self.router.add_api_route(
            "/predict",
            self.predict,
            methods=["POST"]
        )
