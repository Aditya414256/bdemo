import math
from typing import Optional

def calculate_distance(lat1: Optional[float], lon1: Optional[float], 
                       lat2: Optional[float], lon2: Optional[float]) -> Optional[float]:
    """
    Calculate Haversine great-circle distance between two coordinates in kilometers.
    Returns None if any coordinate is None.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    
    try:
        lat1_f, lon1_f = float(lat1), float(lon1)
        lat2_f, lon2_f = float(lat2), float(lon2)
    except (ValueError, TypeError):
        return None

    # Radius of earth in kilometers
    R = 6371.0

    dlat = math.radians(lat2_f - lat1_f)
    dlon = math.radians(lon2_f - lon1_f)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1_f)) * math.cos(math.radians(lat2_f)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 2)


def rank_pharmacies(pharmacies_with_inventory, customer_lat=None, customer_lon=None, customer_city=None, customer_pincode=None):
    """
    Sort and enrich pharmacy inventory results.
    Rules:
    1. If customer coordinates and pharmacy coordinates exist -> calculate distance_km and sort by distance.
    2. Fallback matching: Exact pincode match -> City match -> Deterministic ID order.
    """
    results = []
    
    for pharmacy, inv in pharmacies_with_inventory:
        distance = calculate_distance(customer_lat, customer_lon, pharmacy.latitude, pharmacy.longitude)
        
        # Calculate matching score for fallback ranking if distance is unavailable
        pincode_match = 1 if (customer_pincode and pharmacy.pincode and str(customer_pincode).strip() == str(pharmacy.pincode).strip()) else 0
        city_match = 1 if (customer_city and pharmacy.city and str(customer_city).strip().lower() == str(pharmacy.city).strip().lower()) else 0
        
        results.append({
            'id': pharmacy.id,
            'pharmacy_id': pharmacy.id,
            'owner_id': pharmacy.owner_id,
            'name': pharmacy.name,
            'license_number': pharmacy.license_number,
            'phone': pharmacy.phone,
            'email': pharmacy.email,
            'address': pharmacy.address,
            'city': pharmacy.city,
            'state': pharmacy.state,
            'pincode': pharmacy.pincode,
            'supports_pickup': pharmacy.supports_pickup,
            'supports_delivery': pharmacy.supports_delivery,
            'distance_km': distance,
            'quantity': inv.quantity,
            'available_quantity': inv.quantity,
            'price': inv.price,
            'stock_status': inv.stock_status,
            '_pincode_match': pincode_match,
            '_city_match': city_match
        })
    
    # Sort results:
    # If distance is available, sort primarily by distance_km (nulls last)
    # Otherwise sort by pincode_match desc, city_match desc, price asc, pharmacy_id asc
    def sort_key(item):
        has_distance = item['distance_km'] is not None
        dist = item['distance_km'] if has_distance else float('inf')
        return (
            0 if has_distance else 1,
            dist,
            -item['_pincode_match'],
            -item['_city_match'],
            item['price'],
            item['pharmacy_id']
        )
    
    results.sort(key=sort_key)
    
    # Strip internal sort helper keys
    for r in results:
        r.pop('_pincode_match', None)
        r.pop('_city_match', None)
        
    return results
