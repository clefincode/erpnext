frappe.listview_settings['Instructor Attendance'] = {
	add_fields: ["is_present"],
	get_indicator: function(doc) {
		if(doc.is_present == 1 && doc.docstatus == 1 ) {
			return [__("Present"), "green", "is_present,=,1"];
		} else if (doc.is_present == 0 && doc.docstatus == 1 ) {
			return [__("Absent"), "orange","is_present,=,0"];
		}
	},
	hide_name_column: true
};