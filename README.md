# Data Generator Enhancements & Usage Guide

## Key Enhancements

- **Dynamic Date Ranges:** All datasets with date/datetime fields now support `end: dynamic`, ensuring generated data always ends at the last moment of the current month for realistic time series and forecasting.
- **Industry-Aligned Fields:** Each dataset is tailored with fields, value lists, and weights that reflect real-world industry data.
- **Modular Configs:** YAML-driven, easily extensible for new domains or custom fields.
- **Advanced Tuning:** CLI options for spend/usage multipliers, trend/spike controls, and per-service/plan adjustments.
- **Flexible Export:** Output to JSONL, CSV, or Parquet; S3-style partitioning for big data workflows.
- **Validation:** Built-in config validation for error-free generation.

## Example Usage

### Basic Data Generation

```sh
python samples_run.py --config configs/topics/healthcare_wearables.yaml --num-records 10000 --output-type jsonl
```

### Custom Date Range (Dynamic End)

```yaml
- name: timestamp
  type: date
  start: 2024-01-01
  end: dynamic
  time_format: '%Y-%m-%dT%H:%M:%S'
```

This ensures data always ends at the last day of the current month.

### Tuning Spend/Usage

```sh
python samples_run.py --config configs/topics/aws_cost.yaml --num-records 50000 --spend-multiplier 2.0
```

Doubles all generated spend for stress-testing dashboards.

### Trend/Spike Simulation

```sh
python samples_run.py --config configs/topics/aws_cost.yaml --num-records 10000 --trend up --spike 0.1
```

Adds an upward trend and 10% random spikes to the data.

### S3-Style Partitioned Export

```sh
python samples_run.py --config configs/topics/supply_chain.yaml --num-records 10000 --output data/supply_chain.csv --s3-partition-fields shipped_date,region
```

Adds an `s3_path` field for each record, partitioned by date and region.

### Config Validation

```sh
python validate_config.py configs/topics/education_student_analytics.yaml
```

## Empowering Users

- **Add new configs:** Copy and modify any YAML in `configs/topics/` to create your own domain.
- **Reference pools:** Link to external JSON files for realistic cross-entity relationships.
- **Formulas & Faker:** Use formulas for calculated fields and Faker for realistic names, addresses, etc.
- **CLI Tuning:** All major parameters (record count, output type, multipliers, trends, partitions) are CLI-tunable.

---

## Getting Started

This project provides a modular, YAML-driven data generator for creating realistic synthetic datasets for analytics, demos, and AI/ML workflows.

**Basic Steps:**

1. Validate your config:

   ```sh
   python scripts/validate_config.py configs/topics/<your_topic>.yaml
   ```
2. Generate data (choose output type by file extension or --output-type):

   ```sh
   python scripts/generate_cost_data.py --config configs/topics/<your_topic>.yaml --num-records 10000 --output data/<your_data>.parquet
   ```
3. (Optional) Add S3-style partitioning:

   ```sh
   python scripts/generate_cost_data.py --config configs/topics/<your_topic>.yaml --num-records 10000 --output data/<your_data>.csv --s3-partition-fields date,region
   ```

See below for dataset details, features, and advanced options.

---

# FinOps Raw Cost Data Sample

This dataset contains simulated raw cost and usage data for several cloud providers and industry tools, including AWS, Azure, Datadog, Splunk, and a fictional company. The data is designed to mimic real-world billing exports and can be used for demonstrations, analytics, and AI chatbot development.

## Structure

- **company**: Name of the provider or company
- **account_id**: Account or organization identifier
- **service**: Cloud or SaaS service name
- **region**: Service region
- **usage_type**: Type of usage (e.g., instance type, storage class)
- **usage_quantity**: Amount of usage (e.g., hours, bytes, traces)
- **cost**: Cost for the usage period
- **currency**: Currency code
- **date**: Usage date (YYYY-MM-DD)

## Example Use Cases

- Cost analysis and trend visualization
- Forecasting and anomaly detection
- Demonstrating FinOps chatbot capabilities

## Extending the Data

To add more data, simply append new entries to the JSON file, varying dates, services, and usage types as needed.

# Data Generation Workflow & Features

This project includes a modular, YAML-driven data generator for creating realistic, extensible datasets for FinOps, analytics, and AI demos.

## Key Features

- **YAML-Driven Configs**: Define fields, types, formulas, choices, references, and more in a topic YAML file.
- **Faker Integration**: Use [Faker](https://faker.readthedocs.io/) for realistic company names, addresses, etc.
- **Weighted Choices**: Specify weighted random selection for categorical fields.
- **Reference Pools**: Link fields to external JSON pools (e.g., company IDs, product lists) with optional unique assignment.
- **Formulas**: Compute fields based on other fields, including date math and custom logic.
- **Output Types**: Generate data as JSON, CSV, or Parquet with `--output-type` or by file extension.
- **S3-Style Partitioning**: Optionally add an `s3_path` field with S3-style folder structure (e.g., `year=2025/month=08/day=15/region=us-west/`) using `--s3-partition-fields`.
- **Config Validation**: Validate YAML configs for schema, references, and logic before generating data.

## Example CLI Usage

Generate 10,000 records as Parquet:

```sh
python scripts/generate_cost_data.py --config configs/topics/supply_chain.yaml --num-records 10000 --output data/supply_chain_data.parquet
```

Generate CSV with S3-style partitioning by shipped_date and region:

```sh
python scripts/generate_cost_data.py --config configs/topics/supply_chain.yaml --num-records 5000 --output data/supply_chain_data.csv --output-type csv --s3-partition-fields shipped_date,region
```

Validate a config file:

```sh
python scripts/validate_config.py configs/topics/supply_chain.yaml
```

## S3 Partitioning Details

- If a partition field is a date, the path will be split as `year=YYYY/month=MM/day=DD/`.
- For other fields, the path will be `field=value/`.
- The generated path is added as the `s3_path` field in each record if `--s3-partition-fields` is provided.

## Extending & Customizing

- Add new YAML configs for different business domains or data types.
- Add new reference pools as JSON files for cross-topic linking.
- Use formulas and Faker to increase realism.
- Use the validation script to check configs before generating data.

# Dataset Reference

## Supply Chain

- **Description:** Simulated supply chain and logistics data for inventory, shipping, and supplier analytics.
- **Industries:** Manufacturing, Retail, Logistics
- **Fields:** shipment_id, product, supplier, warehouse, warehouse_id, quantity, cost_per_unit, total_cost, shipped_date, estimated_processing_days, variance_days, actual_processing_days, variance_pct, delivery_days, delivered_date
- **Use Cases:** Inventory optimization, delivery performance, cost analysis

## HR Workforce

- **Description:** Simulated HR and workforce data for employee analytics, payroll, and performance management.
- **Industries:** HR, Enterprise, Staffing, Payroll
- **Fields:** employee_id, first_name, last_name, employer, department, job_title, salary, hire_date, termination_date, is_active, performance_rating, last_review_date
- **Use Cases:** Workforce planning, attrition analysis, HR analytics demos

## Subscription SaaS Usage

- **Description:** Simulated SaaS subscription and usage data for analytics, churn prediction, and customer engagement.
- **Industries:** SaaS, Software, Technology, Analytics
- **Fields:** user_id, company_id, company_name, user_name, user_email, signup_date, plan, status, monthly_fee, usage_events, last_login, renewal_date, churn_risk, features_enabled
- **Use Cases:** Product analytics, upsell/cross-sell, retention modeling

## Lead Generation SaaS Recall

- **Description:** Simulated lead generation list for a SaaS company offering product recall management services.
- **Industries:** SaaS, Product Safety, Manufacturing, Retail, Compliance
- **Fields:** company_id, company_name, company_address, contact_name, contact_email, contact_phone, industry, recall_history, annual_revenue_musd, employee_count, engagement_status, last_contact_date
- **Use Cases:** Sales prospecting, marketing automation, CRM demos

## Cloud Cost

- **Description:** Simulated cloud provider cost and usage data for FinOps analytics.
- **Industries:** Cloud, FinOps, IT
- **Fields:** company, service, usage_quantity, cost, date
- **Use Cases:** Cloud cost analysis, usage optimization, FinOps demos

## Financial Transactions

- **Description:** Simulated financial transaction data for banking, payments, and fraud analytics.
- **Industries:** Banking, Payments, Fintech
- **Fields:** transaction_id, account_id, transaction_type, amount, currency, balance, is_fraud, timestamp
- **Use Cases:** Fraud detection, account analysis, payment system demos

## E-commerce Browsing & Cart

- **Description:** Simulated e-commerce browsing and cart activity data for personalization, conversion, and abandonment analytics.
- **Industries:** E-commerce, Retail, Online Marketplace
- **Fields:** session_id, user_id, user_first_name, user_last_name, product_id, product_name, action, price, quantity, cart_value, abandoned, timestamp
- **Use Cases:** Recommendation engines, recovery campaigns, sales forecasting

## Healthcare Wearables

- **Description:** Simulated healthcare wearable device data for health monitoring, coaching, and anomaly detection.
- **Industries:** Healthcare, Wellness, Fitness, Insurance
- **Fields:** user_id, user_first_name, user_last_name, device_type, heart_rate, steps, sleep_hours, calories_burned, alert, timestamp
- **Use Cases:** Health coaching, anomaly alerts, personalized wellness advice

## Travel Booking

- **Description:** Simulated travel and booking data for flights, hotels, and car rentals—ideal for itinerary management, analytics, and customer support bots.
- **Industries:** Travel, Hospitality, Transportation, SaaS
- **Fields:** booking_id, user_id, user_first_name, user_last_name, trip_type, origin, destination, departure_date, return_date, price, status, feedback_score, timestamp
- **Use Cases:** Itinerary management, upsell/cross-sell, customer support demos

## Social Media Engagement

- **Description:** Simulated social media engagement data for posts, reactions, and trend analytics.
- **Industries:** Social Media, Marketing, Influencer, Brand
- **Fields:** post_id, user_id, user_first_name, user_last_name, platform, engagement_type, sentiment, content_type, reach, engagement_score, timestamp
- **Use Cases:** Trend detection, sentiment analysis, campaign performance

## Transportation Logistics Tracking

- **Description:** Simulated transportation and logistics tracking data for shipments, vehicles, and delivery analytics.
- **Industries:** Transportation, Logistics, Supply Chain, Retail
- **Fields:** shipment_id, carrier, vehicle_type, vehicle_id, origin, destination, status, last_event, event_timestamp, estimated_delivery, actual_delivery, distance_miles, weight_lbs, special_handling
- **Use Cases:** Delivery tracking, route optimization, supply chain analytics

## Sales History

- **Description:** Simulated sales transaction data for retail or SaaS analytics and forecasting.
- **Industries:** Retail, SaaS, eCommerce
- **Fields:** transaction_id, customer_id, product, customer_company, shipping_address, region, price, quantity, discount, total, date
- **Use Cases:** Revenue analysis, trend detection, forecasting demos

## IoT Device Telemetry

- **Description:** Simulated IoT device telemetry data for sensor analytics, device health, and predictive maintenance.
- **Industries:** IoT, Manufacturing, Smart Home, Automotive
- **Fields:** device_id, device_type, location, sensor_type, reading, status, battery_level, timestamp
- **Use Cases:** Anomaly detection, device monitoring, time series analytics

## Real Estate

- **Description:** Simulated real estate property listings and transaction data for analytics, search, and recommendation use cases.
- **Industries:** Real Estate, PropTech, Finance, Insurance
- **Fields:** property_id, address, synthetic_address, property_type, bedrooms, bathrooms, square_feet, year_built, listing_price, status, agent_name, listing_date, sale_date, sale_price, features
- **Use Cases:** Property search, price prediction, market analysis
