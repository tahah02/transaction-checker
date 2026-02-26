namespace ConfigManagementUI.Models.ViewModels
{
    public class CustomerCombinationDto
    {
        public string? CustomerId { get; set; }
        public string? FromAccountNo { get; set; }
        public string? TransferType { get; set; }
    }

    public class CheckStatusDto
    {
        public string? ParameterName { get; set; }
        public bool IsEnabled { get; set; }
    }

    public class ModelStatusDto
    {
        public string? ModelName { get; set; }
        public bool IsEnabled { get; set; }
    }

    public class CustomerConfigDetailDto
    {
        public string? CustomerId { get; set; }
        public string? FromAccountNo { get; set; }
        public string? TransferType { get; set; }
        public List<CheckStatusDto>? Checks { get; set; }
        public List<ModelStatusDto>? Models { get; set; }
    }

    public class UpdateStatusRequest
    {
        public string? CustomerId { get; set; }
        public string? FromAccountNo { get; set; }
        public string? TransferType { get; set; }
        public string? ParameterName { get; set; }
        public bool IsEnabled { get; set; }
    }

    public class ApiResponse<T>
    {
        public bool Success { get; set; }
        public string? Message { get; set; }
        public T? Data { get; set; }
    }
}
