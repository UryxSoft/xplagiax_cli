# test_payment_config.py
"""
Script para verificar la configuración de Stripe y PayPal
Ejecuta este script para asegurarte de que todo está correctamente configurado
"""

import sys

def test_imports():
    """Verificar que las dependencias estén instaladas"""
    print("🔍 Verificando dependencias...")
    
    try:
        import stripe
        print("✅ Stripe instalado correctamente")
    except ImportError:
        print("❌ Stripe no está instalado. Ejecuta: pip install stripe")
        return False
    
    try:
        import paypalrestsdk
        print("✅ PayPal SDK instalado correctamente")
    except ImportError:
        print("❌ PayPal SDK no está instalado. Ejecuta: pip install paypalrestsdk")
        return False
    
    return True

def test_stripe_config():
    """Verificar configuración de Stripe"""
    print("\n🔍 Verificando configuración de Stripe...")
    
    try:
        import stripe
        from config import STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY
        
        if not STRIPE_SECRET_KEY or STRIPE_SECRET_KEY == 'sk_test_xxxxxxxxxxxxxxxxxxxxx':
            print("⚠️  STRIPE_SECRET_KEY no está configurado")
            return False
        
        if not STRIPE_PUBLISHABLE_KEY or STRIPE_PUBLISHABLE_KEY == 'pk_test_xxxxxxxxxxxxxxxxxxxxx':
            print("⚠️  STRIPE_PUBLISHABLE_KEY no está configurado")
            return False
        
        # Probar conexión con Stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        try:
            # Intenta listar productos (esto verifica la API key)
            products = stripe.Product.list(limit=1)
            print("✅ Conexión con Stripe exitosa")
            print(f"   API Key válida: {STRIPE_SECRET_KEY[:7]}...{STRIPE_SECRET_KEY[-4:]}")
            return True
        except stripe.error.AuthenticationError:
            print("❌ API Key de Stripe inválida")
            return False
        except Exception as e:
            print(f"❌ Error conectando con Stripe: {str(e)}")
            return False
            
    except ImportError:
        print("❌ No se puede importar configuración de Stripe")
        print("   Asegúrate de tener config.py con STRIPE_SECRET_KEY y STRIPE_PUBLISHABLE_KEY")
        return False

def test_paypal_config():
    """Verificar configuración de PayPal"""
    print("\n🔍 Verificando configuración de PayPal...")
    
    try:
        import paypalrestsdk
        from config import PAYPAL_MODE, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET
        
        if not PAYPAL_CLIENT_ID or PAYPAL_CLIENT_ID == 'AxxxxxxxxxxxxxxxxxxxxxxxxZQ':
            print("⚠️  PAYPAL_CLIENT_ID no está configurado")
            return False
        
        if not PAYPAL_CLIENT_SECRET or PAYPAL_CLIENT_SECRET == 'ExxxxxxxxxxxxxxxxxxxxxxxxGg':
            print("⚠️  PAYPAL_CLIENT_SECRET no está configurado")
            return False
        
        # Configurar PayPal
        api = paypalrestsdk.configure({
            'mode': PAYPAL_MODE,
            'client_id': PAYPAL_CLIENT_ID,
            'client_secret': PAYPAL_CLIENT_SECRET
        })
        
        # Probar obteniendo un token de acceso
        try:
            import paypalrestsdk.api
            token = paypalrestsdk.api.default().get_token_hash()
            if token:
                print("✅ Conexión con PayPal exitosa")
                print(f"   Modo: {PAYPAL_MODE}")
                print(f"   Client ID: {PAYPAL_CLIENT_ID[:7]}...{PAYPAL_CLIENT_ID[-4:]}")
                return True
            else:
                print("❌ No se pudo obtener token de PayPal")
                return False
        except Exception as e:
            print(f"❌ Error conectando con PayPal: {str(e)}")
            return False
            
    except ImportError:
        print("❌ No se puede importar configuración de PayPal")
        print("   Asegúrate de tener config.py con PAYPAL_MODE, PAYPAL_CLIENT_ID y PAYPAL_CLIENT_SECRET")
        return False

def test_database_plans():
    """Verificar planes en base de datos"""
    print("\n🔍 Verificando planes en base de datos...")
    
    try:
        from app import db
        from modules.models.model import StoragePlan
        
        plans = StoragePlan.query.filter_by(is_active=True).all()
        
        if not plans:
            print("⚠️  No hay planes activos en la base de datos")
            return False
        
        print(f"✅ Encontrados {len(plans)} planes activos:")
        
        issues = []
        for plan in plans:
            print(f"\n   📦 {plan.name}")
            print(f"      Precio mensual: ${plan.price_monthly_usd}")
            print(f"      Precio anual: ${plan.price_annual_usd}")
            
            # Verificar Stripe
            if plan.stripe_price_monthly:
                print(f"      ✅ Stripe Monthly: {plan.stripe_price_monthly}")
            else:
                print(f"      ⚠️  Stripe Monthly: No configurado")
                issues.append(f"{plan.name} - Stripe Monthly")
            
            if plan.stripe_price_annual:
                print(f"      ✅ Stripe Annual: {plan.stripe_price_annual}")
            else:
                print(f"      ⚠️  Stripe Annual: No configurado")
                issues.append(f"{plan.name} - Stripe Annual")
            
            # Verificar PayPal
            if plan.paypal_plan_monthly:
                print(f"      ✅ PayPal Monthly: {plan.paypal_plan_monthly}")
            else:
                print(f"      ⚠️  PayPal Monthly: No configurado")
                issues.append(f"{plan.name} - PayPal Monthly")
            
            if plan.paypal_plan_annual:
                print(f"      ✅ PayPal Annual: {plan.paypal_plan_annual}")
            else:
                print(f"      ⚠️  PayPal Annual: No configurado")
                issues.append(f"{plan.name} - PayPal Annual")
        
        if issues:
            print(f"\n⚠️  Problemas encontrados:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {str(e)}")
        print("   Asegúrate de que la app Flask esté configurada correctamente")
        return False

def test_routes():
    """Verificar que las rutas estén registradas"""
    print("\n🔍 Verificando rutas de billing...")
    
    try:
        from app import app
        
        required_routes = [
            '/billing_bp/plans',
            '/billing_bp/create-checkout-session',
            '/billing_bp/checkout-success',
            '/billing_bp/stripe/webhook',
            '/billing_bp/paypal/create-order',
            '/billing_bp/paypal/execute-agreement',
            '/billing_bp/paypal/webhook',
            '/billing_bp/cancel-subscription',
        ]
        
        # Obtener todas las rutas registradas
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        all_found = True
        for route in required_routes:
            if route in routes:
                print(f"   ✅ {route}")
            else:
                print(f"   ❌ {route} - No encontrada")
                all_found = False
        
        if all_found:
            print("✅ Todas las rutas están registradas correctamente")
            return True
        else:
            print("⚠️  Algunas rutas no están registradas")
            print("   Asegúrate de que billing_bp esté registrado en tu app")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando rutas: {str(e)}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("=" * 60)
    print("🧪 VERIFICACIÓN DE CONFIGURACIÓN DE PAGOS")
    print("=" * 60)
    
    results = {
        'Dependencias': test_imports(),
    }
    
    if results['Dependencias']:
        results['Stripe'] = test_stripe_config()
        results['PayPal'] = test_paypal_config()
        results['Base de Datos'] = test_database_plans()
        results['Rutas'] = test_routes()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ¡Todo está configurado correctamente!")
        print("   Puedes proceder a probar los pagos")
    else:
        print("\n⚠️  Hay problemas de configuración")
        print("   Revisa los errores anteriores y corrígelos")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
