from django.db import migrations

def create_all_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    
    roles = [
        # --- Level 0: Civilians (Public) ---
        {'name': 'Civilian', 'access_level': 0, 'description': 'Default public user. Base role for Suspects, Witnesses, and Complainants.'},
        
        # --- Level 10-30: Field Operations ---
        {'name': 'Cadet', 'access_level': 10, 'description': 'Police Cadet. Reviews and forwards complaints.'},
        {'name': 'Patrol Officer', 'access_level': 20, 'description': 'Patrol Unit. First responder to crime scenes.'},
        {'name': 'Police Officer', 'access_level': 20, 'description': 'General Officer. Files reports and manages basic incidents.'},
        
        # --- Level 30-40: Specialists ---
        {'name': 'Coroner', 'access_level': 30, 'description': 'Forensic Examiner. Reviews and verifies biological evidence.'},
        {'name': 'Detective', 'access_level': 40, 'description': 'Investigates cases, uses detective board, identifies suspects.'},
        
        # --- Level 50-60: Supervisors ---
        {'name': 'Sergeant', 'access_level': 60, 'description': 'Issues interrogation warrants, conducts interrogations.'},
        
        # --- Level 70: Judiciary ---
        {'name': 'Judge', 'access_level': 70, 'description': 'Presides over trials and issues final verdicts.'},
        
        # --- Level 80-90: Command ---
        {'name': 'Captain', 'access_level': 80, 'description': 'Approves cases for trial and manages assignments.'},
        {'name': 'Chief', 'access_level': 90, 'description': 'Police Chief. Handles critical cases and oversees operations.'},
    ]

    for role_data in roles:
        Role.objects.update_or_create(
            name=role_data['name'], 
            defaults=role_data
        )

def remove_all_roles(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    Role.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_all_roles, reverse_code=remove_all_roles),
    ]
