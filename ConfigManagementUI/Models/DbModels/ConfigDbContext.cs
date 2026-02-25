using Microsoft.EntityFrameworkCore;

namespace ConfigManagementUI.Models.DbModels
{
    public class ConfigDbContext : DbContext
    {
        public ConfigDbContext(DbContextOptions<ConfigDbContext> options) : base(options) { }

        public DbSet<FeaturesConfig> FeaturesConfig { get; set; }
        public DbSet<ThresholdConfig> ThresholdConfig { get; set; }
        public DbSet<RetrainingConfig> RetrainingConfig { get; set; }
        public DbSet<ModelVersionConfig> ModelVersionConfig { get; set; }
        public DbSet<ModelTrainingRuns> ModelTrainingRuns { get; set; }
        public DbSet<CustomerAccountTransferTypeConfig> CustomerAccountTransferTypeConfig { get; set; }
        public DbSet<TransactionHistoryLogs> TransactionHistoryLogs { get; set; }
        public DbSet<APITransactionLogs> APITransactionLogs { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<FeaturesConfig>().ToTable("FeaturesConfig").HasKey(x => x.FeatureID);
            modelBuilder.Entity<ThresholdConfig>().ToTable("ThresholdConfig").HasKey(x => x.ThresholdID);
            modelBuilder.Entity<RetrainingConfig>().ToTable("RetrainingConfig").HasKey(x => x.ConfigId);
            modelBuilder.Entity<ModelVersionConfig>().ToTable("ModelVersionConfig").HasKey(x => x.ModelVersionID);
            modelBuilder.Entity<ModelTrainingRuns>().ToTable("ModelTrainingRuns").HasKey(x => x.RunId);
            modelBuilder.Entity<CustomerAccountTransferTypeConfig>().ToTable("CustomerAccountTransferTypeConfig").HasKey(x => x.ConfigID);
            
            // Configure APITransactionLogs decimal precision
            modelBuilder.Entity<APITransactionLogs>().ToTable("APITransactionLogs").HasKey(x => x.TransactionId);
            modelBuilder.Entity<APITransactionLogs>()
                .Property(x => x.Amount).HasPrecision(18, 2);
            modelBuilder.Entity<APITransactionLogs>()
                .Property(x => x.FlagAmount).HasPrecision(18, 2);
            modelBuilder.Entity<APITransactionLogs>()
                .Property(x => x.AmountInAed).HasPrecision(18, 2);

            // Configure TransactionHistoryLogs decimal precision
            modelBuilder.Entity<TransactionHistoryLogs>().ToTable("TransactionHistoryLogs").HasKey(x => x.TransactionId);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.Amount).HasPrecision(18, 2);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.RiskScore).HasPrecision(18, 4);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.ConfidenceLevel).HasPrecision(18, 4);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.ModelAgreement).HasPrecision(18, 4);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.RuleEngineThreshold).HasPrecision(18, 4);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.IsolationForestScore).HasPrecision(18, 4);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.AutoencoderError).HasPrecision(18, 4);
            modelBuilder.Entity<TransactionHistoryLogs>()
                .Property(x => x.AutoencoderThreshold).HasPrecision(18, 4);
        }
    }
}
