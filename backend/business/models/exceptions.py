class BusinessError(Exception):
    """业务层异常基类"""
    def __init__(self, message: str):
        self.message = message

class ConfigFileNotFoundError(BusinessError):
    """配置文件未找到"""
    pass

class DatabaseNotFoundError(BusinessError):
    pass

class NoDataFoundError(BusinessError):
    pass

class MajorNotFoundError(BusinessError):
    """专业不存在"""
    pass