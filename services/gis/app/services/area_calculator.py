"""Area calculation service for GeoJSON polygons."""

from typing import Any

from pyproj import Geod
from shapely import wkt
from shapely.geometry import Polygon, shape
from shapely.validation import explain_validity

from app.schemas.geo import AreaCalculationResult, PolygonValidationResult


# WGS84 ellipsoid for accurate geodetic calculations
GEOD = Geod(ellps="WGS84")

# Conversion factors
SQMETERS_TO_ACRES = 0.000247105
SQMETERS_TO_HECTARES = 0.0001


class AreaCalculator:
    """Service for calculating areas from GeoJSON polygons."""

    def validate_polygon(self, geojson: dict[str, Any]) -> PolygonValidationResult:
        """Validate a GeoJSON polygon geometry.

        Args:
            geojson: GeoJSON geometry object (Polygon type)

        Returns:
            PolygonValidationResult with validation details
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check geometry type
        geom_type = geojson.get("type")
        if geom_type not in ("Polygon", "MultiPolygon"):
            errors.append(f"Invalid geometry type: {geom_type}. Expected Polygon or MultiPolygon.")
            return PolygonValidationResult(
                is_valid=False,
                errors=errors,
                vertex_count=0,
                is_closed=False,
                has_self_intersection=False,
            )

        try:
            geom = shape(geojson)
        except Exception as e:
            errors.append(f"Failed to parse GeoJSON: {str(e)}")
            return PolygonValidationResult(
                is_valid=False,
                errors=errors,
                vertex_count=0,
                is_closed=False,
                has_self_intersection=False,
            )

        # Check if geometry is valid
        if not geom.is_valid:
            reason = explain_validity(geom)
            errors.append(f"Invalid geometry: {reason}")

        # Check for self-intersection
        has_self_intersection = not geom.is_simple

        # Get vertex count
        if isinstance(geom, Polygon):
            vertex_count = len(geom.exterior.coords)
            is_closed = geom.exterior.coords[0] == geom.exterior.coords[-1]
        else:
            vertex_count = sum(len(p.exterior.coords) for p in geom.geoms)
            is_closed = all(p.exterior.coords[0] == p.exterior.coords[-1] for p in geom.geoms)

        # Warnings for potentially problematic polygons
        if vertex_count < 4:
            warnings.append("Polygon has fewer than 4 vertices (minimum for a valid polygon)")

        if vertex_count > 1000:
            warnings.append(f"Polygon has {vertex_count} vertices. Consider simplifying for better performance.")

        # Check for small area (might be an error)
        try:
            area = self._calculate_geodetic_area(geom)
            if area < 100:  # Less than 100 square meters
                warnings.append("Polygon area is very small (< 100 sq meters). Please verify coordinates.")
        except Exception:
            pass

        return PolygonValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            vertex_count=vertex_count,
            is_closed=is_closed,
            has_self_intersection=has_self_intersection,
        )

    def calculate_area(
        self,
        geojson: dict[str, Any],
        validate: bool = True,
    ) -> AreaCalculationResult:
        """Calculate area from GeoJSON polygon.

        Uses geodetic calculations for accurate results on Earth's surface.

        Args:
            geojson: GeoJSON geometry object
            validate: Whether to validate the polygon first

        Returns:
            AreaCalculationResult with area in multiple units
        """
        if validate:
            validation = self.validate_polygon(geojson)
            if not validation.is_valid:
                return AreaCalculationResult(
                    area_acres=0,
                    area_hectares=0,
                    area_square_meters=0,
                    perimeter_meters=0,
                    is_valid=False,
                    message="; ".join(validation.errors),
                )

        try:
            geom = shape(geojson)
            area_sqm = self._calculate_geodetic_area(geom)
            perimeter_m = self._calculate_geodetic_perimeter(geom)

            return AreaCalculationResult(
                area_acres=area_sqm * SQMETERS_TO_ACRES,
                area_hectares=area_sqm * SQMETERS_TO_HECTARES,
                area_square_meters=area_sqm,
                perimeter_meters=perimeter_m,
                is_valid=True,
            )
        except Exception as e:
            return AreaCalculationResult(
                area_acres=0,
                area_hectares=0,
                area_square_meters=0,
                perimeter_meters=0,
                is_valid=False,
                message=f"Failed to calculate area: {str(e)}",
            )

    def simplify_polygon(
        self,
        geojson: dict[str, Any],
        tolerance: float = 0.0001,
    ) -> dict[str, Any]:
        """Simplify a polygon to reduce vertex count.

        Args:
            geojson: GeoJSON geometry object
            tolerance: Simplification tolerance in degrees (default 0.0001 ~ 10m)

        Returns:
            Simplified GeoJSON geometry
        """
        geom = shape(geojson)
        simplified = geom.simplify(tolerance, preserve_topology=True)

        # Convert back to GeoJSON dict
        from shapely.geometry import mapping

        return dict(mapping(simplified))

    def _calculate_geodetic_area(self, geom: Polygon) -> float:
        """Calculate geodetic area using pyproj.

        Args:
            geom: Shapely geometry

        Returns:
            Area in square meters
        """
        if isinstance(geom, Polygon):
            # Get coordinates (lon, lat order for pyproj)
            coords = list(geom.exterior.coords)
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]

            # Calculate geodetic area
            area, _ = GEOD.polygon_area_perimeter(lons, lats)
            return abs(area)
        else:
            # MultiPolygon
            return sum(self._calculate_geodetic_area(p) for p in geom.geoms)

    def _calculate_geodetic_perimeter(self, geom: Polygon) -> float:
        """Calculate geodetic perimeter using pyproj.

        Args:
            geom: Shapely geometry

        Returns:
            Perimeter in meters
        """
        if isinstance(geom, Polygon):
            coords = list(geom.exterior.coords)
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]

            _, perimeter = GEOD.polygon_area_perimeter(lons, lats)
            return abs(perimeter)
        else:
            return sum(self._calculate_geodetic_perimeter(p) for p in geom.geoms)


# Singleton instance
area_calculator = AreaCalculator()
