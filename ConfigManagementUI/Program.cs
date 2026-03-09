using ConfigManagementUI.Models.DbModels;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllersWithViews();

// Database Connection - Environment variable ya appsettings se automatic uthayega
builder.Services.AddDbContext<ConfigDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios.
    app.UseHsts();
}

// 1. Static Files Middleware - Ye routing se pehle hona chahiye
app.UseStaticFiles();

app.UseHttpsRedirection();

// 2. Routing Middleware
app.UseRouting();

app.UseAuthorization();

// 3. Static Assets Mapping (.NET 9 features)
app.MapStaticAssets();

// 4. Default Route Configuration
app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Config}/{action=Index}/{id?}")
    .WithStaticAssets();

app.Run();