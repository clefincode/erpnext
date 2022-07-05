frappe.listview_settings['Certificate'] = {
	get_indicator: function(doc) {
		if (doc.docstatus == "1" && doc.status == "UnPrinted") {
			return [__("UnPrinted"), "orange"];}
		else if (doc.docstatus == "1" && doc.status == "Printed") {
			return [__("Printed"), "green"];
		}
}};