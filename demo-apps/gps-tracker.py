#!/usr/bin/env python3

"""
SDV Runtime Compatible GPS Tracker
Standard vehicle application following Velocitas Python SDK patterns

Features:
- Velocitas VehicleApp inheritance
- Async/await patterns
- Signal subscription architecture
- Structured logging with OpenTelemetry
- Proper VSS signal paths
- GPS distance and speed calculations
- MQTT topic subscriptions
"""

import asyncio
import logging
import signal
import math
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

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

class GPSTrackerApp(VehicleApp):
    """SDV Runtime compatible GPS tracking application"""

    def __init__(self, vehicle_client: Vehicle):
        super().__init__()
        self.Vehicle = vehicle_client
        self._is_running = False
        self._last_location: Optional[Tuple[float, float, datetime]] = None
        self._last_time: Optional[datetime] = None

        logger.info("🛰️ GPSTrackerApp initialized")

    async def on_start(self):
        """Called when app starts - initialize subscriptions and setup"""
        try:
            logger.info("🚀 Starting GPS Tracker App...")
            self._is_running = True

            # Subscribe to GPS signals
            await self.Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Latitude.subscribe(
                self.on_gps_change
            )
            logger.info("✅ Subscribed to GPS Latitude signal")

            await self.Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Longitude.subscribe(
                self.on_gps_change
            )
            logger.info("✅ Subscribed to GPS Longitude signal")

            # Initialize status signals
            await self.Vehicle.Cabin.LocationStatus.set("initializing")
            await self.Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Altitude.set(50.0)
            await self.Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Accuracy.set(5.0)

            # Start periodic location update task
            asyncio.create_task(self.location_update_loop())

            logger.info("🎯 GPS Tracker App started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start GPS Tracker App: {e}")
            self._is_running = False

    async def on_gps_change(self, data: DataPointReply):
        """Callback for GPS location signal changes"""
        try:
            current_time = datetime.now()

            # Get current location data
            lat_reply = await self.Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Latitude.get()
            lon_reply = await self.Vehicle.Cabin.Infotainment.Navigation.CurrentLocation.Longitude.get()

            if lat_reply is None or lon_reply is None:
                logger.warning("⚠️ Incomplete GPS data received")
                return

            lat = lat_reply.value
            lon = lon_reply.value

            # Validate GPS coordinates
            if lat is None or lon is None:
                logger.warning("⚠️ Invalid GPS coordinates: None values")
                return

            # Validate coordinate ranges
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.warning(f"⚠️ Invalid GPS coordinates: lat={lat}, lon={lon}")
                return

            # Log current location
            logger.info(f"📍 Location: {lat:.6f}, {lon:.6f}")

            # Calculate speed from GPS if we have previous location
            speed = self.calculate_gps_speed(lat, lon, current_time)
            if speed is not None:
                await self.Vehicle.Speed.GPS.set(speed)
                logger.info(f"🚀 GPS Speed: {speed:.1f} km/h")

            # Update location status
            location_status = self.get_location_status(speed)
            await self.Vehicle.Cabin.LocationStatus.set(location_status)

            # Update timestamp
            await self.Vehicle.Cabin.Infotainment.Navigation.LastUpdate.set(current_time.isoformat())

            # Store for next iteration
            self._last_location = (lat, lon, current_time)
            self._last_time = current_time

        except Exception as e:
            logger.error(f"❌ Error processing GPS change: {e}")

    async def location_update_loop(self):
        """Periodic task to update location status and provide fallback"""
        while self._is_running:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds

                # Check if we have recent GPS data
                if self._last_time:
                    time_diff = (datetime.now() - self._last_time).total_seconds()
                    if time_diff > 30:  # No GPS data for 30 seconds
                        logger.warning("⚠️ GPS data timeout")
                        await self.Vehicle.Cabin.LocationStatus.set("no_signal")

                # Update periodic status
                if self._last_location:
                    lat, lon, timestamp = self._last_location
                    logger.debug(f"📡 Last known location: {lat:.6f}, {lon:.6f}")

            except Exception as e:
                logger.error(f"❌ Error in location update loop: {e}")

    def calculate_gps_speed(self, lat: float, lon: float, current_time: datetime) -> Optional[float]:
        """Calculate speed based on GPS coordinates using Haversine formula"""
        if self._last_location is None or self._last_time is None:
            return None

        try:
            last_lat, last_lon, last_time = self._last_location

            # Calculate distance using Haversine formula
            distance_km = self.haversine_distance(last_lat, last_lon, lat, lon)

            # Calculate time difference in hours
            time_diff_hours = (current_time - last_time).total_seconds() / 3600.0

            if time_diff_hours > 0:
                speed_kmh = distance_km / time_diff_hours
                # Clamp to realistic range and apply smoothing
                return max(0, min(speed_kmh, 250))

        except Exception as e:
            logger.error(f"❌ Speed calculation error: {e}")

        return 0.0

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two GPS coordinates using Haversine formula"""
        R = 6371.0  # Earth's radius in kilometers

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_location_status(self, speed: Optional[float]) -> str:
        """Determine location status based on GPS speed and data"""
        if speed is None:
            return "unknown"
        elif speed > 1:
            return "moving"
        elif speed > 0.1:
            return "slow_moving"
        else:
            return "stationary"

    @subscribe_topic("navigation/setDestination")
    async def on_set_destination(self, data: Dict[str, Any]) -> None:
        """Example MQTT topic subscription - navigation commands"""
        try:
            logger.info(f"🧭 Received navigation command: {data}")

            # Process navigation destination
            if "latitude" in data and "longitude" in data:
                dest_lat = data["latitude"]
                dest_lon = data["longitude"]

                logger.info(f"🎯 Navigation destination set: {dest_lat:.6f}, {dest_lon:.6f}")

                # Set navigation signals
                await self.Vehicle.Cabin.Infotainment.Navigation.DestinationLatitude.set(dest_lat)
                await self.Vehicle.Cabin.Infotainment.Navigation.DestinationLongitude.set(dest_lon)

        except Exception as e:
            logger.error(f"❌ Error setting navigation destination: {e}")

    @subscribe_topic("location/requestUpdate")
    async def on_request_update(self, data: Dict[str, Any]) -> None:
        """Handle location update requests"""
        try:
            logger.info("📡 Received location update request")

            if self._last_location:
                lat, lon, timestamp = self._last_location

                # Send current location as response
                location_data = {
                    "latitude": lat,
                    "longitude": lon,
                    "timestamp": timestamp.isoformat(),
                    "status": await self.Vehicle.Cabin.LocationStatus.get()
                }

                logger.info(f"📍 Current location sent: {lat:.6f}, {lon:.6f}")

                # Publish location update (if needed)
                # await self.publish_message("location/update", location_data)

        except Exception as e:
            logger.error(f"❌ Error handling location update request: {e}")

    async def on_stop(self):
        """Called when app stops - cleanup"""
        try:
            logger.info("🛑 Stopping GPS Tracker App...")
            self._is_running = False

            # Update final status
            await self.Vehicle.Cabin.LocationStatus.set("stopped")

            # Final timestamp
            await self.Vehicle.Cabin.Infotainment.Navigation.LastUpdate.set(
                datetime.now().isoformat() + "_stopped"
            )

            logger.info("✅ GPS Tracker App stopped gracefully")

        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

    def is_running(self) -> bool:
        """Check if app is currently running"""
        return self._is_running

async def main():
    """Main application entry point"""
    logger.info("🎯 Initializing GPS Tracker Application...")

    try:
        # Create vehicle app instance
        gps_tracker_app = GPSTrackerApp(vehicle)

        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, shutting down...")
            gps_tracker_app.stop()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        # Run the vehicle app
        await gps_tracker_app.run()

    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        raise
    finally:
        logger.info("🏁 GPS Tracker Application terminated")

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