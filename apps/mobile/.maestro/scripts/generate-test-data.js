// Generate unique test data for registration
const timestamp = Date.now();
output.email = `farmer_${timestamp}@example.com`;
output.phone = `+2547${Math.floor(10000000 + Math.random() * 90000000)}`;
