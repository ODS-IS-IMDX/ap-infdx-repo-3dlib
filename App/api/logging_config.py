# © 2025 NTT DATA Japan Co., Ltd. & NTT InfraNet All Rights Reserved.

import logging

def setup_logging(default_level=logging.INFO):
    # 全体のロガー設定
    logging.basicConfig(
        level=default_level,  # デフォルトのログレベルを設定
        format='[infra-dx-app] %(asctime)s - %(levelname)s - %(message)s'
    )

    # 必要なロガーを一括で設定する関数
    def set_logger_level(logger_name, level):
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        if not logger.handlers:
            logger.addHandler(logging.StreamHandler())
        logger.handlers[0].setFormatter(logging.Formatter('[infra-dx-app] %(asctime)s - %(levelname)s - %(message)s'))

    # uvicorn, uvicorn.access, fastapiのロガーも一括で設定
    set_logger_level("uvicorn", default_level)
    set_logger_level("uvicorn.access", default_level)
    set_logger_level("fastapi", default_level)
    set_logger_level("", default_level)  # デフォルトロガーの設定も一括


