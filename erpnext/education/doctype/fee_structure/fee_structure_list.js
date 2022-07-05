frappe.listview_settings['Fee Structure'] = {
	add_fields: [ "status"],
	get_indicator: function(doc) {
		if (doc.status=="Active") {
			return [__("Active"), "green", "status,=,Active"];
		}
		else if (doc.status=="Unactive") {
			return [__("Unactive"), "orange", "status,=,Unactive"];
		}
	},
	hide_name_column: true
};

