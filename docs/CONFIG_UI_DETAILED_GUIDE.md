# Config Management UI - Detailed Implementation Guide

## Overview
Complete .NET Core MVC admin dashboard for managing database configuration tables with real-time toggle functionality, edit modals, and toast notifications.

**Base URL:** `https://localhost:5202`

---

## Architecture

### Technology Stack
- **Framework:** .NET Core 9.0 MVC
- **Database:** SQL Server
- **ORM:** Entity Framework Core
- **Frontend:** Bootstrap 5, jQuery, Razor Views
- **API:** RESTful endpoints with JSON responses

### Project Structure
```
ConfigManagementUI/
├── Controllers/
│   ├── ConfigController.cs          # Main API controller
│   └── HomeController.cs            # Home page controller
├── Models/
│   ├── DbModels/                    # Database entities
│   │   ├── ConfigDbContext.cs       # EF Core DbContext
│   │   ├── FeaturesConfig.cs
│   │   ├── ThresholdConfig.cs
│   │   ├── RetrainingConfig.cs
│   │   ├── ModelVersionConfig.cs
│   │   ├── ModelTrainingRuns.cs
│   │   ├── CustomerAccountTransferTypeConfig.cs
│   │   └── ErrorViewModel.cs
│   └── ViewModels/                  # View-specific models
│       ├── FeatureConfigViewModel.cs
│       ├── ThresholdConfigViewModel.cs
│       └── RetrainingConfigViewModel.cs
├── Views/
│   ├── Config/                      # Configuration pages
│   │   ├── Index.cshtml             # Dashboard
│   │   ├── Features.cshtml          # Features management
│   │   ├── Thresholds.cshtml        # Thresholds management
│   │   ├── Scheduler.cshtml         # Scheduler configuration
│   │   ├── ModelVersions.cshtml     # Model versions
│   │   ├── TrainingRuns.cshtml      # Training history
│   │   └── CustomerConfigs.cshtml   # Customer rules
│   ├── Home/
│   ├── Shared/
│   │   ├── _Layout.cshtml           # Master layout
│   │   └── Error.cshtml
│   └── _ViewImports.cshtml
├── wwwroot/
│   ├── css/
│   ├── js/
│   └── lib/                         # Bootstrap, jQuery
├── Program.cs                       # Startup configuration
├── appsettings.json                 # Configuration
└── ConfigManagementUI.csproj        # Project file
```

---

## Database Models

### 1. FeaturesConfig
**Purpose:** Manage feature flags and toggles

```csharp
public class FeaturesConfig
{
    public int FeatureID { get; set; }
    public string FeatureName { get; set; }
    public string Description { get; set; }
    public bool IsEnabled { get; set; }
    public bool IsActive { get; set; }
    public string FeatureType { get; set; }
    public string Version { get; set; }
    public string RollbackVersion { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public string CreatedBy { get; set; }
    public string UpdatedBy { get; set; }
}
```

**Fields:**
- `FeatureID`: Primary key
- `FeatureName`: Name of feature (e.g., "Velocity Check")
- `IsEnabled`: Toggle status (enabled/disabled)
- `IsActive`: Active/Inactive status
- `FeatureType`: Category (e.g., "Security", "Validation")
- `Version`: Current version number
- `UpdatedAt`: Last modification timestamp
- `UpdatedBy`: User who made changes

---

### 2. ThresholdConfig
**Purpose:** Manage transaction thresholds and limits

```csharp
public class ThresholdConfig
{
    public int ThresholdID { get; set; }
    public string ThresholdName { get; set; }
    public string ThresholdType { get; set; }
    public double ThresholdValue { get; set; }
    public double? MinValue { get; set; }
    public double? MaxValue { get; set; }
    public double? PreviousValue { get; set; }
    public string Description { get; set; }
    public bool IsActive { get; set; }
    public DateTime? EffectiveFrom { get; set; }
    public DateTime? EffectiveTo { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public string CreatedBy { get; set; }
    public string UpdatedBy { get; set; }
    public string ApprovalStatus { get; set; }
    public string ApprovedBy { get; set; }
    public string Rationale { get; set; }
    public string ImpactAnalysis { get; set; }
}
```

**Fields:**
- `ThresholdValue`: Current threshold value
- `MinValue`/`MaxValue`: Validation range
- `PreviousValue`: Track changes
- `ApprovalStatus`: Approval workflow (Pending, Approved, Rejected)
- `EffectiveFrom`/`EffectiveTo`: Time-based activation

---

### 3. RetrainingConfig
**Purpose:** Manage ML model retraining schedule

```csharp
public class RetrainingConfig
{
    public int ConfigId { get; set; }
    public string Interval { get; set; }
    public bool IsEnabled { get; set; }
    public DateTime? LastRun { get; set; }
    public DateTime? NextRun { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public int WeeklyJobDay { get; set; }      // 0=Monday, 6=Sunday
    public int WeeklyJobHour { get; set; }     // 0-23
    public int WeeklyJobMinute { get; set; }   // 0-59
    public int MonthlyJobDay { get; set; }     // 1-31
    public int MonthlyJobHour { get; set; }
    public int MonthlyJobMinute { get; set; }
}
```

**Fields:**
- `Interval`: Schedule type (Weekly, Monthly, Daily)
- `WeeklyJobDay`: Day of week for weekly jobs
- `MonthlyJobDay`: Day of month for monthly jobs
- `LastRun`/`NextRun`: Execution tracking

---

### 4. ModelVersionConfig
**Purpose:** Track ML model versions and metrics

```csharp
public class ModelVersionConfig
{
    public int ModelVersionID { get; set; }
    public string ModelName { get; set; }
    public string VersionNumber { get; set; }
    public string ModelPath { get; set; }
    public string ScalerPath { get; set; }
    public string ThresholdPath { get; set; }
    public bool IsActive { get; set; }
    public double? Accuracy { get; set; }
    public double? Precision { get; set; }
    public double? Recall { get; set; }
    public double? F1Score { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? DeployedAt { get; set; }
    public DateTime? RetiredAt { get; set; }
    public string CreatedBy { get; set; }
    public string DeployedBy { get; set; }
    public long TrainingDataSize { get; set; }
    public long ModelSize { get; set; }
    public string Notes { get; set; }
}
```

---

### 5. ModelTrainingRuns
**Purpose:** Log training execution history

```csharp
public class ModelTrainingRuns
{
    public int RunId { get; set; }
    public DateTime RunDate { get; set; }
    public string ModelVersion { get; set; }
    public string Status { get; set; }
    public int DataSize { get; set; }
    public string Metrics { get; set; }
}
```

---

### 6. CustomerAccountTransferTypeConfig
**Purpose:** Customer-specific transaction rules

```csharp
public class CustomerAccountTransferTypeConfig
{
    public int ConfigID { get; set; }
    public string CustomerID { get; set; }
    public string AccountNo { get; set; }
    public string TransferType { get; set; }
    public string ParameterName { get; set; }
    public string ParameterValue { get; set; }
    public bool? IsEnabled { get; set; }
    public bool? IsActive { get; set; }
    public string DataType { get; set; }
    public double? MinValue { get; set; }
    public double? MaxValue { get; set; }
    public string Description { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public string CreatedBy { get; set; }
    public string UpdatedBy { get; set; }
}
```

---

## API Endpoints

### GET Endpoints (Page Views)

#### 1. Dashboard
```
GET /Config/Index
Response: HTML dashboard page
```

#### 2. Features Management
```
GET /Config/Features
Response: List of all features with toggle controls
```

**Features Page Functionality:**
- Display all features in table format
- Toggle enable/disable with checkbox
- Edit button opens modal
- Toast notifications for actions
- Real-time updates

#### 3. Thresholds Management
```
GET /Config/Thresholds
Response: List of all thresholds
```

#### 4. Scheduler Configuration
```
GET /Config/Scheduler
Response: Retraining schedule configuration
```

#### 5. Model Versions
```
GET /Config/ModelVersions
Response: List of all model versions with metrics
```

#### 6. Training Runs
```
GET /Config/TrainingRuns
Response: Last 100 training runs history
```

#### 7. Customer Configurations
```
GET /Config/CustomerConfigs?customerId=1060284
Response: Customer-specific rules
Query Parameters:
  - customerId (optional): Filter by customer
```

---

### POST Endpoints (API)

#### 1. Toggle Feature
```
POST /Config/ToggleFeature/{id}
Path Parameters:
  - id: Feature ID
Request Body: {} (empty)
Response: 
{
  "success": true,
  "isEnabled": true
}
```

**Functionality:**
- Toggles `IsEnabled` status
- Updates `UpdatedAt` timestamp
- Records `UpdatedBy` user
- Returns new status

#### 2. Update Feature
```
POST /Config/UpdateFeature/{id}
Path Parameters:
  - id: Feature ID
Request Body:
{
  "featureType": "Security",
  "version": "2.0",
  "description": "Updated description",
  "isActive": true
}
Response:
{
  "success": true
}
```

**Functionality:**
- Updates feature details
- Supports partial updates
- Maintains audit trail
- Triggers modal close and page reload

#### 3. Update Threshold
```
POST /Config/UpdateThreshold/{id}?thresholdValue=500&minValue=100&maxValue=1000&approvalStatus=Approved
Path Parameters:
  - id: Threshold ID
Query Parameters:
  - thresholdValue (required): New value
  - minValue (optional): Min validation
  - maxValue (optional): Max validation
  - approvalStatus (optional): Approval state
Response:
{
  "success": true
}
```

**Validation:**
- Checks if value is within min/max range
- Returns 400 Bad Request if out of range
- Stores previous value for audit

#### 4. Update Scheduler
```
POST /Config/UpdateScheduler
Request Body:
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
Response:
{
  "success": true
}
```

---

## UI Components

### Features Page (Features.cshtml)

#### Table Display
```html
<table class="table table-striped table-hover">
  <thead class="table-dark">
    <tr>
      <th>Feature Name</th>
      <th>Type</th>
      <th>Version</th>
      <th>Description</th>
      <th>Status</th>
      <th>Enabled</th>
      <th>Last Updated</th>
      <th>Action</th>
    </tr>
  </thead>
  <tbody>
    <!-- Rows populated from model -->
  </tbody>
</table>
```

#### Toggle Checkbox
```html
<input type="checkbox" class="form-check-input feature-toggle" 
       data-id="@feature.FeatureID" 
       data-name="@feature.FeatureName"
       @(feature.IsEnabled ? "checked" : "") />
```

**Behavior:**
- Sends POST to `/Config/ToggleFeature/{id}`
- Shows success/error toast
- Reverts checkbox on error

#### Edit Modal
```html
<div class="modal fade" id="editModal">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title">Edit Feature</h5>
      </div>
      <div class="modal-body">
        <form id="editForm">
          <input type="hidden" id="featureId" />
          <div class="mb-3">
            <label for="featureName">Feature Name</label>
            <input type="text" id="featureName" readonly />
          </div>
          <div class="mb-3">
            <label for="featureType">Type</label>
            <input type="text" id="featureType" />
          </div>
          <div class="mb-3">
            <label for="version">Version</label>
            <input type="text" id="version" />
          </div>
          <div class="mb-3">
            <label for="description">Description</label>
            <textarea id="description" rows="3"></textarea>
          </div>
          <div class="mb-3 form-check">
            <input type="checkbox" id="isActive" />
            <label for="isActive">Active</label>
          </div>
        </form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary" onclick="saveFeature()">Save Changes</button>
      </div>
    </div>
  </div>
</div>
```

#### Toast Notifications
```javascript
function showToast(message, type) {
    const toastId = 'toast-' + Date.now();
    const bgColor = type === 'success' ? 'bg-success' : 'bg-danger';
    const toastHtml = `
        <div id="${toastId}" class="toast ${bgColor} text-white">
            <div class="toast-body">${message}</div>
        </div>
    `;
    
    const container = document.getElementById('toastContainer');
    container.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}
```

---

## JavaScript Functionality

### Open Edit Modal
```javascript
function openEditModal(id, name, type, version, description, isActive) {
    document.getElementById('featureId').value = id;
    document.getElementById('featureName').value = name;
    document.getElementById('featureType').value = type;
    document.getElementById('version').value = version;
    document.getElementById('description').value = description;
    document.getElementById('isActive').checked = isActive === 'true';
}
```

### Save Feature Changes
```javascript
async function saveFeature() {
    const id = document.getElementById('featureId').value;
    const featureType = document.getElementById('featureType').value;
    const version = document.getElementById('version').value;
    const description = document.getElementById('description').value;
    const isActive = document.getElementById('isActive').checked;
    
    try {
        const response = await fetch(`/Config/UpdateFeature/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                featureType, version, description, isActive
            })
        });
        
        if (response.ok) {
            showToast('Feature updated successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast('Error updating feature', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}
```

### Toggle Feature
```javascript
document.querySelectorAll('.feature-toggle').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const id = this.dataset.id;
        const name = this.dataset.name;
        const isChecked = this.checked;
        
        try {
            const response = await fetch(`/Config/ToggleFeature/${id}`, { 
                method: 'POST' 
            });
            if (response.ok) {
                const status = isChecked ? 'enabled' : 'disabled';
                showToast(`${name} ${status} successfully`, 'success');
            } else {
                showToast('Error toggling feature', 'error');
                this.checked = !isChecked;
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
            this.checked = !isChecked;
        }
    });
});
```

---

## Configuration Files

### Program.cs
```csharp
var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllersWithViews();
builder.Services.AddDbContext<ConfigDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();

// Configure middleware
if (!app.Environment.IsDevelopment()) {
    app.UseExceptionHandler("/Home/Error");
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Config}/{action=Index}/{id?}");

app.Run();
```

### appsettings.json
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=YOUR_SERVER;Database=ConfigDB;Trusted_Connection=true;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "AllowedHosts": "*"
}
```

---

## Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| Feature Toggle | ✅ | Real-time enable/disable with checkbox |
| Edit Modal | ✅ | Modal form for updating feature details |
| Toast Notifications | ✅ | Success/error messages with auto-dismiss |
| Audit Trail | ✅ | Tracks UpdatedAt and UpdatedBy |
| Validation | ✅ | Range checking for thresholds |
| Responsive Design | ✅ | Bootstrap 5 responsive layout |
| Error Handling | ✅ | Graceful error messages |
| Page Reload | ✅ | Auto-refresh after successful update |

---

## Usage Examples

### Toggle a Feature
1. Navigate to `/Config/Features`
2. Find feature in table
3. Click checkbox to toggle
4. See toast notification

### Edit a Feature
1. Navigate to `/Config/Features`
2. Click "Edit" button
3. Modify fields in modal
4. Click "Save Changes"
5. See success toast and page reloads

### View Thresholds
1. Navigate to `/Config/Thresholds`
2. See all thresholds with current values
3. Click Edit to modify

### Configure Scheduler
1. Navigate to `/Config/Scheduler`
2. Set weekly/monthly job times
3. Enable/disable scheduler
4. Save configuration

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 404 Not Found | Feature/Threshold doesn't exist | Check ID in URL |
| 400 Bad Request | Value out of range | Ensure value is within min/max |
| Network Error | Connection issue | Check server is running |
| Modal won't close | JavaScript error | Check browser console |

---

## Performance Considerations

- **Database Queries:** Async/await for non-blocking operations
- **Caching:** Consider caching frequently accessed configs
- **Pagination:** Implement for large datasets (100+ records)
- **Lazy Loading:** Load related data on demand

---

## Security Considerations

- **Authentication:** Add user authentication before production
- **Authorization:** Implement role-based access control
- **Input Validation:** Validate all user inputs
- **SQL Injection:** Using EF Core parameterized queries
- **CSRF Protection:** Add anti-forgery tokens to forms

---

## Future Enhancements

1. **Bulk Operations:** Update multiple features at once
2. **Search/Filter:** Filter configs by name, type, status
3. **Export:** Export configs to CSV/Excel
4. **Import:** Bulk import configurations
5. **Versioning:** Track configuration change history
6. **Approval Workflow:** Multi-level approval for changes
7. **Audit Logs:** Detailed audit trail with timestamps
8. **Real-time Sync:** WebSocket updates across clients
