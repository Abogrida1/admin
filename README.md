# 🔐 Admin Panel - Server Side

## 📋 نظرة عامة

هذا هو **Admin Panel** لنظام إدارة المخزون - الجزء الخاص بالسيرفر فقط.

### المحتويات:
```
admin_app.py           → Admin Panel الرئيسي
admin_api.py           → API endpoints للعملاء
subscription_system.py → نظام إدارة الاشتراكات
templates/
  ├─ admin_login.html
  ├─ admin_panel.html
  └─ subscription_expired.html
```

---

## 🚀 التشغيل السريع

### **1. تثبيت المتطلبات:**
```bash
pip install -r requirements.txt
```

### **2. تشغيل السيرفر:**
```bash
python admin_app.py
```

### **3. الوصول للوحة التحكم:**
```
http://YOUR_SERVER_IP:5001
```

**بيانات الدخول الافتراضية:**
```
اسم المستخدم: admin
كلمة المرور: admin123
```

⚠️ **مهم:** غيّر كلمة المرور من ملف `admin_app.py` (السطر 20-21)

---

## 🌐 API Endpoints (للعملاء)

### **تسجيل حساب جديد:**
```
POST /api/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "اسم المستخدم",
  "device_id": "unique-device-id"
}
```

### **تسجيل دخول:**
```
POST /api/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "device_id": "unique-device-id"
}
```

### **مزامنة الاشتراك:**
```
POST /api/sync-subscription
Content-Type: application/json

{
  "email": "user@example.com",
  "device_id": "unique-device-id"
}
```

### **فحص السيرفر:**
```
GET /api/check-server
```

---

## 📊 الوظائف المتاحة

### **في لوحة التحكم:**

1. **إدارة المستخدمين:**
   - عرض جميع المستخدمين
   - تفعيل/تعطيل حساب
   - حذف مستخدم

2. **إدارة الاشتراكات:**
   - إنشاء اشتراك جديد
   - تمديد اشتراك موجود
   - تغيير خطة الاشتراك

3. **إدارة الخطط:**
   - عرض الخطط المتاحة
   - إضافة خطة جديدة
   - تعديل/حذف خطة

4. **الإحصائيات:**
   - عدد المستخدمين
   - الاشتراكات النشطة
   - الإيرادات

5. **سجل النشاطات:**
   - تتبع كل العمليات
   - تسجيل الدخول
   - التعديلات

---

## 🔒 الأمان

### **قاعدة البيانات:**
```
subscriptions.db
  ├─ users              (جميع المستخدمين)
  ├─ subscriptions      (جميع الاشتراكات)
  ├─ subscription_plans (خطط الاشتراك)
  └─ activity_log       (سجل النشاطات)
```

### **الحماية:**
- ✅ تشفير كلمات المرور (SHA256)
- ✅ Session management
- ✅ Admin authentication
- ✅ Activity logging

---

## 🛠️ التثبيت على VPS/Server

### **Linux (Ubuntu/Debian):**

```bash
# 1. تحديث النظام
sudo apt update && sudo apt upgrade -y

# 2. تثبيت Python
sudo apt install python3 python3-pip -y

# 3. نقل الملفات
# استخدم SCP أو Git

# 4. تثبيت المتطلبات
cd /path/to/admin
pip3 install -r requirements.txt

# 5. تشغيل السيرفر
python3 admin_app.py

# للتشغيل في الخلفية:
nohup python3 admin_app.py > admin.log 2>&1 &
```

### **Windows Server:**

```powershell
# 1. تثبيت Python من python.org

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. تشغيل السيرفر
python admin_app.py
```

---

## 🌍 الوصول من خارج الشبكة

### **الخيار 1: Port Forwarding**
```
1. افتح Port 5001 في الراوتر
2. استخدم IP الخارجي:
   http://YOUR_PUBLIC_IP:5001
```

### **الخيار 2: Ngrok (للتجربة)**
```bash
ngrok http 5001
```

### **الخيار 3: Domain Name**
```
1. احجز دومين
2. وجّه الدومين للسيرفر
3. استخدم:
   http://your-domain.com:5001
```

---

## 📡 ربط العملاء

عند توزيع التطبيق على العملاء، أعطهم:

```
رابط السيرفر:
http://YOUR_SERVER_IP:5001

أو:
https://your-domain.com:5001
```

سيدخلون هذا الرابط في تطبيق العميل عند أول استخدام.

---

## ⚙️ الإعدادات

### **تغيير Port:**
في `admin_app.py` (السطر الأخير):
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # غيّر 5001
```

### **تغيير بيانات Admin:**
في `admin_app.py` (السطر 20-21):
```python
ADMIN_USERNAME = "admin"       # غيّر هنا
ADMIN_PASSWORD = "admin123"    # غيّر هنا
```

### **تغيير بيانات المدير الافتراضي:**
في `subscription_system.py` (السطر 109-110):
```python
admin_email = 'mostshar@gmail.com'  # غيّر هنا
admin_password = 'admin'            # غيّر هنا
```

---

## 📝 الخطط الافتراضية

```
1. تجربة مجانية:  7 أيام  - 0 ج.م
2. شهري:          30 يوم   - 100 ج.م
3. ربع سنوي:      90 يوم   - 250 ج.م
4. سنوي:         365 يوم   - 800 ج.م
```

يمكن تعديلها من لوحة التحكم.

---

## 🆘 استكشاف الأخطاء

### **Port مشغول:**
```bash
# Linux
sudo netstat -tulpn | grep 5001

# Windows
netstat -ano | findstr :5001
```

### **لا يمكن الوصول:**
- تحقق من Firewall
- تحقق من Port Forwarding
- تحقق من IP السيرفر

### **خطأ في قاعدة البيانات:**
- احذف `subscriptions.db`
- شغّل السيرفر مرة أخرى (سيُنشئ جدول جديد)

---

## 📚 للمزيد

راجع الأدلة التفصيلية:
- `ONLINE_OFFLINE_SYSTEM_GUIDE.md`
- `ADMIN_PANEL_GUIDE.md`
- `README_ADMIN.md`

---

## 🎉 جاهز!

السيرفر الآن يعمل ويمكن للعملاء الاتصال به! 🚀

**رابط GitHub:** https://github.com/Abogrida1/admin.git

