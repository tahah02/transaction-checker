namespace ConfigManagementUI.Models.DbModels
{
    public class APITransactionLogs
    {
        public string? TransactionId { get; set; }
        public string? UserId { get; set; }
        public string? CustomerId { get; set; }
        public string? TransferType { get; set; }
        public string? SubTransferType { get; set; }
        public string? FromAccountCurrency { get; set; }
        public string? FromAccountNo { get; set; }
        public string? SwiftCode { get; set; }
        public string? ReceipentAccount { get; set; }
        public string? ReceipentName { get; set; }
        public string? TransferAdditionalDetails { get; set; }
        public decimal? Amount { get; set; }
        public string? Currency { get; set; }
        public string? PurposeCode { get; set; }
        public string? CardId { get; set; }
        public string? CardType { get; set; }
        public string? Charges { get; set; }
        public bool? Status { get; set; }
        public string? StatusMessage { get; set; }
        public string? ReferenceNo { get; set; }
        public DateTime? CreateDate { get; set; }
        public string? RecipientAddress { get; set; }
        public string? Description { get; set; }
        public decimal? FlagAmount { get; set; }
        public string? FlagCurrency { get; set; }
        public decimal? AmountInAed { get; set; }
        public int? BankStatus { get; set; }
        public int? BankName { get; set; }
        public string? PurposeDetails { get; set; }
        public string? ChargesAmount { get; set; }
        public string? BenId { get; set; }
        public string? AccountType { get; set; }
        public string? BankCountry { get; set; }
        public bool? IsNpss { get; set; }
        public string? NpssMessageId { get; set; }
        public DateTime? NpssLastStatusUpdate { get; set; }
        public string? PsReferenceId { get; set; }
        public string? EdiyaCard { get; set; }
        public string? AC25ReferenceNumber { get; set; }
        public string? AC26ReferenceNumber { get; set; }
        public string? ChannelId { get; set; }
        public DateTime? MaxCompletiondate { get; set; }
    }
}
