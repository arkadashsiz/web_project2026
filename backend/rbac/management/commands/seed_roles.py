from django.core.management.base import BaseCommand
from rbac.models import Role, RolePermission


DEFAULT_ROLES = {
    'base user': ['tip.submit'],
    'administrator': ['rbac.manage', 'dashboard.read', 'case.read_all'],
    'chief': [
        'case.assign_detective', 'case.scene.create', 'case.send_to_court',
        'interrogation.chief_review', 'case.read_all', 'dashboard.read', 'case.scene.add_complainant',
    ],
    'captain': [
        'case.assign_detective', 'case.send_to_court',
        'interrogation.captain_decision', 'case.read_all', 'dashboard.read', 'case.scene.add_complainant',
    ],
    'sergeant': [
        'case.assign_detective', 'case.complaint.officer_review',
        'suspect.manage', 'interrogation.manage', 'case.read_all', 'case.scene.add_complainant',
    ],
    'detective': [
        'investigation.board.manage', 'suspect.manage', 'interrogation.manage',
        'tip.detective_review', 'case.read_all', 'case.scene.add_complainant',
    ],
    'police officer': [
        'case.scene.create', 'case.complaint.officer_review',
        'evidence.manage', 'tip.officer_review', 'reward.verify', 'case.read_all', 'case.scene.add_complainant',
    ],
    'patrol officer': ['case.scene.create', 'evidence.manage', 'case.read_all', 'case.scene.add_complainant'],
    'cadet': ['case.complaint.intern_review', 'case.read_all'],
    'complainant': ['case.submit_complaint', 'tip.submit'],
    'witness': ['tip.submit'],
    'suspect': [],
    'criminal': [],
    'judge': ['judiciary.verdict', 'case.read_all'],
    'coroner': ['evidence.biological.review', 'evidence.manage', 'case.read_all'],
}


class Command(BaseCommand):
    help = 'Seed default system roles and role permissions.'

    def handle(self, *args, **options):
        for role_name, actions in DEFAULT_ROLES.items():
            role, _ = Role.objects.get_or_create(name=role_name, defaults={'is_system': True})
            role.is_system = True
            role.save(update_fields=['is_system'])
            role.permissions.all().delete()
            for action in actions:
                RolePermission.objects.create(role=role, action=action)
        self.stdout.write(self.style.SUCCESS('Default roles seeded.'))
