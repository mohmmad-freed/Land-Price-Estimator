from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from Normal_User_Side.models import Project, IntendedUse
from django.contrib.auth import get_user_model
User = get_user_model()

class ProjectModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="TestPassword123",
            type="normal"
        )
        # Create IntendedUse objects for testing
        self.residential_use = IntendedUse.objects.get_or_create(name="residential")[0]
        self.commercial_use = IntendedUse.objects.get_or_create(name="commercial")[0]

    def test_project_creation(self):
        project = Project.objects.create(
            user=self.user,
            name="Test Project",
            governorate="ramallah",
            land_size=500,
            land_type="agricultural",
            political_classification="a",
            status="draft"
        )

        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.user.email, "testuser@example.com")
        self.assertEqual(project.status, "draft")
        self.assertEqual(project.land_size, 500)

    def test_project_with_all_new_fields(self):
        """Test creating a project with all new fields populated"""
        project = Project.objects.create(
            user=self.user,
            name="Complete Test Project",
            governorate="hebron",
            town="central",
            land_size=1000,
            land_type="residential",
            political_classification="b",
            slope="mild",
            has_electricity=True,
            has_water=True,
            has_sewage=False,
            has_paved_road=True,
            has_internet=False,
            status="draft"
        )
        
        # Add intended uses
        project.intended_uses.add(self.residential_use, self.commercial_use)
        
        self.assertEqual(project.town, "central")
        self.assertEqual(project.slope, "mild")
        self.assertTrue(project.has_electricity)
        self.assertTrue(project.has_water)
        self.assertFalse(project.has_sewage)
        self.assertEqual(project.intended_uses.count(), 2)

    def test_intended_use_many_to_many(self):
        """Test adding/removing intended uses from a project"""
        project = Project.objects.create(
            user=self.user,
            name="ManyToMany Test",
            governorate="hebron",
            land_size=500,
            land_type="mixed",
            political_classification="a",
            status="draft"
        )
        
        # Add intended uses
        project.intended_uses.add(self.residential_use)
        self.assertEqual(project.intended_uses.count(), 1)
        
        # Add another
        project.intended_uses.add(self.commercial_use)
        self.assertEqual(project.intended_uses.count(), 2)
        
        # Remove one
        project.intended_uses.remove(self.residential_use)
        self.assertEqual(project.intended_uses.count(), 1)
        self.assertEqual(project.intended_uses.first(), self.commercial_use)

    def test_infrastructure_defaults(self):
        """Test that infrastructure booleans default to False"""
        project = Project.objects.create(
            user=self.user,
            name="Defaults Test",
            governorate="ramallah",
            land_size=300,
            land_type="agricultural",
            political_classification="c",
            status="draft"
        )
        
        self.assertFalse(project.has_electricity)
        self.assertFalse(project.has_water)
        self.assertFalse(project.has_sewage)
        self.assertFalse(project.has_paved_road)
        self.assertFalse(project.has_internet)



class ProjectIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            type="normal_user"
        )
        self.client = Client()
        self.client.login(email="testuser@example.com", password="testpass123")
        
        # Ensure IntendedUse records exist
        self.residential = IntendedUse.objects.get_or_create(name="residential")[0]
        self.commercial = IntendedUse.objects.get_or_create(name="commercial")[0]

        # Updated project_data to include required new fields
        self.project_data = {
            "name": "Test Project",
            "governorate": "ramallah",
            "town": "central",
            "land_type": "agricultural",
            "political_classification": "a",
            "slope": "flat",
            "description": "Test description",
            "land_size": 100,
            "has_electricity": True,
            "has_water": True,
            "has_sewage": False,
            "has_paved_road": False,
            "has_internet": False,
            "intended_uses": [self.residential.id, self.commercial.id]
        }

    def test_create_project_draft(self):
        response = self.client.post(reverse("normal_user:new-project"), {**self.project_data, "action": "save"})
        self.assertEqual(response.status_code, 302, "Draft creation should redirect")
        
        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.status, "draft", "Project status should be 'draft'")
        self.assertEqual(project.user, self.user, "Project should be linked to the logged-in user")
        self.assertEqual(project.town, "central")
        self.assertEqual(project.slope, "flat")

    def test_form_validation_requires_town(self):
        """Test that form validation fails without town selection"""
        data = self.project_data.copy()
        del data['town']
        response = self.client.post(reverse("normal_user:new-project"), {**data, "action": "save"})
        # Should not redirect (form invalid), should re-render form
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_form_validation_requires_intended_use(self):
        """Test that validation fails without selecting intended use"""
        data = self.project_data.copy()
        data['intended_uses'] = []
        response = self.client.post(reverse("normal_user:new-project"), {**data, "action": "save"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_infrastructure_persistence(self):
        """Test that infrastructure checkboxes save correctly"""
        response = self.client.post(reverse("normal_user:new-project"), {**self.project_data, "action": "save"})
        
        project = Project.objects.get(name="Test Project")
        self.assertTrue(project.has_electricity)
        self.assertTrue(project.has_water)
        self.assertFalse(project.has_sewage)
        self.assertFalse(project.has_paved_road)
        self.assertFalse(project.has_internet)

    @patch("Normal_User_Side.views.predict_land_price")
    def test_create_project_with_estimation(self, mock_predict):
        mock_predict.return_value = 50000  
        response = self.client.post(reverse("normal_user:new-project"), {**self.project_data, "action": "estimate"})
        self.assertEqual(response.status_code, 302, "Estimation creation should redirect")

        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.status, "completed", "Project status should be 'completed'")
        self.assertEqual(project.estimated_price, 50000, "Estimated price should match mocked ML value")
        
        # Verify prediction was called with ONLY old features (not new fields)
        mock_predict.assert_called_once()
        call_args = mock_predict.call_args[0][0]
        self.assertIn("governorate", call_args)
        self.assertIn("land_size", call_args)
        self.assertIn("land_type", call_args)
        self.assertIn("political_classification", call_args)
        # New fields should NOT be in prediction input
        self.assertNotIn("town", call_args)
        self.assertNotIn("slope", call_args)
        self.assertNotIn("intended_uses", call_args)

    @patch("Normal_User_Side.views.predict_land_price")
    def test_estimation_failure_handled(self, mock_predict):
        mock_predict.side_effect = Exception("ML error")
        response = self.client.post(reverse("normal_user:new-project"), {**self.project_data, "action": "estimate"})
        self.assertEqual(response.status_code, 302, "Redirect should occur even if ML fails")

        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.status, "draft", "Project should fallback to 'draft' on ML failure")
