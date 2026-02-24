# .NET Core MVC - Config Management Screens Implementation Guide

## Overview
This guide provides step-by-step instructions to build admin screens for managing configuration tables in .NET Core MVC.

**Config Tables to Display:**
1. FeaturesConfig
2. ThresholdConfig
3. RetrainingConfig
4. ModelVersionConfig
5. ModelTrainingRuns
6. CustomerAccountTransferTypeConfig

---

## Step 1: Project Setup

### 1.1 Create New ASP.NET Core MVC Project
```bash
dotnet new mvc -n ConfigManagementUI
cd ConfigManagementUI
```

### 1.2 Install Required NuGet Packages
```bash
dotnet add package Microsoft.EntityFrameworkCore
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
dotnet add package Microsoft.EntityFrameworkCore.Tools
dotnet add package Microsoft.AspNetCore.Identity.EntityFrameworkCore
```

### 1.3 Project Structure
```
ConfigManagementUI/
├── Models/
│   ├── ViewModels/
│   │   ├── FeatureConfigViewModel.cs
│   │   ├── ThresholdConfigViewModel.cs
│   │   ├── RetrainingConfigViewModel.cs
│   │   ├── ModelVersionConfigViewModel.cs
│   │   ├── ModelTrainingRunViewModel.cs
│   │   └── CustomerConfigViewModel.cs
│   └── DbModels/
│       └── ConfigDbContext.cs
├── Controllers/
│   └── ConfigController.cs
├── Views/
│   ├── Config/
│   │   ├── Index.cshtml
│   │   ├── Features.cshtml
│   │   ├── Thresholds.cshtml
│   │   ├── Scheduler.cshtml
│   │   ├── ModelVersions.cshtml
│   │   ├── TrainingRuns.cshtml
│   │   └── CustomerConfigs.cshtml
│   └── Shared/
│       └── _Layout.cshtml
└── appsettings.json
```

---

## Step 2: Database Configuration

### 2.1 Update appsettings.json
```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Server=10.112.32.4;Database=retailchannelLogs;User Id=dbuser;Password=Codebase202212?!;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  }
}
```

### 2.2 Create DbContext
**File: Models/DbModels/ConfigDbContext.cs**

```csharp
using Microsoft.EntityFrameworkCore;

namespace ConfigManagementUI.Models.DbModels
{
    public class ConfigDbContext : DbContext
    {
        public ConfigDbContext(DbContextOptions<ConfigDbContext> options) : base(options) { }

        // Views (Read-only)
        public DbSet<dynamic> vw_FeaturesConfig { get; set; }
        public DbSet<dynamic> vw_ThresholdConfig { get; set; }
        public DbSet<dynamic> vw_RetrainingConfig { get; set; }
        public DbSet<dynamic> vw_ModelVersionConfig { get; set; }
        public DbSet<dynamic> vw_ModelTrainingRuns { get; set; }
        public DbSet<dynamic> vw_CustomerAccountTransferTypeConfig { get; set; }

        // Tables (For Updates)
        public DbSet<FeaturesConfig> FeaturesConfig { get; set; }
        public DbSet<ThresholdConfig> ThresholdConfig { get; set; }
        public DbSet<RetrainingConfig> RetrainingConfig { get; set; }
        public DbSet<ModelVersionConfig> ModelVersionConfig { get; set; }
        public DbSet<ModelTrainingRuns> ModelTrainingRuns { get; set; }
        public DbSet<CustomerAccountTransferTypeConfig> CustomerAccountTransferTypeConfig { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Configure views as keyless
            modelBuilder.Entity<dynamic>().HasNoKey();

            // Configure tables
            modelBuilder.Entity<FeaturesConfig>().ToTable("FeaturesConfig").HasKey(x => x.FeatureID);
            modelBuilder.Entity<ThresholdConfig>().ToTable("ThresholdConfig").HasKey(x => x.ThresholdID);
            modelBuilder.Entity<RetrainingConfig>().ToTable("RetrainingConfig").HasKey(x => x.ConfigId);
            modelBuilder.Entity<ModelVersionConfig>().ToTable("ModelVersionConfig").HasKey(x => x.ModelVersionID);
            modelBuilder.Entity<ModelTrainingRuns>().ToTable("ModelTrainingRuns").HasKey(x => x.RunId);
            modelBuilder.Entity<CustomerAccountTransferTypeConfig>().ToTable("CustomerAccountTransferTypeConfig").HasKey(x => x.ConfigID);
        }
    }
}
```

---

## Step 3: Create Models

### 3.1 FeaturesConfig Model
**File: Models/DbModels/FeaturesConfig.cs**

```csharp
namespace ConfigManagementUI.Models.DbModels
{
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
}
```

### 3.2 ThresholdConfig Model
**File: Models/DbModels/ThresholdConfig.cs**

```csharp
namespace ConfigManagementUI.Models.DbModels
{
    public class ThresholdConfig
    {
        public int ThresholdID { get; set; }
        public string ThresholdName { get; set; }
        public string ThresholdType { get; set; }
        public float ThresholdValue { get; set; }
        public float? MinValue { get; set; }
        public float? MaxValue { get; set; }
        public float? PreviousValue { get; set; }
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
}
```

### 3.3 RetrainingConfig Model
**File: Models/DbModels/RetrainingConfig.cs**

```csharp
namespace ConfigManagementUI.Models.DbModels
{
    public class RetrainingConfig
    {
        public int ConfigId { get; set; }
        public string Interval { get; set; }
        public bool IsEnabled { get; set; }
        public DateTime? LastRun { get; set; }
        public DateTime? NextRun { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public int WeeklyJobDay { get; set; }
        public int WeeklyJobHour { get; set; }
        public int WeeklyJobMinute { get; set; }
        public int MonthlyJobDay { get; set; }
        public int MonthlyJobHour { get; set; }
        public int MonthlyJobMinute { get; set; }
    }
}
```

### 3.4 ModelVersionConfig Model
**File: Models/DbModels/ModelVersionConfig.cs**

```csharp
namespace ConfigManagementUI.Models.DbModels
{
    public class ModelVersionConfig
    {
        public int ModelVersionID { get; set; }
        public string ModelName { get; set; }
        public string VersionNumber { get; set; }
        public string ModelPath { get; set; }
        public string ScalerPath { get; set; }
        public string ThresholdPath { get; set; }
        public bool IsActive { get; set; }
        public float? Accuracy { get; set; }
        public float? Precision { get; set; }
        public float? Recall { get; set; }
        public float? F1Score { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? DeployedAt { get; set; }
        public DateTime? RetiredAt { get; set; }
        public string CreatedBy { get; set; }
        public string DeployedBy { get; set; }
        public long TrainingDataSize { get; set; }
        public long ModelSize { get; set; }
        public string Notes { get; set; }
    }
}
```

### 3.5 ModelTrainingRuns Model
**File: Models/DbModels/ModelTrainingRuns.cs**

```csharp
namespace ConfigManagementUI.Models.DbModels
{
    public class ModelTrainingRuns
    {
        public int RunId { get; set; }
        public DateTime RunDate { get; set; }
        public string ModelVersion { get; set; }
        public string Status { get; set; }
        public int DataSize { get; set; }
        public string Metrics { get; set; }
    }
}
```

### 3.6 CustomerAccountTransferTypeConfig Model
**File: Models/DbModels/CustomerAccountTransferTypeConfig.cs**

```csharp
namespace ConfigManagementUI.Models.DbModels
{
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
        public float? MinValue { get; set; }
        public float? MaxValue { get; set; }
        public string Description { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public string CreatedBy { get; set; }
        public string UpdatedBy { get; set; }
    }
}
```

---

## Step 4: Create ViewModels

### 4.1 FeatureConfigViewModel
**File: Models/ViewModels/FeatureConfigViewModel.cs**

```csharp
namespace ConfigManagementUI.Models.ViewModels
{
    public class FeatureConfigViewModel
    {
        public int FeatureID { get; set; }
        public string FeatureName { get; set; }
        public string Description { get; set; }
        public bool IsEnabled { get; set; }
        public bool IsActive { get; set; }
        public string FeatureType { get; set; }
        public string Version { get; set; }
        public string Status => IsActive && IsEnabled ? "ACTIVE" : IsActive ? "DISABLED" : "INACTIVE";
        public DateTime UpdatedAt { get; set; }
    }
}
```

### 4.2 ThresholdConfigViewModel
**File: Models/ViewModels/ThresholdConfigViewModel.cs**

```csharp
namespace ConfigManagementUI.Models.ViewModels
{
    public class ThresholdConfigViewModel
    {
        public int ThresholdID { get; set; }
        public string ThresholdName { get; set; }
        public string ThresholdType { get; set; }
        public float ThresholdValue { get; set; }
        public float? MinValue { get; set; }
        public float? MaxValue { get; set; }
        public bool IsActive { get; set; }
        public string Description { get; set; }
        public DateTime? EffectiveFrom { get; set; }
        public DateTime? EffectiveTo { get; set; }
        public string ApprovalStatus { get; set; }
        public string ValidationStatus => IsOutOfRange() ? "OUT_OF_RANGE" : "VALID";
        
        private bool IsOutOfRange()
        {
            return ThresholdValue < MinValue || ThresholdValue > MaxValue;
        }
    }
}
```

### 4.3 RetrainingConfigViewModel
**File: Models/ViewModels/RetrainingConfigViewModel.cs**

```csharp
namespace ConfigManagementUI.Models.ViewModels
{
    public class RetrainingConfigViewModel
    {
        public int ConfigId { get; set; }
        public string Interval { get; set; }
        public bool IsEnabled { get; set; }
        public DateTime? LastRun { get; set; }
        public DateTime? NextRun { get; set; }
        public int WeeklyJobDay { get; set; }
        public int WeeklyJobHour { get; set; }
        public int WeeklyJobMinute { get; set; }
        public int MonthlyJobDay { get; set; }
        public int MonthlyJobHour { get; set; }
        public int MonthlyJobMinute { get; set; }
        
        public string WeeklyJobDayName => GetDayName(WeeklyJobDay);
        public string WeeklyJobTime => $"{WeeklyJobHour:D2}:{WeeklyJobMinute:D2}";
        public string MonthlyJobTime => $"{MonthlyJobHour:D2}:{MonthlyJobMinute:D2}";
        
        private string GetDayName(int day)
        {
            return day switch
            {
                0 => "Monday",
                1 => "Tuesday",
                2 => "Wednesday",
                3 => "Thursday",
                4 => "Friday",
                5 => "Saturday",
                6 => "Sunday",
                _ => "Unknown"
            };
        }
    }
}
```

---

## Step 5: Configure Startup

### 5.1 Update Program.cs
```csharp
using ConfigManagementUI.Models.DbModels;
using Microsoft.EntityFrameworkCore;

var builder = WebApplicationBuilder.CreateBuilder(args);

// Add services
builder.Services.AddControllersWithViews();
builder.Services.AddDbContext<ConfigDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();

// Configure middleware
if (!app.Environment.IsDevelopment())
{
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

---

## Step 6: Create Controller

### 6.1 ConfigController
**File: Controllers/ConfigController.cs**

```csharp
using ConfigManagementUI.Models.DbModels;
using ConfigManagementUI.Models.ViewModels;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace ConfigManagementUI.Controllers
{
    public class ConfigController : Controller
    {
        private readonly ConfigDbContext _context;
        private readonly ILogger<ConfigController> _logger;

        public ConfigController(ConfigDbContext context, ILogger<ConfigController> logger)
        {
            _context = context;
            _logger = logger;
        }

        // Dashboard
        public async Task<IActionResult> Index()
        {
            return View();
        }

        // Features
        public async Task<IActionResult> Features()
        {
            var features = await _context.FeaturesConfig
                .Select(f => new FeatureConfigViewModel
                {
                    FeatureID = f.FeatureID,
                    FeatureName = f.FeatureName,
                    Description = f.Description,
                    IsEnabled = f.IsEnabled,
                    IsActive = f.IsActive,
                    FeatureType = f.FeatureType,
                    Version = f.Version,
                    UpdatedAt = f.UpdatedAt
                })
                .ToListAsync();

            return View(features);
        }

        // Thresholds
        public async Task<IActionResult> Thresholds()
        {
            var thresholds = await _context.ThresholdConfig
                .Select(t => new ThresholdConfigViewModel
                {
                    ThresholdID = t.ThresholdID,
                    ThresholdName = t.ThresholdName,
                    ThresholdType = t.ThresholdType,
                    ThresholdValue = t.ThresholdValue,
                    MinValue = t.MinValue,
                    MaxValue = t.MaxValue,
                    IsActive = t.IsActive,
                    Description = t.Description,
                    EffectiveFrom = t.EffectiveFrom,
                    EffectiveTo = t.EffectiveTo,
                    ApprovalStatus = t.ApprovalStatus
                })
                .ToListAsync();

            return View(thresholds);
        }

        // Scheduler
        public async Task<IActionResult> Scheduler()
        {
            var config = await _context.RetrainingConfig.FirstOrDefaultAsync();
            if (config == null)
                return NotFound();

            var viewModel = new RetrainingConfigViewModel
            {
                ConfigId = config.ConfigId,
                Interval = config.Interval,
                IsEnabled = config.IsEnabled,
                LastRun = config.LastRun,
                NextRun = config.NextRun,
                WeeklyJobDay = config.WeeklyJobDay,
                WeeklyJobHour = config.WeeklyJobHour,
                WeeklyJobMinute = config.WeeklyJobMinute,
                MonthlyJobDay = config.MonthlyJobDay,
                MonthlyJobHour = config.MonthlyJobHour,
                MonthlyJobMinute = config.MonthlyJobMinute
            };

            return View(viewModel);
        }

        // Model Versions
        public async Task<IActionResult> ModelVersions()
        {
            var models = await _context.ModelVersionConfig
                .OrderByDescending(m => m.CreatedAt)
                .ToListAsync();

            return View(models);
        }

        // Training Runs
        public async Task<IActionResult> TrainingRuns()
        {
            var runs = await _context.ModelTrainingRuns
                .OrderByDescending(r => r.RunDate)
                .Take(100)
                .ToListAsync();

            return View(runs);
        }

        // Customer Configs
        public async Task<IActionResult> CustomerConfigs(string customerId = null)
        {
            var query = _context.CustomerAccountTransferTypeConfig.AsQueryable();

            if (!string.IsNullOrEmpty(customerId))
                query = query.Where(c => c.CustomerID == customerId);

            var configs = await query.ToListAsync();
            return View(configs);
        }

        // Toggle Feature
        [HttpPost]
        public async Task<IActionResult> ToggleFeature(int id)
        {
            var feature = await _context.FeaturesConfig.FindAsync(id);
            if (feature == null)
                return NotFound();

            feature.IsEnabled = !feature.IsEnabled;
            feature.UpdatedAt = DateTime.Now;
            feature.UpdatedBy = User.Identity?.Name ?? "System";

            await _context.SaveChangesAsync();
            return Ok(new { success = true, isEnabled = feature.IsEnabled });
        }

        // Update Threshold
        [HttpPost]
        public async Task<IActionResult> UpdateThreshold(int id, float value)
        {
            var threshold = await _context.ThresholdConfig.FindAsync(id);
            if (threshold == null)
                return NotFound();

            if (value < threshold.MinValue || value > threshold.MaxValue)
                return BadRequest("Value out of range");

            threshold.PreviousValue = threshold.ThresholdValue;
            threshold.ThresholdValue = value;
            threshold.UpdatedAt = DateTime.Now;
            threshold.UpdatedBy = User.Identity?.Name ?? "System";

            await _context.SaveChangesAsync();
            return Ok(new { success = true });
        }

        // Update Scheduler
        [HttpPost]
        public async Task<IActionResult> UpdateScheduler(RetrainingConfigViewModel model)
        {
            var config = await _context.RetrainingConfig.FindAsync(model.ConfigId);
            if (config == null)
                return NotFound();

            config.IsEnabled = model.IsEnabled;
            config.WeeklyJobDay = model.WeeklyJobDay;
            config.WeeklyJobHour = model.WeeklyJobHour;
            config.WeeklyJobMinute = model.WeeklyJobMinute;
            config.MonthlyJobDay = model.MonthlyJobDay;
            config.MonthlyJobHour = model.MonthlyJobHour;
            config.MonthlyJobMinute = model.MonthlyJobMinute;
            config.UpdatedAt = DateTime.Now;

            await _context.SaveChangesAsync();
            return Ok(new { success = true });
        }
    }
}
```

---

## Step 7: Create Views

### 7.1 Index.cshtml (Dashboard)
**File: Views/Config/Index.cshtml**

```html
@{
    ViewData["Title"] = "Configuration Management";
}

<div class="container-fluid mt-4">
    <h1>Configuration Management Dashboard</h1>
    
    <div class="row mt-4">
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Features</h5>
                    <p class="card-text">Manage feature flags and toggles</p>
                    <a href="@Url.Action("Features")" class="btn btn-primary">View Features</a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Thresholds</h5>
                    <p class="card-text">Configure risk thresholds and limits</p>
                    <a href="@Url.Action("Thresholds")" class="btn btn-primary">View Thresholds</a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Scheduler</h5>
                    <p class="card-text">Configure model retraining schedule</p>
                    <a href="@Url.Action("Scheduler")" class="btn btn-primary">View Scheduler</a>
                </div>
            </div>
        </div>
    </div>

    <div class="row mt-4">
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Model Versions</h5>
                    <p class="card-text">Manage deployed models</p>
                    <a href="@Url.Action("ModelVersions")" class="btn btn-primary">View Models</a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Training Runs</h5>
                    <p class="card-text">View model training history</p>
                    <a href="@Url.Action("TrainingRuns")" class="btn btn-primary">View Runs</a>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Customer Configs</h5>
                    <p class="card-text">Manage customer-specific rules</p>
                    <a href="@Url.Action("CustomerConfigs")" class="btn btn-primary">View Configs</a>
                </div>
            </div>
        </div>
    </div>
</div>
```

### 7.2 Features.cshtml
**File: Views/Config/Features.cshtml**

```html
@model List<FeatureConfigViewModel>

@{
    ViewData["Title"] = "Features Configuration";
}

<div class="container-fluid mt-4">
    <h1>Features Configuration</h1>
    
    <table class="table table-striped table-hover">
        <thead class="table-dark">
            <tr>
                <th>Feature Name</th>
                <th>Type</th>
                <th>Version</th>
                <th>Status</th>
                <th>Enabled</th>
                <th>Last Updated</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            @foreach (var feature in Model)
            {
                <tr>
                    <td>@feature.FeatureName</td>
                    <td>@feature.FeatureType</td>
                    <td>@feature.Version</td>
                    <td>
                        <span class="badge bg-@(feature.IsActive ? "success" : "danger")">
                            @feature.Status
                        </span>
                    </td>
                    <td>
                        <input type="checkbox" class="form-check-input feature-toggle" 
                               data-id="@feature.FeatureID" 
                               @(feature.IsEnabled ? "checked" : "") />
                    </td>
                    <td>@feature.UpdatedAt.ToString("yyyy-MM-dd HH:mm")</td>
                    <td>
                        <button class="btn btn-sm btn-info" data-bs-toggle="modal" 
                                data-bs-target="#detailsModal" 
                                onclick="showDetails('@feature.FeatureName', '@feature.Description')">
                            Details
                        </button>
                    </td>
                </tr>
            }
        </tbody>
    </table>
</div>

<script>
document.querySelectorAll('.feature-toggle').forEach(checkbox => {
    checkbox.addEventListener('change', async function() {
        const id = this.dataset.id;
        const response = await fetch(`/Config/ToggleFeature/${id}`, { method: 'POST' });
        if (response.ok) {
            alert('Feature toggled successfully');
        }
    });
});
</script>
```

---

## Step 8: Run Application

```bash
dotnet build
dotnet run
```

Navigate to: `https://localhost:5001/Config`

---

## Next Steps

1. Add authentication/authorization
2. Implement audit logging
3. Add data validation
4. Create API endpoints for AJAX calls
5. Add search/filter functionality
6. Implement pagination for large datasets
7. Add export to CSV/Excel
8. Create admin approval workflow

---

## Database Views Reference

All views are created in `docs/CREATE_CONFIG_VIEWS.sql`

Run this script before starting the application to ensure views are available.

