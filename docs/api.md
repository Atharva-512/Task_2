# API Documentation

## Overview

The Restaurant POS Analytics Dashboard exposes a lightweight REST API that serves analytical data directly from a DuckDB warehouse.

The API is intentionally read-only. It provides business metrics for the frontend dashboard through parameterized SQL queries executed against the analytical warehouse.

All responses are returned in JSON format.

---

# Base URL

## Local Development

```
http://localhost:8000
```

## Production

```
<Render Backend URL>
```

---

# API Characteristics

| Property | Value |
|----------|-------|
| Architecture | REST |
| Protocol | HTTP / HTTPS |
| Data Format | JSON |
| Authentication | None |
| SQL Execution | Parameterized |
| Database | DuckDB |
| Documentation | Swagger UI (`/docs`) |

---

# Response Format

Successful responses return HTTP 200 along with JSON data.

Example

```json
{
    "total_sales": 125430.50,
    "total_orders": 892,
    "average_order_value": 140.62,
    "total_tax": 8721.42,
    "total_discount": 12341.25
}
```

---

# Error Format

Example

```json
{
    "detail": "Unable to retrieve summary data."
}
```

---

# HTTP Status Codes

| Status | Meaning |
|---------|---------|
| 200 | Success |
| 400 | Invalid request parameters |
| 404 | Resource not found |
| 500 | Internal server error |

---

# Common Query Parameters

Several analytical endpoints support server-side filtering.

| Parameter | Type | Description |
|-----------|------|-------------|
| start_date | string | Start date (YYYY-MM-DD) |
| end_date | string | End date (YYYY-MM-DD) |
| platform | string | Platform name |
| brand | string | Brand name |

Example

```
?start_date=2026-05-01&end_date=2026-05-31&platform=Swiggy&brand=Pizza%20Hut
```

---

# Health Check

## Endpoint

```
GET /health
```

## Purpose

Returns the operational status of the backend service.

### Response

```json
{
    "status": "healthy"
}
```

### Status Codes

| Code | Description |
|------|-------------|
| 200 | Service available |

---

# Summary API

## Endpoint

```
GET /api/summary
```

## Purpose

Returns high-level KPI metrics for the dashboard.

### Supported Filters

- start_date
- end_date
- platform
- brand

### Example

```
GET /api/summary?platform=Swiggy
```

### Response

```json
{
    "total_sales": 152340.20,
    "total_orders": 1123,
    "average_order_value": 135.66,
    "total_tax": 9320.50,
    "total_discount": 18210.00
}
```

### Returned Metrics

| Field | Description |
|--------|-------------|
| total_sales | Gross sales |
| total_orders | Total orders |
| average_order_value | Average order value |
| total_tax | Total tax collected |
| total_discount | Total discount |

---

# Daily Sales API

## Endpoint

```
GET /api/daily-sales
```

## Purpose

Returns daily sales trend information.

### Supported Filters

- start_date
- end_date
- platform
- brand

### Example

```
GET /api/daily-sales?start_date=2026-05-01&end_date=2026-05-31
```

### Response

```json
[
    {
        "business_date":"2026-05-01",
        "sales":14230.50,
        "orders":118
    }
]
```

### Fields

| Field | Description |
|--------|-------------|
| business_date | Business date |
| sales | Gross sales |
| orders | Number of orders |

---

# Platform Performance API

## Endpoint

```
GET /api/platform-performance
```

## Purpose

Returns aggregated sales by ordering platform.

### Supported Filters

- start_date
- end_date
- platform
- brand

### Example

```
GET /api/platform-performance?brand=Pizza%20Hut
```

### Response

```json
[
    {
        "platform":"Swiggy",
        "orders":420,
        "sales":68321.55
    }
]
```

### Fields

| Field | Description |
|--------|-------------|
| platform | Ordering platform |
| orders | Total orders |
| sales | Gross sales |

---

# Brand Performance API

## Endpoint

```
GET /api/brand-performance
```

## Purpose

Returns aggregated sales by restaurant brand.

### Supported Filters

- start_date
- end_date
- platform
- brand

### Example

```
GET /api/brand-performance?platform=Zomato
```

### Response

```json
[
    {
        "brand":"Pizza Hut",
        "orders":318,
        "sales":52140.40
    }
]
```

### Fields

| Field | Description |
|--------|-------------|
| brand | Restaurant brand |
| orders | Total orders |
| sales | Gross sales |

---

# Filters API

## Endpoint

```
GET /api/filters
```

## Purpose

Returns all available dashboard filters.

### Response

```json
{
    "platforms":[
        "Swiggy",
        "Zomato"
    ],
    "brands":[
        "Pizza Hut",
        "KFC"
    ],
    "min_business_date":"2026-05-01",
    "max_business_date":"2026-06-30"
}
```

### Fields

| Field | Description |
|--------|-------------|
| platforms | Available platforms |
| brands | Available brands |
| min_business_date | Earliest available date |
| max_business_date | Latest available date |

---

# Validation

The backend validates incoming query parameters before executing SQL.

Current validation includes:

- Date format validation (`YYYY-MM-DD`)
- Optional query parameters
- Typed response models using Pydantic
- Parameterized SQL execution

Invalid requests return HTTP **400 Bad Request**.

---

# Error Handling

Database-related failures are converted into user-friendly API responses.

Examples include:

- Database unavailable
- Invalid warehouse
- Query execution failure
- Missing analytical data

Sensitive internal implementation details are not exposed to API consumers.

---

# Interactive API Documentation

FastAPI automatically generates Swagger documentation.

Available at

```
/docs
```

The Swagger interface allows developers to:

- Explore endpoints
- View request models
- Test APIs directly
- Inspect response schemas

without requiring additional tools.

---

# API Design Principles

The API follows several design principles:

- Read-only analytics
- RESTful resource design
- Parameterized SQL
- Consistent JSON responses
- Typed request and response models
- Separation between routing and business logic
- Lightweight analytical serving layer

These principles keep the API predictable, maintainable and easy to extend while supporting the analytical dashboard.