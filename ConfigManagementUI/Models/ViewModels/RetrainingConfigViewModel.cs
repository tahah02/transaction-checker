namespace ConfigManagementUI.Models.ViewModels
{
    public class RetrainingConfigViewModel
    {
        public int ConfigId { get; set; }
        public string? Interval { get; set; }
        public bool IsEnabled { get; set; }
        public DateTime? LastRun { get; set; }
        public DateTime? NextRun { get; set; }
        public int? WeeklyJobDay { get; set; }
        public int? WeeklyJobHour { get; set; }
        public int? WeeklyJobMinute { get; set; }
        public int? MonthlyJobDay { get; set; }
        public int? MonthlyJobHour { get; set; }
        public int? MonthlyJobMinute { get; set; }
        
        public string WeeklyJobDayName => GetDayName(WeeklyJobDay ?? 0);
        public string WeeklyJobTime => $"{(WeeklyJobHour ?? 0):D2}:{(WeeklyJobMinute ?? 0):D2}";
        public string MonthlyJobTime => $"{(MonthlyJobHour ?? 0):D2}:{(MonthlyJobMinute ?? 0):D2}";
        
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
