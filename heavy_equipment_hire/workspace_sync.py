import json

import frappe


def sync_heavy_equipment_workspace():
	workspace_name = "Heavy Equipment Hire"
	fixture_path = frappe.get_app_path(
		"heavy_equipment_hire",
		"heavy_equipment_hire",
		"workspace",
		"heavy_equipment_hire",
		"heavy_equipment_hire.json",
	)

	with open(fixture_path, encoding="utf-8") as fixture_file:
		fixture = json.load(fixture_file)

	if frappe.db.exists("Workspace", workspace_name):
		workspace = frappe.get_doc("Workspace", workspace_name)
	else:
		workspace = frappe.new_doc("Workspace")
		workspace.name = workspace_name
		workspace.label = workspace_name

	for fieldname in (
		"charts",
		"custom_blocks",
		"links",
		"number_cards",
		"quick_lists",
		"roles",
		"shortcuts",
	):
		workspace.set(fieldname, [])
		for row in fixture.get(fieldname, []):
			workspace.append(fieldname, row)

	for fieldname in (
		"content",
		"for_user",
		"hide_custom",
		"icon",
		"is_hidden",
		"label",
		"module",
		"parent_page",
		"public",
		"restrict_to_domain",
		"sequence_id",
		"title",
	):
		if fieldname in fixture:
			workspace.set(fieldname, fixture.get(fieldname))

	workspace.flags.ignore_permissions = True
	workspace.save()
	frappe.clear_cache(doctype="Workspace")
	frappe.clear_cache()
	return workspace.name
