import logging
import sys
from typing import Optional


def configure_logging(
    level: str = "INFO",
    format_string: Optional[str] = None
) -> None:
    """
    配置根日志记录器，使所有子记录器继承配置

    Args:
        level: 日志级别
        format_string: 日志格式
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        format_string or
        '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)