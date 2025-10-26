"""
API endpoints للـ Admin Panel للاتصال من التطبيقات
"""

from flask import Flask, request, jsonify
from subscription_system import subscription_system
import hashlib

def add_api_routes(app):
    """إضافة API routes للـ Admin Panel"""
    
    @app.route('/api/register', methods=['POST'])
    def api_register():
        """تسجيل مستخدم جديد"""
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            full_name = data.get('full_name')
            device_id = data.get('device_id')
            
            if not email or not password:
                return jsonify({
                    'success': False,
                    'message': 'البريد وكلمة المرور مطلوبان'
                }), 400
            
            # التحقق من وجود المستخدم
            subscription_system.cursor.execute(
                'SELECT id FROM users WHERE email = ?', (email,)
            )
            existing = subscription_system.cursor.fetchone()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'البريد الإلكتروني مستخدم بالفعل'
                }), 400
            
            # تسجيل المستخدم
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            subscription_system.cursor.execute('''
                INSERT INTO users (email, password_hash, full_name, device_id)
                VALUES (?, ?, ?, ?)
            ''', (email, password_hash, full_name, device_id))
            
            user_id = subscription_system.cursor.lastrowid
            
            # إنشاء اشتراك تجريبي (7 أيام)
            subscription_system.create_trial_subscription(user_id)
            
            subscription_system.conn.commit()
            
            # جلب معلومات الاشتراك
            subscription = subscription_system.get_user_subscription(user_id)
            
            # تسجيل النشاط
            subscription_system.log_activity(
                user_id,
                'تسجيل حساب جديد',
                f'Device: {device_id}'
            )
            
            return jsonify({
                'success': True,
                'message': 'تم التسجيل بنجاح',
                'user': {
                    'id': user_id,
                    'email': email,
                    'full_name': full_name
                },
                'subscription': subscription
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'خطأ في التسجيل: {str(e)}'
            }), 500
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        """تسجيل دخول"""
        try:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            device_id = data.get('device_id')
            
            if not email or not password:
                return jsonify({
                    'success': False,
                    'message': 'البريد وكلمة المرور مطلوبان'
                }), 400
            
            # التحقق من المستخدم
            user = subscription_system.login_user(email, password)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'البريد أو كلمة المرور غير صحيحة'
                }), 401
            
            # تحديث device_id
            subscription_system.cursor.execute('''
                UPDATE users SET device_id = ? WHERE id = ?
            ''', (device_id, user['id']))
            subscription_system.conn.commit()
            
            # التحقق من الاشتراك
            valid, result = subscription_system.check_subscription_valid(user['id'])
            
            if not valid and not user['is_admin']:
                return jsonify({
                    'success': False,
                    'message': 'انتهى الاشتراك. يرجى التواصل مع المدير.'
                }), 403
            
            # جلب معلومات الاشتراك
            subscription = subscription_system.get_user_subscription(user['id'])
            
            # تسجيل النشاط
            subscription_system.log_activity(
                user['id'],
                'تسجيل دخول',
                f'Device: {device_id}'
            )
            
            return jsonify({
                'success': True,
                'message': 'تم تسجيل الدخول بنجاح',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'is_admin': user['is_admin']
                },
                'subscription': subscription
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'خطأ في تسجيل الدخول: {str(e)}'
            }), 500
    
    @app.route('/api/sync-subscription', methods=['POST'])
    def api_sync_subscription():
        """مزامنة الاشتراك"""
        try:
            data = request.get_json()
            email = data.get('email')
            device_id = data.get('device_id')
            
            if not email:
                return jsonify({
                    'success': False,
                    'message': 'البريد الإلكتروني مطلوب'
                }), 400
            
            # جلب المستخدم
            subscription_system.cursor.execute(
                'SELECT id FROM users WHERE email = ?', (email,)
            )
            user = subscription_system.cursor.fetchone()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'المستخدم غير موجود'
                }), 404
            
            user_id = user['id']
            
            # التحقق من الاشتراك
            valid, result = subscription_system.check_subscription_valid(user_id)
            
            if not valid:
                return jsonify({
                    'success': False,
                    'message': 'انتهى الاشتراك',
                    'subscription': {
                        'is_active': False,
                        'message': result
                    }
                }), 403
            
            # جلب معلومات الاشتراك
            subscription = subscription_system.get_user_subscription(user_id)
            
            # تسجيل النشاط
            subscription_system.log_activity(
                user_id,
                'مزامنة الاشتراك',
                f'Device: {device_id}'
            )
            
            return jsonify({
                'success': True,
                'message': 'تمت المزامنة بنجاح',
                'subscription': subscription
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'خطأ في المزامنة: {str(e)}'
            }), 500
    
    @app.route('/api/check-server', methods=['GET'])
    def api_check_server():
        """التحقق من عمل السيرفر"""
        return jsonify({
            'success': True,
            'message': 'السيرفر يعمل',
            'version': '1.0'
        })

