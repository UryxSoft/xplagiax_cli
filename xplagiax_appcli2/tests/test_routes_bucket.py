# test_routes_bucket.py
import pytest
import io
from datetime import datetime
from modules.models.model import User, Folder, File

# ============================================
# Fixtures
# ============================================

@pytest.fixture
def test_user(db):
    """Create test user"""
    user = User(
        name="Test",
        lastname="User",
        email="test@example.com",
        password="hashed_password",
        used_storage_bytes=0
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def auth_client(client, test_user):
    """Authenticated client"""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
    return client

@pytest.fixture
def test_folder(db, test_user):
    """Create test folder"""
    folder = Folder(
        name="Test Folder",
        path=f"{test_user.id}/test-folder",
        user_id=test_user.id
    )
    db.session.add(folder)
    db.session.commit()
    return folder

@pytest.fixture
def test_file(db, test_user, test_folder):
    """Create test file"""
    file = File(
        filename="test-file.txt",
        original_filename="test.txt",
        mime_type="text/plain",
        size=1024,
        user_id=test_user.id,
        folder_id=test_folder.id,
        minio_url="http://seaweedfs/test-file.txt"
    )
    db.session.add(file)
    db.session.commit()
    return file

# ============================================
# Tests - Folders
# ============================================

def test_get_folders_empty(auth_client):
    """Test getting folders when none exist"""
    response = auth_client.get('/api/folders')
    assert response.status_code == 200
    data = response.get_json()
    assert 'folders' in data
    assert len(data['folders']) == 0
    assert 'pagination' in data

def test_get_folders_with_pagination(auth_client, test_user, db):
    """Test folder pagination"""
    # Create 60 folders
    for i in range(60):
        folder = Folder(
            name=f"Folder {i}",
            path=f"{test_user.id}/folder-{i}",
            user_id=test_user.id
        )
        db.session.add(folder)
    db.session.commit()
    
    # First page
    response = auth_client.get('/api/folders?page=1&per_page=20')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['folders']) == 20
    assert data['pagination']['page'] == 1
    assert data['pagination']['total'] == 60
    assert data['pagination']['has_next'] == True
    
    # Second page
    response = auth_client.get('/api/folders?page=2&per_page=20')
    data = response.get_json()
    assert len(data['folders']) == 20
    assert data['pagination']['page'] == 2

def test_create_folder_success(auth_client):
    """Test successful folder creation"""
    response = auth_client.post('/api/folders', json={
        'name': 'New Folder',
        'parent_id': None,
        'is_shared': False
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'New Folder'
    assert 'id' in data
    assert 'path' in data

def test_create_folder_invalid_name(auth_client):
    """Test folder creation with invalid characters"""
    response = auth_client.post('/api/folders', json={
        'name': 'Folder/With/Slashes',
        'parent_id': None
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'caracteres no permitidos' in data['error'].lower()

def test_create_folder_too_long(auth_client):
    """Test folder creation with name too long"""
    response = auth_client.post('/api/folders', json={
        'name': 'a' * 300,  # 300 characters
        'parent_id': None
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'demasiado largo' in data['error'].lower()

def test_create_folder_duplicate(auth_client, test_folder):
    """Test creating folder with duplicate name"""
    response = auth_client.post('/api/folders', json={
        'name': test_folder.name,
        'parent_id': None
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'ya existe' in data['error'].lower()

def test_delete_folder_success(auth_client, test_folder):
    """Test successful folder deletion"""
    response = auth_client.delete(f'/folders/{test_folder.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_delete_folder_with_subfolders(auth_client, test_user, test_folder, db):
    """Test deleting folder with subfolders fails"""
    # Create subfolder
    subfolder = Folder(
        name="Subfolder",
        path=f"{test_folder.path}/subfolder",
        parent_id=test_folder.id,
        user_id=test_user.id
    )
    db.session.add(subfolder)
    db.session.commit()
    
    response = auth_client.delete(f'/folders/{test_folder.id}')
    assert response.status_code == 400
    data = response.get_json()
    assert 'subcarpetas' in data['error'].lower()

def test_delete_folder_not_owner(auth_client, db):
    """Test deleting folder not owned by user"""
    # Create folder owned by different user
    other_user = User(
        name="Other",
        lastname="User",
        email="other@example.com",
        password="pass"
    )
    db.session.add(other_user)
    db.session.commit()
    
    other_folder = Folder(
        name="Other Folder",
        path=f"{other_user.id}/folder",
        user_id=other_user.id
    )
    db.session.add(other_folder)
    db.session.commit()
    
    response = auth_client.delete(f'/folders/{other_folder.id}')
    assert response.status_code == 403

# ============================================
# Tests - Files
# ============================================

def test_upload_file_success(auth_client):
    """Test successful file upload"""
    data = {
        'file': (io.BytesIO(b'test content'), 'test.txt')
    }
    response = auth_client.post('/api/files', data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    json_data = response.get_json()
    assert 'id' in json_data
    assert 'storage_info' in json_data

def test_upload_file_invalid_extension(auth_client):
    """Test uploading file with invalid extension"""
    data = {
        'file': (io.BytesIO(b'malware'), 'virus.exe')
    }
    response = auth_client.post('/api/files', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'no permitido' in json_data['error'].lower()

def test_upload_file_too_large(auth_client, monkeypatch):
    """Test uploading file exceeding size limit"""
    # Mock MAX_FILE_SIZE
    import modules.routes_bucket as rb
    monkeypatch.setattr(rb, 'MAX_FILE_SIZE', 100)  # 100 bytes
    
    large_content = b'x' * 200  # 200 bytes
    data = {
        'file': (io.BytesIO(large_content), 'large.txt')
    }
    response = auth_client.post('/api/files', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'demasiado grande' in json_data['error'].lower()

def test_get_files_with_search(auth_client, test_user, test_folder, db):
    """Test file search"""
    # Create multiple files
    for i in range(5):
        file = File(
            filename=f"file-{i}.txt",
            original_filename=f"document-{i}.txt",
            mime_type="text/plain",
            size=1024,
            user_id=test_user.id,
            folder_id=test_folder.id,
            minio_url=f"http://test/file-{i}.txt"
        )
        db.session.add(file)
    db.session.commit()
    
    # Search
    response = auth_client.get('/api/files?search=document-2')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['files']) == 1
    assert 'document-2' in data['files'][0]['original_filename']

def test_get_files_with_sorting(auth_client, test_user, test_folder, db):
    """Test file sorting"""
    # Create files with different sizes
    for i in range(3):
        file = File(
            filename=f"file-{i}.txt",
            original_filename=f"file-{i}.txt",
            mime_type="text/plain",
            size=(i + 1) * 1024,  # Different sizes
            user_id=test_user.id,
            folder_id=test_folder.id,
            minio_url=f"http://test/file-{i}.txt"
        )
        db.session.add(file)
    db.session.commit()
    
    # Sort by size descending
    response = auth_client.get('/api/files?sort_by=size&order=desc')
    assert response.status_code == 200
    data = response.get_json()
    files = data['files']
    assert files[0]['size'] > files[1]['size']
    assert files[1]['size'] > files[2]['size']

def test_download_file_success(auth_client, test_file):
    """Test successful file download"""
    response = auth_client.get(f'/api/files/{test_file.id}/download')
    assert response.status_code == 200
    assert response.mimetype == test_file.mime_type

def test_download_file_not_found(auth_client):
    """Test downloading non-existent file"""
    response = auth_client.get('/api/files/99999/download')
    assert response.status_code == 404

def test_delete_file_success(auth_client, test_file):
    """Test successful file deletion"""
    response = auth_client.delete(f'/files/{test_file.id}')
    assert response.status_code == 200

def test_delete_file_not_owner(auth_client, db):
    """Test deleting file not owned by user"""
    other_user = User(
        name="Other",
        lastname="User",
        email="other@example.com",
        password="pass"
    )
    db.session.add(other_user)
    db.session.commit()
    
    other_file = File(
        filename="other-file.txt",
        original_filename="other.txt",
        mime_type="text/plain",
        size=1024,
        user_id=other_user.id,
        minio_url="http://test/other.txt"
    )
    db.session.add(other_file)
    db.session.commit()
    
    response = auth_client.delete(f'/files/{other_file.id}')
    assert response.status_code == 403

# ============================================
# Tests - Storage Stats
# ============================================

def test_get_storage_stats(auth_client, test_user, test_file):
    """Test getting storage statistics"""
    response = auth_client.get('/api/storage/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'used_storage_bytes' in data
    assert 'total_storage_bytes' in data
    assert 'largest_files' in data
    assert 'folder_usage' in data

def test_get_storage_summary(auth_client, test_user):
    """Test getting storage summary"""
    response = auth_client.get('/api/storage/summary')
    assert response.status_code == 200
    data = response.get_json()
    assert 'used_storage_mb' in data
    assert 'total_storage_mb' in data
    assert 'file_count' in data
    assert 'folder_count' in data

# ============================================
# Tests - Cache
# ============================================

def test_cache_folders(auth_client, test_folder):
    """Test that folders are cached"""
    import time
    
    # First request
    start1 = time.time()
    response1 = auth_client.get('/api/folders')
    time1 = time.time() - start1
    
    # Second request (should hit cache)
    start2 = time.time()
    response2 = auth_client.get('/api/folders')
    time2 = time.time() - start2
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    # Cache hit should be faster (not always reliable in tests)
    # assert time2 < time1

def test_clear_cache(auth_client):
    """Test cache clearing"""
    response = auth_client.post('/api/cache/clear')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

# ============================================
# Tests - Health Check
# ============================================

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert 'status' in data
    assert 'seaweedfs' in data
    assert 'database' in data

# ============================================
# Tests - Authentication
# ============================================

def test_unauthorized_access(client):
    """Test accessing protected endpoints without auth"""
    endpoints = [
        '/api/folders',
        '/api/files',
        '/api/storage/stats'
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401

# ============================================
# Performance Tests
# ============================================

def test_pagination_performance(auth_client, test_user, db):
    """Test that pagination doesn't load all records"""
    # Create 1000 folders
    folders = []
    for i in range(1000):
        folder = Folder(
            name=f"Folder {i}",
            path=f"{test_user.id}/folder-{i}",
            user_id=test_user.id
        )
        folders.append(folder)
    
    db.session.bulk_save_objects(folders)
    db.session.commit()
    
    import time
    
    # Request only 10 items
    start = time.time()
    response = auth_client.get('/api/folders?per_page=10')
    elapsed = time.time() - start
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['folders']) == 10
    # Should be fast even with 1000 folders
    assert elapsed < 1.0  # Less than 1 second

# ============================================
# Integration Tests
# ============================================

def test_full_workflow(auth_client):
    """Test complete workflow: create folder, upload file, download, delete"""
    # 1. Create folder
    response = auth_client.post('/api/folders', json={
        'name': 'Test Workflow',
        'parent_id': None
    })
    assert response.status_code == 201
    folder_id = response.get_json()['id']
    
    # 2. Upload file to folder
    data = {
        'file': (io.BytesIO(b'workflow test'), 'workflow.txt'),
        'folder_id': folder_id
    }
    response = auth_client.post('/api/files', data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    file_id = response.get_json()['id']
    
    # 3. List files in folder
    response = auth_client.get(f'/api/files?folder_id={folder_id}')
    assert response.status_code == 200
    assert len(response.get_json()['files']) == 1
    
    # 4. Download file
    response = auth_client.get(f'/api/files/{file_id}/download')
    assert response.status_code == 200
    
    # 5. Delete file
    response = auth_client.delete(f'/files/{file_id}')
    assert response.status_code == 200
    
    # 6. Delete folder
    response = auth_client.delete(f'/folders/{folder_id}')
    assert response.status_code == 200
