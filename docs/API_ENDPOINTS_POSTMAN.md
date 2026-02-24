# Config Management API - Postman Guide

**Base URL:** `https://localhost:5202` (or your app URL)

---

## GET ENDPOINTS (Page Views)

### 1. GET /Config/Index
**Description:** Dashboard home page
- **Method:** GET
- **URL:** `https://localhost:5202/Config/Index`
- **Request Body:** None
- **Response:** HTML page
- **Status Code:** 200 OK

---

### 2. GET /Config/Features
**Description:** Get all features configuration
- **Method:** GET
- **URL:** `https://localhost:5202/Config/Features`
- **Request Body:** None
- **Response:** HTML page with features list
- **Response Data Structure:**
```json
[
  {
    "featureID": 1,
    "featureName": "Velocity Check",
    "description": "Check for velocity anomalies",
    "isEnabled": true,
    "isActive": true,
    "featureType": "Security",
    "version": "1.0",
    "status": "ACTIVE",
    "updatedAt": "2024-02-24T10:30:00"
  }
]
```
- **Status Code:** 200 OK

---

### 3. GET /Config/Thresholds
**Description:** Get all threshold configurations
- **Method:** GET
- **URL:** `https://localhost:5202/Config/Thresholds`
- **Request Body:** None
- **Response:** HTML page with thresholds list
- **Response Data Structure:**
```json
[
  {
    "thresholdID": 1,
    "thresholdName": "Amount Threshold",
    "thresholdType": "Amount",
    "thresholdValue": 100000,
    "minValue": 50000,
    "maxValue": 500000,
    "isActive": true,
    "description": "Maximum transaction amount",
    "effectiveFrom": "2024-01-01T00:00:00",
    "effectiveTo": null,
    "approvalStatus": "Approved",
    "validationStatus": "VALID"
  }
]
```
- **Status Code:** 200 OK

---

### 4. GET /Config/Scheduler
**Description:** Get scheduler/retraining configuration
- **Method:** GET
- **URL:** `https://localhost:5202/Config/Scheduler`
- **Request Body:** None
- **Response:** HTML page with scheduler config
- **Response Data Structure:**
```json
{
  "configId": 1,
  "interval": "Weekly",
  "isEnabled": true,
  "lastRun": "2024-02-24T02:00:00",
  "nextRun": "2024-03-03T02:00:00",
  "weeklyJobDay": 0,
  "weeklyJobHour": 2,
  "weeklyJobMinute": 0,
  "monthlyJobDay": 1,
  "monthlyJobHour": 3,
  "monthlyJobMinute": 0,
  "weeklyJobDayName": "Monday",
  "weeklyJobTime": "02:00",
  "monthlyJobTime": "03:00"
}
```
- **Status Code:** 200 OK
- **Note:** Returns 404 if no config found

---

### 5. GET /Config/ModelVersions
**Description:** Get all model versions
- **Method:** GET
- **URL:** `https://localhost:5202/Config/ModelVersions`
- **Request Body:** None
- **Response:** HTML page with model versions
- **Response Data Structure:**
```json
[
  {
    "modelVersionID": 1,
    "modelName": "Autoencoder",
    "versionNumber": "1.0.4",
    "modelPath": "/models/autoencoder.h5",
    "scalerPath": "/models/scaler.pkl",
    "thresholdPath": "/models/threshold.json",
    "isActive": true,
    "accuracy": 0.95,
    "precision": 0.93,
    "recall": 0.94,
    "f1Score": 0.935,
    "createdAt": "2024-02-20T10:00:00",
    "deployedAt": "2024-02-21T15:30:00",
    "retiredAt": null,
    "createdBy": "admin",
    "deployedBy": "admin",
    "trainingDataSize": 50000,
    "modelSize": 2048576,
    "notes": "Production model"
  }
]
```
- **Status Code:** 200 OK

---

### 6. GET /Config/TrainingRuns
**Description:** Get last 100 training runs
- **Method:** GET
- **URL:** `https://localhost:5202/Config/TrainingRuns`
- **Request Body:** None
- **Response:** HTML page with training runs history
- **Response Data Structure:**
```json
[
  {
    "runId": 1,
    "runDate": "2024-02-24T02:00:00",
    "modelVersion": "1.0.4",
    "status": "Success",
    "dataSize": 50000,
    "metrics": "{\"accuracy\": 0.95, \"precision\": 0.93}"
  }
]
```
- **Status Code:** 200 OK

---

### 7. GET /Config/CustomerConfigs
**Description:** Get customer account transfer type configurations
- **Method:** GET
- **URL:** `https://localhost:5202/Config/CustomerConfigs`
- **Query Parameters:**
  - `customerId` (optional): Filter by customer ID
- **Examples:**
  - `https://localhost:5202/Config/CustomerConfigs`
  - `https://localhost:5202/Config/CustomerConfigs?customerId=1060284`
- **Request Body:** None
- **Response:** HTML page with customer configs
- **Response Data Structure:**
```json
[
  {
    "configID": 1,
    "customerID": "1060284",
    "accountNo": "011060284018",
    "transferType": "O",
    "parameterName": "velocity_check_10min",
    "parameterValue": "OFF",
    "isEnabled": true,
    "isActive": true,
    "dataType": "String",
    "minValue": null,
    "maxValue": null,
    "description": "Velocity check for 10 minutes",
    "createdAt": "2024-01-15T10:00:00",
    "updatedAt": "2024-02-24T14:30:00",
    "createdBy": "admin",
    "updatedBy": "admin"
  }
]
```
- **Status Code:** 200 OK

---

## POST ENDPOINTS (API)

### 1. POST /Config/ToggleFeature/{id}
**Description:** Toggle feature enabled/disabled status
- **Method:** POST
- **URL:** `https://localhost:5202/Config/ToggleFeature/1`
- **Path Parameters:**
  - `id` (required): Feature ID
- **Headers:**
  - `Content-Type: application/json`
- **Request Body:** Empty or `{}`
- **Response:**
```json
{
  "success": true,
  "isEnabled": true
}
```
- **Status Code:** 200 OK
- **Error Response:** 404 Not Found if feature doesn't exist

---

### 2. POST /Config/UpdateFeature/{id}
**Description:** Update feature details (Type, Version, Description, Active status)
- **Method:** POST
- **URL:** `https://localhost:5202/Config/UpdateFeature/1`
- **Path Parameters:**
  - `id` (required): Feature ID
- **Headers:**
  - `Content-Type: application/json`
- **Request Body:**
```json
{
  "featureType": "Security",
  "version": "2.0",
  "description": "Updated feature description",
  "isActive": true
}
```
- **Request Fields:**
  - `featureType` (string, optional): Feature type
  - `version` (string, optional): Version number
  - `description` (string, optional): Feature description
  - `isActive` (boolean, required): Active status
- **Response:**
```json
{
  "success": true
}
```
- **Status Code:** 200 OK
- **Error Response:** 404 Not Found if feature doesn't exist

---

### 3. POST /Config/UpdateThreshold/{id}
**Description:** Update threshold values and approval status
- **Method:** POST
- **URL:** `https://localhost:5202/Config/UpdateThreshold/1?thresholdValue=500&minValue=100&maxValue=1000&approvalStatus=Approved`
- **Path Parameters:**
  - `id` (required): Threshold ID
- **Query Parameters:**
  - `thresholdValue` (required, double): New threshold value
  - `minValue` (optional, double): Minimum allowed value
  - `maxValue` (optional, double): Maximum allowed value
  - `approvalStatus` (optional, string): Approval status (e.g., "Approved", "Pending", "Rejected")
- **Headers:**
  - `Content-Type: application/json`
- **Request Body:** None or `{}`
- **Response:**
```json
{
  "success": true
}
```
- **Status Code:** 200 OK
- **Error Responses:**
  - 404 Not Found: Threshold doesn't exist
  - 400 Bad Request: Value out of range (thresholdValue < minValue or > maxValue)

---

### 4. POST /Config/UpdateScheduler
**Description:** Update scheduler/retraining configuration
- **Method:** POST
- **URL:** `https://localhost:5202/Config/UpdateScheduler`
- **Headers:**
  - `Content-Type: application/json`
- **Request Body:**
```json
{
  "configId": 1,
  "isEnabled": true,
  "weeklyJobDay": 0,
  "weeklyJobHour": 2,
  "weeklyJobMinute": 0,
  "monthlyJobDay": 1,
  "monthlyJobHour": 3,
  "monthlyJobMinute": 0
}
```
- **Request Fields:**
  - `configId` (int, required): Configuration ID
  - `isEnabled` (boolean, required): Enable/disable scheduler
  - `weeklyJobDay` (int, required): Day of week (0=Monday, 1=Tuesday, ..., 6=Sunday)
  - `weeklyJobHour` (int, required): Hour (0-23)
  - `weeklyJobMinute` (int, required): Minute (0-59)
  - `monthlyJobDay` (int, required): Day of month (1-31)
  - `monthlyJobHour` (int, required): Hour (0-23)
  - `monthlyJobMinute` (int, required): Minute (0-59)
- **Response:**
```json
{
  "success": true
}
```
- **Status Code:** 200 OK
- **Error Response:** 404 Not Found if config doesn't exist

---

## Postman Collection Import

You can import this as a Postman collection. Create a new collection with these requests and use the base URL variable.

### Environment Variables (Optional)
```json
{
  "base_url": "https://localhost:5202",
  "feature_id": "1",
  "threshold_id": "1",
  "customer_id": "1060284"
}
```

Then use `{{base_url}}` in URLs instead of hardcoding.

---

## Common Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (validation error) |
| 404 | Not Found (resource doesn't exist) |
| 500 | Server Error |

---

## Notes

- All timestamps are in UTC format (ISO 8601)
- GET endpoints return HTML pages by default. To get JSON responses, modify the controller to use `[ApiController]` and return `Ok()` instead of `View()`
- POST endpoints return JSON responses
- Authentication may be required depending on your app configuration
