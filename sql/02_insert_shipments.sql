INSERT INTO shipments (
    shipment_id,
    product_name,
    origin_city,
    destination_city,
    shipment_status
)
VALUES
    ('SHP001', 'Temperature-Sensitive Product', 'Delhi', 'Mumbai', 'IN_TRANSIT'),
    ('SHP002', 'Temperature-Sensitive Product', 'Mumbai', 'Bengaluru', 'IN_TRANSIT'),
    ('SHP003', 'Temperature-Sensitive Product', 'Bengaluru', 'Hyderabad', 'IN_TRANSIT'),
    ('SHP004', 'Temperature-Sensitive Product', 'Hyderabad', 'Chennai', 'IN_TRANSIT'),
    ('SHP005', 'Temperature-Sensitive Product', 'Chennai', 'Delhi', 'IN_TRANSIT')
ON CONFLICT (shipment_id) DO NOTHING;