class AppError(Exception):
    def __init__(self, code: str, message: str, http_status: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status

class AgentError(AppError):
    def __init__(self, message: str):
        super().__init__("Error", message, 500)

class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__("Error",message, 400)