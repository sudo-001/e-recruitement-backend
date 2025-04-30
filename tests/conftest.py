import pytest
from app import create_app, db
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        
@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def employer_token(app):
    from app.models import Employer
    employer = Employer(username="Employer_test", password="password")
    db.session.add(employer)
    db.session.commit()
    token =create_access_token(identity={"id": employer.id, "type":"employer"})
    return token

@pytest.fixture
def job_seeker_token(app):
    from app.models import JobSeeker
    job_seeker = JobSeeker(username="job_seeker_test", password = "password")
    db.session.add(job_seeker)
    db.session.commit()
    token = create_access_token(identity={"id": job_seeker.id, "type": "job_seeker"})
    return token