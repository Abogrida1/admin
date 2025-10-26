@echo off
chcp 65001 >nul
title Admin Panel - إدارة الاشتراكات

echo.
echo ========================================
echo   Admin Panel - لوحة إدارة الاشتراكات
echo ========================================
echo.

echo [*] تشغيل لوحة التحكم...
echo.
echo 📱 افتح المتصفح على:
echo    http://localhost:5001
echo.
echo 🔑 بيانات الدخول:
echo    اسم المستخدم: admin
echo    كلمة المرور: admin123
echo.
echo ⚠️  هذا التطبيق للمدير فقط!
echo.
echo ========================================
echo.

python admin_app.py

pause

