def initialize_storage_plans():
    """Inicializar los planes de almacenamiento por defecto si no existen"""
    from modules.settings_service.connections import db
    from models import StoragePlan

    # Definir planes predeterminados
    default_plans = [
        {"name": "Starter", "base_storage_mb": 50, "description": "Free plan with 50 MB of storage"},
        {"name": "Individual", "base_storage_mb": 5120, "description": "Individual plan with 5 GB of storage"},
        {"name": "Institutes", "base_storage_mb": 51200, "description": "Plan for Institutes with 50 GB of storage"}
    ]
    
    # Verificar si ya existen planes
    existing_plans = StoragePlan.query.all()
    if existing_plans:
        #print("Storage plans are already initialized.")  
        return
    
    # Crear planes predeterminados
    for plan_data in default_plans:
        plan = StoragePlan(
            name=plan_data["name"],
            base_storage_mb=plan_data["base_storage_mb"],
            description=plan_data["description"],
            is_active=True  # Corregido según las recomendaciones
        )
        db.session.add(plan)
    
    # Guardar cambios
    try:
        db.session.commit()
        #print("Storage plans initialized successfully.")  
    except Exception as e:
        db.session.rollback()
        #print(f"Error initializing storage plans: {e}")