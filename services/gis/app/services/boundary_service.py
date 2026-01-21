"""Boundary service for administrative location lookup."""

from typing import Any

from app.schemas.geo import AdminLocation
from app.services.geofence_service import geofence_service


class BoundaryService:
    """Service for administrative boundary operations.

    Note: This is a simplified implementation. In production, this would
    integrate with actual Kenya administrative boundary data (GeoJSON)
    or a geocoding service API.
    """

    # Kenya counties (simplified mapping for demonstration)
    # In production, this would use actual GeoJSON boundary files
    KENYA_COUNTIES = {
        "nairobi": {"name": "Nairobi", "code": "047"},
        "kiambu": {"name": "Kiambu", "code": "022"},
        "nakuru": {"name": "Nakuru", "code": "032"},
        "mombasa": {"name": "Mombasa", "code": "001"},
        "kisumu": {"name": "Kisumu", "code": "042"},
        "uasin_gishu": {"name": "Uasin Gishu", "code": "027"},
        "trans_nzoia": {"name": "Trans Nzoia", "code": "026"},
        "kakamega": {"name": "Kakamega", "code": "037"},
        "bungoma": {"name": "Bungoma", "code": "039"},
        "machakos": {"name": "Machakos", "code": "016"},
        "nyeri": {"name": "Nyeri", "code": "019"},
        "meru": {"name": "Meru", "code": "012"},
        "kajiado": {"name": "Kajiado", "code": "034"},
        "kilifi": {"name": "Kilifi", "code": "003"},
        "nyandarua": {"name": "Nyandarua", "code": "018"},
    }

    async def get_administrative_location(
        self,
        latitude: float,
        longitude: float,
    ) -> AdminLocation:
        """Reverse geocode coordinates to get administrative location.

        Args:
            latitude: Point latitude
            longitude: Point longitude

        Returns:
            AdminLocation with county, sub_county, ward
        """
        # First check if coordinates are in Kenya
        if not geofence_service.check_coordinates_in_kenya(latitude, longitude):
            return AdminLocation(
                is_valid=False,
                message="Coordinates are outside Kenya",
            )

        # In production, this would query actual boundary data
        # For now, return a placeholder based on approximate regions
        county, sub_county, ward = self._lookup_location(latitude, longitude)

        return AdminLocation(
            country="Kenya",
            county=county,
            sub_county=sub_county,
            ward=ward,
            is_valid=True,
        )

    def _lookup_location(
        self,
        latitude: float,
        longitude: float,
    ) -> tuple[str | None, str | None, str | None]:
        """Look up administrative location from coordinates.

        This is a simplified implementation using approximate coordinate ranges.
        In production, use proper point-in-polygon with actual boundary GeoJSON.

        Args:
            latitude: Point latitude
            longitude: Point longitude

        Returns:
            Tuple of (county, sub_county, ward)
        """
        # Nairobi approximate bounds
        if -1.4 <= latitude <= -1.15 and 36.65 <= longitude <= 37.1:
            return ("Nairobi", "Nairobi Central", None)

        # Kiambu approximate bounds
        if -1.3 <= latitude <= -0.8 and 36.5 <= longitude <= 37.2:
            return ("Kiambu", None, None)

        # Nakuru approximate bounds
        if -0.5 <= latitude <= 0.2 and 35.8 <= longitude <= 36.5:
            return ("Nakuru", None, None)

        # Mombasa approximate bounds
        if -4.2 <= latitude <= -3.9 and 39.5 <= longitude <= 39.8:
            return ("Mombasa", None, None)

        # Kisumu approximate bounds
        if -0.2 <= latitude <= 0.15 and 34.5 <= longitude <= 35.0:
            return ("Kisumu", None, None)

        # Uasin Gishu (Eldoret area)
        if 0.3 <= latitude <= 0.7 and 35.0 <= longitude <= 35.5:
            return ("Uasin Gishu", "Eldoret East", None)

        # Trans Nzoia (Kitale area)
        if 0.8 <= latitude <= 1.2 and 34.8 <= longitude <= 35.2:
            return ("Trans Nzoia", "Kitale", None)

        # Kakamega
        if 0.0 <= latitude <= 0.5 and 34.5 <= longitude <= 35.0:
            return ("Kakamega", None, None)

        # Meru
        if -0.2 <= latitude <= 0.4 and 37.5 <= longitude <= 38.2:
            return ("Meru", None, None)

        # Machakos
        if -1.8 <= latitude <= -1.2 and 37.0 <= longitude <= 37.8:
            return ("Machakos", None, None)

        # Kajiado
        if -2.5 <= latitude <= -1.5 and 36.5 <= longitude <= 37.5:
            return ("Kajiado", None, None)

        # Default: Unknown within Kenya
        return (None, None, None)

    async def validate_coordinates_in_kenya(
        self,
        latitude: float,
        longitude: float,
    ) -> bool:
        """Check if coordinates are within Kenya boundaries.

        Args:
            latitude: Point latitude
            longitude: Point longitude

        Returns:
            True if coordinates are in Kenya
        """
        return geofence_service.check_coordinates_in_kenya(latitude, longitude)


# Singleton instance
boundary_service = BoundaryService()
