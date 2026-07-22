-- NYC Airbnb availability warehouse queries
-- Usage: sqlite3 data/warehouse/nyc_airbnb.db < sql/availability_model_queries.sql

-- 1. Listings and high-availability share by borough
SELECT
  neighbourhood_group,
  COUNT(*) AS listings,
  ROUND(AVG(high_availability), 4) AS high_availability_rate,
  ROUND(AVG(price), 2) AS avg_price,
  ROUND(AVG(calculated_host_listings_count), 2) AS avg_host_listing_count
FROM listings_model
GROUP BY 1
ORDER BY high_availability_rate DESC;

-- 2. Room type / borough cut
SELECT
  neighbourhood_group,
  room_type,
  COUNT(*) AS listings,
  ROUND(AVG(high_availability), 4) AS high_availability_rate,
  ROUND(AVG(price), 2) AS avg_price
FROM listings_model
GROUP BY 1,2
ORDER BY listings DESC;

-- 3. Multi-listing host signal
SELECT
  CASE
    WHEN calculated_host_listings_count = 1 THEN 'single_listing_host'
    WHEN calculated_host_listings_count BETWEEN 2 AND 5 THEN 'small_multi_listing_host'
    ELSE 'large_multi_listing_host'
  END AS host_type,
  COUNT(*) AS listings,
  ROUND(AVG(high_availability), 4) AS high_availability_rate,
  ROUND(AVG(availability_365), 1) AS avg_availability_days
FROM listings_model
GROUP BY 1
ORDER BY high_availability_rate DESC;
