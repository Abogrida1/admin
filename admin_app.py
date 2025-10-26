"""
تطبيق Admin منفصل لإدارة الاشتراكات
يعمل بشكل مستقل ويتصل بنفس قاعدة البيانات
+ يوفر API للتطبيقات العملاء
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from subscription_system import subscription_system
from admin_api import add_api_routes
from functools import wraps

app = Flask(__name__)
app.secret_key = 'admin-secret-key-2025-very-secure'

# إضافة API routes
add_api_routes(app)

# ==================== Admin Authentication ====================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # غيّر كلمة المرور دي

def admin_required(f):
    """التحقق من تسجيل دخول Admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return redirect(url_for('admin_panel'))

@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    """تسجيل دخول Admin"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'اسم المستخدم أو كلمة المرور غير صحيحة'})
    
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    
    return render_template('admin_login.html')

@app.route('/logout')
def admin_logout():
    """تسجيل خروج"""
    session.clear()
    return redirect(url_for('admin_login'))

# ==================== Admin Panel ====================

@app.route('/panel')
@admin_required
def admin_panel():
    """لوحة تحكم المدير"""
    users = subscription_system.get_all_users()
    stats = subscription_system.get_statistics()
    plans = subscription_system.get_all_plans()
    
    return render_template('admin_panel.html', 
                         users=users, 
                         stats=stats,
                         plans=plans,
                         admin_mode=True)

# ==================== User Management ====================

@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    """جلب جميع المستخدمين"""
    users = subscription_system.get_all_users()
    return jsonify(users)

@app.route('/api/create-subscription', methods=['POST'])
@admin_required
def create_subscription():
    """إنشاء اشتراك"""
    data = request.get_json()
    
    success = subscription_system.create_subscription(
        user_id=data['user_id'],
        plan_name=data['plan_name'],
        duration_days=data['duration_days'],
        max_products=data['max_products'],
        max_users=data['max_users'],
        price=data['price']
    )
    
    if success:
        subscription_system.log_activity(
            data['user_id'], 
            f'تفعيل اشتراك من Admin Panel',
            f'خطة: {data["plan_name"]}'
        )
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'خطأ في إنشاء الاشتراك'})

@app.route('/api/extend-subscription', methods=['POST'])
@admin_required
def extend_subscription():
    """تمديد اشتراك"""
    data = request.get_json()
    
    success = subscription_system.extend_subscription(
        user_id=data['user_id'],
        days=data['days']
    )
    
    if success:
        subscription_system.log_activity(
            data['user_id'],
            f'تمديد اشتراك {data["days"]} يوم من Admin Panel'
        )
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'خطأ في التمديد'})

@app.route('/api/toggle-user-status', methods=['POST'])
@admin_required
def toggle_user_status():
    """تفعيل/تعطيل مستخدم"""
    data = request.get_json()
    
    subscription_system.update_user_status(
        user_id=data['user_id'],
        is_active=data['is_active']
    )
    
    action = 'تفعيل' if data['is_active'] else 'تعطيل'
    subscription_system.log_activity(
        data['user_id'],
        f'{action} الحساب من Admin Panel'
    )
    
    return jsonify({'success': True})

@app.route('/api/delete-user', methods=['POST'])
@admin_required
def delete_user():
    """حذف مستخدم"""
    data = request.get_json()
    user_id = data['user_id']
    
    try:
        subscription_system.cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
        subscription_system.cursor.execute('DELETE FROM activity_log WHERE user_id = ?', (user_id,))
        subscription_system.cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        subscription_system.conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== Statistics ====================

@app.route('/api/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """إحصائيات"""
    stats = subscription_system.get_statistics()
    return jsonify(stats)

@app.route('/api/activity-log', methods=['GET'])
@admin_required
def get_activity_log():
    """سجل النشاطات"""
    limit = request.args.get('limit', 50, type=int)
    
    subscription_system.cursor.execute('''
        SELECT a.*, u.email, u.full_name
        FROM activity_log a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', (limit,))
    
    activities = [dict(row) for row in subscription_system.cursor.fetchall()]
    return jsonify(activities)

# ==================== Plans Management ====================

@app.route('/api/plans', methods=['GET'])
@admin_required
def get_plans():
    """جلب خطط الاشتراك"""
    plans = subscription_system.get_all_plans()
    return jsonify(plans)

@app.route('/api/plans', methods=['POST'])
@admin_required
def create_plan():
    """إنشاء خطة جديدة"""
    data = request.get_json()
    
    try:
        subscription_system.cursor.execute('''
            INSERT INTO subscription_plans 
            (name, duration_days, price, max_products, max_users, features)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['name'],
            data['duration_days'],
            data['price'],
            data['max_products'],
            data['max_users'],
            data['features']
        ))
        subscription_system.conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/plans/<int:plan_id>', methods=['PUT'])
@admin_required
def update_plan(plan_id):
    """تحديث خطة"""
    data = request.get_json()
    
    try:
        subscription_system.cursor.execute('''
            UPDATE subscription_plans
            SET name = ?, duration_days = ?, price = ?,
                max_products = ?, max_users = ?, features = ?
            WHERE id = ?
        ''', (
            data['name'],
            data['duration_days'],
            data['price'],
            data['max_products'],
            data['max_users'],
            data['features'],
            plan_id
        ))
        subscription_system.conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/plans/<int:plan_id>', methods=['DELETE'])
@admin_required
def delete_plan(plan_id):
    """حذف خطة"""
    try:
        subscription_system.cursor.execute('DELETE FROM subscription_plans WHERE id = ?', (plan_id,))
        subscription_system.conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ==================== تشغيل التطبيق ====================

if __name__ == '__main__':
    import os
    
    print('=' * 70)
    print('🔐 Admin Panel - نظام إدارة الاشتراكات')
    print('=' * 70)
    print()
    print('⚠️  هذا التطبيق للمدير فقط!')
    print()
    print('📱 افتح المتصفح على:')
    print('   http://localhost:5001')
    print()
    print('🔑 بيانات الدخول:')
    print('   اسم المستخدم: admin')
    print('   كلمة المرور: admin123')
    print()
    print('💾 قاعدة البيانات: subscriptions.db')
    print('   (مشتركة مع التطبيق الأساسي)')
    print()
    print('⚠️  للإيقاف: اضغط Ctrl+C')
    print('=' * 70)
    print()
    
    # تشغيل على port مختلف (يدعم Render)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)

