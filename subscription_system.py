"""
نظام الاشتراكات - للـ Admin Panel
"""

import sqlite3
import hashlib
from datetime import datetime, timedelta
import threading

class SubscriptionSystem:
    def __init__(self, db_path='subscriptions.db'):
        """تهيئة نظام الاشتراكات"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()
        
        self.create_tables()
        self.create_default_admin()
        self.create_default_plans()
    
    def create_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        with self.lock:
            # جدول المستخدمين
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    device_id TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول الاشتراكات
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    max_products INTEGER DEFAULT 100,
                    max_users INTEGER DEFAULT 1,
                    price REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # جدول خطط الاشتراك
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscription_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    duration_days INTEGER NOT NULL,
                    price REAL NOT NULL,
                    max_products INTEGER DEFAULT 100,
                    max_users INTEGER DEFAULT 1,
                    features TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول سجل النشاطات
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            self.conn.commit()
    
    def hash_password(self, password):
        """تشفير كلمة المرور"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_default_admin(self):
        """إنشاء حساب مدير افتراضي"""
        self.cursor.execute('SELECT COUNT(*) FROM users WHERE is_admin = 1')
        if self.cursor.fetchone()[0] == 0:
            # حساب المدير الرئيسي
            admin_email = 'mostshar@gmail.com'
            admin_password = 'admin'
            
            self.cursor.execute('''
                INSERT INTO users (email, password_hash, full_name, is_admin)
                VALUES (?, ?, ?, 1)
            ''', (admin_email, self.hash_password(admin_password), 'المدير'))
            
            self.conn.commit()
    
    def create_default_plans(self):
        """إنشاء خطط اشتراك افتراضية"""
        self.cursor.execute('SELECT COUNT(*) FROM subscription_plans')
        if self.cursor.fetchone()[0] == 0:
            plans = [
                ('تجربة مجانية', 7, 0, 50, 1, 'اشتراك تجريبي لمدة 7 أيام'),
                ('شهري', 30, 100, 500, 5, 'اشتراك شهري'),
                ('ربع سنوي', 90, 250, 1000, 10, 'اشتراك 3 أشهر'),
                ('سنوي', 365, 800, 5000, 50, 'اشتراك سنة كاملة'),
            ]
            
            self.cursor.executemany('''
                INSERT INTO subscription_plans 
                (name, duration_days, price, max_products, max_users, features)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', plans)
            
            self.conn.commit()
    
    def register_user(self, email, password, full_name=''):
        """تسجيل مستخدم جديد"""
        try:
            with self.lock:
                password_hash = self.hash_password(password)
                
                self.cursor.execute('''
                    INSERT INTO users (email, password_hash, full_name)
                    VALUES (?, ?, ?)
                ''', (email, password_hash, full_name))
                
                user_id = self.cursor.lastrowid
                self.conn.commit()
                
                # إنشاء اشتراك تجريبي
                self.create_trial_subscription(user_id)
                
                return user_id
        except sqlite3.IntegrityError:
            return None
    
    def login_user(self, email, password):
        """تسجيل دخول المستخدم"""
        with self.lock:
            password_hash = self.hash_password(password)
            
            self.cursor.execute('''
                SELECT * FROM users 
                WHERE email = ? AND password_hash = ? AND is_active = 1
            ''', (email, password_hash))
            
            user = self.cursor.fetchone()
            return dict(user) if user else None
    
    def create_trial_subscription(self, user_id):
        """إنشاء اشتراك تجريبي"""
        return self.create_subscription(
            user_id=user_id,
            plan_name='تجربة مجانية',
            duration_days=7,
            max_products=50,
            max_users=1,
            price=0
        )
    
    def create_subscription(self, user_id, plan_name, duration_days, max_products, max_users, price):
        """إنشاء اشتراك جديد"""
        with self.lock:
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=duration_days)
            
            self.cursor.execute('''
                INSERT INTO subscriptions 
                (user_id, plan_name, start_date, end_date, max_products, max_users, price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, plan_name, start_date, end_date, max_products, max_users, price))
            
            self.conn.commit()
            return True
    
    def get_user_subscription(self, user_id):
        """جلب اشتراك المستخدم"""
        with self.lock:
            self.cursor.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? 
                ORDER BY end_date DESC 
                LIMIT 1
            ''', (user_id,))
            
            sub = self.cursor.fetchone()
            
            if not sub:
                return None
            
            # حساب الأيام المتبقية
            end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d')
            today = datetime.now()
            days_remaining = (end_date - today).days
            
            return {
                'id': sub['id'],
                'plan_name': sub['plan_name'],
                'start_date': sub['start_date'],
                'end_date': sub['end_date'],
                'days_remaining': max(0, days_remaining),
                'is_active': bool(sub['is_active']) and days_remaining >= 0,
                'max_products': sub['max_products'],
                'max_users': sub['max_users'],
                'price': sub['price']
            }
    
    def check_subscription_valid(self, user_id):
        """التحقق من صلاحية الاشتراك"""
        subscription = self.get_user_subscription(user_id)
        
        if not subscription:
            return False, "لا يوجد اشتراك نشط"
        
        if not subscription['is_active']:
            return False, "انتهى الاشتراك. يرجى التجديد."
        
        return True, subscription
    
    def extend_subscription(self, user_id, days):
        """تمديد الاشتراك"""
        with self.lock:
            self.cursor.execute('''
                UPDATE subscriptions 
                SET end_date = date(end_date, '+' || ? || ' days')
                WHERE user_id = ? AND is_active = 1
            ''', (days, user_id))
            
            self.conn.commit()
            return self.cursor.rowcount > 0
    
    def update_user_status(self, user_id, is_active):
        """تحديث حالة المستخدم"""
        with self.lock:
            self.cursor.execute('''
                UPDATE users SET is_active = ? WHERE id = ?
            ''', (1 if is_active else 0, user_id))
            
            self.conn.commit()
    
    def get_all_users(self):
        """جلب جميع المستخدمين"""
        with self.lock:
            self.cursor.execute('''
                SELECT 
                    u.*,
                    s.plan_name,
                    s.end_date,
                    s.is_active as subscription_active
                FROM users u
                LEFT JOIN subscriptions s ON u.id = s.user_id
                ORDER BY u.created_at DESC
            ''')
            
            return [dict(row) for row in self.cursor.fetchall()]
    
    def get_all_plans(self):
        """جلب جميع الخطط"""
        with self.lock:
            self.cursor.execute('SELECT * FROM subscription_plans ORDER BY price')
            return [dict(row) for row in self.cursor.fetchall()]
    
    def log_activity(self, user_id, action, details=''):
        """تسجيل نشاط"""
        with self.lock:
            self.cursor.execute('''
                INSERT INTO activity_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, details))
            
            self.conn.commit()
    
    def get_statistics(self):
        """جلب إحصائيات"""
        with self.lock:
            # إجمالي المستخدمين
            self.cursor.execute('SELECT COUNT(*) as total FROM users WHERE is_admin = 0')
            total_users = self.cursor.fetchone()['total']
            
            # الاشتراكات النشطة
            self.cursor.execute('''
                SELECT COUNT(*) as total FROM subscriptions 
                WHERE is_active = 1 AND date(end_date) >= date('now')
            ''')
            active_subs = self.cursor.fetchone()['total']
            
            # الاشتراكات المنتهية
            self.cursor.execute('''
                SELECT COUNT(*) as total FROM subscriptions 
                WHERE date(end_date) < date('now')
            ''')
            expired_subs = self.cursor.fetchone()['total']
            
            # إجمالي الإيرادات
            self.cursor.execute('SELECT SUM(price) as total FROM subscriptions')
            total_revenue = self.cursor.fetchone()['total'] or 0
            
            return {
                'total_users': total_users,
                'active_subscriptions': active_subs,
                'expired_subscriptions': expired_subs,
                'total_revenue': total_revenue
            }


# مثيل عام
subscription_system = SubscriptionSystem()
