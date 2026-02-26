using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ConfigManagementUI.Models.DbModels;
using ConfigManagementUI.Models.ViewModels;

namespace ConfigManagementUI.Controllers
{
    public class CustomerConfigController : Controller
    {
        private readonly ConfigDbContext _context;
        private readonly ILogger<CustomerConfigController> _logger;

        public CustomerConfigController(ConfigDbContext context, ILogger<CustomerConfigController> logger)
        {
            _context = context;
            _logger = logger;
        }

        // GET: CustomerConfig
        public IActionResult Index()
        {
            return View();
        }

        // API: Get unique customer combinations
        [HttpGet("api/customer-config/combinations")]
        public async Task<IActionResult> GetUniqueCustomerCombinations()
        {
            try
            {
                var combinations = await _context.TransactionHistoryLogs
                    .Where(t => !string.IsNullOrEmpty(t.CustomerId) && !string.IsNullOrEmpty(t.FromAccountNo) && t.TransferType != null)
                    .Select(t => new CustomerCombinationDto
                    {
                        CustomerId = t.CustomerId,
                        FromAccountNo = t.FromAccountNo,
                        TransferType = t.TransferType.ToString()
                    })
                    .Distinct()
                    .OrderBy(c => c.CustomerId)
                    .ThenBy(c => c.FromAccountNo)
                    .ThenBy(c => c.TransferType)
                    .ToListAsync();

                // Also get from APITransactionLogs
                var apiCombinations = await _context.APITransactionLogs
                    .Where(t => !string.IsNullOrEmpty(t.CustomerId) && !string.IsNullOrEmpty(t.FromAccountNo) && !string.IsNullOrEmpty(t.TransferType))
                    .Select(t => new CustomerCombinationDto
                    {
                        CustomerId = t.CustomerId,
                        FromAccountNo = t.FromAccountNo,
                        TransferType = t.TransferType
                    })
                    .Distinct()
                    .ToListAsync();

                // Merge and remove duplicates
                var allCombinations = combinations.Concat(apiCombinations)
                    .Distinct(new CombinationComparer())
                    .OrderBy(c => c.CustomerId)
                    .ThenBy(c => c.FromAccountNo)
                    .ThenBy(c => c.TransferType)
                    .ToList();

                return Ok(new ApiResponse<List<CustomerCombinationDto>>
                {
                    Success = true,
                    Data = allCombinations
                });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error fetching combinations: {ex.Message}");
                return BadRequest(new ApiResponse<object>
                {
                    Success = false,
                    Message = "Error fetching combinations"
                });
            }
        }

        // API: Get customer config details
        [HttpGet("api/customer-config/details")]
        public async Task<IActionResult> GetCustomerConfigDetails(string customerId, string fromAccountNo, string transferType)
        {
            try
            {
                var checks = new List<CheckStatusDto>
                {
                    new CheckStatusDto { ParameterName = "velocity_check_10min", IsEnabled = true },
                    new CheckStatusDto { ParameterName = "velocity_check_1hour", IsEnabled = true },
                    new CheckStatusDto { ParameterName = "monthly_spending_check", IsEnabled = true },
                    new CheckStatusDto { ParameterName = "new_beneficiary_check", IsEnabled = true }
                };

                var models = new List<ModelStatusDto>
                {
                    new ModelStatusDto { ModelName = "isolation_forest_enabled", IsEnabled = true },
                    new ModelStatusDto { ModelName = "autoencoder_enabled", IsEnabled = true }
                };

                // Get existing config from database
                var existingConfigs = await _context.CustomerAccountTransferTypeConfig
                    .Where(c => c.CustomerID == customerId && c.AccountNo == fromAccountNo && c.TransferType == transferType)
                    .ToListAsync();

                // Update checks with existing values
                foreach (var check in checks)
                {
                    var existing = existingConfigs.FirstOrDefault(c => c.ParameterName == check.ParameterName);
                    if (existing != null)
                    {
                        check.IsEnabled = existing.IsEnabled ?? true;
                    }
                }

                // Update models with existing values
                foreach (var model in models)
                {
                    var existing = existingConfigs.FirstOrDefault(c => c.ParameterName == model.ModelName);
                    if (existing != null)
                    {
                        model.IsEnabled = existing.IsEnabled ?? true;
                    }
                }

                var detail = new CustomerConfigDetailDto
                {
                    CustomerId = customerId,
                    FromAccountNo = fromAccountNo,
                    TransferType = transferType,
                    Checks = checks,
                    Models = models
                };

                return Ok(new ApiResponse<CustomerConfigDetailDto>
                {
                    Success = true,
                    Data = detail
                });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error fetching config details: {ex.Message}");
                return BadRequest(new ApiResponse<object>
                {
                    Success = false,
                    Message = "Error fetching config details"
                });
            }
        }

        // API: Update check or model status
        [HttpPost("api/customer-config/update-status")]
        public async Task<IActionResult> UpdateCheckOrModelStatus([FromBody] UpdateStatusRequest request)
        {
            try
            {
                var existing = await _context.CustomerAccountTransferTypeConfig
                    .OrderByDescending(x => x.ConfigID)
                    .FirstOrDefaultAsync(c => c.CustomerID == request.CustomerId && 
                                             c.AccountNo == request.FromAccountNo && 
                                             c.TransferType == request.TransferType &&
                                             c.ParameterName == request.ParameterName);

                if (existing != null)
                {
                    existing.IsEnabled = request.IsEnabled;
                    existing.UpdatedAt = DateTime.Now;
                    existing.UpdatedBy = User?.Identity?.Name ?? "System";
                }
                else
                {
                    var newConfig = new CustomerAccountTransferTypeConfig
                    {
                        CustomerID = request.CustomerId,
                        AccountNo = request.FromAccountNo,
                        TransferType = request.TransferType,
                        ParameterName = request.ParameterName,
                        IsEnabled = request.IsEnabled,
                        IsActive = true,
                        CreatedAt = DateTime.Now,
                        UpdatedAt = DateTime.Now,
                        CreatedBy = User?.Identity?.Name ?? "System",
                        UpdatedBy = User?.Identity?.Name ?? "System"
                    };
                    _context.CustomerAccountTransferTypeConfig.Add(newConfig);
                }

                await _context.SaveChangesAsync();

                return Ok(new ApiResponse<object>
                {
                    Success = true,
                    Message = "Status updated successfully"
                });
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error updating status: {ex.Message}");
                return BadRequest(new ApiResponse<object>
                {
                    Success = false,
                    Message = "Error updating status"
                });
            }
        }
    }

    // Comparer for removing duplicate combinations
    public class CombinationComparer : IEqualityComparer<CustomerCombinationDto>
    {
        public bool Equals(CustomerCombinationDto? x, CustomerCombinationDto? y)
        {
            return x?.CustomerId == y?.CustomerId && 
                   x?.FromAccountNo == y?.FromAccountNo && 
                   x?.TransferType == y?.TransferType;
        }

        public int GetHashCode(CustomerCombinationDto obj)
        {
            return HashCode.Combine(obj.CustomerId, obj.FromAccountNo, obj.TransferType);
        }
    }
}
