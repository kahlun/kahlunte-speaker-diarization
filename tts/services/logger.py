"""
 Copyright (C) 2021 Intel Corporation
 SPDX-License-Identifier: BSD-3-Clause
"""

import os
import logging


def get_logger():
    import logging

    level = logging.DEBUG

    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)-20s ] - %(message)s",
        level=level,
    )
    logging.root.setLevel(level)
    logger = logging.getLogger()
    logger.setLevel(level)
    return logger
