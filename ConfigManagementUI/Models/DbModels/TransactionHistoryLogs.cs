namespace ConfigManagementUI.Models.DbModels
{
    public class TransactionHistoryLogs
    {
        public string? TransactionId { get; set; }
        public string? CustomerId { get; set; }
        public string? FromAccountNo { get; set; }
        public string? ToAccountNo { get; set; }
        public decimal? Amount { get; set; }
        public char? TransferType { get; set; }
        public string? BankCountry { get; set; }
        public string? Advice { get; set; }
        public decimal? RiskScore { get; set; }
        public string? RiskLevel { get; set; }
        public decimal? ConfidenceLevel { get; set; }
        public decimal? ModelAgreement { get; set; }
        public string? Reasons { get; set; }
        public bool? RuleEngineViolated { get; set; }
        public decimal? RuleEngineThreshold { get; set; }
        public decimal? IsolationForestScore { get; set; }
        public bool? IsolationForestAnomaly { get; set; }
        public decimal? AutoencoderError { get; set; }
        public decimal? AutoencoderThreshold { get; set; }
        public bool? AutoencoderAnomaly { get; set; }
        public string? UserAction { get; set; }
        public string? ActionedBy { get; set; }
        public DateTime? ActionTimestamp { get; set; }
        public string? ActionComments { get; set; }
        public DateTime? CreatedAt { get; set; }
        public int? ProcessingTimeMs { get; set; }
        public string? FromAccountCurrency { get; set; }
        public string? TransferCurrency { get; set; }
        public string? ChargesType { get; set; }
        public string? SwiftCode { get; set; }
        public bool? CheckConstraint { get; set; }
    }
}
