# App-by-App Guide

## `accounts`
- Custom user with unique username/email/phone/national_id.
- Register/Login/Me endpoints.

## `rbac`
- Dynamic role CRUD by superuser.
- RolePermission action strings.
- UserRole assignment.
- `seed_roles` command for defaults.

## `cases`
- Complaint and scene-based case creation.
- Intern/officer review flow.
- 3-strike invalid complaint auto-void.
- Case complainants, witnesses, logs.

## `evidence`
- Witness evidence.
- Biological/medical evidence.
- Vehicle evidence with plate/serial XOR validation.
- Identification evidence with key-value metadata.
- Other evidence.

## `investigation`
- Detective board + nodes + edges.
- Suspects and arrest state.
- Interrogation scores: detective/sergeant/captain/chief review.
- Notifications.
- High-alert ranking and reward formula endpoint.

## `judiciary`
- Court session, verdict, punishment details.

## `rewards`
- Public tips.
- Officer validation.
- Detective approval.
- Unique claim code and reward payment verification.

## `payments`
- Bail/fine payment record and callback endpoint.
- Return page template for gateway callback.

## `dashboard`
- Aggregated stats endpoint for homepage/dashboard.
