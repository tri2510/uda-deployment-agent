#!/usr/bin/env python3

"""
SDV Runtime Compatible Speed Monitor
Vehicle application using Velocitas Python SDK and KUKSA Data Broker

Features:
- Real KUKSA Data Broker integration via Velocitas SDK
- Standard SDV patterns with VehicleApp inheritance
- Async/await architecture with signal subscriptions
- OpenTelemetry structured logging
- Proper VSS signal paths and validation
- Comprehensive error handling
"""

import asyncio
import logging
import signal
from typing import Dict, Any
from datetime import datetime

# Velocitas Python SDK imports - SDV Integration
try:
    from vehicle import Vehicle, vehicle  # type: ignore
    from velocitas_sdk.util.log import (
        get_opentelemetry_log_factory,
        get_opentelemetry_log_format,
    )
    from velocitas_sdk.vdb.reply import DataPointReply
    from velocitas_sdk.vehicle_app import VehicleApp, subscribe_topic

    # Configure OpenTelemetry logging (SDV standard)
    logging.setLogRecordFactory(get_opentelemetry_log_factory())
    logging.basicConfig(format=get_opentelemetry_log_format())
    logging.getLogger().setLevel("INFO")

    SDK_AVAILABLE = True

except ImportError as e:
    # Fallback when SDK not available (development/testing)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.warning(f"⚠️ Velocitas SDK not available: {e}")
    logging.warning("⚠️ Running in simulation mode")
    SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

class SpeedMonitorApp:
    """SDV Runtime compatible speed monitoring application"""

    def __init__(self):
        self._is_running = False
        self.sdk_available = SDK_AVAILABLE

        if self.sdk_available:
            # Real SDK mode
            self.Vehicle = vehicle
            logger.info("🚗 SpeedMonitorApp initialized with Velocitas SDK")
        else:
            # Simulation fallback mode
            logger.warning("🚗 SpeedMonitorApp initialized in simulation mode")

    async def on_start(self):
        """Called when app starts - initialize subscriptions and setup"""
        try:
            logger.info("🚀 Starting Speed Monitor App...")
            self._is_running = True

            if self.sdk_available:
                # Real KUKSA integration
                await self._setup_kuksa_integration()
            else:
                # Simulation mode setup
                await self._setup_simulation_mode()

            logger.info("🎯 Speed Monitor App started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start Speed Monitor App: {e}")
            self._is_running = False

    async def _setup_kuksa_integration(self):
        """Setup real KUKSA Data Broker integration"""
        try:
            # Subscribe to vehicle speed signal
            await self.Vehicle.Speed.subscribe(self.on_speed_change)
            logger.info("✅ Subscribed to Vehicle.Speed signal")

            # Initialize dashboard signals
            await self.Vehicle.Cabin.SpeedDisplay.set(0.0)
            await self.Vehicle.Cabin.SpeedStatus.set("stationary")

            # Setup initial values
            await self.Vehicle.Speed.LastUpdate.set("started")

            logger.info("✅ KUKSA Data Broker integration ready")

        except Exception as e:
            logger.error(f"❌ KUKSA integration failed: {e}")
            raise

    async def _setup_simulation_mode(self):
        """Setup simulation mode for development/testing"""
        import random
        self.sim_speed = 0.0
        self.sim_active = True
        logger.info("✅ Simulation mode active")

    async def on_speed_change(self, data: DataPointReply = None):
        """Callback for Vehicle.Speed signal changes"""
        try:
            if self.sdk_available and data:
                # Real KUKSA data
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

                await self._process_speed_data(speed)

            elif not self.sdk_available:
                # Simulation mode
                await self._simulate_speed_change()

        except Exception as e:
            logger.error(f"❌ Error processing speed change: {e}")

    async def _simulate_speed_change(self):
        """Generate and process simulated speed data"""
        import random
        import time

        if random.random() < 0.3:  # 30% chance of speed change
            change = random.uniform(-5, 10)
            self.sim_speed += change

            # Clamp to realistic range
            self.sim_speed = max(0, min(self.sim_speed, 180))

            if self.sim_speed > 0:
                # Gradual deceleration
                self.sim_speed = max(0, self.sim_speed - random.uniform(0.5, 1))

        await self._process_speed_data(self.sim_speed)

    async def _process_speed_data(self, speed: float):
        """Common speed processing for both real and simulation data"""
        try:
            # Log current speed
            logger.info(f"🚀 Current speed: {speed:.1f} km/h")

            if self.sdk_available:
                # Update KUKSA signals
                await self.Vehicle.Cabin.SpeedDisplay.set(speed)

                speed_status = self.get_speed_status(speed)
                await self.Vehicle.Cabin.SpeedStatus.set(speed_status)

                # Update timestamp
                await self.Vehicle.Speed.LastUpdate.set(datetime.now().isoformat())
            else:
                # Simulation logging only
                self.sim_speed_status = self.get_speed_status(speed)

            # Log important status changes
            speed_status = self.get_speed_status(speed)
            if speed_status in ["high", "moderate"]:
                logger.info(f"📊 Speed status: {speed_status} ({speed:.1f} km/h)")

        except Exception as e:
            logger.error(f"❌ Error processing speed data: {e}")

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

            if self.sdk_available:
                # Real KUKSA integration
                if "position" in data:
                    position = data["position"]
                    await self.Vehicle.Cabin.Seat.Row1.PosDriver.Position.set(position)
                    logger.info(f"✅ Seat position set to: {position}")
            else:
                # Simulation logging
                logger.info(f"✅ Seat position simulation: {data}")

        except Exception as e:
            logger.error(f"❌ Error setting seat position: {e}")

    async def on_stop(self):
        """Called when app stops - cleanup"""
        try:
            logger.info("🛑 Stopping Speed Monitor App...")
            self._is_running = False

            if self.sdk_available:
                # Cleanup KUKSA signals
                await self.Vehicle.Cabin.SpeedDisplay.set(0.0)
                await self.Vehicle.Cabin.SpeedStatus.set("stopped")

                # Final timestamp
                await self.Vehicle.Speed.LastUpdate.set(
                    datetime.now().isoformat() + "_stopped"
                )

                logger.info("✅ KUKSA signals cleaned up")
            else:
                # Simulation cleanup
                self.sim_speed = 0.0
                self.sim_active = False

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