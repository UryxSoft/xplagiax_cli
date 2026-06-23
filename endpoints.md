


----------------AUTH_SERVICE ENDPOINTS---------------
GET POST auth_bp/api/login
body: { "email": "...", "password": "..." }
response: [{ 'message': 'Session started successfully',
            'redirect': next_url },201]

GET POST auth_bp/api/signup
body: { "email": "...", "password": "...","name": "..." }
response: [{  'message': 'Username created successfully. Check your email to confirm your account.' },201]

GET POST auth_bp/api/forgot-password
body: { "email": "..." }
response: [{  'message': 'Success' },200]

GET POST auth_bp/api/reset-password/<token>
body:
response: [{ 'message': 'Password updated','redirect': url },200]

POST auth_bp/api/resend-confirmation
body: { "email": "..." }
response: [{  'message': 'New confirmation link sent.' },200]

POST auth_bp/api/start-trial
body: { "plan": "..." }
response: [{  'message': '...','trial_ends':'','redirect': url },200]

GET auth_bp/api/check-trial-status
@login_required
body: { "plan": "..." }
response: [{  'message': '...','trial_ends':'','redirect': url },200]

GET PUT auth_bp/api/profile
response: [{
            'email': '...',
            'name': '...',
            'lastname': '...',
            'institute': '...',
            'country': '...',
            'user_type': '...',
            'is_on_trial': '...',
            'trial_ends_at': '...',
            'subscription_status': '...',
            'storage_usage': {
                'used_bytes': '...',
                'total_bytes': '...',
                'percentage': '...'
            }
        }
    ]

auth_bp/google/login

auth_bp/microsoft/login

--------------------------------------------

__________BILLING_SERVICE ENDPOINTS---------

POST  billing_bp/create-checkout-session
@login_required
    return jsonify({
        'id': checkout_session.id,
        'url': checkout_session.url
    })

POST billing_bp/paypal/create-order
@login_required

POST billing_bp/paypal/webhook
@login_required
    return jsonify({'status': 'success'})


POST billing_bp/cancel-subscription
@login_required
    return jsonify({
                'message': 'Suscripción cancelada. Mantendrás el acceso hasta el final del período actual.'
            }), 200

billing_bp/subscription-status
@login_required
   return jsonify({
        'has_subscription': current_user.has_active_subscription(),
        'subscription_provider': current_user.subscription_provider,
        'subscription_status': current_user.subscription_status,
        'subscription_type': current_user.subscription_type,
        'subscription_starts_at': current_user.subscription_starts_at.isoformat() if current_user.subscription_starts_at else None,
        'subscription_ends_at': current_user.subscription_ends_at.isoformat() if current_user.subscription_ends_at else None,
        'is_on_trial': current_user.is_on_trial,
        'trial_ends_at': current_user.trial_ends_at.isoformat() if current_user.trial_ends_at else None,
        'can_access_premium': current_user.can_access_premium_features(),
        'user_type': current_user.user_type,
        'storage': {
            'used_bytes': current_user.used_storage_bytes,
            'total_bytes': current_user.get_total_storage_limit_bytes(),
            'percentage': current_user.get_storage_usage_percentage()
        }
    })

POST Billing_bp/renew-annual
@login_required
    return jsonify({'checkout_url': checkout_session.url })


--------------------------------------------

__________BUCKET_SERVICE ENDPOINTS----------

------files----------
POST x_buck/api/files
    return jsonify({
        'id': new_file.id,
        'filename': new_file.filename,
        'original_filename': new_file.original_filename,
        'mime_type': new_file.mime_type,
        'size': new_file.size,
        'created_at': new_file.created_at.isoformat(),
        'url': new_file.minio_url,
        'folder_id': new_file.folder_id
    }), 201

GET  x_buck/files/<int:file_id>
    return send_file(
        file_obj,
        mimetype=file.mime_type,
        as_attachment=True,
        download_name=file.original_filename
    )

DELETE   x_buck/files/<int:file_id>
    return jsonify({"message": "Archivo eliminado correctamente"}), 200

GET  x_buck/api/storage/stats
    return jsonify(stats), 200
--------------------------------------------


__________ANALYSIS_SERVICE ENDPOINTS--------
 
POST x_doc/uploadanalysis

    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'user_id': user_id,
        'language': language,
        'result_ai': results_ai or [],
        'result_db': (results_db.get("result") if results_db else []),
        'result_view': html_url or '',
        'annotations': annotations,
        'images': images_urls or [],
        'urls': urls,
        'pages': pages,
        'analysis_date': current_date,
        'metadata': metadata,
        'theme': theme,
        'stats': stats
    }), 200

POST  x_doc/uploadsave
   
    return jsonify({
        'success': True,
        'message': 'Document processed and saved successfully',
        'document_id': doc_id,
        'elasticsearch_id': doc_id,
        'minio_status': 'success',
        'milvus_status': 'success' if milvus_result.get('success') else 'warning',
        'processing_time': f"{total_time:.2f}s",
        'performance_metrics': {
            'total_time': f"{total_time:.2f}s",
            'elasticsearch_time': f"{time.time() - elastic_start:.2f}s",
            'parallel_operations_time': f"{time.time() - parallel_start:.2f}s"
        }
    }), 200

DELETE  x_doc/deletesave/<string:document_id>

    return jsonify({
        "message": "Document successfully deleted on all services.",
        "results": results
    }), 200

--------------------------------------------


__________SETTINGS_SERVICE ENDPOINTS--------


--------------------------------------------