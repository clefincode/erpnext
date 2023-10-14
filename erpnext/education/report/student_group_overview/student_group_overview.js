frappe.query_reports["Student Group Overview"] = {
	"filters": [
			{
				"fieldname":"company",
				"label": __("Company"),
				"fieldtype": "Link",
				"options": "Company",
				"default": frappe.defaults.get_user_default("Company"),
				"reqd": 1
			},
			{
				"fieldname":"academic_year",
				"label": __("Academic Year"),
				"fieldtype": "Link",
				"options": "Academic Year",
				"default": frappe.defaults.get_user_default("academic_year"),
				"reqd": 1,
				"on_change": function(query_report){
					var academic_year = query_report.get_values().academic_year;
					if(!academic_year){
						return;
					}
					frappe.model.with_doc("Academic Year", academic_year, function(r){
						var ay = frappe.model.get_doc("Academic Year", academic_year);
						frappe.query_report.set_filter_value({
							from_date: ay.year_start_date,
							to_date: ay.year_end_date
							});
				});
				}
			},
			{
				"fieldname":"program",
				"label": __("Program"),
				"fieldtype": "Link",
				"options": "Program"
			},
			{
				"fieldname":"status",
				"label": __("Status"),
				"fieldtype": "Select",
				"options": ["","Pending" , "Available", "Active", "Finished"]
			},
			{
				"fieldname":"from_date",
				"label": __("From"),
				"fieldtype": "Date",
				"default": frappe.defaults.get_user_default("year_start_date")
			},
			{
				"fieldname":"to_date",
				"label": __("To"),
				"fieldtype": "Date",
				"default": frappe.defaults.get_user_default("year_end_date")
			}
		],
		"onload": function(){
			var academic_year = frappe.defaults.get_user_default("academic_year")
			frappe.model.with_doc("Academic Year", academic_year, function(r){
						var ay = frappe.model.get_doc("Academic Year", academic_year);
						frappe.query_report.set_filter_value({
							from_date: ay.year_start_date,
							to_date: ay.year_end_date
							});
				});
		}
		}