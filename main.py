"""
Marvel Trading Dashboard - Main Entry Point
Production-grade MT5 multi-account hedge recovery system
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.dashboard import main as launch_dashboard
from app.utils.logger import get_logger


def main():
    """Launch Marvel Trading Dashboard"""
    logger = get_logger()
    
    try:
        logger.info("=" * 60)
        logger.info("MARVEL TRADING DASHBOARD v1.0.0")
        logger.info("Multi-Account Hedge Recovery System")
        logger.info("=" * 60)
        
        # Launch UI
        launch_dashboard()
        
    except Exception as e:
        logger.log_error(e, "Critical startup error")
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
