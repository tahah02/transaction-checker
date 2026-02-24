# Scheduler Configuration Guide

## Overview

The weekly and monthly retraining job times are now **fully dynamic** and configurable via the **RetrainingConfig** database table. No code changes or environment variables needed.

## Database Configuration

### Table: RetrainingConfig

The table now includes these new columns:

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| WeeklyJobDay | INT | 0 | Day of week (0=Monday, 1=Tuesday, ..., 6=Sunday) |
| WeeklyJobHour | INT | 2 | Hour (0-23) |
| WeeklyJobMinute | INT | 0 | Minute (0-59) |
| MonthlyJobDay | INT | 1 | Day of month (1-31) |
| MonthlyJobHour | INT | 3 | Hour (0-23) |
| MonthlyJobMinute | INT | 0 | Minute (0-59) |

### Migration

Run this SQL to add the columns:

```sql
ALTER TABLE RetrainingConfig
ADD 
    WeeklyJobDay INT DEFAULT 0,
    WeeklyJobHour INT DEFAULT 2,
    WeeklyJobMinute INT DEFAULT 0,
    MonthlyJobDay INT DEFAULT 1,
    MonthlyJobHour INT DEFAULT 3,
    MonthlyJobMinute INT DEFAULT 0;

UPDATE RetrainingConfig 
SET 
    WeeklyJobDay = 0,
    WeeklyJobHour = 2,
    WeeklyJobMinute = 0,
    MonthlyJobDay = 1,
    MonthlyJobHour = 3,
    MonthlyJobMinute = 0
WHERE ConfigId = 1;
```

Or use the migration script: `docs/SCHEDULER_TABLE_MIGRATION.sql`

## How to Change Schedule

### Change Weekly Job Time

```sql
-- Run weekly job on Friday at 4:30 AM
UPDATE RetrainingConfig 
SET WeeklyJobDay = 4, WeeklyJobHour = 4, WeeklyJobMinute = 30 
WHERE ConfigId = 1;
```

**Day Values:**
- 0 = Monday
- 1 = Tuesday
- 2 = Wednesday
- 3 = Thursday
- 4 = Friday
- 5 = Saturday
- 6 = Sunday

### Change Monthly Job Time

```sql
-- Run monthly job on 15th at 5:00 AM
UPDATE RetrainingConfig 
SET MonthlyJobDay = 15, MonthlyJobHour = 5, MonthlyJobMinute = 0 
WHERE ConfigId = 1;
```

**Day Values:** 1-31 (day of month)

### View Current Configuration

```sql
SELECT 
    WeeklyJobDay, WeeklyJobHour, WeeklyJobMinute,
    MonthlyJobDay, MonthlyJobHour, MonthlyJobMinute
FROM RetrainingConfig 
WHERE ConfigId = 1;
```

## How It Works

1. **Scheduler Startup**: When the API starts, `start_scheduler()` reads the configuration from the database
2. **Weekly Job**: Runs on the specified day and time
3. **Monthly Job**: Runs on the specified day of month and time
4. **Config Checker**: Runs every 5 minutes to detect changes
5. **Dynamic Updates**: If you change the database values, the scheduler detects the change within 5 minutes

## Examples

### Example 1: Daily Retraining at Midnight

```sql
-- Keep weekly job but change to daily via Interval
UPDATE RetrainingConfig 
SET Interval = '1D' 
WHERE ConfigId = 1;
```

### Example 2: Weekly on Sunday at 11 PM

```sql
UPDATE RetrainingConfig 
SET WeeklyJobDay = 6, WeeklyJobHour = 23, WeeklyJobMinute = 0 
WHERE ConfigId = 1;
```

### Example 3: Monthly on Last Day at 2 AM

```sql
UPDATE RetrainingConfig 
SET MonthlyJobDay = 31, MonthlyJobHour = 2, MonthlyJobMinute = 0 
WHERE ConfigId = 1;
```

### Example 4: Weekly on Wednesday at 3:15 AM, Monthly on 10th at 4:30 AM

```sql
UPDATE RetrainingConfig 
SET 
    WeeklyJobDay = 2, WeeklyJobHour = 3, WeeklyJobMinute = 15,
    MonthlyJobDay = 10, MonthlyJobHour = 4, MonthlyJobMinute = 30
WHERE ConfigId = 1;
```

## Verification

### Check if Changes Took Effect

1. Look at API logs for confirmation:
   ```
   Added weekly retraining job: 2 3:15
   Added monthly retraining job: day 10 4:30
   ```

2. Query the database:
   ```sql
   SELECT * FROM RetrainingConfig WHERE ConfigId = 1;
   ```

3. Check ModelTrainingRuns table for recent runs:
   ```sql
   SELECT TOP 10 RunDate, ModelVersion, Status 
   FROM ModelTrainingRuns 
   ORDER BY RunDate DESC;
   ```

## Troubleshooting

### Changes Not Taking Effect

1. **Check database connection**: Verify API can connect to database
2. **Check logs**: Look for errors in API startup logs
3. **Restart API**: Changes are read at startup, so restart if needed
4. **Wait 5 minutes**: Config checker runs every 5 minutes

### Invalid Values

- **WeeklyJobDay**: Must be 0-6
- **MonthlyJobDay**: Must be 1-31
- **Hour**: Must be 0-23
- **Minute**: Must be 0-59

Invalid values will cause errors in logs.

## Default Configuration

If no configuration is found in the database, the scheduler uses these defaults:

- **Weekly Job**: Monday at 2:00 AM
- **Monthly Job**: 1st of month at 3:00 AM

## Related Files

- `backend/mlops/scheduler.py` - Scheduler implementation
- `docs/SCHEDULER_TABLE_MIGRATION.sql` - Migration script
- `docs/MLOPS_SCHEDULER_GUIDE.md` - Complete MLOps guide
