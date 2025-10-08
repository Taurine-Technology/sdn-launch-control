# File: tasks.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def save_classification_statistics():
    """
    Periodic task to save classification statistics to database.
    This task runs every 5 minutes to persist accumulated stats.
    """
    from .model_manager import model_manager
    
    try:
        result = model_manager.save_classification_stats()
        if result:
            logger.info("Successfully saved classification statistics")
            return "Classification statistics saved successfully"
        else:
            logger.debug("No classification statistics to save")
            return "No statistics to save"
    except Exception as e:
        logger.error(f"Error in save_classification_statistics task: {e}")
        return f"Error: {e}"

