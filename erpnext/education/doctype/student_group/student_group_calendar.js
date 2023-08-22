// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.views.calendar["Student Group"] = {
	fields:  ["start_date", "program",  "name"],
	field_map: {
		"start": "start_date",
		"end": "start_date",
		"id": "name",
		"title": "program",
	},
	gantt: true,
	get_events_method: "frappe.desk.calendar.get_events"
}
