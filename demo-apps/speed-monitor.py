#!/usr/bin/env python3

"""
SDV Runtime Compatible Speed Monitor
Standard vehicle application following Velocitas Python SDK patterns

Features:
- Velocitas VehicleApp inheritance
- Async/await patterns
- Signal subscription architecture
- Structured logging with OpenTelemetry
- Proper VSS signal paths
- Error handling and graceful shutdown
"""

import asyncio
import logging
import signal
from typing import Dict, Any

# Velocitas Python SDK imports
from vehicle import Vehicle, vehicle  # type: ignore
from velocitas_sdk.util.log import (
    get_opentelemetry_log_factory,
    get_opentelemetry_log_format,
)
from velocitas_sdk.vdb.reply import DataPointReply
from velocitas_sdk.vehicle_app import VehicleApp, subscribe_topic

# Configure structured logging
logging.setLogRecordFactory(get_opentelemetry_log_factory())
logging.basicConfig(format=get_opentelemetry_log_format())
logging.getLogger().setLevel("INFO")
logger = logging.getLogger(__name__)

class SpeedMonitorApp(VehicleApp):
    """SDV Runtime compatible speed monitoring application"""

    def __init__(self, vehicle_client: Vehicle):
        super().__init__()
        self.Vehicle = vehicle_client
        self._is_running = False

        logger.info("🚗 SpeedMonitorApp initialized")

    async def on_start(self):
        """Called when app starts - initialize subscriptions and setup"""
        try:
            logger.info("🚀 Starting Speed Monitor App...")
            self._is_running = True

            # Subscribe to vehicle speed signal
            await self.Vehicle.Speed.subscribe(self.on_speed_change)
            logger.info("✅ Subscribed to Vehicle.Speed signal")

            # Initialize dashboard signals
            await self.Vehicle.Cabin.SpeedDisplay.set(0.0)
            await self.Vehicle.Cabin.SpeedStatus.set("stationary")

            # Setup initial values
            await self.Vehicle.Speed.LastUpdate.set("started")

            logger.info("🎯 Speed Monitor App started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start Speed Monitor App: {e}")
            self._is_running = False

    async def on_speed_change(self, data: DataPointReply):
        """Callback for Vehicle.Speed signal changes"""
        try:
            speed = data.get(self.Vehicle.Speed).value

            # Validate speed data
            if speed is None:
                logger.warning("⚠️ Received None speed value")
                return

            if not isinstance(speed, (int, float)):
                logger.warning(f"⚠️ Invalid speed type: {type(speed)}")
                return

            # Clamp to realistic range
            speed = max(0, min(speed, 300))  # Max 300 km/h

            # Log current speed
            logger.info(f"🚀 Current speed: {speed:.1f} km/h")

            # Update dashboard display
            await self.Vehicle.Cabin.SpeedDisplay.set(speed)

            # Determine speed status
            speed_status = self.get_speed_status(speed)
            await self.Vehicle.Cabin.SpeedStatus.set(speed_status)

            # Update timestamp
            from datetime import datetime
            await self.Vehicle.Speed.LastUpdate.set(datetime.now().isoformat())

            # Log speed status change
            if speed_status in ["high", "moderate"]:
                logger.info(f"📊 Speed status: {speed_status} ({speed:.1f} km/h)")

        except Exception as e:
            logger.error(f"❌ Error processing speed change: {e}")

    def get_speed_status(self, speed: float) -> str:
        """Determine speed status based on speed value"""
        if speed > 120:
            return "high"
        elif speed > 80:
            return "moderate"
        elif speed > 10:
            return "normal"
        elif speed > 0.1:
            return "low"
        else:
            return "stationary"

    @subscribe_topic("seatadjuster/setPosition")
    async def on_set_position(self, data: Dict[str, Any]) -> None:
        """Example MQTT topic subscription - seat adjustment commands"""
        try:
            logger.info(f"🪑 Received seat adjustment: {data}")

            # Process seat adjustment (example)
            if "position" in data:
                position = data["position"]
                await self.Vehicle.Cabin.Seat.Row1.PosDriver.Position.set(position)
                logger.info(f"✅ Seat position set to: {position}")

        except Exception as e:
            logger.error(f"❌ Error setting seat position: {e}")

    async def on_stop(self):
        """Called when app stops - cleanup"""
        try:
            logger.info("🛑 Stopping Speed Monitor App...")
            self._is_running = False

            # Cleanup dashboard signals
            await self.Vehicle.Cabin.SpeedDisplay.set(0.0)
            await self.Vehicle.Cabin.SpeedStatus.set("stopped")

            # Final timestamp
            from datetime import datetime
            await self.Vehicle.Speed.LastUpdate.set(datetime.now().isoformat() + "_stopped")

            logger.info("✅ Speed Monitor App stopped gracefully")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

    def is_running(self) -> bool:
        """Check if app is currently running"""
        return self._is_running

async def main():
    """Main application entry point"""
    logger.info("🎯 Initializing Speed Monitor Application...")

    try:
        # Create vehicle app instance
        speed_monitor_app = SpeedMonitorApp(vehicle)

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, shutting down...")
            speed_monitor_app.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Run the vehicle app
        await speed_monitor_app.run()

    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        raise
    finally:
        logger.info("🏁 Speed Monitor Application terminated")

if __name__ == "__main__":
    # Create asyncio event loop
    loop = asyncio.get_event_loop()

    # Set up signal handling
    loop.add_signal_handler(signal.SIGTERM, loop.stop)
    loop.add_signal_handler(signal.SIGINT, loop.stop)

    try:
        # Run the main async function
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        loop.stop()
    finally:
        # Clean up
        loop.close()
        logger.info("🔚 Event loop closed")