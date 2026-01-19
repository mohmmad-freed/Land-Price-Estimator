from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from core.models import Project, Governorate, Town, Area, Neighborhood
from django.contrib.auth import get_user_model
User = get_user_model()


class ProjectModelTest(TestCase):
    """Tests for the Project model."""

    @classmethod
    def setUpTestData(cls):
        """Set up location hierarchy for tests."""
        cls.governorate = Governorate.objects.create(name_ar="Test Governorate")
        cls.town = Town.objects.create(governorate=cls.governorate, name_ar="Test Town")
        cls.area = Area.objects.create(town=cls.town, name_ar="Test Area")
        cls.neighborhood = Neighborhood.objects.create(area=cls.area, name_ar="Test Neighborhood")

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="TestPassword123",
            type="normal"
        )

    def test_project_creation(self):
        """Test basic project creation with required fields."""
        project = Project.objects.create(
            created_by=self.user,
            project_name="Test Project",
            governorate=self.governorate,
            town=self.town,
            area=self.area,
            neighborhood=self.neighborhood,
            neighborhood_no="123",
            parcel_no="456",
            area_m2=500,
            land_type="PRIVATE",
            political_classification="AREA_A",
            slope="FLAT",
            view_quality="GOOD",
            parcel_shape="SQUARE",
            electricity="YES_3PHASE",
            water="YES",
            sewage="YES_PUBLIC",
            ownership_document_type="TABU",
            status="DRAFT"
        )

        self.assertEqual(project.project_name, "Test Project")
        self.assertEqual(project.created_by.email, "testuser@example.com")
        self.assertEqual(project.status, "DRAFT")
        self.assertEqual(project.area_m2, 500)

    def test_project_with_land_use_booleans(self):
        """Test creating a project with land use boolean fields."""
        project = Project.objects.create(
            created_by=self.user,
            project_name="Land Uses Test",
            governorate=self.governorate,
            town=self.town,
            area=self.area,
            neighborhood=self.neighborhood,
            neighborhood_no="123",
            parcel_no="789",
            area_m2=1000,
            land_type="PRIVATE",
            political_classification="AREA_B",
            slope="MILD",
            view_quality="FANTASTIC",
            parcel_shape="RECTANGLE",
            electricity="YES_1PHASE",
            water="YES",
            sewage="NO",
            ownership_document_type="FINAL_SETTLEMENT",
            status="DRAFT",
            land_use_residential=True,
            land_use_commercial=True,
            land_use_agricultural=False,
            land_use_industrial=False,
        )
        
        self.assertTrue(project.land_use_residential)
        self.assertTrue(project.land_use_commercial)
        self.assertFalse(project.land_use_agricultural)
        self.assertFalse(project.land_use_industrial)

    def test_infrastructure_properties(self):
        """Test infrastructure property methods."""
        project = Project.objects.create(
            created_by=self.user,
            project_name="Infrastructure Test",
            governorate=self.governorate,
            town=self.town,
            area=self.area,
            neighborhood=self.neighborhood,
            neighborhood_no="123",
            parcel_no="101",
            area_m2=300,
            land_type="PRIVATE",
            political_classification="AREA_C",
            slope="FLAT",
            view_quality="BAD",
            parcel_shape="IRREGULAR",
            electricity="YES_3PHASE",
            water="YES",
            sewage="YES_PRIVATE",
            ownership_document_type="TABU",
            status="DRAFT"
        )
        
        self.assertTrue(project.has_electricity)
        self.assertTrue(project.has_water)
        self.assertTrue(project.has_sewage)

    def test_infrastructure_no_utilities(self):
        """Test infrastructure properties when utilities are absent."""
        project = Project.objects.create(
            created_by=self.user,
            project_name="No Utils Test",
            governorate=self.governorate,
            town=self.town,
            area=self.area,
            neighborhood=self.neighborhood,
            neighborhood_no="123",
            parcel_no="102",
            area_m2=300,
            land_type="PUBLIC",
            political_classification="AREA_A",
            slope="STEEP",
            view_quality="BAD",
            parcel_shape="TRIANGLE",
            electricity="NO",
            water="NO",
            sewage="NO",
            ownership_document_type="HUJJA",
            status="DRAFT"
        )
        
        self.assertFalse(project.has_electricity)
        self.assertFalse(project.has_water)
        self.assertFalse(project.has_sewage)


class ProjectIntegrationTest(TestCase):
    """Integration tests for project creation views."""

    @classmethod
    def setUpTestData(cls):
        """Set up location hierarchy for tests."""
        cls.governorate = Governorate.objects.create(name_ar="Test Gov")
        cls.town = Town.objects.create(governorate=cls.governorate, name_ar="Test Town")
        cls.area = Area.objects.create(town=cls.town, name_ar="Test Area")
        cls.neighborhood = Neighborhood.objects.create(area=cls.area, name_ar="Test Neighborhood")

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            type="normal"
        )
        self.client = Client()
        self.client.login(email="testuser@example.com", password="testpass123")

        self.project_data = {
            "project_name": "Test Project",
            "governorate": self.governorate.id,
            "town": self.town.id,
            "area": self.area.id,
            "neighborhood": self.neighborhood.id,
            "neighborhood_no": "123",
            "parcel_no": "456",
            "land_type": "PRIVATE",
            "political_classification": "AREA_A",
            "slope": "FLAT",
            "view_quality": "GOOD",
            "parcel_shape": "SQUARE",
            "electricity": "YES_3PHASE",
            "water": "YES",
            "sewage": "YES_PUBLIC",
            "ownership_document_type": "TABU",
            "area_m2": 100,
            "land_use_residential": True,
            "land_use_commercial": False,
            "land_use_agricultural": False,
            "land_use_industrial": False,
            # Road formset management form data (required for inline formsets)
            "projectroad_set-TOTAL_FORMS": "3",
            "projectroad_set-INITIAL_FORMS": "0",
            "projectroad_set-MIN_NUM_FORMS": "0",
            "projectroad_set-MAX_NUM_FORMS": "3",
        }

    def test_create_project_draft(self):
        """Test creating a project as draft."""
        response = self.client.post(
            reverse("normal:new-project"), 
            {**self.project_data, "action": "save"}
        )
        self.assertEqual(response.status_code, 302, "Draft creation should redirect")
        
        project = Project.objects.get(project_name="Test Project")
        self.assertEqual(project.status, "DRAFT", "Project status should be 'DRAFT'")
        self.assertEqual(project.created_by, self.user, "Project should be linked to the logged-in user")

    def test_form_validation_requires_land_use(self):
        """Test that validation fails without selecting at least one land use."""
        data = self.project_data.copy()
        data['land_use_residential'] = False
        response = self.client.post(
            reverse("normal:new-project"), 
            {**data, "action": "save"}
        )
        # Should not redirect (form invalid), should re-render form
        self.assertEqual(response.status_code, 200)

    @patch("Normal_User_Side.views.predict_land_price")
    def test_create_project_with_estimation(self, mock_predict):
        """Test creating a project with ML estimation."""
        mock_predict.return_value = 50.0  # 50k JOD per m²
        response = self.client.post(
            reverse("normal:new-project"), 
            {**self.project_data, "action": "complete"}
        )
        self.assertEqual(response.status_code, 302, "Estimation creation should redirect")

        project = Project.objects.get(project_name="Test Project")
        self.assertEqual(project.status, "COMPLETED", "Project status should be 'COMPLETED'")
        self.assertEqual(project.estimated_price, 50.0, "Estimated price should match mocked ML value")
