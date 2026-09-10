from fastapi import HTTPException


class NotFoundError(HTTPException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(status_code=404, detail=f"{resource} '{identifier}' not found")


class ValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=400, detail=message)
