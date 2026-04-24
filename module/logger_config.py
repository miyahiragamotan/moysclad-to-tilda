import os
import logging
import datetime


class LoggerConfig:
    def __init__(self, log_dir: str = 'logs/logs-stock'):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def get_logger(self, name: str | None = None) -> logging.Logger:
        """Создаёт и возвращает изолированный логгер"""
        logger = logging.getLogger(name or __name__)
        logger.setLevel(logging.INFO)

        # Проверяем, чтобы не добавлять дубликаты обработчиков
        if not logger.handlers:
            log_file = os.path.join(
                self.log_dir,
                datetime.datetime.now().strftime('%Y-%m-%d') + '.txt'
            )

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            stream_handler = logging.StreamHandler()

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            stream_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)

        return logger
