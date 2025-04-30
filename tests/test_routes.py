def test_register_employer(client):
    response = client.post("/register/employer", json={
        "username": "Patricia",
        "password": "password123"
    })
    
    assert response.status_code == 201
    assert response.get_json()["message"] == "Employer registered successfully"
    
def test_register_job_seeker(client):
    response = client.post('/register/job_seeker', json={
        'username': 'Furel',
        'password': "password123"
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == "Job seeker registered successfully"
    
def test_login(client):
    client.post('/register/employer', json={
        'username': "Emmanuel",
        'password': "password123"
    })
    response = client.post('/login', json={
        'username': 'Emmanuel',
        'password': "password123"
    })
    
    assert response.status_code == 200
    assert 'access_token' in response.get_json()
    
def test_get_all_offers_empty(client):
    response = client.get('/job_offers')
    assert response.status_code == 200
    assert response.get_json() == []