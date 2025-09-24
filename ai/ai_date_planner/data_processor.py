import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import os
from dataclasses import dataclass

@dataclass
class Location:
    """Data class to represent a unified location object"""
    id: str
    name: str
    location_type: str  # 'food', 'attraction', 'activity', 'heritage'
    coordinates: tuple  # (longitude, latitude)
    address: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DataProcessor:
    """Processes GeoJSON and KML files to create unified location objects"""
    
    def __init__(self, data_dir: str = "ai/ai_date_planner/data"):
        self.data_dir = data_dir
        self.locations: List[Location] = []
    
    def process_all_files(self) -> List[Location]:
        """Process all data files and return unified location list"""
        print("Starting data processing...")
        
        # Process each file type
        self._process_geojson("EatingEstablishments.geojson", "food")
        self._process_geojson("TouristAttractions.geojson", "attraction") 
        self._process_geojson("SportSGSportFacilitiesGEOJSON.geojson", "activity")
        self._process_kml("HeritageTrails.kml", "heritage")
        
        print(f"Processed {len(self.locations)} total locations")
        return self.locations
    
    def _process_geojson(self, filename: str, location_type: str):
        """Process a GeoJSON file and extract locations"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found")
            return
            
        print(f"Processing {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract features from GeoJSON
        features = data.get('features', [])
        processed_count = 0
        
        for feature in features:
            location = self._extract_geojson_location(feature, location_type)
            if location:
                self.locations.append(location)
                processed_count += 1
        
        print(f"  - Extracted {processed_count} {location_type} locations")
    
    def _extract_geojson_location(self, feature: Dict, location_type: str) -> Optional[Location]:
        """Extract location data from a GeoJSON feature"""
        try:
            # Get coordinates from geometry
            geometry = feature.get('geometry', {})
            coordinates = geometry.get('coordinates', [])
            
            if not coordinates:
                return None
            
            # Handle different geometry types
            if geometry.get('type') == 'Point':
                lon, lat = coordinates[0], coordinates[1]
            elif geometry.get('type') == 'Polygon':
                # Use centroid of polygon (first ring, first point)
                # Handle both 2D [lon, lat] and 3D [lon, lat, alt] coordinates
                first_point = coordinates[0][0]
                if len(first_point) >= 2:
                    lon, lat = first_point[0], first_point[1]
                else:
                    return None
            else:
                return None
            
            # Extract properties
            properties = feature.get('properties', {})
            
            # Try to get name from different possible fields
            name = self._extract_name(properties)
            if not name:
                return None
            
            # Create unique ID
            location_id = f"{location_type}_{len(self.locations)}_{hash(name) % 10000}"
            
            # Extract address and description
            address = self._extract_address(properties)
            description = self._extract_description(properties, location_type)
            
            return Location(
                id=location_id,
                name=name,
                location_type=location_type,
                coordinates=(lon, lat),
                address=address,
                description=description,
                metadata=properties
            )
            
        except Exception as e:
            print(f"Error processing feature: {e}")
            return None
    
    def _process_kml(self, filename: str, location_type: str):
        """Process a KML file and extract locations"""
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found")
            return
            
        print(f"Processing {filename}...")
        
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # KML namespace
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            # Find all Placemark elements
            placemarks = root.findall('.//kml:Placemark', ns)
            processed_count = 0
            
            for placemark in placemarks:
                location = self._extract_kml_location(placemark, location_type, ns)
                if location:
                    self.locations.append(location)
                    processed_count += 1
            
            print(f"  - Extracted {processed_count} {location_type} locations")
            
        except Exception as e:
            print(f"Error processing KML file: {e}")
    
    def _extract_kml_location(self, placemark, location_type: str, ns: Dict) -> Optional[Location]:
        """Extract location data from a KML Placemark"""
        try:
            # Get name from ExtendedData/SimpleData fields
            name = None
            trail_name = None
            
            # Look for ExtendedData/SimpleData fields
            extended_data = placemark.find('.//kml:ExtendedData/kml:SchemaData', ns)
            if extended_data is not None:
                for simple_data in extended_data.findall('kml:SimpleData', ns):
                    field_name = simple_data.get('name')
                    if field_name == 'Main Title':
                        name = simple_data.text.strip() if simple_data.text else None
                    elif field_name == 'Trail Name':
                        trail_name = simple_data.text.strip() if simple_data.text else None
            
            # Fallback to <name> element if available
            if not name:
                name_elem = placemark.find('kml:name', ns)
                name = name_elem.text.strip() if name_elem is not None else None
            
            if not name:
                return None
            
            # Get coordinates
            coordinates_elem = placemark.find('.//kml:coordinates', ns)
            if coordinates_elem is None:
                return None
            
            coords_text = coordinates_elem.text.strip()
            # KML format: "lon,lat,alt" or "lon,lat"
            coords = coords_text.split(',')
            lon, lat = float(coords[0]), float(coords[1])
            
            # Get description
            description_elem = placemark.find('kml:description', ns)
            description = description_elem.text.strip() if description_elem is not None else None
            
            # Create unique ID
            location_id = f"{location_type}_{len(self.locations)}_{hash(name) % 10000}"
            
            # Create metadata with trail information
            metadata = {
                'source': 'kml',
                'trail_name': trail_name,
                'landmark_name': name
            }
            
            return Location(
                id=location_id,
                name=name,
                location_type=location_type,
                coordinates=(lon, lat),
                address=None,  # KML doesn't have structured addresses
                description=f"Heritage trail: {name} (Part of {trail_name})" if trail_name else f"Heritage trail: {name}",
                metadata=metadata
            )
            
        except Exception as e:
            print(f"Error processing KML placemark: {e}")
            return None
    
    def _extract_name(self, properties: Dict) -> Optional[str]:
        """Extract name from properties using various possible field names"""
        # First try direct field names
        name_fields = ['Name', 'BUSINESS_NAME', 'name', 'title', 'LIC_NAME']
        
        for field in name_fields:
            if field in properties and properties[field]:
                name = str(properties[field]).strip()
                # Skip generic names like "kml_1", "kml_2"
                if not name.startswith('kml_'):
                    return name
        
        # For GeoJSON files, try to extract from HTML description
        if 'Description' in properties:
            name = self._extract_name_from_html(properties['Description'])
            if name:
                return name
        
        return None
    
    def _extract_name_from_html(self, html_description: str) -> Optional[str]:
        """Extract name from HTML description table"""
        try:
            # Look for PAGETITLE (tourist attractions) or SPORTS_CEN (sports facilities)
            import re
            
            # Try PAGETITLE first (for tourist attractions)
            pagetitle_match = re.search(r'<th>PAGETITLE</th>\s*<td>([^<]+)</td>', html_description)
            if pagetitle_match:
                return pagetitle_match.group(1).strip()
            
            # Try SPORTS_CEN (for sports facilities)
            sports_cen_match = re.search(r'<th>SPORTS_CEN</th>\s*<td>([^<]+)</td>', html_description)
            if sports_cen_match:
                return sports_cen_match.group(1).strip()
            
            # Try BUSINESS_NAME in HTML (for restaurants)
            business_name_match = re.search(r'<th>BUSINESS_NAME</th>\s*<td>([^<]+)</td>', html_description)
            if business_name_match:
                return business_name_match.group(1).strip()
                
        except Exception as e:
            print(f"Error extracting name from HTML: {e}")
        
        return None
    
    def _extract_address(self, properties: Dict) -> Optional[str]:
        """Extract address from properties"""
        # Try to extract from HTML description first (for GeoJSON files)
        if 'Description' in properties:
            address = self._extract_address_from_html(properties['Description'])
            if address:
                return address
        
        # Try to build address from direct fields (for restaurants)
        address_parts = []
        
        # Restaurant address fields - build Google Maps style address
        if 'BLK_HOUSE' in properties and properties['BLK_HOUSE']:
            address_parts.append(str(properties['BLK_HOUSE']))
        if 'STR_NAME' in properties and properties['STR_NAME']:
            address_parts.append(str(properties['STR_NAME']))
        if 'UNIT_NO' in properties and properties['UNIT_NO']:
            address_parts.append(f"#{properties['UNIT_NO']}")
        
        # Add Singapore if we have address parts
        if address_parts:
            address_parts.append("Singapore")
        
        return ', '.join(address_parts) if address_parts else None
    
    def _extract_address_from_html(self, html_description: str) -> Optional[str]:
        """Extract address from HTML description table"""
        try:
            import re
            
            # Try ADDRESS field (for tourist attractions)
            address_match = re.search(r'<th>ADDRESS</th>\s*<td>([^<]+)</td>', html_description)
            if address_match:
                return address_match.group(1).strip()
            
            # Try building full address from restaurant fields (BLK_HOUSE + STR_NAME + UNIT_NO + POSTCODE)
            address_parts = []
            
            # Restaurant address fields
            blk_house_match = re.search(r'<th>BLK_HOUSE</th>\s*<td>([^<]+)</td>', html_description)
            if blk_house_match:
                blk_house = blk_house_match.group(1).strip()
                if blk_house and blk_house != '':
                    address_parts.append(blk_house)
            
            str_name_match = re.search(r'<th>STR_NAME</th>\s*<td>([^<]+)</td>', html_description)
            if str_name_match:
                str_name = str_name_match.group(1).strip()
                if str_name and str_name != '':
                    address_parts.append(str_name)
            
            unit_no_match = re.search(r'<th>UNIT_NO</th>\s*<td>([^<]+)</td>', html_description)
            if unit_no_match:
                unit_no = unit_no_match.group(1).strip()
                if unit_no and unit_no != '':
                    address_parts.append(f"#{unit_no}")
            
            postcode_match = re.search(r'<th>POSTCODE</th>\s*<td>([^<]+)</td>', html_description)
            if postcode_match:
                postcode = postcode_match.group(1).strip()
                if postcode and postcode != '':
                    address_parts.append(f"Singapore {postcode}")
            
            # If we have restaurant address parts, return them
            if address_parts:
                return ', '.join(address_parts)
            
            # Try building full address from sports facility fields (HOUSE_BLOC + ROAD_NAME + POSTAL_COD)
            address_parts = []
            
            house_match = re.search(r'<th>HOUSE_BLOC</th>\s*<td>([^<]+)</td>', html_description)
            if house_match:
                house_block = house_match.group(1).strip()
                if house_block and house_block != '':
                    address_parts.append(house_block)
            
            road_match = re.search(r'<th>ROAD_NAME</th>\s*<td>([^<]+)</td>', html_description)
            if road_match:
                road_name = road_match.group(1).strip()
                if road_name and road_name != '':
                    address_parts.append(road_name)
            
            postal_match = re.search(r'<th>POSTAL_COD</th>\s*<td>([^<]+)</td>', html_description)
            if postal_match:
                postal_code = postal_match.group(1).strip()
                if postal_code and postal_code != '':
                    address_parts.append(f"Singapore {postal_code}")
            
            # Format as Google Maps style address
            if address_parts:
                return ', '.join(address_parts)
                
        except Exception as e:
            print(f"Error extracting address from HTML: {e}")
        
        return None
    
    def _extract_description(self, properties: Dict, location_type: str) -> str:
        """Create a description for the location"""
        if location_type == "food":
            # Try to get name from HTML or direct field
            name = self._extract_name(properties) or "Unknown"
            return f"Food place: {name}"
        elif location_type == "attraction":
            # Try to get name from HTML (PAGETITLE) or direct field
            name = self._extract_name(properties) or "Unknown"
            return f"Tourist attraction: {name}"
        elif location_type == "activity":
            # Try to get name from HTML (SPORTS_CEN) or direct field
            name = self._extract_name(properties) or "Unknown"
            return f"Activity venue: {name}"
        elif location_type == "heritage":
            # For heritage, this method won't be called as description is set in KML processing
            name = properties.get('landmark_name', 'Unknown')
            trail_name = properties.get('trail_name', '')
            return f"Heritage trail: {name} (Part of {trail_name})" if trail_name else f"Heritage trail: {name}"
        else:
            return f"{location_type.title()} location in Singapore"
