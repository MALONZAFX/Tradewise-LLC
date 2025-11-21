# complete_blog_fix.ps1
Write-Host "🎯 APPLYING COMPLETE BLOGPOST FIX..." -ForegroundColor Green

# 1. Clean migrations
Write-Host "🧹 Cleaning migrations..." -ForegroundColor Yellow
Remove-Item myapp/migrations/0*.py -Force
Remove-Item myapp/migrations/__pycache__ -Recurse -Force

# 2. Reset and create fresh migrations
Write-Host "🔄 Creating fresh migrations..." -ForegroundColor Yellow
python manage.py migrate --fake myapp zero
python manage.py makemigrations myapp
python manage.py migrate

# 3. Run the blog fix script
Write-Host "🔧 Running blog fix..." -ForegroundColor Yellow
python fix_blog.py

Write-Host "🎉 COMPLETE! Your blog system should now work permanently." -ForegroundColor Green