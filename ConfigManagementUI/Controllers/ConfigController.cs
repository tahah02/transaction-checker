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

        public async Task<IActionResult> Index()
        {
            return View();
        }

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

        public async Task<IActionResult> Scheduler()
        {
            var config = await _context.RetrainingConfig.OrderByDescending(x => x.ConfigId).FirstOrDefaultAsync();
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

        public async Task<IActionResult> ModelVersions()
        {
            var models = await _context.ModelVersionConfig
                .OrderByDescending(m => m.CreatedAt)
                .ToListAsync();

            return View(models);
        }

        public async Task<IActionResult> TrainingRuns()
        {
            var runs = await _context.ModelTrainingRuns
                .OrderByDescending(r => r.RunDate)
                .Take(100)
                .ToListAsync();

            return View(runs);
        }

        public async Task<IActionResult> CustomerConfigs(string customerId = null)
        {
            var query = _context.CustomerAccountTransferTypeConfig.AsQueryable();

            if (!string.IsNullOrEmpty(customerId))
                query = query.Where(c => c.CustomerID == customerId);

            var configs = await query.ToListAsync();
            return View(configs);
        }

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

        [HttpPost]
        public async Task<IActionResult> UpdateFeature(int id, [FromBody] dynamic model)
        {
            var feature = await _context.FeaturesConfig.FindAsync(id);
            if (feature == null)
                return NotFound();

            feature.FeatureType = model.featureType ?? feature.FeatureType;
            feature.Version = model.version ?? feature.Version;
            feature.Description = model.description ?? feature.Description;
            feature.IsActive = model.isActive;
            feature.UpdatedAt = DateTime.Now;
            feature.UpdatedBy = User.Identity?.Name ?? "System";

            await _context.SaveChangesAsync();
            return Ok(new { success = true });
        }

        [HttpPost]
        public async Task<IActionResult> UpdateThreshold(int id, double thresholdValue, double? minValue, double? maxValue, string? approvalStatus)
        {
            var threshold = await _context.ThresholdConfig.FindAsync(id);
            if (threshold == null)
                return NotFound();

            if (thresholdValue < (minValue ?? 0) || thresholdValue > (maxValue ?? double.MaxValue))
                return BadRequest("Value out of range");

            threshold.PreviousValue = threshold.ThresholdValue;
            threshold.ThresholdValue = thresholdValue;
            
            if (minValue.HasValue)
                threshold.MinValue = minValue;
            
            if (maxValue.HasValue)
                threshold.MaxValue = maxValue;
            
            if (!string.IsNullOrEmpty(approvalStatus))
                threshold.ApprovalStatus = approvalStatus;
            
            threshold.UpdatedAt = DateTime.Now;
            threshold.UpdatedBy = User.Identity?.Name ?? "System";

            await _context.SaveChangesAsync();
            return Ok(new { success = true });
        }

        [HttpPost]
        public async Task<IActionResult> UpdateScheduler([FromBody] RetrainingConfigViewModel model)
        {
            try
            {
                _logger.LogInformation($"UpdateScheduler called with ConfigId: {model.ConfigId}");
                
                var config = await _context.RetrainingConfig.FindAsync(model.ConfigId);
                if (config == null)
                {
                    _logger.LogWarning($"Config not found for ConfigId: {model.ConfigId}");
                    return NotFound();
                }

                config.IsEnabled = model.IsEnabled;
                config.WeeklyJobDay = model.WeeklyJobDay ?? 0;
                config.WeeklyJobHour = model.WeeklyJobHour ?? 0;
                config.WeeklyJobMinute = model.WeeklyJobMinute ?? 0;
                config.MonthlyJobDay = model.MonthlyJobDay ?? 1;
                config.MonthlyJobHour = model.MonthlyJobHour ?? 0;
                config.MonthlyJobMinute = model.MonthlyJobMinute ?? 0;
                config.UpdatedAt = DateTime.Now;

                await _context.SaveChangesAsync();
                _logger.LogInformation("Configuration saved successfully");
                return Ok(new { success = true });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error updating scheduler: {ex.Message}");
                return BadRequest(new { success = false, message = ex.Message });
            }
        }
    }
}
